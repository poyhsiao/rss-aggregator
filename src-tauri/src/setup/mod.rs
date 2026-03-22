mod config;
mod database;

pub use config::*;
pub use database::*;

use tauri::{AppHandle, Manager, Runtime};

pub fn setup_first_run_check<R: Runtime>(
    app: &AppHandle<R>,
) -> Result<(), Box<dyn std::error::Error>> {
    let app_data_dir = app.path().app_data_dir()?;
    let setup_done_marker = app_data_dir.join(".setup_done");

    if !setup_done_marker.exists() {
        std::fs::create_dir_all(&app_data_dir)?;

        let config = config::Config::default();
        config::save_config(&app_data_dir, &config)?;

        std::fs::write(&setup_done_marker, "")?;
    }

    Ok(())
}

pub fn is_first_run<R: Runtime>(app: &AppHandle<R>) -> Result<bool, Box<dyn std::error::Error>> {
    let app_data_dir = app.path().app_data_dir()?;
    let setup_done_marker = app_data_dir.join(".setup_done");
    Ok(!setup_done_marker.exists())
}
