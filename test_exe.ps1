$exePath = "D:\ANEXOS KDP Y DIGITALES\KDP_MASTER\dist\KDP_Master_Suite_v3.4.7\KDP_Master_Suite_v3.4.7.exe"
$errLog = "$env:TEMP\kdp_exe_test.log"

$proc = Start-Process -FilePath $exePath -PassThru -RedirectStandardError $errLog -WindowStyle Hidden
Start-Sleep -Seconds 6

if ($proc.HasExited) {
    Write-Host "ERROR: Proceso salió con código: $($proc.ExitCode)"
} else {
    Write-Host "OK: App corriendo"
    Stop-Process -Id $proc.Id -Force
}

if (Test-Path $errLog) {
    Write-Host "=== ERROR LOG ==="
    Get-Content $errLog
}