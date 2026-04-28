param(
  [int[]]$Ports = @(5174, 8000)
)

$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -in $Ports }

if (-not $listeners) {
  Write-Host ("No listeners found on ports: {0}" -f ($Ports -join ", "))
  exit 0
}

$targetPids = $listeners |
  Select-Object -ExpandProperty OwningProcess -Unique

foreach ($targetPid in $targetPids) {
  try {
    $process = Get-Process -Id $targetPid -ErrorAction Stop
    Stop-Process -Id $targetPid -Force -ErrorAction Stop
    Write-Host ("Stopped PID {0} ({1})" -f $targetPid, $process.ProcessName)
  } catch {
    Write-Warning ("Failed to stop PID {0}: {1}" -f $targetPid, $_.Exception.Message)
  }
}

Start-Sleep -Seconds 1

$remaining = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -in $Ports }

if ($remaining) {
  Write-Warning "Some ports are still occupied:"
  $remaining |
    Select-Object LocalPort, OwningProcess, State |
    Format-Table -AutoSize
  exit 1
}

Write-Host ("Ports released: {0}" -f ($Ports -join ", "))
