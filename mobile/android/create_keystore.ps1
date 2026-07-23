# Generate Play Store upload keystore (run once on your PC).
# Requires Java keytool (Android Studio JBR is fine).

$ErrorActionPreference = "Stop"
$AndroidDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Keystore = Join-Path $AndroidDir "upload-keystore.jks"
$Props = Join-Path $AndroidDir "key.properties"

if (Test-Path $Keystore) {
    Write-Host "Keystore already exists: $Keystore" -ForegroundColor Yellow
    Write-Host "Delete it only if you intentionally want a NEW key (breaks Play updates)."
    exit 0
}

$keytool = $null
$candidates = @(
    "$env:JAVA_HOME\bin\keytool.exe",
    "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe",
    "C:\Program Files\Android\Android Studio\jre\bin\keytool.exe"
)
foreach ($c in $candidates) {
    if ($c -and (Test-Path $c)) { $keytool = $c; break }
}
if (-not $keytool) {
    $cmd = Get-Command keytool -ErrorAction SilentlyContinue
    if ($cmd) { $keytool = $cmd.Source }
}
if (-not $keytool) {
    Write-Host "keytool not found. Install Android Studio (includes JBR) or JDK, then re-run." -ForegroundColor Red
    exit 1
}

$pass = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
Write-Host "Using keytool: $keytool"
& $keytool -genkey -v `
  -keystore $Keystore `
  -storetype JKS `
  -keyalg RSA `
  -keysize 2048 `
  -validity 10000 `
  -alias upload `
  -storepass $pass `
  -keypass $pass `
  -dname "CN=WorkTaskMe, OU=Mobile, O=LyomaStech, L=Cairo, ST=Cairo, C=EG"

@"
storePassword=$pass
keyPassword=$pass
keyAlias=upload
storeFile=upload-keystore.jks
"@ | Set-Content -Path $Props -Encoding ASCII

Write-Host ""
Write-Host "Created:" -ForegroundColor Green
Write-Host "  $Keystore"
Write-Host "  $Props"
Write-Host ""
Write-Host "IMPORTANT: Back up both files offline. Do NOT commit them to Git." -ForegroundColor Yellow
Write-Host "Password is inside key.properties — keep it private."
