//! Article preview fetching module
//!
//! Fetches article content from URLs and converts to markdown.
//! Uses markdown.new API or local processing.

use serde::{Deserialize, Serialize};
use std::time::Duration;

/// Preview content response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PreviewContent {
    pub url: String,
    pub url_hash: String,
    pub markdown_content: String,
    pub title: Option<String>,
}

/// Markdown.new API request
#[derive(Debug, Serialize)]
struct MarkdownNewRequest {
    url: String,
    retain_images: bool,
}

/// Markdown.new API response
#[derive(Debug, Deserialize)]
struct MarkdownNewResponse {
    success: bool,
    url: String,
    title: Option<String>,
    content: String,
    #[serde(default)]
    error: Option<String>,
}

/// Preview service error
#[derive(Debug, thiserror::Error)]
pub enum PreviewError {
    #[error("Network error: {0}")]
    Network(String),

    #[error("API error: {0}")]
    Api(String),

    #[error("Timeout error")]
    Timeout,

    #[error("Invalid URL: {0}")]
    InvalidUrl(String),
}

/// Compute SHA256 hash of URL
pub fn compute_url_hash(url: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(url.as_bytes());
    format!("{:x}", hasher.finalize())
}

/// Fetch article preview from markdown.new API
pub async fn fetch_preview(url: &str) -> Result<PreviewContent, PreviewError> {
    log::info!("[PREVIEW-MODULE] Starting fetch for URL: {}", url);

    // Validate URL
    if url.is_empty() {
        return Err(PreviewError::InvalidUrl("URL is empty".to_string()));
    }

    let url_hash = compute_url_hash(url);
    log::info!("[PREVIEW-MODULE] URL hash: {}", url_hash);

    // Try markdown.new API
    log::info!("[PREVIEW-MODULE] Creating HTTP client...");
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .map_err(|e| {
            log::error!("[PREVIEW-MODULE] Failed to create HTTP client: {}", e);
            PreviewError::Network(e.to_string())
        })?;

    let request = MarkdownNewRequest {
        url: url.to_string(),
        retain_images: true,
    };

    log::info!("[PREVIEW-MODULE] Sending request to markdown.new API...");
    let response = client
        .post("https://markdown.new/")
        .json(&request)
        .header("Content-Type", "application/json")
        .header("User-Agent", "RSS-Aggregator/1.0")
        .send()
        .await
        .map_err(|e| {
            log::error!("[PREVIEW-MODULE] HTTP request failed: {}", e);
            if e.is_timeout() {
                PreviewError::Timeout
            } else {
                PreviewError::Network(e.to_string())
            }
        })?;

    log::info!("[PREVIEW-MODULE] Response status: {}", response.status());

    if !response.status().is_success() {
        return Err(PreviewError::Api(format!(
            "HTTP error: {}",
            response.status()
        )));
    }

    log::info!("[PREVIEW-MODULE] Parsing JSON response...");
    let data: MarkdownNewResponse = response
        .json()
        .await
        .map_err(|e| {
            log::error!("[PREVIEW-MODULE] Failed to parse JSON: {}", e);
            PreviewError::Api(format!("Failed to parse response: {}", e))
        })?;

    if !data.success {
        log::error!("[PREVIEW-MODULE] API returned success=false: {:?}", data.error);
        return Err(PreviewError::Api(
            data.error.unwrap_or_else(|| "Unknown error".to_string()),
        ));
    }

    log::info!("[PREVIEW-MODULE] Successfully fetched preview, content length: {}", data.content.len());
    Ok(PreviewContent {
        url: url.to_string(),
        url_hash,
        markdown_content: data.content,
        title: data.title,
    })
}

/// Extract title from markdown content
pub fn extract_title(markdown: &str) -> Option<String> {
    // Try to find frontmatter title
    if let Some(start) = markdown.find("---") {
        if let Some(end) = markdown[start + 3..].find("---") {
            let frontmatter = &markdown[start + 3..start + 3 + end];
            for line in frontmatter.lines() {
                if let Some(title) = line.strip_prefix("title:") {
                    let title = title.trim().trim_matches('"').trim_matches('\'');
                    return Some(title.to_string());
                }
            }
        }
    }

    // Try to find first H1
    for line in markdown.lines() {
        if let Some(title) = line.strip_prefix("# ") {
            return Some(title.trim().to_string());
        }
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_url_hash() {
        let hash = compute_url_hash("https://example.com/article");
        assert_eq!(hash.len(), 64); // SHA256 hex string
    }

    #[test]
    fn test_extract_title_from_frontmatter() {
        let markdown = r#"---
title: "Test Article"
date: 2024-01-01
---

# Body Title

Content here.
"#;
        let title = extract_title(markdown);
        assert_eq!(title, Some("Test Article".to_string()));
    }

    #[test]
    fn test_extract_title_from_h1() {
        let markdown = r#"# Article Title

Content here.
"#;
        let title = extract_title(markdown);
        assert_eq!(title, Some("Article Title".to_string()));
    }

    #[test]
    fn test_extract_title_none() {
        let markdown = "Just some content without a title";
        let title = extract_title(markdown);
        assert_eq!(title, None);
    }
}
