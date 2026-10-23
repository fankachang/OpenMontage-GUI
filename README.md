# OpenMontage GUI

A standalone local browser interface for reviewing OpenMontage workflows and local service connections.

## Project boundary

This repository contains the GUI and its workflow inventory snapshot. It is separate from the OpenMontage source repository and does not modify or include that project.

## Run locally

Serve this directory over HTTP, then open it in a browser. For example:

```sh
python3 -m http.server 4760
```

Open `http://127.0.0.1:4760/`.

## Current scope

- Browse production goals, workflows, and stages.
- Review LiteLLM, ComfyUI, and Backlot connection information.
- Save interface preferences and connection labels in browser storage.
- No API keys are stored.
- Git clone/pull, OpenMontage project creation, and workflow execution are not implemented yet.
