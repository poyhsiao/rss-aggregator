use std::path::Path;

pub fn database_exists(data_dir: &Path) -> bool {
    data_dir.join("rss.db").exists()
}

pub fn ensure_database(data_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let db_path = data_dir.join("rss.db");

    if !db_path.exists() {
        std::fs::File::create(&db_path)?;
    }

    Ok(())
}

pub fn validate_database(db_path: &Path) -> Result<bool, Box<dyn std::error::Error>> {
    if !db_path.exists() {
        return Ok(false);
    }

    let content = std::fs::read(db_path)?;

    if content.len() < 16 {
        return Ok(false);
    }

    let header = &content[0..16];
    Ok(header.starts_with(b"SQLite format 3"))
}
