# EchoPath

EchoPath is an AI/ML playlist generator for the JIIT course project, built as a web-first experience.
This repository now contains:

- a FastAPI backend for tracks, playlist generation, analytics, and future dataset-backed streaming
- a React frontend for browsing the library, generating playlists, and reviewing model/search outputs
- a training scaffold for ingestion, classical ML, CNNs, and search benchmarking

`/home/life2harsh/rustplayer` stays separate. We are not coupling it here; the future handoff will be playlist exports and shared API contracts.

## Current Status

This first implementation is dataset-ready but does not require the real music files yet.
Until a manifest is provided, the backend serves a curated sample library from `artifacts/sample-data/demo_library.json`.

## Structure

```text
backend/   FastAPI app and API tests
frontend/  React + TypeScript + Vite web client
training/  Ingest and training entrypoints for the ML pipeline
artifacts/ Sample metadata and future experiment outputs
data/      Future dataset manifests and derived assets
```

## Quick Start

### Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` requests to `http://127.0.0.1:8000`.

## Dataset Hand-Off

When the real dataset is ready, point the backend to a manifest file:

```bash
export ECHOPATH_LIBRARY_PATH=/absolute/path/to/tracks.json
```

The manifest should follow the same schema used in `artifacts/sample-data/demo_library.json`.

## Research Pipeline

The training package provides reproducible ingestion, artist-isolated splits, classical and CNN evaluation, search benchmarks, ablations, and report generation:

```bash
cd training
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -e .
echopath ingest --dataset-root /path/to/fma
echopath train-classical
echopath train-cnn --architecture all --mixed-precision
echopath benchmark-search
echopath summarize-research --results-root /path/to/results
```

For the reproducible Windows GPU workflow, see `docs/RESEARCH_WORKFLOW.md` or double-click `RUN_ECHOPATH_RESEARCH.bat`. The launcher can install Python and download FMA Small automatically.

Experiment artifacts include split assignments, configurations, predictions, classification reports, confusion matrices, raw benchmark runs, aggregate confidence intervals, figures, and checksums.
