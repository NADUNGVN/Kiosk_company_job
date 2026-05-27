param(
    [string]$TokenName = "MSTTS_V110_viVN_An"
)

$ErrorActionPreference = "Stop"

$source = "HKLM:\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens\$TokenName"
$destinationRoot = "HKLM:\SOFTWARE\Microsoft\Speech\Voices\Tokens"
$destination = "$destinationRoot\$TokenName"
$backupDir = Join-Path $PSScriptRoot "registry_backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

function Assert-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an elevated PowerShell session (Run as Administrator)."
    }
}

function Export-RegKey {
    param(
        [string]$RegPath,
        [string]$OutputFile
    )

    $nativePath = $RegPath -replace "^HKLM:\\", "HKLM\"
    & reg.exe export $nativePath $OutputFile /y | Out-Null
}

Assert-Admin

if (-not (Test-Path $source)) {
    throw "Source OneCore voice does not exist: $source"
}

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$sourceBackup = Join-Path $backupDir "$TokenName.onecore.$timestamp.reg"
Export-RegKey -RegPath $source -OutputFile $sourceBackup
Write-Host "Backed up source voice token: $sourceBackup"

if (Test-Path $destination) {
    $destinationBackup = Join-Path $backupDir "$TokenName.sapi_existing.$timestamp.reg"
    Export-RegKey -RegPath $destination -OutputFile $destinationBackup
    Write-Host "Backed up existing SAPI token: $destinationBackup"
}

New-Item -ItemType Directory -Force -Path $destinationRoot | Out-Null
Copy-Item -Path $source -Destination $destinationRoot -Recurse -Force

Write-Host ""
Write-Host "Copied OneCore voice token to SAPI:"
Write-Host "  From: $source"
Write-Host "  To:   $destination"
Write-Host ""
Write-Host "Close and reopen the terminal, then run:"
Write-Host "  python experiments\realtime_voicebot_lab\kiosk_tts_probe\windows_tts_realtime_probe.py --list-voices"
Write-Host "  python experiments\realtime_voicebot_lab\kiosk_tts_probe\windows_tts_realtime_probe.py --backend sapi --voice-contains `"Microsoft An`""
