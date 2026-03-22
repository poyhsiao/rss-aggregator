//! JSON-RPC client for communicating with the Python sidecar
//!
//! Provides high-level HTTP-like API that internally uses JSON-RPC.

use serde_json::json;

use super::process::{SidecarError, SidecarManager};

/// HTTP method types
#[derive(Debug, Clone, Copy)]
pub enum HttpMethod {
    Get,
    Post,
    Put,
    Delete,
    Patch,
}

impl HttpMethod {
    pub fn as_str(&self) -> &'static str {
        match self {
            HttpMethod::Get => "GET",
            HttpMethod::Post => "POST",
            HttpMethod::Put => "PUT",
            HttpMethod::Delete => "DELETE",
            HttpMethod::Patch => "PATCH",
        }
    }
}

impl std::fmt::Display for HttpMethod {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

/// HTTP response wrapper
#[derive(Debug)]
pub struct HttpResponse {
    pub status: u16,
    pub headers: Option<serde_json::Value>,
    pub body: Option<serde_json::Value>,
}

impl HttpResponse {
    /// Check if response is successful (2xx status)
    pub fn is_success(&self) -> bool {
        self.status >= 200 && self.status < 300
    }

    /// Get body as a specific type
    pub fn body_as<T: for<'de> serde::Deserialize<'de>>(
        &self,
    ) -> Result<Option<T>, serde_json::Error> {
        match &self.body {
            Some(value) => Ok(Some(serde_json::from_value(value.clone())?)),
            None => Ok(None),
        }
    }
}

/// JSON-RPC client for the sidecar
///
/// Provides a simple HTTP-like interface that internally uses JSON-RPC
/// to communicate with the Python backend.
pub struct JsonRpcClient {
    manager: std::sync::Arc<SidecarManager>,
}

impl JsonRpcClient {
    /// Create a new client
    pub fn new(manager: std::sync::Arc<SidecarManager>) -> Self {
        Self { manager }
    }

    /// Send an HTTP-like request through JSON-RPC
    pub fn request(
        &self,
        method: HttpMethod,
        path: &str,
        query: Option<serde_json::Value>,
        headers: Option<serde_json::Value>,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        let rpc_method = format!("{} {}", method, path);

        let response = self
            .manager
            .send_request(&rpc_method, query, headers, body)?;

        Ok(HttpResponse {
            status: response.result.as_ref().map(|r| r.status).unwrap_or(500),
            headers: response.result.as_ref().and_then(|r| r.headers.clone()),
            body: response.result.and_then(|r| r.body),
        })
    }

    /// Convenience method for GET requests
    pub fn get(
        &self,
        path: &str,
        query: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request(HttpMethod::Get, path, query, None, None)
    }

    /// Convenience method for POST requests
    pub fn post(
        &self,
        path: &str,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request(HttpMethod::Post, path, None, None, body)
    }

    /// Convenience method for PUT requests
    pub fn put(
        &self,
        path: &str,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request(HttpMethod::Put, path, None, None, body)
    }

    /// Convenience method for DELETE requests
    pub fn delete(&self, path: &str) -> Result<HttpResponse, SidecarError> {
        self.request(HttpMethod::Delete, path, None, None, None)
    }

    /// Convenience method for PATCH requests
    pub fn patch(
        &self,
        path: &str,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request(HttpMethod::Patch, path, None, None, body)
    }

    /// Make a request with API key authentication
    pub fn request_with_auth(
        &self,
        method: HttpMethod,
        path: &str,
        api_key: &str,
        query: Option<serde_json::Value>,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        let headers = json!({
            "X-API-Key": api_key
        });

        self.request(method, path, query, Some(headers), body)
    }

    /// GET with authentication
    pub fn get_with_auth(
        &self,
        path: &str,
        api_key: &str,
        query: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request_with_auth(HttpMethod::Get, path, api_key, query, None)
    }

    /// POST with authentication
    pub fn post_with_auth(
        &self,
        path: &str,
        api_key: &str,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request_with_auth(HttpMethod::Post, path, api_key, None, body)
    }

    /// PUT with authentication
    pub fn put_with_auth(
        &self,
        path: &str,
        api_key: &str,
        body: Option<serde_json::Value>,
    ) -> Result<HttpResponse, SidecarError> {
        self.request_with_auth(HttpMethod::Put, path, api_key, None, body)
    }

    /// DELETE with authentication
    pub fn delete_with_auth(
        &self,
        path: &str,
        api_key: &str,
    ) -> Result<HttpResponse, SidecarError> {
        self.request_with_auth(HttpMethod::Delete, path, api_key, None, None)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_http_method_display() {
        assert_eq!(format!("{}", HttpMethod::Get), "GET");
        assert_eq!(format!("{}", HttpMethod::Post), "POST");
        assert_eq!(format!("{}", HttpMethod::Put), "PUT");
        assert_eq!(format!("{}", HttpMethod::Delete), "DELETE");
        assert_eq!(format!("{}", HttpMethod::Patch), "PATCH");
    }

    #[test]
    fn test_http_response_is_success() {
        let response = HttpResponse {
            status: 200,
            headers: None,
            body: None,
        };
        assert!(response.is_success());

        let response = HttpResponse {
            status: 404,
            headers: None,
            body: None,
        };
        assert!(!response.is_success());
    }
}
