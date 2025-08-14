# UE Config Assistant User Guide

This document provides a quick start guide for running the UE Config Assistant and explains the main workflow.

## 1. Installation

1. Ensure Python 3.10+ is installed.
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Launching the Application

Run the main script from the repository root:
```bash
python main.py
```
This opens the **Project Chooser** window.

## 3. Selecting a Project

1. Click **"Browse for .uproject"** and pick your Unreal project file.
2. Recently opened projects appear in the list for quick access.

## 4. Building/Loading the CVar Cache

- On first launch for a given engine version, the tool needs to index the Unreal Engine headers to gather console variables and settings.
- If no cache is found, you will be prompted to locate your Unreal Engine installation. Select the engine root directory (the folder containing `Engine/`).
- A progress bar will show the indexing process. The cache is stored under `~/.ue5_config_assistant/cvar_cache.json` for reuse.

## 5. Searching for Settings

The main window consists of a search pane (left) and a details pane (right):

1. Use the search box to filter settings by name or description.
2. Use the category drop-down to narrow results further.
3. Click a result row to view full details such as description, default value, and valid range.

## 6. Adding a Setting to Config

1. In the details pane, adjust the desired value.
2. Choose the target `.ini` file from the drop-down list.
3. Click **"Add to Config"** to stage the change in memory.

## 7. Resolving Duplicate Entries

- Select **"Show Duplicates"** from the menu or press <kbd>Ctrl+D</kbd> to open the conflict pane.
- For each duplicate key, choose whether to comment out or delete lower priority entries.
- Click **"Apply"** to update the staged configuration.

## 8. Viewing Config Files

- Select **"Config Files"** from the menu or press <kbd>Ctrl+F</kbd> to view and edit your project's configuration files.

## 9. Saving Changes

1. Choose **"Save"** from the menu or press <kbd>Ctrl+S</kbd>.
2. The tool validates syntax and duplicate resolution.
3. On success, new `.ini` files are written to your project’s `Config` folder.
4. Originals are backed up to `Config/Backup/<timestamp>/`.

## 10. Working with Presets

- Select **"Presets"** from the menu or press <kbd>Ctrl+P</kbd> to manage reusable configuration snippets.
- **Import** adds settings from an existing preset file.
- **Export Current** saves your merged configuration as a preset.

## 11. Tips

- Window sizes and recent projects are stored in `~/.ue5_config_assistant/` so they persist across sessions.
- You can rerun the tool at any time to edit or review your project’s configuration.

---
Enjoy configuring your Unreal Engine projects!
