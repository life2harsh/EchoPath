# EchoPath Research Workflow

## Windows GPU Run

1. Clone the repository.
2. Double-click `RUN_ECHOPATH_RESEARCH.bat`.
3. Send `echopath_research_results.zip` to the project owner when the run completes.

The launcher verifies Python, the NVIDIA driver, CUDA-enabled PyTorch, dataset paths, and expected outputs. It can install Python for the current user and download FMA Small plus its metadata when they are absent. Existing datasets under `archive/` are reused. Completed stages are resumed when the settings and inputs have not changed.

The default run uses all available FMA Small tracks, 30-second audio excerpts, a fixed artist-isolated 70/15/15 split, LeNet-style, VGG-style, and ResNet-style CNNs, mixed precision, primary search comparisons, and A* ablations.

## Output Layout

```text
research/windows/results/
  data/
  classical/
  cnn/
  search/
  report/
```

The packaged ZIP excludes the mel cache, model checkpoints, unrecognized files, and files larger than the configured size limit. Model checkpoints remain on the GPU machine.

## Configuration

Edit `scripts/windows/research-settings.json` before launching to change epochs, batch size, paths, case counts, or the CUDA wheel index. Environment variables `ECHOPATH_DATASET_ROOT`, `ECHOPATH_METADATA_CSV`, `ECHOPATH_PYTHON`, and `ECHOPATH_TORCH_INDEX_URL` override the corresponding settings.

## Evaluation Rules

- Artist groups do not cross train, validation, and test partitions.
- Model and checkpoint selection uses validation macro F1.
- The held-out test set is evaluated only after model selection.
- Search runs use seeded cases, explicit cache modes, repeated trials, raw outputs, aggregate confidence intervals, and recorded environment metadata.
- CNN predictions are exported before manifest enrichment and are distinguished from cluster-majority proxies.
