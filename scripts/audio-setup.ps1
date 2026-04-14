# audio-setup.ps1 ¡ª VoiceMeeter auto-configuration for Interview Assistant
# Usage:
#   .\audio-setup.ps1 -Action setup    # configure audio for interview
#   .\audio-setup.ps1 -Action restore  # restore original audio settings
#   .\audio-setup.ps1 -Action check    # check if VoiceMeeter is installed

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("setup", "restore", "check")]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$StateFile = Join-Path $PSScriptRoot ".audio-state.json"
$VmPath = "C:\Program Files (x86)\VB\Voicemeeter"
$VmDll = Join-Path $VmPath "VoicemeeterRemote64.dll"
$VmExe = Join-Path $VmPath "voicemeeter.exe"

# ©¤©¤ PolicyConfig COM for setting default audio device ©¤©¤
function Ensure-PolicyConfig {
    if (-not ([System.Management.Automation.PSTypeName]'AudioSwitcher').Type) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

[Guid("f8679f50-850a-41cf-9c72-430f290290c8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPolicyConfig {
    int GetMixFormat(); int GetDeviceFormat(); int ResetDeviceFormat(); int SetDeviceFormat();
    int GetProcessingPeriod(); int SetProcessingPeriod(); int GetShareMode(); int SetShareMode();
    int GetPropertyValue(); int SetPropertyValue();
    [PreserveSig] int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string deviceId, int role);
    int SetEndpointVisibility();
}
[ComImport, Guid("870af99c-171d-4f9e-af0d-e63df40c2bc9")] class PolicyConfigClient {}

public class AudioSwitcher {
    public static void SetDefault(string deviceId) {
        var pc = (IPolicyConfig)new PolicyConfigClient();
        pc.SetDefaultEndpoint(deviceId, 0);
        pc.SetDefaultEndpoint(deviceId, 1);
        pc.SetDefaultEndpoint(deviceId, 2);
    }
}
'@
    }
}

# ©¤©¤ Find a device ID from the registry by partial name match ©¤©¤
function Find-AudioDevice {
    param([string]$NamePattern, [string]$Type)
    $regPath = if ($Type -eq "Render") {
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
    } else {
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture"
    }
    $prefix = if ($Type -eq "Render") { "{0.0.0.00000000}" } else { "{0.0.1.00000000}" }

    foreach ($key in (Get-ChildItem $regPath -ErrorAction SilentlyContinue)) {
        $props = Get-ItemProperty "$($key.PSPath)\Properties" -ErrorAction SilentlyContinue
        if ($props) {
            $name = $props.'{a45c254e-df1c-4efd-8020-67d146a850e0},2'
            if ($name -and $name -like "*$NamePattern*") {
                return @{ Name = $name; Id = "$prefix.$($key.PSChildName)" }
            }
        }
    }
    return $null
}

# ©¤©¤ Get current default playback device ©¤©¤
function Get-CurrentDefault {
    $regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
    # Fallback: find the device that is currently "default" by checking Role:0 in the registry
    # Simpler approach: use the render endpoint with DeviceState=1 and Role_0
    $renderPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
    foreach ($key in (Get-ChildItem $renderPath -ErrorAction SilentlyContinue)) {
        $props = Get-ItemProperty "$($key.PSPath)\Properties" -ErrorAction SilentlyContinue
        if ($props) {
            $name = $props.'{a45c254e-df1c-4efd-8020-67d146a850e0},2'
            $state = (Get-ItemProperty $key.PSPath -ErrorAction SilentlyContinue).DeviceState
            if ($name -and $state -eq 1 -and $name -notlike "*Voicemeeter*") {
                return @{ Name = $name; Id = "{0.0.0.00000000}.$($key.PSChildName)" }
            }
        }
    }
    return $null
}

# ©¤©¤ Load VoiceMeeter Remote API ©¤©¤
function Ensure-VmRemote {
    if (-not ([System.Management.Automation.PSTypeName]'VmRemote').Type) {
        $escaped = $VmDll.Replace('\', '\\')
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class VmRemote {
    [DllImport("$escaped", EntryPoint = "VBVMR_Login")]
    public static extern int Login();
    [DllImport("$escaped", EntryPoint = "VBVMR_Logout")]
    public static extern int Logout();
    [DllImport("$escaped", EntryPoint = "VBVMR_SetParameterStringA")]
    public static extern int SetParamStr(
        [MarshalAs(UnmanagedType.LPStr)] string p,
        [MarshalAs(UnmanagedType.LPStr)] string v);
    [DllImport("$escaped", EntryPoint = "VBVMR_SetParameterFloat")]
    public static extern int SetParamFloat(
        [MarshalAs(UnmanagedType.LPStr)] string p, float v);
    [DllImport("$escaped", EntryPoint = "VBVMR_IsParametersDirty")]
    public static extern int IsParamsDirty();
}
"@
    }
}

# ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T CHECK ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T
if ($Action -eq "check") {
    if (Test-Path $VmExe) {
        Write-Host "INSTALLED"
        exit 0
    } else {
        Write-Host "NOT_INSTALLED"
        exit 1
    }
}

# ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T SETUP ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T
if ($Action -eq "setup") {
    # 1) Start VoiceMeeter if not running
    $vmProc = Get-Process voicemeeter -ErrorAction SilentlyContinue
    if (-not $vmProc) {
        Write-Host "[1/5] Starting VoiceMeeter..." -ForegroundColor Cyan
        Start-Process $VmExe
        Start-Sleep -Seconds 3
    } else {
        Write-Host "[1/5] VoiceMeeter already running" -ForegroundColor Green
    }

    # 2) Save current default playback device
    Write-Host "[2/5] Saving current audio settings..." -ForegroundColor Cyan
    $original = Get-CurrentDefault
    if ($original) {
        @{ OriginalDeviceId = $original.Id; OriginalDeviceName = $original.Name } |
            ConvertTo-Json | Set-Content $StateFile -Encoding UTF8
        Write-Host "  Saved: $($original.Name)"
    }

    # 3) Set VoiceMeeter Input as default playback
    Write-Host "[3/5] Setting VoiceMeeter as default playback..." -ForegroundColor Cyan
    Ensure-PolicyConfig
    $vmInput = Find-AudioDevice -NamePattern "Voicemeeter Input" -Type "Render"
    if ($vmInput) {
        [AudioSwitcher]::SetDefault($vmInput.Id)
        Write-Host "  OK: $($vmInput.Name)" -ForegroundColor Green
    } else {
        Write-Host "  WARN: VoiceMeeter Input not found" -ForegroundColor Yellow
    }

    # 4) Configure VoiceMeeter routing
    Write-Host "[4/5] Configuring VoiceMeeter routing..." -ForegroundColor Cyan
    Ensure-VmRemote
    $login = [VmRemote]::Login()
    if ($login -ne 0) {
        Write-Host "  WARN: Could not connect to VoiceMeeter API (code $login)" -ForegroundColor Yellow
    } else {
        Start-Sleep -Seconds 1

        # Hardware Input 1 -> physical microphone (auto-detect)
        $micNames = @("Microphone Array", "Mic", "Realtek", "USB")
        $micSet = $false
        foreach ($mic in $micNames) {
            $r = [VmRemote]::SetParamStr("Strip[0].device.wdm", $mic)
            if ($r -eq 0) {
                Write-Host "  Microphone: $mic" -ForegroundColor Green
                $micSet = $true
                break
            }
        }
        if (-not $micSet) {
            Write-Host "  WARN: Could not auto-detect microphone, please set manually in VoiceMeeter" -ForegroundColor Yellow
        }

        # A1 output -> physical speakers (try common names)
        $spkNames = @("Realtek", "Speakers", "Headphones", "USB")
        foreach ($spk in $spkNames) {
            $r = [VmRemote]::SetParamStr("Bus[0].device.wdm", $spk)
            if ($r -eq 0) {
                Write-Host "  Speakers: $spk" -ForegroundColor Green
                break
            }
        }
        [VmRemote]::SetParamFloat("Bus[0].Mute", 0.0) | Out-Null

        # Hardware input (mic) -> A1 (hear) + B1 (capture), unmuted
        [VmRemote]::SetParamFloat("Strip[0].A1", 1.0) | Out-Null
        [VmRemote]::SetParamFloat("Strip[0].B1", 1.0) | Out-Null
        [VmRemote]::SetParamFloat("Strip[0].Mute", 0.0) | Out-Null

        # Virtual input (meeting audio) -> A1 (hear) + B1 (capture)
        [VmRemote]::SetParamFloat("Strip[2].A1", 1.0) | Out-Null
        [VmRemote]::SetParamFloat("Strip[2].B1", 1.0) | Out-Null

        # Unmute B1 bus output
        [VmRemote]::SetParamFloat("Bus[2].Mute", 0.0) | Out-Null

        Start-Sleep -Milliseconds 500
        [VmRemote]::IsParamsDirty() | Out-Null
        [VmRemote]::Logout() | Out-Null
        Write-Host "  OK: Routing configured" -ForegroundColor Green
    }

    Write-Host "[5/5] Audio setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  In browser, select 'VoiceMeeter Out B1' as microphone" -ForegroundColor Yellow
    exit 0
}

# ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T RESTORE ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T
if ($Action -eq "restore") {
    if (-not (Test-Path $StateFile)) {
        Write-Host "No saved audio state to restore." -ForegroundColor Yellow
        exit 0
    }

    $state = Get-Content $StateFile -Raw | ConvertFrom-Json
    Write-Host "Restoring audio: $($state.OriginalDeviceName)..." -ForegroundColor Cyan

    Ensure-PolicyConfig
    [AudioSwitcher]::SetDefault($state.OriginalDeviceId)

    Remove-Item $StateFile -ErrorAction SilentlyContinue
    Write-Host "[OK] Audio restored to: $($state.OriginalDeviceName)" -ForegroundColor Green
    exit 0
}
