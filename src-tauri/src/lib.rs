use std::sync::Arc;
use tauri::Manager;

mod commands;
mod interceptor;
mod setup;
mod sidecar;
mod utils;

pub use commands::{open_data_folder, export_data, import_data, restart_backend, get_app_version, get_data_path, is_first_run, get_setup_config, save_setup_config, complete_setup, SetupConfig, toggle_devtools};
pub use interceptor::*;
pub use setup::{Config, setup_first_run_check};
pub use sidecar::*;
pub use utils::*;

pub fn run() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();
    
    log::info!("Starting RSS Aggregator Desktop...");

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .register_asynchronous_uri_scheme_protocol("app", interceptor::handle_request)
        .invoke_handler(tauri::generate_handler![
            commands::open_data_folder,
            commands::export_data,
            commands::import_data,
            commands::restart_backend,
            commands::get_app_version,
            commands::get_data_path,
            commands::is_first_run,
            commands::get_setup_config,
            commands::save_setup_config,
            commands::complete_setup,
            commands::toggle_devtools,
        ])
        .setup(|app| {
            log::info!("Setup phase starting...");
            
            let handle = app.handle();
            let manager = Arc::new(sidecar::SidecarManager::new(handle.clone()));
            app.manage(manager.clone());

            log::info!("Starting sidecar...");
            match manager.start() {
                Ok(_) => log::info!("Sidecar started successfully"),
                Err(e) => log::error!("Failed to start sidecar: {}", e),
            }

            log::info!("Running first-run check...");
            match setup_first_run_check(handle) {
                Ok(_) => log::info!("First-run check completed"),
                Err(e) => log::error!("First-run check failed: {}", e),
            }
            
            log::info!("Setup complete, app ready!");
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}