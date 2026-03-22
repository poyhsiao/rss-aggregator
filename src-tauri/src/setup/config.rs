use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub version: String,
    pub setup_completed_at: Option<String>,
    pub timezone: String,
    pub language: String,
    pub last_run_at: Option<String>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            version: env!("CARGO_PKG_VERSION").to_string(),
            setup_completed_at: None,
            timezone: "Asia/Taipei".to_string(),
            language: "en".to_string(),
            last_run_at: None,
        }
    }
}

pub fn load_config(data_dir: &Path) -> Result<Config, Box<dyn std::error::Error>> {
    let config_path = data_dir.join("config.json");

    if !config_path.exists() {
        return Ok(Config::default());
    }

    let content = std::fs::read_to_string(&config_path)?;
    let config: Config = serde_json::from_str(&content)?;

    Ok(config)
}

pub fn save_config(data_dir: &Path, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    let config_path = data_dir.join("config.json");
    let content = serde_json::to_string_pretty(config)?;
    std::fs::write(&config_path, content)?;

    Ok(())
}

pub fn update_last_run(data_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let mut config = load_config(data_dir)?;
    config.last_run_at = Some(chrono::Local::now().to_rfc3339());
    save_config(data_dir, &config)?;
    Ok(())
}
