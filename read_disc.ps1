#Requires -Version 5.1
# Read-only drive inventory; media access happens only with -IncludeMedia.
param(
    [switch]$IncludeMedia,
    [string]$DriveLetter = ''
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$result = [ordered]@{ Drives = @(); Error = $null }
try {
    $master = New-Object -ComObject IMAPI2.MsftDiscMaster2
    $drives = @(
        foreach ($id in $master) {
            $recorder = New-Object -ComObject IMAPI2.MsftDiscRecorder2
            $recorder.InitializeDiscRecorder($id)
            $volumes = @($recorder.VolumePathNames)
            $item = [ordered]@{
                DriveLetter = if ($volumes.Count -gt 0) { ([string]$volumes[0]).Substring(0, 2).ToUpperInvariant() } else { '' }
                VolumePaths = @($volumes | ForEach-Object { [string]$_ })
                Vendor = ([string]$recorder.VendorId).Trim()
                Product = ([string]$recorder.ProductId).Trim()
                Revision = ([string]$recorder.ProductRevision).Trim()
                MediaQueried = $false
                MediaTypeCode = $null
                MediaStatusCode = $null
                TotalSectors = $null
                FreeSectors = $null
                PhysicallyBlank = $null
                HeuristicallyBlank = $null
                VolumeLabel = $null
                FileSystem = $null
                Error = $null
            }
            if ($IncludeMedia -and (!$DriveLetter -or $item.DriveLetter -eq $DriveLetter)) {
                $item.MediaQueried = $true
                try {
                    $format = New-Object -ComObject IMAPI2.MsftDiscFormat2Data
                    $format.Recorder = $recorder
                    $item.MediaTypeCode = [int]$format.CurrentPhysicalMediaType
                    $item.MediaStatusCode = [int]$format.CurrentMediaStatus
                    $item.TotalSectors = [int64]$format.TotalSectorsOnMedia
                    $item.FreeSectors = [int64]$format.FreeSectorsOnMedia
                    $item.PhysicallyBlank = [bool]$format.MediaPhysicallyBlank
                    $item.HeuristicallyBlank = [bool]$format.MediaHeuristicallyBlank
                }
                catch {
                    $item.Error = $_.Exception.Message
                }
                if ($item.DriveLetter) {
                    try {
                        $driveInfo = [System.IO.DriveInfo]::new($item.DriveLetter)
                        if ($driveInfo.IsReady) {
                            $item.VolumeLabel = $driveInfo.VolumeLabel
                            $item.FileSystem = $driveInfo.DriveFormat
                        }
                    }
                    catch { }
                }
            }
            [pscustomobject]$item
        }
    )
    $result.Drives = $drives
}
catch {
    $result.Error = $_.Exception.Message
}

[Console]::WriteLine(($result | ConvertTo-Json -Depth 5 -Compress))
