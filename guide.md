# UE Config Assistant User Guide

This guide explains how to install and use the **UE Config Assistant** to manage Unreal Engine configuration variables.

## 1. Installation

1. Install Python 3.9+.
2. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Launching the Application

Run the tool from the repository root:
```bash
python main.py
```

On first launch you will see the **Project Chooser** window.

## 3. Selecting a Project

1. Click **Browse for .uproject** and select your Unreal project file.
2. The project will be added to the recent list for quicker access next time.

The tool loads the project’s `Config` directory so it can scan existing `.ini` files.

## 4. Building the CVar Index

If a cache file is not found, the app asks for the engine installation directory.
It then parses the engine headers and builds a searchable index of console variables (CVars).
This may take a few minutes on large installs, but only needs to run once per engine version.

## 5. Searching for Settings

After indexing, the **Main Window** opens. Use the search box at the top left to
filter CVars by name or description. Use the category drop‑down to limit results
to a specific area (Rendering, Audio, etc.).

Click a row to show full details in the right‑hand pane.

## 6. Adding Settings to Config Files

1. In the details pane, adjust the value if needed.
2. Choose the target `.ini` file from the drop‑down list.
3. Press **Add to Config**. The setting is inserted into the in‑memory config database.

## 7. Resolving Duplicate Entries

From the menu bar choose **Show Duplicates** to open the conflict resolver. Any
settings defined in multiple files will be listed.

* Select **Comment**, **Delete** or **Ignore** for each duplicate.
* Click **Apply** to enact the chosen actions.

## 8. Saving Changes

Click **Save** in the menu bar when you are ready to write the updated
configuration. The tool validates the `.ini` files and stores backups under
`Config/Backup/<timestamp>/` before overwriting.

## 9. Using Presets

Open the **Presets** window from the menu to manage reusable snippets.

* **Import** copies an external `.ini` snippet into the project and merges it.
* **Export Current** saves the merged configuration as a preset file.

Presets are stored inside the project’s `Presets` folder.

## 10. Tips and Notes

* The CVar cache and application settings are stored under
  `~/.ue5_config_assistant/` on your system.
* Window sizes and recent projects are remembered automatically.
* Backups allow you to revert if anything goes wrong.

With these steps you can quickly discover CVars, update your project’s config
files and keep everything organised.
