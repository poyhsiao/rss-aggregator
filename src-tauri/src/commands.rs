use std::fs;
use std::path::PathBuf;
use std::sync::Arc;

use serde::{Deserialize, Serialize};
use tauri::{command, AppHandle, Manager};

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
    
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&data_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }
    
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(&data_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }
    
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&data_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
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