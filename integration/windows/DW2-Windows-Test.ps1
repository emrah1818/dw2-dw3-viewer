# DW2 Mod Studio 1.0.0-rc4: Windows-Test. Aendert keine vorhandene Datei ausserhalb dieses Ordners.
# Liest ..\dw2.pak (nur lesen). Ergebnisse in results\ .
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
$res = Join-Path $here 'results'
New-Item -ItemType Directory -Force $res | Out-Null
$log = Join-Path $res 'summary.txt'
function L($t) { $line = "$(Get-Date -Format 'HH:mm:ss') $t"; Write-Host $line; Add-Content -Path $log -Value $line -Encoding utf8 }
Set-Content -Path $log -Value '' -Encoding utf8
L "Start in $here"
foreach ($v in Get-CimInstance Win32_VideoController) { L "GPU: $($v.Name) | Treiber $($v.DriverVersion) | $($v.CurrentHorizontalResolution)x$($v.CurrentVerticalResolution)" }
L "Windows: $((Get-CimInstance Win32_OperatingSystem).Caption) $((Get-CimInstance Win32_OperatingSystem).Version)"
$pak = (Resolve-Path (Join-Path $here '..\dw2.pak')).Path
L "dw2.pak: $pak ($((Get-Item $pak).Length) Bytes)"

# 1. Port und Testprogramme entpacken
$portZip = Get-ChildItem $here -Filter 'DW2_PC_Port_API2_*_Windows_x64.zip' | Select-Object -First 1
if (-not (Test-Path 'Port')) { Expand-Archive $portZip.FullName 'Port'; L "Port entpackt: $($portZip.Name)" }
$port = (Get-ChildItem 'Port' -Directory | Select-Object -First 1).FullName
$exe = Join-Path $port 'dw2.exe'
if (Test-Path 'port-tests.zip') { if (-not (Test-Path 'PortTests')) { Expand-Archive 'port-tests.zip' 'PortTests' } }
if (-not (Test-Path (Join-Path $port 'Mods'))) { Copy-Item -Recurse 'Mods' (Join-Path $port 'Mods') }

# 2. Faehigkeiten
$p0 = Start-Process -FilePath $exe -ArgumentList '--mod-api' -RedirectStandardOutput (Join-Path $res 'mod_api.json') -PassThru -Wait -NoNewWindow
L "mod-api: $((Get-Content (Join-Path $res 'mod_api.json') -Raw).Trim())"

# 3. Renderer-Test mit echter Grafikkarte (synthetische Szene, keine Spieldaten)
if ($false -and (Test-Path 'PortTests\hd_test.exe')) {
  Copy-Item (Join-Path $port 'SDL3.dll') 'PortTests\' -Force -ErrorAction SilentlyContinue
  foreach ($s in 2, 4, 8) {
    $o = Join-Path $res "hd_test_scale$s"
    & 'PortTests\hd_test.exe' --out $o --require-gpu --scale $s > "$o.txt" 2>&1
    L "hd_test --require-gpu --scale $s : Exit $LASTEXITCODE | $((Get-Content "$o.txt" | Select-Object -Last 1))"
  }
  & 'PortTests\modconf_test.exe' > (Join-Path $res 'modconf_test.txt') 2>&1
  L "modconf_test: Exit $LASTEXITCODE"
}

function RunGame($name, [string[]]$extra) {
  $sd = Join-Path $res "$name"
  New-Item -ItemType Directory -Force $sd | Out-Null
  Remove-Item -Recurse -Force 'run_saves' -ErrorAction SilentlyContinue
  Copy-Item -Recurse 'saves' 'run_saves'
  $a = @('--pak', $pak, '--settings', (Join-Path $here 'test_settings.ini'), '--lang', 'en', '--no-update-check', '--save-dir', (Join-Path $here 'run_saves'), '--shot-dir', $sd) + $extra
  $t0 = Get-Date
  $p = Start-Process -FilePath $exe -ArgumentList ($a | ForEach-Object { if ($_ -match ' ') { '"' + $_ + '"' } else { $_ } }) -WorkingDirectory $port -RedirectStandardOutput (Join-Path $res "$name.log") -RedirectStandardError (Join-Path $res "$name.err.log") -PassThru -Wait
  L "$name : Exit $($p.ExitCode) nach $([int]((Get-Date) - $t0).TotalSeconds) s, Bilder: $((Get-ChildItem $sd -Filter *.png).Count)"
}

$battle = (Join-Path $here 'press_battle.txt')
$winshots = @('--window-shot-vb', '4921', '--window-shot-vb', '5421', '--window-shot-vb', '5921', '--window-shot-vb', '6821', '--window-shot-vb', '7921', '--window-shot-vb', '9821', '--window-shot-vb', '11821', '--window-shot-vb', '14321')
$softshots = @()

# GPU-Renderer mit HD-Paket (2048x4096) und ohne Paket zum Vergleich, gleiche Eingaben
RunGame 'gpu_hd' (@('--renderer', 'gpu', '--scale', '4', '--windowed', '--cheats', '--pad2-keys', '--press-file', $battle, '--vblanks', '6300', '--window-shot-vb', '4921', '--window-shot-vb', '5421', '--window-shot-vb', '5921', '--window-shot-vb', '6821', '--window-shot-vb', '7921'))
RunGame 'gpu_nopack' (@('--renderer', 'gpu', '--scale', '4', '--windowed', '--no-texture-packs', '--cheats', '--pad2-keys', '--press-file', $battle, '--vblanks', '6300', '--window-shot-vb', '4921', '--window-shot-vb', '5421', '--window-shot-vb', '5921', '--window-shot-vb', '6821', '--window-shot-vb', '7921'))
L 'FERTIG'
