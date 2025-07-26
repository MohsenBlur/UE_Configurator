# UE_Configurator
Below is a self‑contained **Engineering Design & Build Guide** for the “UE5 Config Assistant” exactly as we’ve refined it. Hand this to Codex (or any dev) and they can begin coding straight away.

---

## 1. Purpose & Scope

A desktop GUI (PySide6) that helps UE 5.4+ novices **discover, set and validate** console variables (CVars) / .ini settings while **avoiding duplicates** and respecting UE’s config‑file hierarchy.

* **Platform** Windows first; runs as a plain Python script/venv (no packaging yet).
* **Project mode** Single project at a time, but remembers recently opened projects.
* **Engine support** Reads the engine specified by `EngineAssociation` in the project’s `.uproject`. Works with stock or custom source installations.
* **Core tasks**

  1. Build (or rebuild) a local CVar/setting index from engine headers & tooltip metadata.
  2. Let users search that index by name, keyword‑in‑description, and category filter.
  3. Let users insert chosen settings into the *right* .ini file, with range hints.
  4. Detect duplicate or shadowed settings across the config hierarchy; default action = **comment‑out** lower‑priority entry (option to delete).
  5. Offer syntax + duplicate validation before saving.
  6. Keep timestamped backups inside `Config/Backup/YYYY‑MM‑DD‑HHMMSS/`.
  7. Export / import “presets” as raw `.ini` snippets.

Nice‑to‑haves such as live CVar validation, Git integration or one‑click packaging are explicitly out of scope for v‑0.1.

---

## 2. High‑Level Architecture

```
┌─────────────┐      .ini Scanner     ┌───────────────┐
│  UI Layer   │◀───file summary──────│   Config DB   │
│  (PySide6)  │                      └───────────────┘
│             │                      ▲              ▲
│  Search &   │──search query───────┘              │
│  Explorer   │                                    │
│             │   index lookup        ┌────────────┴─────────┐
│  Dup Fixer  │◀──────────────────────│  CVar Index & Cache  │
│             │                       └──────────────────────┘
└──────┬──────┘                                    ▲
       │ write‑back                                │ rebuild
       ▼                                           │
┌────────────────┐         parse headers           │
│  .ini Files    │◀────────Indexer─────────────┐   │
│  on disk       │                             │   │
└────────────────┘                             │   │
                                               ▼   ▼
                          UE Source (Engine/Editor headers, Macros)
```

* **UI Layer** – 5 PySide6 widgets (ProjectChooser, SearchPane, DetailsPane, ConflictPane, PresetPane) bound together by a `MainWindow`.
* **Config DB** – in‑memory model of current project’s merged `.ini` files using `configupdater` (keeps comments & order).
* **CVar Index & Cache** – persistent SQLite (or simple JSON) containing:

  * `name`, `type`, `category`, `description`, `valid_range`, `file_defined`
  * `introduced_in` (UE version) – helps hide outdated vars.
* **Indexer** – Python module that, on first launch or on “Re‑index” command:

  1. Finds engine root via `.uproject → EngineAssociation`.
  2. Walks `*/Source/*`, parsing `IConsoleVariable::Register` and `UE_CVAR_*` macros with regex.
  3. Extracts tooltip strings & metadata; stores into cache.
* **.ini Scanner** – loads every `Default*.ini`, `Project*.ini`, `GameUserSettings.ini` and platform overrides, capturing key/value, file, line‑number.

---

## 3. User Flow

1. **Launch → ProjectChooser**
   *Browse* (folder dialog) → chooses `.uproject`. Tool stores path in `recent.json`.
2. **Indexer check**
   Prompt “Build CVar index (first run)?” → progress bar → cache ready.
3. **SearchPane**
   *Keyword box* + category dropdown → results table (name|brief|valid range).
4. **DetailsPane** (on row click)
   Shows full description, valid range, where‑defined‑in‑engine, buttons:
   *Add to Config…* → dropdown of eligible .ini targets ordered by priority.
5. **ConflictPane** (auto‑opens after add/save)
   Lists duplicates with priority arrow (higher wins). Default action “Comment‑out losers”. Toggle to “Delete” or “Ignore”.
6. **Save**
   Performs syntax & duplicate validation. If OK:

   * Write new .ini files (UTF‑8, preserve original format).
   * Store originals in `Config/Backup/<timestamp>/`.
     Toast “Settings saved!”
7. **PresetPane**
   *Export current diff as snippet* → user names file, saved in `Presets/`.
   *Import preset* → merges; conflicts resolved via ConflictPane.

---

## 4. GUI Implementation Notes (PySide6)

| Widget             | Key elements / libraries                                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **ProjectChooser** | `QFileDialog`, `QListWidget` (recents), *Remove* context‑menu.                                                                       |
| **SearchPane**     | `QLineEdit` (with `QCompleter`), `QComboBox` (categories), `QTableView` backed by `QSortFilterProxyModel` for instant search/filter. |
| **DetailsPane**    | `QTextBrowser` (rich desc.), `QSpinBox` / `QLineEdit` for value, `QComboBox` target‑ini selector.                                    |
| **ConflictPane**   | `QTreeWidget` grouped by key; radio buttons (Comment/Delete/Ignore) per group, default = Comment.                                    |
| **PresetPane**     | `QListWidget` (local snippets), import/export buttons.                                                                               |

Styling: light theme, high‑contrast fonts; save all UI geometry/state in `settings.json`.

---

## 5. Core Algorithms

### 5.1 Config Hierarchy Resolution

1. Build ordered list (lowest → highest priority):
   `Default*.ini` → `Project*.ini` → `Platform*.ini` → `GameUserSettings.ini` → `CommandLine`\* (informational only).
2. When inserting a new setting, propose highest file that doesn’t already define it.
3. Duplicate detection: for each section\&key, store `(file, line)`. If count > 1, mark all except highest priority as duplicates.

### 5.2 Macro Parsing (Indexer)

Regex patterns (simplified):

```python
REGISTER = re.compile(
    r'IConsoleVariable::Register[^"]*"(?P<name>[A-Za-z0-9_.]+)".*?"(?P<desc>[^"]+)"[^;]*;')
UE_CVAR  = re.compile(
    r'UE_CVAR_(?:INTEGER|FLOAT|STRING)\s*\(\s*"(?P<name>[^"]+)"\s*,.*?"(?P<desc>[^"]+)"')
```

After match, attempt to capture default value (argument 2) to infer type/range where obvious.

---

## 6. Persistence & Back‑ups

* **CVar cache** → `~/.ue5_config_assistant/cvar_cache‑<EngineVersion>.json`.
* **App prefs** (recent projects, window sizes) → `settings.json` next to cache.
* **Backups** → `PROJECT/Config/Backup/2025‑07‑26‑120501/` mirrors original tree.
* **Presets** → `PROJECT/Presets/*.ini` (raw snippets, no JSON).

---

## 7. Step‑by‑Step Build Plan

| Sprint | Deliverable                                                      | Notes                        |
| ------ | ---------------------------------------------------------------- | ---------------------------- |
| **0**  | Repo scaffold + venv, README, MIT license (unless changed).      | —                            |
| **1**  | ProjectChooser + recent list.                                    | Hard‑code dummy CVar index.  |
| **2**  | Indexer module + real CVar cache build.                          | CLI only to start.           |
| **3**  | SearchPane + DetailsPane, live search.                           | Read‑only; no file writes.   |
| **4**  | .ini Scanner + ConfigDB, duplicate detector.                     | View conflicts only.         |
| **5**  | ConflictPane with comment‑out/delete actions.                    | First write‑back to backups. |
| **6**  | Preset import/export.                                            |                              |
| **7**  | Validation pass (syntax + dup) & user settings UI persistence.   |                              |
| **8**  | Polishing, icons, error dialogs; smoke‑test on Windows & Ubuntu. |                              |

---

## 8. Testing Strategy

* **Unit** – Indexer (macro cases), ConfigDB (merge, dedup).
* **Integration** – End‑to‑end on an empty sample project & Epic’s Lyra sample (ensures thousands of CVars indexed).
* **Manual** – Open a UE project, set a CVar, launch editor, verify `.ini` change takes effect.

---

## 9. Dependencies

```txt
PySide6       # UI
configupdater # .ini read/write while keeping comments
pytest        # tests
rich          # nice CLI progress during index build
```

(Plus standard library modules: `re`, `json`, `pathlib`, `shutil`, `datetime`, `sqlite3` **or** plain JSON for cache.)

---

## 10. Open Decisions (minor)

* **License** – defaulted to MIT here; replace if necessary.
* **Packaging** – once stable, PyInstaller can bundle to single EXE.
* **Future live‑validation** – headless UE launch could be added as plug‑in module.

---

### Handover

The guide above is ready for Codex or a human coder to implement. It defines **what** to build, **how** to build it, and the order in which to tackle work, leaving almost no ambiguous holes.

If anything still feels vague, just shout and we’ll tighten it up even further!
