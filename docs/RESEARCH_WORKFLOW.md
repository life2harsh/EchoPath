# EchoPath Research Workflow

## Windows GPU Run

1. Clone or extract the repository to a short local path such as `C:\EchoPath` (not OneDrive, not a ZIP preview).
2. Double-click `RUN_ECHOPATH_RESEARCH.bat`.
3. Send `echopath_research_results.zip` to the project owner when the run completes. If the run stops, send `echopath_research_FAILED_logs.zip` instead; after a fix, run the launcher again.

`START_HERE.txt` is the plain-language version of these steps for the person running the job.

Requirements: Windows 10 or 11, an NVIDIA GPU with a current driver, about 30 GB of free disk space (12 GB if FMA Small is already extracted), and an internet connection for the first run.

The launcher checks the folder location, free disk space, the NVIDIA driver, and Python 3.11 to 3.13 (installing Python 3.12 for the current user with `winget` when none is found). It picks the PyTorch CUDA wheel that matches the driver (CUDA 12.8 builds for drivers reporting 12.8 or newer, which RTX 50-series GPUs need), then runs a short convolution on the GPU before any long work starts. It downloads FMA Small (7.7 GB) and its metadata with resumable transfers, verifies all 8,000 MP3 files after extraction, and deletes the downloaded archive. It keeps Windows awake and disables console QuickEdit so a stray click cannot pause the run.

Feature extraction and mel-spectrogram preprocessing run in parallel worker processes (`Workers` in the settings, `0` for automatic). Interrupted feature extraction resumes from a checkpoint, and completed stages are skipped when the settings and inputs have not changed.

Python output from every stage is appended to `research/windows/logs/python_<timestamp>.log`; the PowerShell transcript is `research/windows/logs/research_<timestamp>.log`. Both logs are included in the results ZIP and the failure ZIP.

The default run uses all available FMA Small tracks, full 30-second clips for both handcrafted features and CNN spectrograms (64 mel bands by 1,292 frames), a fixed artist-isolated 70/15/15 split, LeNet-style, VGG-style, and ResNet-style CNNs, mixed precision, primary search comparisons, and A* ablations.

## Output Layout

```text
research/windows/results/
  data/
  classical/
  cnn/
  search/
  report/
```

The packaged ZIP includes `data/features.csv` and `data/tracks_enriched.json`; the latter records absolute audio paths from the GPU machine. It excludes the mel cache, model checkpoints, unrecognized files, and files larger than the configured size limit. Model checkpoints remain on the GPU machine.

## Configuration

Edit `scripts/windows/research-settings.json` before launching to change epochs, batch size, paths, case counts, or the CUDA wheel index. Environment variables `ECHOPATH_DATASET_ROOT`, `ECHOPATH_METADATA_CSV`, `ECHOPATH_PYTHON`, and `ECHOPATH_TORCH_INDEX_URL` override the corresponding settings.

## Evaluation Rules

- Artist groups do not cross train, validation, and test partitions.
- Model and checkpoint selection uses validation macro F1.
- The held-out test set is evaluated only after model selection.
- Search runs use seeded cases, explicit cache modes, repeated trials, raw outputs, aggregate confidence intervals, and recorded environment metadata.
- CNN predictions are exported before manifest enrichment and are distinguished from cluster-majority proxies.
