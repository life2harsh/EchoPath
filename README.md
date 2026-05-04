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

## Training Scaffold

The training package is intentionally lightweight for now, but the command surface is ready:

```bash
cd training
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -e .
echopath ingest --dataset-root /path/to/fma
echopath train-classical
echopath train-cnn --hf-repo your-org/echopath-models
echopath benchmark-search
```

## Next Steps

1. Plug in the real dataset manifest and local audio files.
2. Replace sample analytics with feature-extracted outputs.
3. Expand the training commands into full data pipelines and model jobs.
