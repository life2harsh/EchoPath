$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:PIP_NO_INPUT = "1"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptRoot "..\..")).Path
$SettingsPath = Join-Path $ScriptRoot "research-settings.json"
$ResearchRoot = Join-Path $RepoRoot "research\windows"
$ResultsRoot = Join-Path $ResearchRoot "results"
$LogsRoot = Join-Path $ResearchRoot "logs"
$StateRoot = Join-Path $ResearchRoot "state"
$VenvRoot = Join-Path $ResearchRoot ".venv"
$ArchiveRoot = Join-Path $RepoRoot "archive"
$DownloadsRoot = Join-Path $ArchiveRoot "downloads"
$ZipPath = Join-Path $RepoRoot "echopath_research_results.zip"
$FailureZipPath = Join-Path $RepoRoot "echopath_research_FAILED_logs.zip"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogsRoot "research_$RunStamp.log"
$PythonLogPath = Join-Path $LogsRoot "python_$RunStamp.log"
$ExitCode = 0
$TranscriptStarted = $false
$FmaSmallMp3Count = 8000
$MinimumPython = [version]"3.11"
$MaximumPythonExclusive = [version]"3.14"

function Write-Stage([string]$Message) {
    Write-Host ""
    Write-Host "========== $Message ==========" -ForegroundColor Cyan
}

function Invoke-Checked([string]$Program, [string[]]$Arguments, [string]$Description) {
    Write-Host "[$Description]"
    Write-Host ("Command: " + $Program + " " + ($Arguments -join " "))
    & $Program @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Invoke-Native([string]$Program, [string[]]$Arguments) {
    $ErrorActionPreference = "Continue"
    try {
        $arguments = @($Arguments | Where-Object { -not [string]::IsNullOrEmpty($_) })
        if ($arguments.Count -eq 0) {
            $output = & $Program 2>$null
        } else {
            $output = & $Program @arguments 2>$null
        }
        return @{ ExitCode = $LASTEXITCODE; Output = @($output | ForEach-Object { "$_" }) }
    } catch {
        return @{ ExitCode = -1; Output = @() }
    }
}

function Get-PythonVersion([string]$Program, [string[]]$Prefix) {
    $result = Invoke-Native $Program (@($Prefix) + @("-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"))
    if ($result.ExitCode -ne 0) {
        return $null
    }
    $line = $result.Output | Where-Object { $_ -match "^\d+\.\d+\.\d+$" } | Select-Object -Last 1
    if (-not $line) {
        return $null
    }
    return [version]$line.Trim()
}

function Test-SupportedPython($Version) {
    return $null -ne $Version -and $Version -ge $MinimumPython -and $Version -lt $MaximumPythonExclusive
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
    }
    foreach ($minor in @("3.12", "3.11", "3.13")) {
        $candidates += ,@("py", @("-$minor"))
    }
    foreach ($folder in @("Python312", "Python311", "Python313")) {
        $candidates += ,@((Join-Path $env:LOCALAPPDATA "Programs\Python\$folder\python.exe"), @())
    }
    $candidates += ,@("python", @())
    $candidates += ,@("python3", @())

    foreach ($candidate in $candidates) {
        $program = [string]$candidate[0]
        $prefix = [string[]]$candidate[1]
        $command = Get-Command $program -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }
        if ([string]$command.Source -like "*\WindowsApps\*") {
            continue
        }
        $version = Get-PythonVersion $program $prefix
        if (-not $version) {
            continue
        }
        Write-Host "Found Python $version using: $program $($prefix -join ' ')"
        if (Test-SupportedPython $version) {
            return @{ Program = $program; Prefix = $prefix; Version = $version }
        }
    }

    if ($InstallIfMissing -and (Get-Command "winget.exe" -ErrorAction SilentlyContinue)) {
        Write-Host "A supported Python (3.11 to 3.13) was not found. Installing Python 3.12 for the current Windows user."
        Invoke-Native "winget.exe" @("install", "--id", "Python.Python.3.12", "--exact", "--scope", "user", "--silent", "--accept-package-agreements", "--accept-source-agreements") | Out-Null
        $installed = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
        $installedVersion = Get-PythonVersion $installed @()
        if (Test-SupportedPython $installedVersion) {
            Write-Host "Installed Python $installedVersion"
            return @{ Program = $installed; Prefix = @(); Version = $installedVersion }
        }
    }
    throw "Python 3.11, 3.12, or 3.13 (64-bit) is required. Install Python 3.12 from https://www.python.org/downloads/windows/ and run this file again. Python 3.14 is not supported yet by the GPU build of PyTorch."
}

function Get-Mp3Count([string]$Path) {
    if (-not (Test-Path $Path -PathType Container)) {
        return 0
    }
    return @(Get-ChildItem $Path -Recurse -File -Filter *.mp3 -ErrorAction SilentlyContinue).Count
}

function Test-HasAudio([string]$Path) {
    if (-not (Test-Path $Path -PathType Container)) {
        return $false
    }
    $audio = Get-ChildItem $Path -Recurse -File -Include *.mp3,*.wav,*.flac,*.ogg,*.m4a -ErrorAction SilentlyContinue | Select-Object -First 1
    return [bool]$audio
}

function Receive-Archive([string]$Url, [string]$Destination, [int64]$ExpectedBytes, [string]$Name) {
    if ((Test-Path $Destination -PathType Leaf) -and (Get-Item $Destination).Length -eq $ExpectedBytes) {
        return
    }
    if (-not (Get-Command "curl.exe" -ErrorAction SilentlyContinue)) {
        throw "curl.exe is required for the automatic FMA download. Update Windows 10/11, or extract FMA Small under archive\fma_small yourself."
    }
    New-Item (Split-Path $Destination -Parent) -ItemType Directory -Force | Out-Null
    $partial = "$Destination.part"
    if ((Test-Path $Destination -PathType Leaf) -and -not (Test-Path $partial -PathType Leaf)) {
        Move-Item $Destination $partial -Force
    }
    if ((Test-Path $partial -PathType Leaf) -and (Get-Item $partial).Length -gt $ExpectedBytes) {
        Remove-Item $partial -Force
    }
    if (-not ((Test-Path $partial -PathType Leaf) -and (Get-Item $partial).Length -eq $ExpectedBytes)) {
        Invoke-Checked "curl.exe" @("-L", "--fail", "--retry", "10", "--retry-delay", "5", "-C", "-", "-o", $partial, $Url) "Download $Name"
    }
    if ((Get-Item $partial).Length -ne $ExpectedBytes) {
        throw "$Name has an unexpected size. Run the launcher again to resume the download."
    }
    Move-Item $partial $Destination -Force
}

function Expand-Zip([string]$Zip, [string]$Destination) {
    $staging = "$Destination.extracting"
    if (Test-Path $staging) {
        Remove-Item $staging -Recurse -Force
    }
    New-Item $staging -ItemType Directory -Force | Out-Null
    $tar = Join-Path $env:SystemRoot "System32\tar.exe"
    $extracted = $false
    if (Test-Path $tar -PathType Leaf) {
        try {
            Invoke-Checked $tar @("-xf", $Zip, "-C", $staging) "Extract $(Split-Path $Zip -Leaf)"
            $extracted = $true
        } catch {
            Write-Warning "tar.exe could not extract $Zip; falling back to .NET extraction (slower). $($_.Exception.Message)"
            Remove-Item $staging -Recurse -Force
            New-Item $staging -ItemType Directory -Force | Out-Null
        }
    }
    if (-not $extracted) {
        Write-Host "[Extract $(Split-Path $Zip -Leaf)]"
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($Zip, $staging)
    }
    if (Test-Path $Destination) {
        Remove-Item $Destination -Recurse -Force
    }
    Move-Item $staging $Destination
}

function Install-FmaAudio {
    $root = Join-Path $ArchiveRoot "fma_small"
    $audio = Join-Path $root "fma_small"
    if ((Get-Mp3Count $audio) -ge $FmaSmallMp3Count) {
        return $audio
    }
    if ((Get-Mp3Count $root) -ge $FmaSmallMp3Count -and -not (Test-Path $audio)) {
        return $root
    }
    $zip = Join-Path $DownloadsRoot "fma_small.zip"
    Receive-Archive "https://os.unil.cloud.switch.ch/fma/fma_small.zip" $zip 7679594875 "FMA Small (7.7 GB)"
    Expand-Zip $zip $root
    $count = Get-Mp3Count $audio
    if ($count -lt $FmaSmallMp3Count) {
        throw "FMA Small extraction is incomplete: found $count of $FmaSmallMp3Count MP3 files. Run the launcher again."
    }
    Remove-Item $zip -Force
    return $audio
}

function Install-FmaMetadata {
    $root = Join-Path $ArchiveRoot "fma_metadata"
    $tracks = Join-Path $root "fma_metadata\tracks.csv"
    if (Test-Path $tracks -PathType Leaf) {
        return $tracks
    }
    $zip = Join-Path $DownloadsRoot "fma_metadata.zip"
    Receive-Archive "https://os.unil.cloud.switch.ch/fma/fma_metadata.zip" $zip 358412441 "FMA metadata (342 MB)"
    Expand-Zip $zip $root
    if (-not (Test-Path $tracks -PathType Leaf)) {
        throw "FMA metadata extraction did not produce $tracks. Run the launcher again."
    }
    return $tracks
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
        if (-not (Test-HasAudio $candidate)) {
            throw "Dataset override contains no supported audio files: $candidate"
        }
        return (Resolve-Path $candidate).Path
    }

    foreach ($candidate in @((Join-Path $RepoRoot "data\fma_small"), (Join-Path $RepoRoot "data"))) {
        if (Test-HasAudio $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }
    if ($DownloadIfMissing) {
        return (Resolve-Path (Install-FmaAudio)).Path
    }
    foreach ($candidate in @((Join-Path $ArchiveRoot "fma_small\fma_small"), (Join-Path $ArchiveRoot "fma_small"))) {
        if (Test-HasAudio $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }
    throw "No audio dataset was found. Set DownloadDatasetIfMissing to true in $SettingsPath, or extract FMA Small and set DatasetRoot."
}

function Resolve-Metadata([string]$ConfiguredPath, [string]$DatasetRoot, [bool]$DownloadIfMissing) {
    $override = $env:ECHOPATH_METADATA_CSV
    if ([string]::IsNullOrWhiteSpace($override)) {
        $override = $ConfiguredPath
    }
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $expanded = [Environment]::ExpandEnvironmentVariables($override)
        if (-not [IO.Path]::IsPathRooted($expanded)) {
            $expanded = Join-Path $RepoRoot $expanded
        }
        if (-not (Test-Path $expanded -PathType Leaf)) {
            throw "MetadataCsv override does not exist: $expanded"
        }
        return (Resolve-Path $expanded).Path
    }
    $candidates = @(
        (Join-Path $ArchiveRoot "fma_metadata\fma_metadata\tracks.csv"),
        (Join-Path $ArchiveRoot "fma_metadata\tracks.csv"),
        (Join-Path $DatasetRoot "fma_metadata\tracks.csv"),
        (Join-Path (Split-Path $DatasetRoot -Parent) "fma_metadata\tracks.csv")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate -PathType Leaf) {
            return (Resolve-Path $candidate).Path
        }
    }
    if ($DownloadIfMissing) {
        return (Resolve-Path (Install-FmaMetadata)).Path
    }
    throw "FMA tracks.csv was not found. Set DownloadDatasetIfMissing to true or set MetadataCsv in $SettingsPath."
}

function Get-CudaFromDriver([string]$Driver) {
    $driverVersion = $null
    if (-not [version]::TryParse($Driver, [ref]$driverVersion)) {
        return $null
    }
    $table = @(
        @("570.65", "12.8"),
        @("560.76", "12.6"),
        @("551.61", "12.4"),
        @("531.14", "12.1"),
        @("520.06", "11.8")
    )
    foreach ($row in $table) {
        if ($driverVersion -ge [version]$row[0]) {
            return [version]$row[1]
        }
    }
    return $null
}

function Get-CudaInfo {
    $query = Invoke-Native "nvidia-smi" @("--query-gpu=name,driver_version", "--format=csv,noheader")
    if ($query.ExitCode -ne 0 -or $query.Output.Count -eq 0) {
        return @{ Found = $false; Version = $null; Name = $null; Driver = $null; Details = $null }
    }
    $fields = ([string]($query.Output | Select-Object -First 1)).Split(",")
    $name = $fields[0].Trim()
    $driver = if ($fields.Count -gt 1) { $fields[1].Trim() } else { "" }
    $details = (Invoke-Native "nvidia-smi" @("-q", "-d", "COMPUTE")).Output -join "`n"
    $cudaVersion = $null
    if ($details -match "CUDA Version\s*:?\s*([0-9]+\.[0-9]+)") {
        $cudaVersion = [version]$Matches[1]
    }
    $driverCuda = Get-CudaFromDriver $driver
    if (-not $cudaVersion -or ($driverCuda -and $driverCuda -gt $cudaVersion)) {
        $cudaVersion = $driverCuda
    }
    return @{ Found = $true; Version = $cudaVersion; Name = $name; Driver = $driver; Details = $details.Trim() }
}

function Resolve-TorchIndexes([string]$Setting, $CudaInfo) {
    $override = $env:ECHOPATH_TORCH_INDEX_URL
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $Setting = $override
    }
    if ($Setting -ne "auto") {
        if ($Setting -match "^https?://") {
            return ,@($Setting.TrimEnd("/"))
        }
        return ,@("https://download.pytorch.org/whl/$Setting")
    }
    if (-not $CudaInfo.Found) {
        return ,@("https://download.pytorch.org/whl/cpu")
    }
    $builds = @(
        @("12.8", "cu128"),
        @("12.6", "cu126"),
        @("12.4", "cu124"),
        @("12.1", "cu121"),
        @("11.8", "cu118")
    )
    $indexes = @()
    foreach ($build in $builds) {
        if (-not $CudaInfo.Version -or $CudaInfo.Version -ge [version]$build[0]) {
            $indexes += "https://download.pytorch.org/whl/$($build[1])"
        }
    }
    if ($indexes.Count -eq 0) {
        throw "The NVIDIA driver is too old (CUDA $($CudaInfo.Version)). Install the latest driver from https://www.nvidia.com/Download/index.aspx and run this file again."
    }
    return ,$indexes
}

function Test-TorchGpu([string]$Python) {
    $probe = Join-Path $StateRoot "gpu_probe.py"
    @(
        "import sys, torch",
        "print('PyTorch:', torch.__version__, '| built for CUDA:', torch.version.cuda)",
        "if not torch.cuda.is_available():",
        "    print('CUDA available: no')",
        "    sys.exit(3 if torch.version.cuda is None else 4)",
        "print('GPU:', torch.cuda.get_device_name(0))",
        "x = torch.randn(4, 1, 64, 256, device='cuda', requires_grad=True)",
        "conv = torch.nn.Conv2d(1, 16, 3, padding=1).cuda()",
        "with torch.autocast('cuda', dtype=torch.float16):",
        "    y = conv(x).relu().mean()",
        "y.backward()",
        "torch.cuda.synchronize()",
        "print('CUDA kernel test: ok')"
    ) | Set-Content $probe -Encoding ASCII
    & $Python $probe | Out-Host
    return $LASTEXITCODE
}

function Assert-SafeLocation {
    $inTemp = (-not [string]::IsNullOrWhiteSpace($env:TEMP) -and $RepoRoot.StartsWith($env:TEMP, [StringComparison]::OrdinalIgnoreCase)) -or $RepoRoot -like "*\AppData\Local\Temp\*"
    if ($inTemp) {
        throw "This folder is running from inside a ZIP preview. Right-click the ZIP, choose 'Extract All...', move the folder to C:\EchoPath, and run RUN_ECHOPATH_RESEARCH.bat from there."
    }
    foreach ($oneDrive in @($env:OneDrive, $env:OneDriveConsumer, $env:OneDriveCommercial)) {
        if (-not [string]::IsNullOrWhiteSpace($oneDrive) -and $RepoRoot.StartsWith($oneDrive, [StringComparison]::OrdinalIgnoreCase)) {
            throw "This folder is inside OneDrive, which would try to upload about 20 GB of data. Move the folder to C:\EchoPath and run it again."
        }
    }
    $longPaths = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -ErrorAction SilentlyContinue).LongPathsEnabled
    if ($longPaths -ne 1 -and $RepoRoot.Length -gt 80) {
        throw "The folder path is too long for Windows to install PyTorch ($($RepoRoot.Length) characters). Move the folder to C:\EchoPath and run it again."
    }
}

function Assert-FreeSpace([double]$RequiredGb) {
    try {
        $drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($RepoRoot))
        $freeGb = [math]::Round($drive.AvailableFreeSpace / 1GB, 1)
    } catch {
        Write-Warning "Could not check free disk space: $($_.Exception.Message)"
        return
    }
    Write-Host "Free disk space on $($drive.Name): $freeGb GB (about $RequiredGb GB needed)"
    if ($freeGb -lt $RequiredGb) {
        throw "Not enough free disk space on $($drive.Name): $freeGb GB free, about $RequiredGb GB needed. Free up space or move the folder to a larger drive, then run again."
    }
}

function Set-LongRunConsole([bool]$Enable) {
    try {
        if (-not ("EchoPath.Native" -as [type])) {
            Add-Type -Namespace EchoPath -Name Native -MemberDefinition @"
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int nStdHandle);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint lpMode);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode);
"@
        }
        if ($Enable) {
            [void][EchoPath.Native]::SetThreadExecutionState([uint32]2147483649)
            $handle = [EchoPath.Native]::GetStdHandle(-10)
            [uint32]$mode = 0
            if ([EchoPath.Native]::GetConsoleMode($handle, [ref]$mode)) {
                $newMode = [uint32]($mode -bor 0x80)
                if ($newMode -band 0x40) {
                    $newMode = [uint32]($newMode - 0x40)
                }
                [void][EchoPath.Native]::SetConsoleMode($handle, $newMode)
            }
        } else {
            [void][EchoPath.Native]::SetThreadExecutionState([uint32]2147483648)
        }
    } catch {
        Write-Warning "Could not adjust sleep or console settings: $($_.Exception.Message)"
    }
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
    foreach ($logFile in @($LogPath, $PythonLogPath)) {
        if (Test-Path $logFile -PathType Leaf) {
            $packageFiles += Get-Item $logFile
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

function New-FailureZip {
    $stage = Join-Path $env:TEMP "echopath_research_failure_$RunStamp"
    if (Test-Path $stage) {
        Remove-Item $stage -Recurse -Force
    }
    New-Item $stage -ItemType Directory -Force | Out-Null
    $candidates = @($LogPath, $PythonLogPath, $SettingsPath, (Join-Path $ResultsRoot "data\ingest_failures.txt"))
    if (Test-Path $StateRoot -PathType Container) {
        $candidates += @(Get-ChildItem $StateRoot -File -Filter *.json | ForEach-Object { $_.FullName })
    }
    foreach ($file in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($file) -and (Test-Path $file -PathType Leaf)) {
            Copy-Item $file (Join-Path $stage (Split-Path $file -Leaf)) -Force
        }
    }
    if (Test-Path $FailureZipPath) {
        Remove-Item $FailureZipPath -Force
    }
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $FailureZipPath -CompressionLevel Optimal
    Remove-Item $stage -Recurse -Force
}

function Show-FileInExplorer([string]$Path) {
    try {
        Start-Process "explorer.exe" "/select,`"$Path`""
    } catch {
        Write-Host "Open this folder to find it: $(Split-Path $Path -Parent)"
    }
}

try {
    if (-not (Test-Path $SettingsPath -PathType Leaf)) {
        throw "Settings file is missing: $SettingsPath"
    }
    $Settings = Get-Content $SettingsPath -Raw | ConvertFrom-Json
    New-Item $ResultsRoot, $LogsRoot, $StateRoot -ItemType Directory -Force | Out-Null
    foreach ($staleZip in @($ZipPath, $FailureZipPath)) {
        if (Test-Path $staleZip -PathType Leaf) {
            Remove-Item $staleZip -Force
        }
    }
    Start-Transcript -Path $LogPath -Force | Out-Null
    $TranscriptStarted = $true
    Set-Location $RepoRoot
    Set-LongRunConsole $true
    $env:ECHOPATH_LOG_FILE = $PythonLogPath

    Write-Host "EchoPath research run. This usually takes several hours."
    Write-Host "Leave this window open. Do not click inside it. Keep the computer plugged in."
    Write-Host "If anything goes wrong, just run RUN_ECHOPATH_RESEARCH.bat again: finished steps are skipped."

    Write-Stage "System checks"
    Write-Host "Repository: $RepoRoot"
    Write-Host "Settings: $SettingsPath"
    Assert-SafeLocation
    $DatasetReady = (-not [string]::IsNullOrWhiteSpace([string]$Settings.DatasetRoot)) -or
        (-not [string]::IsNullOrWhiteSpace($env:ECHOPATH_DATASET_ROOT)) -or
        ((Get-Mp3Count (Join-Path $ArchiveRoot "fma_small\fma_small")) -ge $FmaSmallMp3Count)
    Assert-FreeSpace $(if ($DatasetReady) { 12 } else { 30 })

    $Cuda = Get-CudaInfo
    if ($Cuda.Found) {
        Write-Host "NVIDIA GPU: $($Cuda.Name)"
        Write-Host "NVIDIA driver: $($Cuda.Driver)"
        Write-Host "Driver-reported CUDA: $($Cuda.Version)"
        Write-Host $Cuda.Details
    } else {
        Write-Warning "nvidia-smi was not found. The NVIDIA driver may be missing or no NVIDIA GPU is available."
        if (-not [bool]$Settings.AllowCpuFallback) {
            throw "No NVIDIA GPU driver was found. Install the latest driver from https://www.nvidia.com/Download/index.aspx (or set AllowCpuFallback to true), then run this file again."
        }
    }
    $TorchIndexes = Resolve-TorchIndexes ([string]$Settings.TorchIndexUrl) $Cuda

    $Python = Resolve-Python ([string]$Settings.PythonCommand) ([bool]$Settings.InstallPythonIfMissing)
    $GitRevision = "unavailable"
    $gitResult = Invoke-Native "git" @("-C", $RepoRoot, "rev-parse", "HEAD")
    if ($gitResult.ExitCode -eq 0 -and $gitResult.Output.Count -gt 0) {
        $GitRevision = $gitResult.Output[0].Trim()
        Write-Host "Git revision: $GitRevision"
    } else {
        Write-Host "Git revision: unavailable (not a Git checkout or Git is not installed)"
    }

    Write-Stage "Dataset"
    $DatasetRoot = Resolve-Dataset ([string]$Settings.DatasetRoot) ([bool]$Settings.DownloadDatasetIfMissing)
    $MetadataCsv = Resolve-Metadata ([string]$Settings.MetadataCsv) $DatasetRoot ([bool]$Settings.DownloadDatasetIfMissing)
    $SourceFingerprint = Get-SourceFingerprint $GitRevision
    $DatasetFingerprint = Get-DatasetFingerprint $DatasetRoot
    $MetadataFingerprint = Get-FileFingerprint $MetadataCsv
    Write-Host "Dataset: $DatasetRoot ($($DatasetFingerprint.FileCount) audio files)"
    Write-Host "Metadata: $MetadataCsv"

    Write-Stage "Python environment"
    $VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
    if (Test-Path $VenvPython -PathType Leaf) {
        $venvVersion = Get-PythonVersion $VenvPython @()
        if (-not (Test-SupportedPython $venvVersion)) {
            Write-Host "Recreating the virtual environment (found Python '$venvVersion')."
            Remove-Item $VenvRoot -Recurse -Force
        }
    }
    if (-not (Test-Path $VenvPython -PathType Leaf)) {
        Invoke-Checked $Python.Program (@($Python.Prefix) + @("-m", "venv", $VenvRoot)) "Create virtual environment"
    }
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") "Update packaging tools"
    $TorchMarker = Join-Path $VenvRoot "echopath-torch-index.txt"
    $PreviousTorchIndex = if (Test-Path $TorchMarker -PathType Leaf) { (Get-Content $TorchMarker -Raw).Trim() } else { "" }
    $TorchIndex = $TorchIndexes[0]
    if ($PreviousTorchIndex -and $TorchIndexes -contains $PreviousTorchIndex) {
        $TorchIndex = $PreviousTorchIndex
    }
    Write-Host "PyTorch wheel index: $TorchIndex"
    $TorchArguments = @("-m", "pip", "install", "--index-url", $TorchIndex, "torch>=2.5,<3.0")
    if ($PreviousTorchIndex -and $PreviousTorchIndex -ne $TorchIndex) {
        $TorchArguments += @("--force-reinstall", "--no-deps")
    }
    Invoke-Checked $VenvPython $TorchArguments "Install PyTorch"
    Set-Content $TorchMarker $TorchIndex -Encoding ASCII
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-e", (Join-Path $RepoRoot "training"), "-e", (Join-Path $RepoRoot "backend")) "Install EchoPath dependencies"

    Write-Stage "GPU check"
    $GpuStatus = Test-TorchGpu $VenvPython
    if ($Cuda.Found -and $GpuStatus -ne 0) {
        foreach ($candidate in $TorchIndexes) {
            if ($candidate -eq $TorchIndex) {
                continue
            }
            Write-Host "PyTorch from $TorchIndex cannot use the GPU. Trying $candidate"
            Invoke-Checked $VenvPython @("-m", "pip", "install", "--index-url", $candidate, "torch>=2.5,<3.0", "--force-reinstall", "--no-deps") "Reinstall PyTorch"
            $TorchIndex = $candidate
            Set-Content $TorchMarker $TorchIndex -Encoding ASCII
            $GpuStatus = Test-TorchGpu $VenvPython
            if ($GpuStatus -eq 0) {
                break
            }
        }
    }
    if ($Cuda.Found -and $GpuStatus -ne 0) {
        throw "PyTorch cannot run on this GPU ($($Cuda.Name), driver $($Cuda.Driver)). Install the latest NVIDIA driver from https://www.nvidia.com/Download/index.aspx, restart the computer, and run this file again."
    }
    if (-not $Cuda.Found) {
        Write-Warning "Continuing on the CPU because AllowCpuFallback is true. CNN training will be very slow."
    }

    $Workers = [int]$Settings.Workers
    if ($Workers -le 0) {
        $Workers = [math]::Max(1, [math]::Min([Environment]::ProcessorCount - 1, 8))
    }
    Write-Host "CPU worker processes for audio decoding: $Workers"

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
        $arguments = @("-m", "echopath", "ingest", "--dataset-root", $DatasetRoot, "--output-manifest", $Manifest, "--features-csv", $Features, "--audio-duration", [string]$Settings.AudioDurationSeconds, "--clusters", [string]$Settings.Clusters, "--workers", [string]$Workers, "--resume")
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
        $arguments = @("-m", "echopath", "train-cnn", "--manifest", $Manifest, "--dataset-root", $DatasetRoot, "--output-dir", $CnnOutput, "--splits", $Splits, "--label-column", "genre_label", "--architecture", [string]$Settings.CnnArchitecture, "--epochs", [string]$Settings.CnnEpochs, "--batch-size", [string]$Settings.CnnBatchSize, "--audio-duration", [string]$Settings.AudioDurationSeconds, "--top-classes", [string]$Settings.TopClasses, "--validation-size", "0.15", "--test-size", "0.15", "--min-per-class", [string]$Settings.MinimumTracksPerClass, "--preprocess-workers", [string]$Workers)
        if ($Cuda.Found) { $arguments += "--mixed-precision" }
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
    $ReportSignature = @{ EnrichedManifest = Get-FileFingerprint $EnrichedManifest; Features = Get-FileFingerprint $Features; ClassicalValidation = Get-FileFingerprint $ClassicalMetrics; ClassicalTest = Get-FileFingerprint $ClassicalTestMetrics; CnnComparison = Get-FileFingerprint $CnnMetrics; CnnTest = Get-FileFingerprint $CnnTestMetrics; Search = Get-FileFingerprint $SearchSummary; Ablations = Get-FileFingerprint $AblationSummary }
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
    Set-LongRunConsole $false
    if ($TranscriptStarted) {
        Stop-Transcript | Out-Null
    }
    try {
        if ($ExitCode -eq 0 -and (Test-Path $ResultsRoot)) {
            New-ResultsZip ([int]$Settings.MaximumZipFileSizeMb)
            Add-Content $LogPath "Results ZIP: $ZipPath"
        }
    } catch {
        $ExitCode = 1
        Add-Content $LogPath "Packaging error: $($_.Exception.Message)"
        Write-Host "ERROR: Could not package results: $($_.Exception.Message)" -ForegroundColor Red
    }
    if ($ExitCode -eq 0) {
        Write-Host ""
        Write-Host "ALL DONE. Send this file back:" -ForegroundColor Green
        Write-Host "  $ZipPath" -ForegroundColor Green
        Show-FileInExplorer $ZipPath
    } else {
        try {
            New-FailureZip
            Write-Host ""
            Write-Host "The run stopped. Send this file back so the problem can be fixed:" -ForegroundColor Yellow
            Write-Host "  $FailureZipPath" -ForegroundColor Yellow
            Write-Host "After a fix, run RUN_ECHOPATH_RESEARCH.bat again; finished steps are skipped." -ForegroundColor Yellow
            Show-FileInExplorer $FailureZipPath
        } catch {
            Write-Host "Could not create the failure ZIP. Send the files in $LogsRoot instead." -ForegroundColor Yellow
        }
    }
    Set-Location $RepoRoot
}

exit $ExitCode
