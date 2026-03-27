# Backup and Restore Feature Design

**Date**: 2026-03-27
**Version**: 0.10.0
**Author**: Kimhsiao

## Overview

This document describes the design for backup, restore, and migration functionality for the RSS Aggregator application. The feature supports:

1. **Local backup/restore** - Users backup and restore data on the same machine
2. **Cross-machine migration** - Users migrate data between different machines
3. **Version upgrade migration** - Data migration during application upgrades

## Requirements

### Backup Scope

- Full backup including:
  - Database (SQLite)
  - Configuration (timezone, language)
  - Application version information

### Backup Format

- JSON format for readability and debugging
- Compressed and encrypted as ZIP file
- Password from environment variable `BACKUP_PASSWORD` (default: `kimhsiao`)

### Restore Strategy

- Merge mode: backup data takes precedence
- Existing data preserved, same records overwritten by backup

### Platform Support

- Desktop (Tauri): Native file dialogs
- Web/Docker: REST API + browser download/upload

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                      │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │  Desktop (Tauri)│              │    Web / Docker     │   │
│  │  - File dialogs │              │  - Download/Upload  │   │
│  │  - Tauri cmds   │              │  - REST API calls   │   │
│  └────────┬────────┘              └──────────┬──────────┘   │
│           │                                  │              │
│           ▼                                  ▼              │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │  Tauri Commands │              │    REST API         │   │
│  │  export_backup  │              │  /api/v1/backup/*   │   │
│  │  import_backup  │              │                     │   │
│  └────────┬────────┘              └──────────┬──────────┘   │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            ▼                                  ▼
┌───────────────────────────────────────────────────────────────┐
│                    Backend Services (Python)                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                 BackupService                           │   │
│  │  - export_backup() → JSON + ZIP encryption             │   │
│  │  - import_backup() → Decrypt ZIP + JSON parse + merge  │   │
│  │  - _serialize_data() → Convert DB to JSON              │   │
│  │  - _merge_data() → Merge logic (backup takes priority) │   │
│  │  - _encrypt_zip() / _decrypt_zip() → Encryption        │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                 BackupPasswordProvider                  │   │
│  │  - Read from BACKUP_PASSWORD env var                   │   │
│  │  - Default: kimhsiao                                   │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## Backup JSON Structure

```json
{
  "version": "0.10.0",
  "exported_at": "2026-03-27T15:30:00+08:00",
  "app_name": "RSS-Aggregator",
  "data": {
    "sources": [...],
    "feed_items": [...],
    "api_keys": [...],
    "preview_contents": [...],
    "fetch_batches": [...],
    "fetch_logs": [...],
    "stats": [...]
  },
  "config": {
    "timezone": "Asia/Taipei",
    "language": "zh"
  }
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `version` | Application version for compatibility check |
| `exported_at` | Export timestamp (ISO 8601) |
| `app_name` | Application name |
| `data` | All database table contents |
| `config` | Application settings |

### Data Table Order (considering foreign keys)

1. `sources` - No dependencies, import first
2. `api_keys` - No dependencies
3. `fetch_batches` - No dependencies
4. `feed_items` - Depends on sources, fetch_batches
5. `fetch_logs` - Depends on sources
6. `preview_contents` - No dependencies
7. `stats` - No dependencies

## Merge Logic

### Merge Rules

| Table | Merge Logic |
|-------|-------------|
| `sources` | Key: `url`, overwrite if same URL, add if different |
| `api_keys` | Key: `key`, overwrite if same key, add if different |
| `feed_items` | Key: `link`, overwrite if same link, add if different |
| `fetch_batches` | Add all backup batches (no overwrite) |
| `fetch_logs` | Add all backup logs (no overwrite) |
| `preview_contents` | Key: `url_hash`, overwrite if same, add if different |
| `stats` | Key: `date`, overwrite if same date, add if different |

### Merge Flow

```
Start Restore
    │
    ▼
Decrypt ZIP file
    │
    ▼
Parse JSON
    │
    ▼
Verify version compatibility
    │
    ├─ Incompatible → Return error
    │
    ▼
Process each data table in order:
    │
    ├─ sources    → Merge by url
    ├─ api_keys   → Merge by key
    ├─ fetch_batches → Add all
    ├─ feed_items → Merge by link (remap source_id)
    ├─ fetch_logs → Add all (remap source_id)
    ├─ preview_contents → Merge by url_hash
    └─ stats      → Merge by date
    │
    ▼
Update config (timezone, language)
    │
    ▼
Complete
```

### ID Remapping

After merging `sources`, build old ID → new ID mapping:

```python
source_id_mapping = {
    1: 5,   # Backup source ID=1 → merged ID=5
    2: 6,
    3: 3,   # New source
}
```

Use this mapping when processing `feed_items` and `fetch_logs`.

## REST API Design

### Export Backup

```
POST /api/v1/backup/export
```

**Request**:
```json
{
  "include_feed_items": true,
  "include_preview_contents": true,
  "include_logs": false
}
```

**Response**:
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="rss-backup-v0.10.0-2026-03-27.zip"`
- Body: Encrypted ZIP file

### Import Backup

```
POST /api/v1/backup/import
Content-Type: multipart/form-data
```

**Request**:
- `file`: Encrypted ZIP file

**Response**:
```json
{
  "success": true,
  "message": "Backup imported successfully",
  "summary": {
    "sources_imported": 5,
    "sources_merged": 2,
    "feed_items_imported": 100,
    "api_keys_imported": 1
  }
}
```

### Preview Backup

```
POST /api/v1/backup/preview
Content-Type: multipart/form-data
```

**Request**:
- `file`: Encrypted ZIP file

**Response**:
```json
{
  "version": "0.10.0",
  "exported_at": "2026-03-27T15:30:00+08:00",
  "counts": {
    "sources": 5,
    "feed_items": 100,
    "api_keys": 1,
    "preview_contents": 50
  },
  "config": {
    "timezone": "Asia/Taipei",
    "language": "zh"
  }
}
```

## Tauri Commands Design

### Export Backup

```rust
#[command]
pub async fn export_backup(
    app: AppHandle,
    include_feed_items: bool,
    include_preview_contents: bool,
    include_logs: bool,
) -> Result<String, String>
```

**Flow**:
1. Open "Save File" dialog with default filename `rss-backup-v0.10.0-2026-03-27.zip`
2. Call backend sidecar API to generate backup JSON
3. Encrypt and write ZIP in Tauri
4. Return saved path

### Import Backup

```rust
#[command]
pub async fn import_backup(
    app: AppHandle,
) -> Result<ImportResult, String>
```

**Flow**:
1. Open "Open File" dialog (filter `.zip`)
2. Read and decrypt ZIP
3. Call backend sidecar API to execute merge
4. Return import result

### Preview Backup

```rust
#[command]
pub async fn preview_backup(
    app: AppHandle,
) -> Result<BackupPreview, String>
```

**Flow**:
1. Open "Open File" dialog
2. Read and decrypt ZIP
3. Parse JSON and return summary (no import)

### Data Structures

```rust
#[derive(Serialize)]
pub struct ImportResult {
    pub success: bool,
    pub message: String,
    pub summary: ImportSummary,
}

#[derive(Serialize)]
pub struct ImportSummary {
    pub sources_imported: i32,
    pub sources_merged: i32,
    pub feed_items_imported: i32,
    pub api_keys_imported: i32,
}

#[derive(Serialize)]
pub struct BackupPreview {
    pub version: String,
    pub exported_at: String,
    pub counts: BackupCounts,
    pub config: BackupConfig,
}
```

## Frontend UI Design

### Page Location

Add "Data Management" section in **Settings page**.

### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Settings / 設定                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Data Management / 資料管理                          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  [📥 Export Backup / 匯出備份]                       │   │
│  │                                                     │   │
│  │  Export Options:                                    │   │
│  │  ☑ Include RSS Items                                │   │
│  │  ☑ Include Article Previews                         │   │
│  │  ☐ Include Fetch Logs                               │   │
│  │                                                     │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │                                                     │   │
│  │  [📤 Import Backup / 匯入備份]                       │   │
│  │                                                     │   │
│  │  [Choose File / 選擇檔案]  (Web version)             │   │
│  │  Selected: rss-backup-v0.10.0-2026-03-27.zip        │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ Backup Preview                               │   │   │
│  │  │ Version: v0.10.0                            │   │   │
│  │  │ Exported: 2026-03-27 15:30:00               │   │   │
│  │  │ Sources: 5  Items: 100  API Keys: 1         │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  [Confirm Import / 確認匯入]                         │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Desktop vs Web Differences

| Feature | Desktop (Tauri) | Web (REST API) |
|---------|-----------------|----------------|
| Export | Button → Native save dialog → Choose path | Button → Direct download to browser |
| Import | Button → Native open dialog → Choose file | Button → Browser file picker |
| Preview | Auto-display after file selection | Upload → API preview call |

### Interaction Flow

**Export**:
1. User selects export options
2. Click "Export Backup" button
3. Show loading state
4. Complete → Show success message (Desktop shows saved path)

**Import**:
1. User selects backup file
2. Auto-preview backup content
3. User confirms and clicks "Confirm Import"
4. Show loading state
5. Complete → Show import summary (added/merged counts)

## Error Handling

### Error Types

| Error Code | Message | Handling |
|------------|---------|----------|
| `BACKUP_VERSION_INCOMPATIBLE` | Backup version incompatible | Show error, suggest upgrade/downgrade |
| `BACKUP_PASSWORD_INVALID` | Invalid password | Show error (should not occur with auto password) |
| `BACKUP_FILE_CORRUPTED` | File corrupted or invalid format | Show error, suggest re-download |
| `BACKUP_FILE_NOT_FOUND` | File not found | Show error |
| `BACKUP_IMPORT_FAILED` | Import failed: {reason} | Show error, log details |
| `BACKUP_EXPORT_FAILED` | Export failed: {reason} | Show error, log details |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "BACKUP_VERSION_INCOMPATIBLE",
    "message": "Backup version 0.5.0 is not compatible with current version 0.10.0",
    "details": {
      "backup_version": "0.5.0",
      "current_version": "0.10.0"
    }
  }
}
```

### Version Compatibility Check

```python
def is_version_compatible(backup_version: str, current_version: str) -> bool:
    """
    Check version compatibility.
    
    Rules:
    - Same major version → Compatible
    - Different major version → Incompatible
    
    Examples:
    - 0.10.0 vs 0.11.0 → Compatible
    - 0.10.0 vs 1.0.0  → Incompatible
    - 0.10.0 vs 0.9.0  → Compatible
    """
    backup_major = backup_version.split('.')[0]
    current_major = current_version.split('.')[0]
    return backup_major == current_major
```

## File Naming Convention

Backup filename format: `rss-backup-v{version}-{date}.zip`

Examples:
- `rss-backup-v0.10.0-2026-03-27.zip`
- `rss-backup-v1.0.0-2026-04-15.zip`

## Security Considerations

1. **Password Storage**: Password read from environment variable, never stored in code
2. **Encryption**: Use standard ZIP encryption (AES-256 if available)
3. **File Validation**: Validate file structure before processing
4. **Size Limits**: Consider maximum file size for Web version uploads

## Testing Requirements

### Unit Tests

- `BackupService.export_backup()` - Test JSON serialization and encryption
- `BackupService.import_backup()` - Test decryption and merge logic
- `BackupService.is_version_compatible()` - Test version compatibility
- ID remapping logic

### Integration Tests

- Full export → import cycle
- Merge scenarios (new, overwrite, conflict)
- Error handling scenarios

### E2E Tests

- Desktop: Export → Save → Import cycle
- Web: Export → Download → Upload → Import cycle
- Cross-platform migration (Desktop backup → Web restore)

## Implementation Priority

1. **Phase 1**: Backend service (BackupService, API endpoints)
2. **Phase 2**: Web frontend UI
3. **Phase 3**: Desktop (Tauri commands)
4. **Phase 4**: E2E tests

## Dependencies

### Python (Backend)

- `pyzipper` - ZIP encryption/decryption with AES support
- Standard library: `json`, `io`, `zipfile`

### Rust (Tauri)

- `zip` - ZIP file handling
- `zip_extensions` - ZIP encryption support

### Frontend

- Existing API client infrastructure
- File handling utilities (for Web version)