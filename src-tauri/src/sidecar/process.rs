//! Sidecar process lifecycle management
//!
//! Manages spawning, monitoring, and shutting down the Python backend.

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter};
use thiserror::Error;

/// Errors that can occur during sidecar operations
#[derive(Error, Debug)]
pub enum SidecarError {
    #[error("Failed to spawn sidecar process: {0}")]
    SpawnFailed(String),

    #[error("Sidecar process is not running")]
    NotRunning,

    #[error("Sidecar process crashed")]
    Crashed,

    #[error("Failed to communicate with sidecar: {0}")]
    CommunicationFailed(String),

    #[error("JSON-RPC error: {0}")]
    JsonRpc(String),

    #[error("Timeout waiting for sidecar response")]
    Timeout,
}

/// JSON-RPC 2.0 request structure
#[derive(Serialize, Debug)]
pub struct JsonRpcRequest {
    pub jsonrpc: &'static str,
    pub method: String,
    pub params: RequestParams,
    pub id: u64,
}

/// JSON-RPC 2.0 request parameters
#[derive(Serialize, Debug)]
pub struct RequestParams {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub query: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub headers: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub body: Option<serde_json::Value>,
}

/// JSON-RPC 2.0 success response
#[derive(Deserialize, Debug)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    pub result: Option<ResponseResult>,
    pub error: Option<JsonRpcError>,
    pub id: u64,
}

/// JSON-RPC response result
#[derive(Deserialize, Debug)]
pub struct ResponseResult {
    pub status: u16,
    #[serde(default)]
    pub headers: Option<serde_json::Value>,
    pub body: Option<serde_json::Value>,
}

/// JSON-RPC error
#[derive(Deserialize, Debug)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
    #[serde(default)]
    pub data: Option<serde_json::Value>,
}

/// Sidecar process manager
///
/// Manages the lifecycle of the Python backend process, including
/// spawning, communication via JSON-RPC over stdio, and graceful shutdown.
pub struct SidecarManager {
    /// The child process
    process: Arc<Mutex<Option<Child>>>,
    /// stdin for writing JSON-RPC requests
    stdin: Arc<Mutex<Option<ChildStdin>>>,
    /// stdout reader
    stdout: Arc<Mutex<Option<BufReader<ChildStdout>>>>,
    /// Request ID counter
    request_id: AtomicU64,
    /// Running state
    running: AtomicBool,
    /// App handle for emitting events
    app_handle: AppHandle,
}

impl SidecarManager {
    /// Create a new sidecar manager
    pub fn new(app_handle: AppHandle) -> Self {
        Self {
            process: Arc::new(Mutex::new(None)),
            stdin: Arc::new(Mutex::new(None)),
            stdout: Arc::new(Mutex::new(None)),
            request_id: AtomicU64::new(1),
            running: AtomicBool::new(false),
            app_handle,
        }
    }

    /// Start the sidecar process
    pub fn start(&self) -> Result<(), SidecarError> {
        if self.running.load(Ordering::SeqCst) {
            log::info!("Sidecar already running");
            return Ok(());
        }

        log::info!("Getting sidecar path...");
        let sidecar_path = Self::get_sidecar_path()?;
        log::info!("Sidecar path: {}", sidecar_path);

        log::info!("Spawning sidecar process...");

        let data_dir = dirs::data_local_dir()
            .unwrap_or_else(|| std::path::PathBuf::from("."))
            .join("RSS Aggregator");

        log::info!("Data directory: {}", data_dir.display());

        // Ensure data directory exists
        if !data_dir.exists() {
            std::fs::create_dir_all(&data_dir).map_err(|e| {
                SidecarError::SpawnFailed(format!("Failed to create data directory: {}", e))
            })?;
            log::info!("Created data directory: {}", data_dir.display());
        }

        // Spawn the sidecar process (uses relative path ./rss.db from current_dir)
        let mut child = Command::new(&sidecar_path)
            .current_dir(&data_dir)
            .env("DATABASE_URL", "sqlite+aiosqlite:///./rss.db")
            .env("REQUIRE_API_KEY", "false")
            .env("SCHEDULER_ENABLED", "false")
            .env(
                "DEFAULT_SOURCES",
                "TechCrunch|https://techcrunch.com/feed/|1800,BBC News|https://feeds.bbci.co.uk/news/rss.xml|1800"
            )
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| {
                log::error!("Failed to spawn sidecar: {}", e);
                SidecarError::SpawnFailed(e.to_string())
            })?;

        log::info!("Sidecar process spawned, PID: {:?}", child.id());

        // Take stdin, stdout, and stderr
        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| SidecarError::SpawnFailed("Failed to open stdin".to_string()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| SidecarError::SpawnFailed("Failed to open stdout".to_string()))?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| SidecarError::SpawnFailed("Failed to open stderr".to_string()))?;

        // Spawn a thread to consume stderr to prevent blocking
        std::thread::spawn(move || {
            use std::io::BufRead;
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                match line {
                    Ok(l) => log::debug!("[sidecar stderr] {}", l),
                    Err(_) => break,
                }
            }
        });

        // Store handles
        *self.stdin.lock().unwrap() = Some(stdin);
        *self.stdout.lock().unwrap() = Some(BufReader::new(stdout));
        *self.process.lock().unwrap() = Some(child);

        self.running.store(true, Ordering::SeqCst);
        log::info!("Sidecar started successfully");

        // Emit event that sidecar started
        let _ = self.app_handle.emit("sidecar:started", ());

        Ok(())
    }

    /// Stop the sidecar process
    pub fn stop(&self) -> Result<(), SidecarError> {
        if !self.running.load(Ordering::SeqCst) {
            return Ok(());
        }

        // Clear stdin/stdout handles
        *self.stdin.lock().unwrap() = None;
        *self.stdout.lock().unwrap() = None;

        // Kill the process
        if let Some(mut process) = self.process.lock().unwrap().take() {
            let _ = process.kill();
            let _ = process.wait();
        }

        self.running.store(false, Ordering::SeqCst);

        // Emit event that sidecar stopped
        let _ = self.app_handle.emit("sidecar:stopped", ());

        Ok(())
    }

    /// Check if sidecar is running
    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    /// Restart the sidecar process
    pub fn restart(&self) -> Result<(), SidecarError> {
        self.stop()?;
        std::thread::sleep(Duration::from_millis(100));
        self.start()
    }

    /// Send a JSON-RPC request and wait for response
    pub fn send_request(
        &self,
        method: &str,
        query: Option<serde_json::Value>,
        headers: Option<serde_json::Value>,
        body: Option<serde_json::Value>,
    ) -> Result<JsonRpcResponse, SidecarError> {
        if !self.running.load(Ordering::SeqCst) {
            return Err(SidecarError::NotRunning);
        }

        let id = self.request_id.fetch_add(1, Ordering::SeqCst);

        let request = JsonRpcRequest {
            jsonrpc: "2.0",
            method: method.to_string(),
            params: RequestParams {
                query,
                headers,
                body,
            },
            id,
        };

        // Serialize request
        let request_json = serde_json::to_string(&request)
            .map_err(|e| SidecarError::CommunicationFailed(e.to_string()))?;

        log::info!("[JSON-RPC] Sending request: {}", request_json);

        // Write to stdin
        {
            let mut stdin = self.stdin.lock().unwrap();
            let stdin = stdin.as_mut().ok_or(SidecarError::NotRunning)?;

            writeln!(stdin, "{}", request_json)
                .map_err(|e| SidecarError::CommunicationFailed(e.to_string()))?;
            stdin
                .flush()
                .map_err(|e| SidecarError::CommunicationFailed(e.to_string()))?;
        }

        // Read response from stdout
        let response_json = {
            let mut stdout = self.stdout.lock().unwrap();
            let stdout = stdout.as_mut().ok_or(SidecarError::NotRunning)?;

            let mut line = String::new();
            let bytes_read = stdout
                .read_line(&mut line)
                .map_err(|e| SidecarError::CommunicationFailed(e.to_string()))?;

            log::info!("[JSON-RPC] Read {} bytes from stdout", bytes_read);
            log::info!("[JSON-RPC] Line content: {:?}", line);

            line
        };

        log::info!("[JSON-RPC] Received response: {}", response_json);

        // Parse response
        let response: JsonRpcResponse = serde_json::from_str(&response_json)
            .map_err(|e| SidecarError::CommunicationFailed(format!("{}: {}", e, response_json)))?;

        // Check for JSON-RPC error
        if let Some(error) = &response.error {
            log::error!("[JSON-RPC] Error: {:?}", error);
            let error_message = if let Some(data) = &error.data {
                if let Some(detail) = data.get("detail") {
                    format!("{}: {}", error.message, detail)
                } else {
                    error.message.clone()
                }
            } else {
                error.message.clone()
            };
            return Err(SidecarError::JsonRpc(error_message));
        }

        Ok(response)
    }

    /// Get the sidecar binary name with platform target for development
    fn get_sidecar_binary_name_with_target() -> String {
        #[cfg(target_os = "windows")]
        {
            "rss-sidecar-x86_64-pc-windows-msvc.exe".to_string()
        }
        #[cfg(all(target_os = "macos", target_arch = "x86_64"))]
        {
            "rss-sidecar-x86_64-apple-darwin".to_string()
        }
        #[cfg(all(target_os = "macos", target_arch = "aarch64"))]
        {
            "rss-sidecar-aarch64-apple-darwin".to_string()
        }
        #[cfg(target_os = "linux")]
        {
            "rss-sidecar-x86_64-unknown-linux-gnu".to_string()
        }
    }

    /// Get the sidecar binary name for production (without target suffix)
    fn get_sidecar_binary_name() -> String {
        #[cfg(target_os = "windows")]
        {
            "rss-sidecar.exe".to_string()
        }
        #[cfg(not(target_os = "windows"))]
        {
            "rss-sidecar".to_string()
        }
    }

    /// Get the absolute path to the sidecar binary
    fn get_sidecar_path() -> Result<String, SidecarError> {
        let exe_path = std::env::current_exe()
            .map_err(|e| SidecarError::SpawnFailed(format!("Failed to get exe path: {}", e)))?;
        log::info!("Current exe path: {}", exe_path.display());

        let exe_dir = exe_path
            .parent()
            .ok_or_else(|| SidecarError::SpawnFailed("Failed to get exe directory".to_string()))?
            .to_path_buf();
        log::info!("Exe directory: {}", exe_dir.display());

        // In production, sidecar is placed next to the app binary (without target suffix)
        let prod_name = Self::get_sidecar_binary_name();
        let prod_path = exe_dir.join(&prod_name);
        log::info!("Checking production path: {}", prod_path.display());

        if prod_path.exists() {
            log::info!("Found sidecar at production path");
            return Ok(prod_path.to_string_lossy().to_string());
        }

        // In development, sidecar is in binaries/ directory with target suffix
        let dev_name = Self::get_sidecar_binary_name_with_target();
        let dev_path = exe_dir.join("binaries").join(&dev_name);
        log::info!("Checking development path: {}", dev_path.display());

        if dev_path.exists() {
            log::info!("Found sidecar at development path");
            return Ok(dev_path.to_string_lossy().to_string());
        }

        log::error!("Sidecar not found at either path!");
        Err(SidecarError::SpawnFailed(format!(
            "Sidecar binary not found. Tried:\n  - {}\n  - {}",
            prod_path.display(),
            dev_path.display()
        )))
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_request_serialization() {
        let request = JsonRpcRequest {
            jsonrpc: "2.0",
            method: "GET /api/v1/feed".to_string(),
            params: RequestParams {
                query: Some(json!({"format": "json"})),
                headers: None,
                body: None,
            },
            id: 1,
        };

        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("\"jsonrpc\":\"2.0\""));
        assert!(json.contains("\"method\":\"GET /api/v1/feed\""));
        assert!(json.contains("\"id\":1"));
    }

    #[test]
    fn test_response_deserialization() {
        let json = r#"{"jsonrpc":"2.0","result":{"status":200,"body":{"items":[]}},"id":1}"#;
        let response: JsonRpcResponse = serde_json::from_str(json).unwrap();

        assert_eq!(response.jsonrpc, "2.0");
        assert_eq!(response.id, 1);
        assert!(response.result.is_some());
        let result = response.result.unwrap();
        assert_eq!(result.status, 200);
    }

    #[test]
    fn test_error_response_deserialization() {
        let json =
            r#"{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":1}"#;
        let response: JsonRpcResponse = serde_json::from_str(json).unwrap();

        assert!(response.error.is_some());
        let error = response.error.unwrap();
        assert_eq!(error.code, -32601);
        assert_eq!(error.message, "Method not found");
    }
}
