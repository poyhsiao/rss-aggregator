use std::fs;
use std::path::PathBuf;
use std::sync::Arc;

use serde::{Deserialize, Serialize};
use tauri::{command, AppHandle, Manager};
use tauri_plugin_dialog::DialogExt;

use crate::preview::{self, PreviewContent};
use crate::setup::{self, Config};
use crate::sidecar::SidecarManager;

/// Configuration for setup wizard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SetupConfig {
    pub timezone: String,
    pub language: String,
}

#[command]
pub async fn is_first_run(app: AppHandle) -> Result<bool, String> {
    setup::is_first_run(&app).map_err(|e| e.to_string())
}

#[command]
pub async fn get_setup_config(app: AppHandle) -> Result<Config, String> {
    let data_dir = get_data_path_internal(&app)?;
    setup::load_config(&data_dir).map_err(|e| e.to_string())
}

#[command]
pub async fn save_setup_config(app: AppHandle, config: SetupConfig) -> Result<(), String> {
    let data_dir = get_data_path_internal(&app)?;
    let mut current_config = setup::load_config(&data_dir).map_err(|e| e.to_string())?;
    
    current_config.timezone = config.timezone;
    current_config.language = config.language;
    
    setup::save_config(&data_dir, &current_config).map_err(|e| e.to_string())
}

#[command]
pub async fn complete_setup(app: AppHandle) -> Result<(), String> {
    let data_dir = get_data_path_internal(&app)?;
    let mut config = setup::load_config(&data_dir).map_err(|e| e.to_string())?;
    
    config.setup_completed_at = Some(chrono::Local::now().to_rfc3339());
    setup::save_config(&data_dir, &config).map_err(|e| e.to_string())?;
    
    let setup_done = data_dir.join(".setup_done");
    fs::write(&setup_done, "").map_err(|e| e.to_string())?;
    
    Ok(())
}

#[command]
pub async fn open_data_folder(app: AppHandle) -> Result<(), String> {
    let data_path = get_data_path_internal(&app)?;
    
    if !data_path.exists() {
        fs::create_dir_all(&data_path)
            .map_err(|e| format!("Failed to create data folder: {}", e))?;
    }
    
    #[cfg(target_os = "macos")]
    {
        let status = std::process::Command::new("open")
            .arg(&data_path)
            .status()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
        
        if !status.success() {
            return Err(format!("Failed to open folder: exit code {:?}", status.code()));
        }
    }
    
    #[cfg(target_os = "windows")]
    {
        let status = std::process::Command::new("explorer")
            .arg(&data_path)
            .status()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
        
        if !status.success() {
            return Err(format!("Failed to open folder: exit code {:?}", status.code()));
        }
    }
    
    #[cfg(target_os = "linux")]
    {
        let status = std::process::Command::new("xdg-open")
            .arg(&data_path)
            .status()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
        
        if !status.success() {
            return Err(format!("Failed to open folder: exit code {:?}", status.code()));
        }
    }
    
    Ok(())
}

#[command]
pub async fn export_data(app: AppHandle) -> Result<String, String> {
    let data_path = get_data_path_internal(&app)?;
    Ok(data_path.to_string_lossy().to_string())
}

#[command]
pub async fn import_data(app: AppHandle, source_path: String) -> Result<(), String> {
    let data_path = get_data_path_internal(&app)?;
    let db_path = data_path.join("rss.db");
    
    let source = PathBuf::from(&source_path);
    if !source.exists() {
        return Err("Source file does not exist".to_string());
    }
    
    fs::copy(&source, &db_path)
        .map_err(|e| format!("Failed to import data: {}", e))?;
    
    Ok(())
}

#[command]
pub async fn restart_backend(app: AppHandle) -> Result<(), String> {
    let manager = app
        .state::<Arc<SidecarManager>>()
        .inner()
        .clone();
    
    manager.restart()
        .map_err(|e| format!("Failed to restart backend: {}", e))?;
    
    Ok(())
}

#[command]
pub fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[command]
pub fn get_data_path(app: AppHandle) -> Result<String, String> {
    let path = get_data_path_internal(&app)?;
    Ok(path.to_string_lossy().to_string())
}

fn get_data_path_internal(_app: &AppHandle) -> Result<PathBuf, String> {
    let exe_dir = std::env::current_exe()
        .map_err(|e| format!("Failed to get exe path: {}", e))?
        .parent()
        .ok_or("Failed to get exe directory")?
        .to_path_buf();
    
    Ok(exe_dir.join("data"))
}

#[command]
pub fn toggle_devtools(app: AppHandle) -> Result<bool, String> {
    if let Some(window) = app.get_webview_window("main") {
        if window.is_devtools_open() {
            window.close_devtools();
            Ok(false)
        } else {
            window.open_devtools();
            Ok(true)
        }
    } else {
        Err("Could not get main window".to_string())
    }
}

/// Fetch article preview content from markdown.new API
/// This bypasses the sidecar and fetches directly from external API
#[command]
pub async fn fetch_preview(url: String) -> Result<PreviewContent, String> {
    log::info!("[COMMAND] fetch_preview called with URL: {}", url);
    
    preview::fetch_preview(&url)
        .await
        .map_err(|e| {
            log::error!("[COMMAND] fetch_preview failed: {}", e);
            e.to_string()
        })
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportOptions {
    pub include_feed_items: Option<bool>,
    pub include_preview_contents: Option<bool>,
    pub include_logs: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupCounts {
    pub sources: i32,
    pub feed_items: i32,
    pub api_keys: i32,
    pub preview_contents: i32,
    pub fetch_batches: i32,
    pub fetch_logs: i32,
    pub stats: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupConfig {
    pub timezone: String,
    pub language: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupPreview {
    pub version: String,
    pub exported_at: String,
    pub counts: BackupCounts,
    pub config: BackupConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportSummary {
    pub sources_imported: i32,
    pub sources_merged: i32,
    pub feed_items_imported: i32,
    pub api_keys_imported: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportResult {
    pub success: bool,
    pub message: String,
    pub summary: Option<ImportSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportBackupResult {
    pub filename: String,
}

/// Export database to encrypted ZIP backup file
#[command]
pub async fn export_backup(
    app: AppHandle,
    options: Option<ExportOptions>,
) -> Result<ExportBackupResult, String> {
    log::info!("[COMMAND] export_backup called");

    let file_path = app
        .dialog()
        .file()
        .add_filter("ZIP", &["zip"])
        .set_title("Save Backup File")
        .blocking_save_file();

    let file_path = match file_path {
        Some(path) => path.into_path().map_err(|e| format!("Invalid path: {}", e))?,
        None => return Err("No file selected".to_string()),
    };

    let path_str = file_path.to_string_lossy().to_string();
    log::info!("[COMMAND] Selected save path: {}", path_str);

    let manager = app
        .state::<Arc<SidecarManager>>()
        .inner()
        .clone();

    let client = crate::sidecar::JsonRpcClient::new(manager);

    let body = options.map(|o| {
        serde_json::json!({
            "include_feed_items": o.include_feed_items.unwrap_or(true),
            "include_preview_contents": o.include_preview_contents.unwrap_or(true),
            "include_logs": o.include_logs.unwrap_or(false),
        })
    });

    let response = client
        .post("/api/v1/backup/export", body)
        .map_err(|e| format!("Failed to call backend: {}", e))?;

    if !response.is_success() {
        let error = response
            .body
            .and_then(|b| b.get("detail").and_then(|d| d.as_str().map(|s| s.to_string())))
            .unwrap_or_else(|| format!("HTTP {}", response.status));
        return Err(format!("Export failed: {}", error));
    }

    let body = response.body.ok_or("No response body")?;
    let data = body
        .get("data")
        .and_then(|d| d.as_str())
        .ok_or("No data in response")?;
    let filename = body
        .get("filename")
        .and_then(|f| f.as_str())
        .unwrap_or("backup.zip");

    let zip_data = base64::Engine::decode(&base64::engine::general_purpose::STANDARD, data)
        .map_err(|e| format!("Failed to decode base64: {}", e))?;

    fs::write(&file_path, &zip_data).map_err(|e| format!("Failed to write file: {}", e))?;

    log::info!("[COMMAND] Backup saved to: {}", path_str);

    Ok(ExportBackupResult {
        filename: filename.to_string(),
    })
}

/// Import database from encrypted ZIP backup file
#[command]
pub async fn import_backup(app: AppHandle) -> Result<ImportResult, String> {
    log::info!("[COMMAND] import_backup called");

    let file_path = app
        .dialog()
        .file()
        .add_filter("ZIP", &["zip"])
        .set_title("Select Backup File")
        .blocking_pick_file();

    let file_path = match file_path {
        Some(path) => path.into_path().map_err(|e| format!("Invalid path: {}", e))?,
        None => return Err("No file selected".to_string()),
    };

    log::info!("[COMMAND] Selected file: {}", file_path.display());

    let zip_data = fs::read(&file_path).map_err(|e| format!("Failed to read file: {}", e))?;
    let zip_base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &zip_data);

    let manager = app
        .state::<Arc<SidecarManager>>()
        .inner()
        .clone();

    let client = crate::sidecar::JsonRpcClient::new(manager);

    let body = serde_json::json!({ "data": zip_base64 });

    let response = client
        .post("/api/v1/backup/import", Some(body))
        .map_err(|e| format!("Failed to call backend: {}", e))?;

    if !response.is_success() {
        let error = response
            .body
            .and_then(|b| b.get("detail").and_then(|d| d.as_str().map(|s| s.to_string())))
            .unwrap_or_else(|| format!("HTTP {}", response.status));
        return Err(format!("Import failed: {}", error));
    }

    let body = response.body.ok_or("No response body")?;

    let result = ImportResult {
        success: body.get("success").and_then(|s| s.as_bool()).unwrap_or(false),
        message: body
            .get("message")
            .and_then(|m| m.as_str())
            .unwrap_or("")
            .to_string(),
        summary: body.get("summary").and_then(|s| {
            if s.is_null() {
                None
            } else {
                Some(ImportSummary {
                    sources_imported: s.get("sources_imported")?.as_i64()? as i32,
                    sources_merged: s.get("sources_merged")?.as_i64()? as i32,
                    feed_items_imported: s.get("feed_items_imported")?.as_i64()? as i32,
                    api_keys_imported: s.get("api_keys_imported")?.as_i64()? as i32,
                })
            }
        }),
    };

    log::info!("[COMMAND] Import result: success={}", result.success);

    Ok(result)
}

/// Preview backup file content without importing
#[command]
pub async fn preview_backup(app: AppHandle) -> Result<Option<(String, BackupPreview)>, String> {
    log::info!("[COMMAND] preview_backup called");

    let file_path = app
        .dialog()
        .file()
        .add_filter("ZIP", &["zip"])
        .set_title("Select Backup File to Preview")
        .blocking_pick_file();

    let file_path = match file_path {
        Some(path) => match path.into_path() {
            Ok(p) => p,
            Err(_) => return Ok(None),
        },
        None => return Ok(None),
    };

    let path_str = file_path.to_string_lossy().to_string();
    log::info!("[COMMAND] Selected file for preview: {}", path_str);

    let zip_data = fs::read(&file_path).map_err(|e| format!("Failed to read file: {}", e))?;
    let zip_base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &zip_data);

    let manager = app
        .state::<Arc<SidecarManager>>()
        .inner()
        .clone();

    let client = crate::sidecar::JsonRpcClient::new(manager);

    let body = serde_json::json!({ "data": zip_base64 });

    let response = client
        .post("/api/v1/backup/preview", Some(body))
        .map_err(|e| format!("Failed to call backend: {}", e))?;

    if !response.is_success() {
        let error = response
            .body
            .and_then(|b| b.get("detail").and_then(|d| d.as_str().map(|s| s.to_string())))
            .unwrap_or_else(|| format!("HTTP {}", response.status));
        return Err(format!("Preview failed: {}", error));
    }

    let body = response.body.ok_or("No response body")?;

    let preview = BackupPreview {
        version: body
            .get("version")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string(),
        exported_at: body
            .get("exported_at")
            .and_then(|e| e.as_str())
            .unwrap_or("")
            .to_string(),
        counts: BackupCounts {
            sources: body
                .get("counts")
                .and_then(|c| c.get("sources"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
            feed_items: body
                .get("counts")
                .and_then(|c| c.get("feed_items"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
            api_keys: body
                .get("counts")
                .and_then(|c| c.get("api_keys"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
            preview_contents: body
                .get("counts")
                .and_then(|c| c.get("preview_contents"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
            fetch_batches: body
                .get("counts")
                .and_then(|c| c.get("fetch_batches"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
            fetch_logs: body
                .get("counts")
                .and_then(|c| c.get("fetch_logs"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
            stats: body
                .get("counts")
                .and_then(|c| c.get("stats"))
                .and_then(|s| s.as_i64())
                .unwrap_or(0) as i32,
        },
        config: BackupConfig {
            timezone: body
                .get("config")
                .and_then(|c| c.get("timezone"))
                .and_then(|t| t.as_str())
                .unwrap_or("UTC")
                .to_string(),
            language: body
                .get("config")
                .and_then(|c| c.get("language"))
                .and_then(|l| l.as_str())
                .unwrap_or("en")
                .to_string(),
        },
    };

    log::info!("[COMMAND] Preview successful for version: {}", preview.version);

    Ok(Some((path_str, preview)))
}

/// Import backup from a specific file path (used after preview)
#[command]
pub async fn import_backup_with_path(app: AppHandle, file_path: String) -> Result<ImportResult, String> {
    log::info!("[COMMAND] import_backup_with_path called with: {}", file_path);

    let file_path = PathBuf::from(&file_path);
    
    if !file_path.exists() {
        return Err("File does not exist".to_string());
    }

    let zip_data = fs::read(&file_path).map_err(|e| format!("Failed to read file: {}", e))?;
    let zip_base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &zip_data);

    let manager = app
        .state::<Arc<SidecarManager>>()
        .inner()
        .clone();

    let client = crate::sidecar::JsonRpcClient::new(manager);

    let body = serde_json::json!({ "data": zip_base64 });

    let response = client
        .post("/api/v1/backup/import", Some(body))
        .map_err(|e| format!("Failed to call backend: {}", e))?;

    if !response.is_success() {
        let error = response
            .body
            .and_then(|b| b.get("detail").and_then(|d| d.as_str().map(|s| s.to_string())))
            .unwrap_or_else(|| format!("HTTP {}", response.status));
        return Err(format!("Import failed: {}", error));
    }

    let body = response.body.ok_or("No response body")?;

    let result = ImportResult {
        success: body.get("success").and_then(|s| s.as_bool()).unwrap_or(false),
        message: body
            .get("message")
            .and_then(|m| m.as_str())
            .unwrap_or("")
            .to_string(),
        summary: body.get("summary").and_then(|s| {
            if s.is_null() {
                None
            } else {
                Some(ImportSummary {
                    sources_imported: s.get("sources_imported")?.as_i64()? as i32,
                    sources_merged: s.get("sources_merged")?.as_i64()? as i32,
                    feed_items_imported: s.get("feed_items_imported")?.as_i64()? as i32,
                    api_keys_imported: s.get("api_keys_imported")?.as_i64()? as i32,
                })
            }
        }),
    };

    log::info!("[COMMAND] Import result: success={}", result.success);

    Ok(result)
}