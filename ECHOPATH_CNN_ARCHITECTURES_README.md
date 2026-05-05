# EchoPath CNN Architecture Comparison Patch

This patch upgrades `echopath train-cnn` so it can train and compare:

- LeNet-style baseline
- VGG-style deeper CNN
- ResNet-style CNN with residual blocks

It writes:

```text
cnn_architecture_comparison.csv
lenet/classification_report.txt
vgg/classification_report.txt
resnet/classification_report.txt
lenet/model.pt
vgg/model.pt
resnet/model.pt
```

## Apply

From the project root:

```powershell
cd H:\desktop\aimlpbl
Expand-Archive -Path .\echopath_cnn_architectures_patch.zip -DestinationPath . -Force
.\.venv\Scripts\Activate.ps1
cd training
pip install -e .
```

## CPU-safe run

Use the balanced top-5 manifest you already created:

```powershell
echopath train-cnn `
  --manifest ..\data\library\tracks_cnn_top5_balanced.json `
  --architecture all `
  --epochs 5 `
  --batch-size 4 `
  --output-dir ..\artifacts\models\cnn_arch_compare
```

## GPU run

```powershell
echopath train-cnn `
  --manifest ..\data\library\tracks_cnn_top5_balanced.json `
  --architecture all `
  --epochs 20 `
  --batch-size 32 `
  --output-dir ..\artifacts\models\cnn_arch_compare_gpu
```

## Individual architecture runs

```powershell
echopath train-cnn --manifest ..\data\library\tracks_cnn_top5_balanced.json --architecture lenet --epochs 5 --batch-size 8 --output-dir ..\artifacts\models\cnn_lenet
echopath train-cnn --manifest ..\data\library\tracks_cnn_top5_balanced.json --architecture vgg --epochs 5 --batch-size 8 --output-dir ..\artifacts\models\cnn_vgg
echopath train-cnn --manifest ..\data\library\tracks_cnn_top5_balanced.json --architecture resnet --epochs 5 --batch-size 8 --output-dir ..\artifacts\models\cnn_resnet
```
