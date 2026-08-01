$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptRoot "..\..")).Path
$SettingsPath = Join-Path $ScriptRoot "research-settings.json"
$ResearchRoot = Join-Path $RepoRoot "research\windows"
$ResultsRoot = Join-Path $ResearchRoot "results"
$LogsRoot = Join-Path $ResearchRoot "logs"
$StateRoot = Join-Path $ResearchRoot "state"
$VenvRoot = Join-Path $ResearchRoot ".venv"
$ZipPath = Join-Path $RepoRoot "echopath_research_results.zip"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogsRoot "research_$RunStamp.log"
$ExitCode = 0
$TranscriptStarted = $false

function Write-Stage([string]$Message) {
    Write-Host ""
    Write-Host "========== $Message ==========" -ForegroundColor Cyan
}

function Invoke-Checked([string]$Program, [string[]]$Arguments, [string]$Description) {
    Write-Host "[$Description]"
    Write-Host ("Command: " + $Program + " " + ($Arguments -join " "))
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Get-CommandVersion([string]$Program, [string[]]$Prefix) {
    $output = & $Program @Prefix -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>&1
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    return (($output | Select-Object -Last 1).ToString().Trim())
}

function Resolve-Python([string]$ConfiguredCommand, [bool]$InstallIfMissing) {
    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($env:ECHOPATH_PYTHON)) {
        $ConfiguredCommand = $env:ECHOPATH_PYTHON
    }
    if (-not [string]::IsNullOrWhiteSpace($ConfiguredCommand)) {
        $expanded = [Environment]::ExpandEnvironmentVariables($ConfiguredCommand.Trim().Trim('"'))
        if (Test-Path $expanded -PathType Leaf) {
            $candidates += ,@((Resolve-Path $expanded).Path, @())
        } else {
            $parts = $ConfiguredCommand.Trim() -split "\s+"
            $candidates += ,@($parts[0], @($parts | Select-Object -Skip 1))
        }
    } else {
        $candidates += ,@("py", @("-3.11"))
        $candidates += ,@("py", @("-3"))
        $candidates += ,@("python", @())
        $candidates += ,@("python3", @())
    }

    foreach ($candidate in $candidates) {
        $program = [string]$candidate[0]
        $prefix = [string[]]$candidate[1]
        if (-not (Get-Command $program -ErrorAction SilentlyContinue)) {
            continue
        }
        $version = Get-CommandVersion $program $prefix
        if ($version) {
            $parsed = [version]$version
            Write-Host "Found Python $version using: $program $($prefix -join ' ')"
            if ($parsed -ge [version]"3.11") {
                return @{ Program = $program; Prefix = $prefix; Version = $version }
            }
        }
    }
    if ($InstallIfMissing -and (Get-Command "winget.exe" -ErrorAction SilentlyContinue)) {
        Write-Host "Python 3.11 was not found. Installing it for the current Windows user."
        & winget.exe install --id Python.Python.3.11 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            $installed = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"
            if (Test-Path $installed -PathType Leaf) {
                $installedVersion = Get-CommandVersion $installed @()
                return @{ Program = $installed; Prefix = @(); Version = $installedVersion }
            }
        }
    }
    throw "Python 3.11 or newer was not found. Install 64-bit Python from python.org, enable the Python launcher, and run this file again. No administrator terminal is required."
}

function Install-Dataset {
    $archiveRoot = Join-Path $RepoRoot "archive"
    $downloads = Join-Path $archiveRoot "downloads"
    $audioZip = Join-Path $downloads "fma_small.zip"
    $metadataZip = Join-Path $downloads "fma_metadata.zip"
    New-Item $downloads -ItemType Directory -Force | Out-Null
    if (-not (Get-Command "curl.exe" -ErrorAction SilentlyContinue)) {
        throw "curl.exe is required for the automatic FMA download. Install curl or extract FMA Small under archive\fma_small yourself."
    }

    function Receive-Archive([string]$Url, [string]$Destination, [int64]$ExpectedBytes, [string]$Name) {
        if ((Test-Path $Destination -PathType Leaf) -and (Get-Item $Destination).Length -eq $ExpectedBytes) {
            return
        }
        $partial = "$Destination.part"
        if ((Test-Path $Destination -PathType Leaf) -and -not (Test-Path $partial -PathType Leaf)) {
            Move-Item $Destination $partial -Force
        }
        if ((Test-Path $partial -PathType Leaf) -and (Get-Item $partial).Length -gt $ExpectedBytes) {
            Remove-Item $partial -Force
        }
        Invoke-Checked "curl.exe" @("-L", "--fail", "--retry", "5", "-C", "-", "-o", $partial, $Url) "Download $Name"
        if ((Get-Item $partial).Length -ne $ExpectedBytes) {
            throw "$Name has an unexpected size. Run the launcher again to resume the download."
        }
        Move-Item $partial $Destination -Force
    }

    Receive-Archive "https://os.unil.cloud.switch.ch/fma/fma_small.zip" $audioZip 7679594875 "FMA Small"
    Receive-Archive "https://os.unil.cloud.switch.ch/fma/fma_metadata.zip" $metadataZip 358412441 "FMA metadata"
    $audioDestination = Join-Path $archiveRoot "fma_small"
    $metadataDestination = Join-Path $archiveRoot "fma_metadata"
    if (-not (Test-Path (Join-Path $audioDestination "fma_small") -PathType Container)) {
        Expand-Archive $audioZip $audioDestination -Force
    }
    if (-not (Test-Path (Join-Path $metadataDestination "fma_metadata") -PathType Container)) {
        Expand-Archive $metadataZip $metadataDestination -Force
    }
}

function Resolve-Dataset([string]$ConfiguredRoot, [bool]$DownloadIfMissing) {
    $override = $env:ECHOPATH_DATASET_ROOT
    if ([string]::IsNullOrWhiteSpace($override)) {
        $override = $ConfiguredRoot
    }
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $candidate = [Environment]::ExpandEnvironmentVariables($override)
        if (-not [IO.Path]::IsPathRooted($candidate)) {
            $candidate = Join-Path $RepoRoot $candidate
        }
        if (-not (Test-Path $candidate -PathType Container)) {
            throw "Dataset override does not exist: $candidate. Update DatasetRoot in $SettingsPath or clear ECHOPATH_DATASET_ROOT."
        }
        $audio = Get-ChildItem $candidate -Recurse -File -Include *.mp3,*.wav,*.flac,*.ogg,*.m4a -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $audio) {
            throw "Dataset override contains no supported audio files: $candidate"
        }
        return (Resolve-Path $candidate).Path
    }

    $known = @(
        (Join-Path $RepoRoot "archive\fma_small\fma_small"),
        (Join-Path $RepoRoot "archive\fma_small"),
        (Join-Path $RepoRoot "data\fma_small"),
        (Join-Path $RepoRoot "data")
    )
    foreach ($candidate in $known) {
        if (Test-Path $candidate -PathType Container) {
            $audio = Get-ChildItem $candidate -Recurse -File -Include *.mp3,*.wav,*.flac,*.ogg,*.m4a -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($audio) {
                return (Resolve-Path $candidate).Path
            }
        }
    }
    if ($DownloadIfMissing) {
        Install-Dataset
        $downloaded = Join-Path $RepoRoot "archive\fma_small\fma_small"
        $count = @(Get-ChildItem $downloaded -Recurse -File -Filter *.mp3).Count
        if ($count -lt 8000) {
            throw "The FMA Small download is incomplete: found $count of 8000 MP3 files. Run the launcher again to resume."
        }
        return (Resolve-Path $downloaded).Path
    }
    throw "No audio dataset was found. Extract the dataset yourself, then set DatasetRoot in $SettingsPath or set ECHOPATH_DATASET_ROOT. This workflow will not download a multi-GB dataset."
}

function Resolve-Metadata([string]$ConfiguredPath, [string]$DatasetRoot) {
    $override = $env:ECHOPATH_METADATA_CSV
    if ([string]::IsNullOrWhiteSpace($override)) {
        $override = $ConfiguredPath
    }
    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $expanded = [Environment]::ExpandEnvironmentVariables($override)
        if (-not [IO.Path]::IsPathRooted($expanded)) {
            $expanded = Join-Path $RepoRoot $expanded
        }
        $candidates += $expanded
    }
    $candidates += Join-Path $RepoRoot "archive\fma_metadata\fma_metadata\tracks.csv"
    $candidates += Join-Path $RepoRoot "archive\fma_metadata\tracks.csv"
    $candidates += Join-Path $DatasetRoot "fma_metadata\tracks.csv"
    $candidates += Join-Path (Split-Path $DatasetRoot -Parent) "fma_metadata\tracks.csv"
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate -PathType Leaf) {
            return (Resolve-Path $candidate).Path
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        throw "MetadataCsv override does not exist: $override"
    }
    Write-Warning "FMA tracks.csv was not found. File names will be used and genre training may not be possible."
    return $null
}

function Get-CudaInfo {
    if (-not (Get-Command "nvidia-smi.exe" -ErrorAction SilentlyContinue) -and -not (Get-Command "nvidia-smi" -ErrorAction SilentlyContinue)) {
        return @{ Found = $false; Version = $null; Name = $null }
    }
    $query = & nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
    $full = & nvidia-smi 2>&1 | Out-String
    $cudaVersion = $null
    if ($full -match "CUDA Version:\s*([0-9]+\.[0-9]+)") {
        $cudaVersion = [version]$Matches[1]
    }
    return @{ Found = $true; Version = $cudaVersion; Name = (($query | Select-Object -First 1).ToString().Trim()); Details = $full.Trim() }
}

function Resolve-TorchIndex([string]$Setting, $CudaInfo) {
    $override = $env:ECHOPATH_TORCH_INDEX_URL
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $Setting = $override
    }
    if ($Setting -ne "auto") {
        if ($Setting -match "^https?://") {
            return $Setting.TrimEnd("/")
        }
        return "https://download.pytorch.org/whl/$Setting"
    }
    if (-not $CudaInfo.Found -or -not $CudaInfo.Version) {
        return "https://download.pytorch.org/whl/cpu"
    }
    if ($CudaInfo.Version -ge [version]"12.4") {
        return "https://download.pytorch.org/whl/cu124"
    }
    if ($CudaInfo.Version -ge [version]"12.1") {
        return "https://download.pytorch.org/whl/cu121"
    }
    if ($CudaInfo.Version -ge [version]"11.8") {
        return "https://download.pytorch.org/whl/cu118"
    }
    return "https://download.pytorch.org/whl/cpu"
}

function Get-FileFingerprint([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path -PathType Leaf)) {
        return $null
    }
    $item = Get-Item $Path
    return @{
        Path = $item.FullName
        Bytes = $item.Length
        ModifiedUtc = $item.LastWriteTimeUtc.ToString("o")
        Sha256 = (Get-FileHash $item.FullName -Algorithm SHA256).Hash
    }
}

function Get-DatasetFingerprint([string]$Path) {
    $files = Get-ChildItem $Path -Recurse -File -Include *.mp3,*.wav,*.flac,*.ogg,*.m4a
    $checksum = Join-Path $Path "checksums"
    return @{
        Path = $Path
        FileCount = @($files).Count
        TotalBytes = ($files | Measure-Object Length -Sum).Sum
        LatestWriteUtc = ($files | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.ToString("o")
        ChecksumManifest = Get-FileFingerprint $checksum
    }
}

function Get-TextHash([string]$Value) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
    $hash = [Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return [BitConverter]::ToString($hash).Replace("-", "")
}

function Get-SourceFingerprint([string]$Revision) {
    $roots = @(
        (Join-Path $RepoRoot "backend\app"),
        (Join-Path $RepoRoot "backend\tests"),
        (Join-Path $RepoRoot "training\echopath"),
        (Join-Path $RepoRoot "training\tests"),
        (Join-Path $RepoRoot "scripts\windows"),
        (Join-Path $RepoRoot "frontend\src")
    )
    $files = @()
    foreach ($root in $roots) {
        if (Test-Path $root -PathType Container) {
            $files += Get-ChildItem $root -Recurse -File | Where-Object { @(".py", ".ps1", ".json", ".ts", ".tsx", ".css") -contains $_.Extension.ToLowerInvariant() }
        }
    }
    foreach ($relative in @("RUN_ECHOPATH_RESEARCH.bat", "backend\pyproject.toml", "training\pyproject.toml", "frontend\package.json", "frontend\package-lock.json")) {
        $candidate = Join-Path $RepoRoot $relative
        if (Test-Path $candidate -PathType Leaf) {
            $files += Get-Item $candidate
        }
    }
    $entries = $files | Sort-Object FullName -Unique | ForEach-Object {
        $relative = $_.FullName.Substring($RepoRoot.Length).TrimStart("\").Replace("\", "/")
        "$relative`:$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)"
    }
    return @{ Revision = $Revision; FileCount = @($entries).Count; ContentHash = Get-TextHash (@($entries) -join "`n") }
}

function Test-Step([string]$Name, [hashtable]$Signature, [string[]]$Outputs, [bool]$Resume) {
    if (-not $Resume) {
        return $false
    }
    foreach ($output in $Outputs) {
        if (-not (Test-Path $output -PathType Leaf)) {
            return $false
        }
    }
    $statePath = Join-Path $StateRoot "$Name.json"
    if (-not (Test-Path $statePath -PathType Leaf)) {
        return $false
    }
    try {
        $saved = Get-Content $statePath -Raw | ConvertFrom-Json
        $wanted = $Signature | ConvertTo-Json -Depth 8 -Compress
        $actual = $saved.Signature | ConvertTo-Json -Depth 8 -Compress
        $wantedOutputs = ConvertTo-Json -InputObject @($Outputs | ForEach-Object { Get-FileFingerprint $_ }) -Depth 8 -Compress
        $actualOutputs = ConvertTo-Json -InputObject @($saved.Outputs) -Depth 8 -Compress
        return $wanted -eq $actual -and $wantedOutputs -eq $actualOutputs
    } catch {
        return $false
    }
}

function Complete-Step([string]$Name, [hashtable]$Signature, [string[]]$Outputs) {
    $statePath = Join-Path $StateRoot "$Name.json"
    @{ CompletedUtc = [DateTime]::UtcNow.ToString("o"); Signature = $Signature; Outputs = @($Outputs | ForEach-Object { Get-FileFingerprint $_ }) } | ConvertTo-Json -Depth 8 | Set-Content $statePath -Encoding UTF8
}

function Invoke-Step([string]$Name, [hashtable]$Signature, [string[]]$Outputs, [bool]$Resume, [scriptblock]$Action) {
    Write-Stage $Name
    if (Test-Step $Name $Signature $Outputs $Resume) {
        Write-Host "Resuming: valid outputs from the matching completed step were found."
        return
    }
    & $Action
    foreach ($output in $Outputs) {
        if (-not (Test-Path $output -PathType Leaf)) {
            throw "$Name completed without expected output: $output"
        }
    }
    Complete-Step $Name $Signature $Outputs
}

function New-ResultsZip([int]$MaximumFileSizeMb) {
    $stage = Join-Path $env:TEMP "echopath_research_package_$RunStamp"
    if (Test-Path $stage) {
        Remove-Item $stage -Recurse -Force
    }
    New-Item $stage -ItemType Directory -Force | Out-Null
    $maxBytes = [int64]$MaximumFileSizeMb * 1MB
    $allowedExtensions = @(".csv", ".json", ".txt", ".md", ".png", ".log")
    $packageFiles = @()
    $artifactManifest = Join-Path $ResultsRoot "report\artifact_manifest.json"
    if (Test-Path $artifactManifest -PathType Leaf) {
        $manifest = Get-Content $artifactManifest -Raw | ConvertFrom-Json
        foreach ($artifact in $manifest.artifacts) {
            $candidate = Join-Path $ResultsRoot ([string]$artifact.path)
            if (Test-Path $candidate -PathType Leaf) {
                $item = Get-Item $candidate
                $actualHash = (Get-FileHash $item.FullName -Algorithm SHA256).Hash
                if ($item.Length -ne [int64]$artifact.bytes -or $actualHash -ne [string]$artifact.sha256) {
                    throw "Artifact changed after report generation: $($artifact.path)"
                }
                $packageFiles += $item
            } else {
                throw "Artifact is missing after report generation: $($artifact.path)"
            }
        }
    }
    foreach ($reportFile in $ReportExpected) {
        if (Test-Path $reportFile -PathType Leaf) {
            $packageFiles += Get-Item $reportFile
        } else {
            throw "Required report artifact is missing: $reportFile"
        }
    }
    $packageFiles | Sort-Object FullName -Unique | Where-Object {
        $_.Length -le $maxBytes -and
        $allowedExtensions -contains $_.Extension.ToLowerInvariant() -and
        $_.FullName -notmatch "[\\/]mel_cache[\\/]"
    } | ForEach-Object {
        if ($_.FullName.StartsWith($ResultsRoot)) {
            $relative = Join-Path "results" $_.FullName.Substring($ResultsRoot.Length).TrimStart("\")
        } else {
            $relative = Join-Path "logs" $_.Name
        }
        $destination = Join-Path $stage $relative
        New-Item (Split-Path $destination -Parent) -ItemType Directory -Force | Out-Null
        Copy-Item $_.FullName $destination -Force
    }
    $packageEntries = Get-ChildItem $stage -Recurse -File | ForEach-Object {
        @{
            Path = $_.FullName.Substring($stage.Length).TrimStart("\").Replace("\", "/")
            Bytes = $_.Length
            Sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
        }
    }
    @{ SchemaVersion = 1; CreatedUtc = [DateTime]::UtcNow.ToString("o"); Files = @($packageEntries) } | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $stage "package_manifest.json") -Encoding UTF8
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $ZipPath -CompressionLevel Optimal
    Remove-Item $stage -Recurse -Force
}

try {
    if (-not (Test-Path $SettingsPath -PathType Leaf)) {
        throw "Settings file is missing: $SettingsPath"
    }
    $Settings = Get-Content $SettingsPath -Raw | ConvertFrom-Json
    New-Item $ResultsRoot, $LogsRoot, $StateRoot -ItemType Directory -Force | Out-Null
    if (Test-Path $ZipPath -PathType Leaf) {
        Remove-Item $ZipPath -Force
    }
    Start-Transcript -Path $LogPath -Force | Out-Null
    $TranscriptStarted = $true
    Set-Location $RepoRoot

    Write-Stage "System checks"
    Write-Host "Repository: $RepoRoot"
    Write-Host "Settings: $SettingsPath"
    $Python = Resolve-Python ([string]$Settings.PythonCommand) ([bool]$Settings.InstallPythonIfMissing)
    if (Get-Command "git.exe" -ErrorAction SilentlyContinue) {
        Write-Host ("Git: " + (& git --version))
    } elseif (Get-Command "git" -ErrorAction SilentlyContinue) {
        Write-Host ("Git: " + (& git --version))
    } else {
        Write-Warning "Git was not found. The local workflow can continue, but Git is recommended for project integrity."
    }

    $Cuda = Get-CudaInfo
    if ($Cuda.Found) {
        Write-Host "NVIDIA GPU: $($Cuda.Name)"
        Write-Host "Driver-reported CUDA: $($Cuda.Version)"
        Write-Host $Cuda.Details
    } else {
        Write-Warning "nvidia-smi was not found. The NVIDIA driver may be missing or no NVIDIA GPU is available."
        if (-not [bool]$Settings.AllowCpuFallback) {
            throw "CUDA is required by settings. Install a current NVIDIA driver or set AllowCpuFallback to true."
        }
    }

    $DatasetRoot = Resolve-Dataset ([string]$Settings.DatasetRoot) ([bool]$Settings.DownloadDatasetIfMissing)
    $MetadataCsv = Resolve-Metadata ([string]$Settings.MetadataCsv) $DatasetRoot
    $GitRevision = if (Get-Command "git" -ErrorAction SilentlyContinue) { (& git rev-parse HEAD).Trim() } else { "unavailable" }
    $SourceFingerprint = Get-SourceFingerprint $GitRevision
    $DatasetFingerprint = Get-DatasetFingerprint $DatasetRoot
    $MetadataFingerprint = Get-FileFingerprint $MetadataCsv
    Write-Host "Dataset: $DatasetRoot"
    Write-Host "Metadata: $(if ($MetadataCsv) { $MetadataCsv } else { 'not found' })"

    Write-Stage "Python environment"
    $VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
    if (-not (Test-Path $VenvPython -PathType Leaf)) {
        Invoke-Checked $Python.Program (@($Python.Prefix) + @("-m", "venv", $VenvRoot)) "Create virtual environment"
    }
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") "Update packaging tools"
    $TorchIndex = Resolve-TorchIndex ([string]$Settings.TorchIndexUrl) $Cuda
    Write-Host "PyTorch wheel index: $TorchIndex"
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--index-url", $TorchIndex, "torch>=2.5,<3.0") "Install PyTorch"
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-e", (Join-Path $RepoRoot "training"), "-e", (Join-Path $RepoRoot "backend")) "Install EchoPath dependencies"
    Invoke-Checked $VenvPython @("-c", "import torch; print('PyTorch:', torch.__version__); print('Built CUDA:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')") "Verify PyTorch"
    $TorchCuda = & $VenvPython -c "import torch; print('yes' if torch.cuda.is_available() else 'no')"
    if ($Cuda.Found -and (($TorchCuda | Select-Object -Last 1).ToString().Trim() -ne "yes")) {
        throw "An NVIDIA GPU was detected, but PyTorch cannot use CUDA. Update the NVIDIA driver or set TorchIndexUrl in $SettingsPath to a compatible tag such as cu124, cu121, or cu118."
    }

    $DataOutput = Join-Path $ResultsRoot "data"
    $ClassicalOutput = Join-Path $ResultsRoot "classical"
    $CnnOutput = Join-Path $ResultsRoot "cnn"
    $SearchOutput = Join-Path $ResultsRoot "search"
    New-Item $DataOutput, $ClassicalOutput, $CnnOutput, $SearchOutput -ItemType Directory -Force | Out-Null
    $Manifest = Join-Path $DataOutput "tracks.json"
    $Features = Join-Path $DataOutput "features.csv"
    $Splits = Join-Path $DataOutput "splits.csv"
    $EnrichedManifest = Join-Path $DataOutput "tracks_enriched.json"
    $Resume = [bool]$Settings.Resume

    $PrepareSignature = @{ Source = $SourceFingerprint; Dataset = $DatasetFingerprint; Metadata = $MetadataFingerprint; Limit = [int]$Settings.IngestLimit; Duration = [double]$Settings.AudioDurationSeconds; Clusters = [int]$Settings.Clusters }
    Invoke-Step "prepare" $PrepareSignature @($Manifest, $Features) $Resume {
        $arguments = @("-m", "echopath", "ingest", "--dataset-root", $DatasetRoot, "--output-manifest", $Manifest, "--features-csv", $Features, "--audio-duration", [string]$Settings.AudioDurationSeconds, "--clusters", [string]$Settings.Clusters)
        if ($MetadataCsv) { $arguments += @("--metadata-csv", $MetadataCsv) }
        if ([int]$Settings.IngestLimit -gt 0) { $arguments += @("--limit", [string]$Settings.IngestLimit) }
        Invoke-Checked $VenvPython $arguments "Prepare dataset"
    }

    $ClassicalMetrics = Join-Path $ClassicalOutput "validation_metrics.csv"
    $ClassicalTestMetrics = Join-Path $ClassicalOutput "final_test_metrics.json"
    $ClassicalExpected = @(
        $ClassicalMetrics,
        $ClassicalTestMetrics,
        $Splits,
        "$Splits.metadata.json",
        (Join-Path $ClassicalOutput "validation_predictions.csv"),
        (Join-Path $ClassicalOutput "class_distribution.csv"),
        (Join-Path $ClassicalOutput "final_test_classification_report.txt"),
        (Join-Path $ClassicalOutput "final_test_confusion_matrix.csv"),
        (Join-Path $ClassicalOutput "test_predictions.csv"),
        (Join-Path $ClassicalOutput "training_config.json"),
        (Join-Path $ClassicalOutput "best_classical_model.joblib")
    )
    foreach ($modelName in @("logistic_regression", "linear_svm", "svm_rbf", "random_forest", "extra_trees", "mlp")) {
        $ClassicalExpected += Join-Path $ClassicalOutput "$($modelName)_validation_classification_report.txt"
    }
    $ClassicalSignature = @{ Prepare = $PrepareSignature; Features = Get-FileFingerprint $Features; Manifest = Get-FileFingerprint $Manifest; Classes = @($Settings.Classes); TopClasses = [int]$Settings.TopClasses; Maximum = [int]$Settings.MaxTracksPerClass; Minimum = [int]$Settings.MinimumTracksPerClass; ValidationSize = 0.15; TestSize = 0.15 }
    Invoke-Step "classical" $ClassicalSignature $ClassicalExpected $Resume {
        $arguments = @("-m", "echopath", "train-classical", "--features", $Features, "--manifest", $Manifest, "--output-dir", $ClassicalOutput, "--splits", $Splits, "--label-column", "genre_label", "--min-per-class", [string]$Settings.MinimumTracksPerClass, "--top-classes", [string]$Settings.TopClasses, "--validation-size", "0.15", "--test-size", "0.15")
        $arguments += "--formal-evaluation"
        $arguments += "--classes"
        $arguments += [string[]]$Settings.Classes
        if ([int]$Settings.MaxTracksPerClass -gt 0) { $arguments += @("--balance-classes", "--max-per-class", [string]$Settings.MaxTracksPerClass) }
        Invoke-Checked $VenvPython $arguments "Run classical experiments"
    }

    $CnnMetrics = Join-Path $CnnOutput "cnn_architecture_comparison.csv"
    $CnnTestMetrics = Join-Path $CnnOutput "final_test_metrics.json"
    $CnnPredictions = Join-Path $CnnOutput "cnn_predictions.csv"
    $CnnExpected = @(
        $CnnMetrics,
        $CnnTestMetrics,
        $CnnPredictions,
        (Join-Path $CnnOutput "test_predictions.csv"),
        (Join-Path $CnnOutput "final_test_classification_report.txt"),
        (Join-Path $CnnOutput "final_test_confusion_matrix.csv"),
        (Join-Path $CnnOutput "training_config.json")
    )
    $CnnArchitectures = if ([string]$Settings.CnnArchitecture -eq "all") { @("lenet", "vgg", "resnet") } else { @([string]$Settings.CnnArchitecture) }
    foreach ($architecture in $CnnArchitectures) {
        $architectureRoot = Join-Path $CnnOutput $architecture
        foreach ($name in @("history.csv", "validation_classification_report.txt", "validation_predictions.csv", "model.pt", "best_checkpoint.pt")) {
            $CnnExpected += Join-Path $architectureRoot $name
        }
    }
    $CnnSignature = @{ Prepare = $PrepareSignature; Manifest = Get-FileFingerprint $Manifest; Splits = Get-FileFingerprint $Splits; Classes = @($Settings.Classes); Architecture = [string]$Settings.CnnArchitecture; Epochs = [int]$Settings.CnnEpochs; Batch = [int]$Settings.CnnBatchSize; TopClasses = [int]$Settings.TopClasses; Maximum = [int]$Settings.MaxTracksPerClass; Minimum = [int]$Settings.MinimumTracksPerClass; ValidationSize = 0.15; TestSize = 0.15 }
    Invoke-Step "cnn" $CnnSignature $CnnExpected $Resume {
        $arguments = @("-m", "echopath", "train-cnn", "--manifest", $Manifest, "--dataset-root", $DatasetRoot, "--output-dir", $CnnOutput, "--splits", $Splits, "--label-column", "genre_label", "--architecture", [string]$Settings.CnnArchitecture, "--epochs", [string]$Settings.CnnEpochs, "--batch-size", [string]$Settings.CnnBatchSize, "--audio-duration", [string]$Settings.AudioDurationSeconds, "--top-classes", [string]$Settings.TopClasses, "--validation-size", "0.15", "--test-size", "0.15", "--min-per-class", [string]$Settings.MinimumTracksPerClass, "--mixed-precision")
        $arguments += "--formal-evaluation"
        $arguments += "--classes"
        $arguments += [string[]]$Settings.Classes
        if ([int]$Settings.MaxTracksPerClass -gt 0) { $arguments += @("--balance-classes", "--max-per-class", [string]$Settings.MaxTracksPerClass) }
        if ($Resume) { $arguments += "--resume" }
        Invoke-Checked $VenvPython $arguments "Run CNN experiments"
    }

    $EnrichSignature = @{ Manifest = Get-FileFingerprint $Manifest; Features = Get-FileFingerprint $Features; CnnPredictions = Get-FileFingerprint $CnnPredictions }
    Invoke-Step "enrich" $EnrichSignature @($EnrichedManifest) $Resume {
        Invoke-Checked $VenvPython @("-m", "echopath", "enrich-manifest", "--manifest", $Manifest, "--features", $Features, "--cnn-predictions", $CnnPredictions, "--output", $EnrichedManifest) "Enrich manifest"
    }

    $SearchCsv = Join-Path $SearchOutput "search_benchmark.csv"
    $SearchSummary = Join-Path $SearchOutput "search_benchmark_summary.csv"
    $SearchMetadata = Join-Path $SearchOutput "search_benchmark_metadata.json"
    $SearchSignature = @{ EnrichedManifest = Get-FileFingerprint $EnrichedManifest; Cases = [int]$Settings.SearchCases; Repetitions = [int]$Settings.SearchRepetitions; EvaluationSplit = "test"; PlaylistLength = 5; TempoPolicy = "lift" }
    Invoke-Step "search" $SearchSignature @($SearchCsv, $SearchSummary, $SearchMetadata) $Resume {
        Invoke-Checked $VenvPython @("-m", "echopath", "benchmark-search", "--manifest", $EnrichedManifest, "--output", $SearchCsv, "--playlist-length", "5", "--max-cases", [string]$Settings.SearchCases, "--repetitions", [string]$Settings.SearchRepetitions, "--evaluation-split", "test", "--tempo-policy", "lift") "Run search experiments"
    }

    $AblationCsv = Join-Path $SearchOutput "search_ablations.csv"
    $AblationSummary = Join-Path $SearchOutput "search_ablations_summary.csv"
    $AblationMetadata = Join-Path $SearchOutput "search_ablations_metadata.json"
    $AblationSignature = @{ Search = $SearchSignature; Algorithm = "astar" }
    Invoke-Step "search-ablations" $AblationSignature @($AblationCsv, $AblationSummary, $AblationMetadata) $Resume {
        Invoke-Checked $VenvPython @("-m", "echopath", "benchmark-search", "--manifest", $EnrichedManifest, "--output", $AblationCsv, "--playlist-length", "5", "--max-cases", [string]$Settings.SearchCases, "--repetitions", [string]$Settings.SearchRepetitions, "--evaluation-split", "test", "--algorithms", "astar", "--ablations", "no-ml-signals", "no-target-ranking", "no-hill-climbing", "no-heuristic-target", "no-heuristic-signals", "no-heuristic-depth", "--neighbor-limits", "4", "16", "--tempo-policy", "lift") "Run search ablations"
    }

    $ReportOutput = Join-Path $ResultsRoot "report"
    $ReportSummary = Join-Path $ReportOutput "research_summary.md"
    $ReportManifest = Join-Path $ReportOutput "artifact_manifest.json"
    $ReportExpected = @(
        $ReportSummary,
        $ReportManifest,
        (Join-Path $ReportOutput "tables\classical_validation.csv"),
        (Join-Path $ReportOutput "tables\cnn_validation.csv"),
        (Join-Path $ReportOutput "tables\search_primary.csv"),
        (Join-Path $ReportOutput "tables\search_ablations.csv"),
        (Join-Path $ReportOutput "figures\classical_macro_f1.png"),
        (Join-Path $ReportOutput "figures\cnn_macro_f1.png"),
        (Join-Path $ReportOutput "figures\search_target_success.png"),
        (Join-Path $ReportOutput "figures\search_runtime.png")
    )
    $ReportSignature = @{ ClassicalValidation = Get-FileFingerprint $ClassicalMetrics; ClassicalTest = Get-FileFingerprint $ClassicalTestMetrics; CnnComparison = Get-FileFingerprint $CnnMetrics; CnnTest = Get-FileFingerprint $CnnTestMetrics; Search = Get-FileFingerprint $SearchSummary; Ablations = Get-FileFingerprint $AblationSummary }
    Invoke-Step "report" $ReportSignature $ReportExpected $Resume {
        Invoke-Checked $VenvPython @("-m", "echopath", "summarize-research", "--results-root", $ResultsRoot, "--output-dir", $ReportOutput) "Generate research report"
    }

    Write-Stage "Packaging"
    Write-Host "Files larger than $($Settings.MaximumZipFileSizeMb) MB will be omitted from the results ZIP."
} catch {
    $ExitCode = 1
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "The completed steps are preserved. Run the launcher again after fixing the issue to resume."
} finally {
    if ($TranscriptStarted) {
        Stop-Transcript | Out-Null
    }
    try {
        if ($ExitCode -eq 0 -and (Test-Path $ResultsRoot)) {
            New-ResultsZip ([int]$Settings.MaximumZipFileSizeMb)
            Add-Content $LogPath "Results ZIP: $ZipPath"
            Write-Host "Results ZIP: $ZipPath"
        }
    } catch {
        $ExitCode = 1
        Add-Content $LogPath "Packaging error: $($_.Exception.Message)"
        Write-Host "ERROR: Could not package results: $($_.Exception.Message)" -ForegroundColor Red
    }
    Set-Location $RepoRoot
}

exit $ExitCode
