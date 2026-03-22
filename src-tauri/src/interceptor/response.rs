pub fn build_response(
    _http_response: crate::sidecar::HttpResponse,
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let body = _http_response
        .body
        .map(|v| serde_json::to_vec(&v).unwrap_or_default())
        .unwrap_or_default();
    Ok(body)
}

pub fn build_error_response(
    _status: u16,
    _message: &str,
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let body = serde_json::json!({
        "error": {
            "message": _message
        }
    });
    Ok(serde_json::to_vec(&body)?)
}
