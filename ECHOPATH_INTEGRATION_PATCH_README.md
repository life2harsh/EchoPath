# EchoPath Integration Patch

This patch makes the live backend/frontend demo closer to the project synopsis.

It adds:

- ML/CNN-derived fields in track records
- manifest enrichment command
- preference-aware and CNN/proxy-aware search cost
- A*/IDA* heuristic support from model signals
- hill-climbing refinement after search
- playlist quality metrics
- frontend metric display

## Apply

From project root:

```powershell
cd H:\desktop\aimlpbl
Expand-Archive -Path .\echopath_integration_patch.zip -DestinationPath . -Force
```

Reinstall packages:

```powershell
.\.venv\Scripts\Activate.ps1

cd training
pip install -e .

cd ..\backend
pip install -e .[dev]
```

## Enrich the manifest

```powershell
cd H:\desktop\aimlpbl\training

echopath enrich-manifest `
  --manifest ..\data\library\tracks.json `
  --features ..\artifacts\features.csv `
  --output ..\data\library\tracks_enriched.json
```

Use the enriched manifest:

```powershell
cd H:\desktop\aimlpbl\backend
$env:ECHOPATH_LIBRARY_PATH = "..\data\library\tracks_enriched.json"
uvicorn app.main:app --reload
```

## Frontend

```powershell
cd H:\desktop\aimlpbl\frontend
npm run dev
```

## Demo settings

Use A* or IDA* for live demo:

```text
Algorithm: Astar
Playlist length: 5
Target type: Genre or Cluster
Tempo policy: Lift or Steady
```

Avoid BFS length 10 on 4000 tracks. It is intentionally slow because it is uninformed.

## About CNN/proxy fields

If you do not provide a CNN prediction CSV, `enrich-manifest` uses a cluster-majority proxy as `cnn_genre_prediction` and marks `signal_source` as `cluster_majority_proxy`.

That is not fake live CNN inference. It is a fallback integration signal. If you later export actual CNN predictions, use:

```powershell
--cnn-predictions ..\artifacts\models\cnn_top5_balanced\cnn_predictions.csv
```

The CSV must contain:

```text
track_id,prediction,confidence
```
