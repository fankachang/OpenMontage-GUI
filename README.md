# OpenMontage GUI

A standalone local browser interface for reviewing OpenMontage workflows and local service connections.

## Project boundary

This repository contains the GUI and its workflow inventory snapshot. It is separate from the OpenMontage source repository and does not modify or include that project.

## Run locally

On macOS, double-click `start.command`, or start the local server from Terminal:

```sh
python3 server.py
```

Open `http://127.0.0.1:4760/`. Python 3 is required; the server uses only its standard library.

On first launch, the server creates the SQLite schema and settings database automatically. By default, the database lives in `~/Library/Application Support/OpenMontage-GUI/settings.sqlite3`. Set `OPENMONTAGE_GUI_DATA_DIR` to choose another local data folder. Database files and user settings are excluded from Git; cloning this repository never downloads someone's settings.

See [SITE_MAP.md](SITE_MAP.md) for the complete page outline.

## Current scope

- Browse production goals, workflows, and stages.
- Review the project, workspace, asset library, activity, settings, and dashboard page outlines.
- Review LiteLLM, ComfyUI, and Backlot connection information.
- Browse the complete tool requirements snapshot by capability and status, including dependencies and install notes.
- Save interface preferences, service endpoints, and tool paths in the GUI's local SQLite database. Existing browser settings are imported once on first launch.
- No API keys are stored.
- Git clone/pull, OpenMontage project creation, and workflow execution are not implemented yet.
