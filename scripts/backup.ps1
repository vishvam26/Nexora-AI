# Windows PowerShell Backup Script — Volume 5 QA & Hardening
# Compresses database files and local storage upload configurations.

$backupDir = "storage/backups"
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipFile = "$backupDir/backup_$timestamp.zip"

Write-Host "[Backup] Collecting Windows development assets..." -ForegroundColor Cyan

# Package storage folders
Compress-Archive -Path "storage/*" -DestinationPath $zipFile -Force -Exclude "storage/backups"

Write-Host "[Backup] Windows ZIP archive created successfully at: $zipFile" -ForegroundColor Green
