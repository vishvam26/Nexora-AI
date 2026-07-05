# Windows PowerShell Restore Script — Volume 5 QA & Hardening
# Extracts data from the specified ZIP archive.

param (
    [Parameter(Mandatory=$true)]
    [string]$backupFile
)

if (!(Test-Path $backupFile)) {
    Write-Error "Error: Backup file not found: $backupFile"
    exit 1
}

Write-Host "[Restore] Restoring Windows development assets from $backupFile..." -ForegroundColor Cyan

# Extract ZIP archive
Expand-Archive -Path $backupFile -DestinationPath "storage" -Force

Write-Host "[Restore] Restore completed successfully." -ForegroundColor Green
