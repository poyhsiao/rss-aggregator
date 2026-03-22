use std::path::PathBuf;

pub fn get_app_data_dir(app_data_dir: PathBuf) -> PathBuf {
    app_data_dir
}

pub fn ensure_dir_exists(path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    if !path.exists() {
        std::fs::create_dir_all(path)?;
    }
    Ok(())
}
