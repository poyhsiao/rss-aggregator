//! Protocol interceptor for app://localhost requests

use std::collections::HashMap;
use std::sync::Arc;

use http::{Request, Response, StatusCode};
use tauri::{AppHandle, Manager, Runtime, UriSchemeContext, UriSchemeResponder};
use urlencoding::decode;

use crate::sidecar::{JsonRpcClient, SidecarManager};

pub fn setup_protocol_interceptor<R: Runtime>(
    _app: &AppHandle<R>,
) -> Result<(), Box<dyn std::error::Error>> {
    Ok(())
}

pub fn handle_request<R: Runtime>(
    context: UriSchemeContext<'_, R>,
    request: Request<Vec<u8>>,
    responder: UriSchemeResponder,
) {
    let app_handle = context.app_handle();

    if request.method() == "OPTIONS" {
        let response = Response::builder()
            .status(StatusCode::OK)
            .header("Access-Control-Allow-Origin", "*")
            .header(
                "Access-Control-Allow-Methods",
                "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            )
            .header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
            .header("Access-Control-Max-Age", "86400")
            .body(Vec::new())
            .unwrap();
        responder.respond(response);
        return;
    }

    let manager = match app_handle.try_state::<Arc<SidecarManager>>() {
        Some(m) => m.inner().clone(),
        None => {
            respond_with_error(
                responder,
                StatusCode::INTERNAL_SERVER_ERROR,
                "Sidecar manager not found",
            );
            return;
        }
    };

    if !manager.is_running() {
        respond_with_error(
            responder,
            StatusCode::SERVICE_UNAVAILABLE,
            "Backend service not running",
        );
        return;
    }

    let parsed = match parse_request(&request) {
        Ok(p) => p,
        Err(e) => {
            respond_with_error(responder, StatusCode::BAD_REQUEST, &e);
            return;
        }
    };

    let client = JsonRpcClient::new(manager);

    let headers_json = if parsed.headers.is_empty() {
        None
    } else {
        Some(serde_json::to_value(&parsed.headers).unwrap_or(serde_json::Value::Null))
    };

    let query_json = if parsed.query.is_empty() {
        None
    } else {
        Some(serde_json::to_value(&parsed.query).unwrap_or(serde_json::Value::Null))
    };

    let body_json = if parsed.body.is_empty() {
        None
    } else {
        serde_json::from_slice(&parsed.body).ok()
    };

    let method = match parsed.method.as_str() {
        "GET" => crate::sidecar::HttpMethod::Get,
        "POST" => crate::sidecar::HttpMethod::Post,
        "PUT" => crate::sidecar::HttpMethod::Put,
        "DELETE" => crate::sidecar::HttpMethod::Delete,
        "PATCH" => crate::sidecar::HttpMethod::Patch,
        _ => {
            respond_with_error(
                responder,
                StatusCode::METHOD_NOT_ALLOWED,
                "Method not allowed",
            );
            return;
        }
    };

    match client.request(method, &parsed.path, query_json, headers_json, body_json) {
        Ok(response) => build_http_response(responder, response),
        Err(e) => {
            let error_msg = format!("Backend error: {}", e);
            respond_with_error(responder, StatusCode::INTERNAL_SERVER_ERROR, &error_msg);
        }
    }
}

struct ParsedRequest {
    method: String,
    path: String,
    query: HashMap<String, String>,
    headers: HashMap<String, String>,
    body: Vec<u8>,
}

fn parse_request(request: &Request<Vec<u8>>) -> Result<ParsedRequest, String> {
    let uri = request.uri();
    let (path, query) = parse_uri(uri.path(), uri.query());

    let mut headers = HashMap::new();
    for (name, value) in request.headers() {
        if let Ok(v) = value.to_str() {
            headers.insert(name.to_string(), v.to_string());
        }
    }

    let body = request.body().clone();
    let method = request.method().to_string();

    Ok(ParsedRequest {
        method,
        path,
        query,
        headers,
        body,
    })
}

fn parse_uri(path: &str, query: Option<&str>) -> (String, HashMap<String, String>) {
    let path = if path.starts_with('/') {
        path.to_string()
    } else {
        format!("/{}", path)
    };

    let mut query_params = HashMap::new();
    if let Some(q) = query {
        for pair in q.split('&') {
            if let Some((key, value)) = pair.split_once('=') {
                let decoded_key = decode(key)
                    .map(|s| s.into_owned())
                    .unwrap_or_else(|_| key.to_string());
                let decoded_value = decode(value)
                    .map(|s| s.into_owned())
                    .unwrap_or_else(|_| value.to_string());
                query_params.insert(decoded_key, decoded_value);
            } else if !pair.is_empty() {
                let decoded_key = decode(pair)
                    .map(|s| s.into_owned())
                    .unwrap_or_else(|_| pair.to_string());
                query_params.insert(decoded_key, String::new());
            }
        }
    }

    (path, query_params)
}

/// Check if content type is JSON
fn is_json_content_type(content_type: Option<&str>) -> bool {
    match content_type {
        Some(ct) => {
            let ct_lower = ct.to_lowercase();
            ct_lower.contains("application/json") || ct_lower.ends_with("+json")
        }
        None => false,
    }
}

/// Check if content type is text-based (should be returned as raw string)
fn is_text_content_type(content_type: Option<&str>) -> bool {
    match content_type {
        Some(ct) => {
            let ct_lower = ct.to_lowercase();
            ct_lower.starts_with("text/")
                || ct_lower.contains("application/xml")
                || ct_lower.contains("text/xml")
                || ct_lower.contains("text/markdown")
                || ct_lower.contains("text/plain")
        }
        None => false,
    }
}

/// Extract content type from response headers
fn get_content_type(headers: &Option<serde_json::Value>) -> Option<String> {
    headers.as_ref().and_then(|h| {
        if let serde_json::Value::Object(map) = h {
            for (key, value) in map {
                if key.to_lowercase() == "content-type" {
                    if let Some(v) = value.as_str() {
                        return Some(v.to_string());
                    }
                }
            }
        }
        None
    })
}

fn build_http_response(responder: UriSchemeResponder, response: crate::sidecar::HttpResponse) {
    let content_type = get_content_type(&response.headers);
    let content_type_str = content_type.as_deref();

    let mut builder = Response::builder()
        .status(StatusCode::from_u16(response.status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR))
        .header("Access-Control-Allow-Origin", "*")
        .header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        )
        .header("Access-Control-Allow-Headers", "Content-Type, X-API-Key");

    if let Some(ref headers) = response.headers {
        if let serde_json::Value::Object(map) = headers {
            for (key, value) in map {
                if let Some(v) = value.as_str() {
                    builder = builder.header(key, v);
                }
            }
        }
    }

    // Determine how to serialize the body based on content type
    let body_data = match &response.body {
        Some(body_value) => {
            if is_json_content_type(content_type_str) {
                // JSON content - serialize as JSON
                serde_json::to_vec(body_value).unwrap_or_default()
            } else if is_text_content_type(content_type_str) {
                // Text content (RSS, Markdown, etc.) - extract as raw string
                match body_value {
                    serde_json::Value::String(s) => s.as_bytes().to_vec(),
                    _ => {
                        // If it's not a string, try to convert it
                        match body_value.as_str() {
                            Some(s) => s.as_bytes().to_vec(),
                            None => serde_json::to_vec(body_value).unwrap_or_default(),
                        }
                    }
                }
            } else {
                // Default: treat as JSON if no content type or unknown type
                serde_json::to_vec(body_value).unwrap_or_default()
            }
        }
        None => Vec::new(),
    };

    // Set default content type if not present
    let has_content_type = response.headers.as_ref().map_or(false, |h| {
        matches!(h, serde_json::Value::Object(map) if map.keys().any(|k| k.to_lowercase() == "content-type"))
    });

    if !has_content_type {
        builder = builder.header("Content-Type", "application/json");
    }

    match builder.body(body_data) {
        Ok(http_response) => responder.respond(http_response),
        Err(_) => {
            respond_with_error(
                responder,
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to build response",
            );
        }
    }
}

fn respond_with_error(responder: UriSchemeResponder, status: StatusCode, message: &str) {
    let body = serde_json::json!({
        "error": message,
        "status": status.as_u16()
    });

    let response = Response::builder()
        .status(status)
        .header("Content-Type", "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        )
        .header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        .body(serde_json::to_vec(&body).unwrap_or_default())
        .unwrap();

    responder.respond(response);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_uri() {
        let (path, query) = parse_uri("/api/v1/feed", Some("format=json&sort_by=published_at"));
        assert_eq!(path, "/api/v1/feed");
        assert_eq!(query.get("format"), Some(&"json".to_string()));
        assert_eq!(query.get("sort_by"), Some(&"published_at".to_string()));
    }

    #[test]
    fn test_parse_uri_no_query() {
        let (path, query) = parse_uri("/api/v1/sources", None);
        assert_eq!(path, "/api/v1/sources");
        assert!(query.is_empty());
    }

    #[test]
    fn test_parse_uri_encoded() {
        let (path, query) = parse_uri("/api/v1/feed", Some("keywords=test%20space"));
        assert_eq!(path, "/api/v1/feed");
        assert_eq!(query.get("keywords"), Some(&"test space".to_string()));
    }

    #[test]
    fn test_is_json_content_type() {
        assert!(is_json_content_type(Some("application/json")));
        assert!(is_json_content_type(Some(
            "application/json; charset=utf-8"
        )));
        assert!(is_json_content_type(Some("application/ld+json")));
        assert!(!is_json_content_type(Some("text/plain")));
        assert!(!is_json_content_type(Some("application/xml")));
        assert!(!is_json_content_type(None));
    }

    #[test]
    fn test_is_text_content_type() {
        assert!(is_text_content_type(Some("text/plain")));
        assert!(is_text_content_type(Some("text/markdown")));
        assert!(is_text_content_type(Some("application/xml")));
        assert!(is_text_content_type(Some("text/xml")));
        assert!(!is_text_content_type(Some("application/json")));
        assert!(!is_text_content_type(None));
    }
}
