# RSS Aggregator Desktop - User Guide

## Installation

### Windows

1. Download `RSS-Aggregator_x.x.x_x64.msi`
2. Double-click to install
3. Launch from Start Menu

### macOS

1. Download the appropriate DMG:
   - `RSS-Aggregator_x.x.x_x64.dmg` for Intel Macs
   - `RSS-Aggregator_x.x.x_aarch64.dmg` for Apple Silicon (M1/M2/M3)
2. Open the DMG file
3. Drag RSS Aggregator to Applications folder
4. Launch from Applications

**Note:** On first launch, you may need to:
- Right-click the app and select "Open"
- Go to System Preferences > Privacy & Security > click "Open Anyway"

### Linux

**DEB (Debian/Ubuntu):**
```bash
sudo dpkg -i rss-aggregator_x.x.x_amd64.deb
```

**AppImage:**
```bash
chmod +x rss-aggregator_x.x.x_amd64.AppImage
./rss-aggregator_x.x.x_amd64.AppImage
```

## First Run Setup

When you launch RSS Aggregator for the first time, you'll see a setup wizard:

### Step 1: Welcome
Introduction to the application.

### Step 2: Language & Timezone
- Select your preferred language (English/Chinese)
- Choose your timezone for correct time display

### Step 3: RSS Sources (Optional)
Add your favorite RSS feeds. You can skip this and add sources later.

### Step 4: Import Data (Optional)
Import an existing database from a previous installation:
- Select a `.db` file from your old installation
- The database will be copied to the new location

### Step 5: Complete
Setup is finished. Click "Start Using App" to begin.

## Data Storage

All data is stored in the `data/` directory next to the application:

```
RSS-Aggregator/
├── data/
│   ├── rss.db           # SQLite database
│   ├── config.json      # Application configuration
│   └── .setup_done      # Setup completion marker
└── RSS-Aggregator.exe   # (or app binary)
```

**Portable Mode:**
- Copy the entire folder to a USB drive
- Run from any computer
- All your feeds and settings travel with you

## Desktop-Specific Features

### Open Data Folder
Access your database and configuration files directly.

**Location:** Settings > Desktop Settings > Open Data Folder

### Import Database
Import an existing database from another installation.

**Location:** Settings > Desktop Settings > Import Database

**Steps:**
1. Click "Import Database"
2. Select your `.db` file
3. Restart the application

### Export Database
Copy your database to another location for backup or transfer.

**Location:** Settings > Desktop Settings > Export Data

### Restart Backend
Restart the Python backend without closing the application.

**Location:** Settings > Desktop Settings > Restart Backend

## Troubleshooting

### Application Won't Start

**Windows:**
- Check Windows Defender isn't blocking the app
- Run as Administrator

**macOS:**
- Right-click > Open on first launch
- Check Privacy & Security settings

**Linux:**
- Ensure you have the required libraries:
  ```bash
  sudo apt install libwebkit2gtk-4.1-dev
  ```

### Database Errors

1. Open Data Folder
2. Check if `rss.db` exists
3. If corrupted, delete `rss.db` and restart
4. The app will create a new database

### Reset to Factory Defaults

1. Close the application
2. Delete the `data/` folder
3. Restart the application
4. Complete the setup wizard again

## Updating

1. Download the new version
2. Replace the old application
3. Your `data/` folder is preserved
4. Launch the new version

## Uninstalling

### Windows
- Use "Add or Remove Programs" in Settings

### macOS
- Drag the app from Applications to Trash

### Linux
- DEB: `sudo apt remove rss-aggregator`
- AppImage: Delete the `.AppImage` file

**Note:** Your `data/` folder is not automatically deleted. Delete it manually if desired.

## Comparison: Desktop vs Docker

| Feature | Desktop | Docker |
|---------|---------|--------|
| Installation | One-click | Docker required |
| TCP Ports | Not required | Required |
| Data Location | Portable `./data/` | Docker volume |
| Updates | Download new version | Pull new image |
| Background | Always running | Container-based |

## Support

- GitHub Issues: https://github.com/poyhsiao/rss-aggretator/issues
- Email: white.shopping@gmail.com