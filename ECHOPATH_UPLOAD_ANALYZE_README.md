# EchoPath Upload/Analyze Patch

This patch adds support for a random downloaded song:

- upload an MP3/WAV/FLAC/OGG/M4A/AAC from the Builder page
- backend extracts audio features with librosa
- backend generates a mel-spectrogram PNG
- backend assigns nearest mood cluster from the current library
- backend estimates genre from nearest neighbors
- backend creates preference and mood-fit scores
- uploaded track is inserted into the in-memory graph and can be used as the seed immediately

## Apply

```powershell
cd H:\desktop\aimlpbl
Expand-Archive -Path .\echopath_upload_analyze_patch.zip -DestinationPath . -Force

.\.venv\Scripts\Activate.ps1

cd backend
pip install -e .[dev]
```

If frontend types changed:

```powershell
cd ..\frontend
npm install
npm run dev
```

## Run backend

Use enriched manifest:

```powershell
cd H:\desktop\aimlpbl\backend
$env:ECHOPATH_LIBRARY_PATH = "..\data\library\tracks_enriched.json"
uvicorn app.main:app --reload
```

## Demo

1. Open `http://localhost:5173`
2. Go to Builder
3. Upload a random song
4. Click "Analyze and use as seed"
5. Choose A* and playlist length 5
6. Generate playlist

## Notes

This is not pretending the random song is in FMA. It is analyzed on upload and temporarily added to the graph. The prediction is nearest-neighbor/library-based unless you later connect exported CNN inference.
