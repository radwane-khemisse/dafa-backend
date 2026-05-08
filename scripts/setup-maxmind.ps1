param(
  [Parameter(Mandatory = $true)]
  [string]$AccountId,

  [Parameter(Mandatory = $true)]
  [string]$LicenseKey,

  [string]$OutputDir = "./maxmind",

  [string[]]$EditionIds = @("GeoLite2-City", "GeoLite2-Country", "GeoLite2-Anonymous-IP")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

foreach ($edition in $EditionIds) {
  $archivePath = Join-Path $OutputDir "$edition.tar.gz"
  $url = "https://download.maxmind.com/geoip/databases/$edition/download?suffix=tar.gz"
  $pair = "${AccountId}:${LicenseKey}"
  $token = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))

  Invoke-WebRequest -Uri $url -Headers @{ Authorization = "Basic $token" } -OutFile $archivePath
  tar -xzf $archivePath -C $OutputDir
  $database = Get-ChildItem -Path $OutputDir -Recurse -Filter "$edition.mmdb" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($database) {
    Copy-Item -Force -LiteralPath $database.FullName -Destination (Join-Path $OutputDir "$edition.mmdb")
  }
}

Write-Host "MaxMind databases are ready in $((Resolve-Path $OutputDir).Path)"
