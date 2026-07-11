<#
.SYNOPSIS
    SSH 瀹¤鎶€鑳藉寘瀹夎鑴氭湰
.DESCRIPTION
    涓€閿畬鎴愶細
    1. 妫€娴嬭嚜甯﹀祵鍏ュ紡 Python 3.11.8 杩愯鏃讹紙鏃犻渶绯荤粺瀹夎 Python锛?    2. 楠岃瘉 paramiko 渚濊禆锛堝凡棰勮锛岀己澶辨椂鑷姩浠?wheels 绂荤嚎瀹夎鎴栬仈缃戝畨瑁咃級
    3. 璁剧疆 AGENT_SSH_AUDIT_HOME 鐜鍙橀噺锛堜紭鍏?Machine 绾э紝澶辫触闄嶇骇 User 绾э級
    4. 鍒涘缓 logs 鐩綍缁撴瀯
    5. 鍒濆鍖?credentials.txt 妯℃澘
    6. 楠岃瘉瀹夎瀹屾暣鎬?.NOTES
    涓嶉渶瑕佺鐞嗗憳鏉冮檺锛圡achine 绾у啓澶辫触浼氳嚜鍔ㄩ檷绾т负 User 绾э級
#>
param(
    [switch]$Uninstall  # 鍗歌浇锛氱Щ闄ょ幆澧冨彉閲?)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

# === 棰滆壊杈撳嚭 ===
function Write-Step($msg) { Write-Host "  [+] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  [X] $msg" -ForegroundColor Red }

$INSTALL_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SSH 瀹¤鎶€鑳藉寘 - 瀹夎" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  瀹夎鐩綍: $INSTALL_DIR"
Write-Host ""

# ========== 鍗歌浇妯″紡 ==========
if ($Uninstall) {
    Write-Step "鍗歌浇锛氱Щ闄?AGENT_SSH_AUDIT_HOME 鐜鍙橀噺..."

    $machineKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    try {
        $currentMachine = [Environment]::GetEnvironmentVariable("AGENT_SSH_AUDIT_HOME", "Machine")
        if ($currentMachine) {
            [Environment]::SetEnvironmentVariable("AGENT_SSH_AUDIT_HOME", $null, "Machine")
            Write-Step "宸茬Щ闄?Machine 绾?AGENT_SSH_AUDIT_HOME"
        }
        Remove-ItemProperty -Path $machineKey -Name "AGENT_SSH_AUDIT_HOME" -ErrorAction SilentlyContinue
    } catch {
        Write-Warn "绉婚櫎 Machine 绾ф敞鍐岃〃澶辫触: $_"
    }

    try {
        $currentUser = [Environment]::GetEnvironmentVariable("AGENT_SSH_AUDIT_HOME", "User")
        if ($currentUser) {
            [Environment]::SetEnvironmentVariable("AGENT_SSH_AUDIT_HOME", $null, "User")
            Write-Step "宸茬Щ闄?User 绾?AGENT_SSH_AUDIT_HOME"
        }
    } catch {
        Write-Warn "娓呴櫎 User 绾уけ璐? $_"
    }

    # 骞挎挱鐜鍙橀噺鍙樻洿
    try {
        $HWND_BROADCAST = 0xFFFF
        $WM_SETTINGCHANGE = 0x001A
        Add-Type -Name "NativeMethods" -Namespace "Win32" -MemberDefinition @"
            [DllImport("user32.dll", SetLastError = true)]
            public static extern IntPtr SendMessageTimeout(
                IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
                uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
        $null = [Win32.NativeMethods]::SendMessageTimeout(
            $HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, "Environment",
            0x0002, 5000, [ref] [UIntPtr]::Zero)
        Write-Step "宸插箍鎾幆澧冨彉閲忓彉鏇撮€氱煡"
    } catch {
        Write-Warn "骞挎挱鍙樻洿澶辫触锛堥渶閲嶅惎鐢熸晥锛? $_"
    }

    Write-Host ""
    Write-Host "鍗歌浇瀹屾垚銆傚闇€閲嶆柊瀹夎锛岃鍘绘帀 -Uninstall 鍙傛暟銆? -ForegroundColor Cyan
    exit 0
}

# ========== 瀹夎妯″紡 ==========

# 1. 妫€娴嬭嚜甯︾殑宓屽叆寮?Python
Write-Step "妫€娴?Python 杩愯鏃?.."
$PYTHON_EXE = Join-Path $INSTALL_DIR "python\python.exe"
if (Test-Path $PYTHON_EXE) {
    $pyVer = & $PYTHON_EXE --version 2>&1
    Write-Step "鑷甫 Python 鐗堟湰: $pyVer"
} else {
    Write-Err "鏈壘鍒拌嚜甯?Python 杩愯鏃讹紙$PYTHON_EXE锛夈€傝纭瀹夎鍖呭畬鏁淬€?
    exit 1
}

# 2. 楠岃瘉渚濊禆锛堝祵鍏ュ紡 Python 宸查瑁?paramiko锛岃烦杩囧畨瑁咃級
Write-Step "楠岃瘉 Python 渚濊禆..."
$wheelsDir = Join-Path $INSTALL_DIR "wheels"
$verifyResult = & $PYTHON_EXE -c "import paramiko; print('paramiko', paramiko.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Step "渚濊禆灏辩华: $verifyResult"
} else {
    Write-Warn "渚濊禆缂哄け锛屽皾璇曞畨瑁?.."
    $installed = $false
    if (Test-Path $wheelsDir) {
        Write-Step "绂荤嚎瀹夎..."
        & $PYTHON_EXE -m pip install --no-index --find-links="$wheelsDir" paramiko 2>&1
        if ($LASTEXITCODE -eq 0) { $installed = $true }
    }
    if (-not $installed) {
        Write-Step "鑱旂綉瀹夎..."
        & $PYTHON_EXE -m pip install paramiko 2>&1
        if ($LASTEXITCODE -eq 0) { $installed = $true }
    }
    if (-not $installed) {
        Write-Err "paramiko 瀹夎澶辫触锛岃妫€鏌ョ綉缁滄垨 wheels 鐩綍"
    } else {
        Write-Step "渚濊禆瀹夎瀹屾垚"
    }
}

# 3. 鍒涘缓鐩綍缁撴瀯
Write-Step "鍒涘缓 logs 鐩綍缁撴瀯..."
$logsDir = Join-Path $INSTALL_DIR "logs"
$sessionsDir = Join-Path $logsDir "sessions"
New-Item -ItemType Directory -Force -Path $sessionsDir | Out-Null
Write-Step "  logs\"
Write-Step "    sessions\"

# 4. 鍒濆鍖?credentials.txt锛堝鏋滀笉瀛樺湪锛?$credFile = Join-Path $INSTALL_DIR "credentials.txt"
if (-not (Test-Path $credFile)) {
    Write-Step "鍒涘缓 credentials.txt 妯℃澘..."
    @"
# SSH 鍑嵁鏂囦欢锛坘ey=value 鏍煎紡锛屼竴琛屼竴鏉★紝value 涓?Base64 缂栫爜鐨勫瘑鐮侊級
# 绀轰緥: 192.168.1.100=YXBwZW4=
# 鏈枃浠剁敱 AI 鑷姩绠＄悊锛岃鍕挎墜鍔ㄧ紪杈戙€?"@ | Out-File -FilePath $credFile -Encoding UTF8
    Write-Step "  credentials.txt锛堟ā鏉匡級"
} else {
    Write-Step "credentials.txt 宸插瓨鍦紝璺宠繃"
}

# 5. 璁剧疆鐜鍙橀噺锛堜紭鍏?Machine 绾э紝澶辫触鑷姩闄嶇骇 User 绾э級
Write-Step "璁剧疆鐜鍙橀噺 AGENT_SSH_AUDIT_HOME=$INSTALL_DIR ..."
$envSetOK = $false

# 灏濊瘯 Machine 绾э紙闇€瑕佺鐞嗗憳鏉冮檺锛?try {
    [Environment]::SetEnvironmentVariable("AGENT_SSH_AUDIT_HOME", $INSTALL_DIR, "Machine")
    Write-Step "宸插啓鍏?Machine 绾х幆澧冨彉閲?
    $envSetOK = $true
} catch {
    Write-Warn "Machine 绾у啓鍏ュけ璐ワ紙闇€瑕佺鐞嗗憳鏉冮檺锛夛紝闄嶇骇鍒?User 绾?.."
}

# 闄嶇骇锛歎ser 绾э紙涓嶉渶瑕佺鐞嗗憳鏉冮檺锛?if (-not $envSetOK) {
    try {
        [Environment]::SetEnvironmentVariable("AGENT_SSH_AUDIT_HOME", $INSTALL_DIR, "User")
        Write-Step "宸插啓鍏?User 绾х幆澧冨彉閲?
        $envSetOK = $true
    } catch {
        Write-Err "User 绾у啓鍏ヤ篃澶辫触: $_"
    }
}

# 鏃犺鎸佷箙鍖栨槸鍚︽垚鍔燂紝閮芥敞鍏ュ綋鍓嶈繘绋?$env:AGENT_SSH_AUDIT_HOME = $INSTALL_DIR
Write-Step "宸叉敞鍏ュ綋鍓嶈繘绋?

# 6. 骞挎挱鐜鍙橀噺鍙樻洿
try {
    $HWND_BROADCAST = 0xFFFF
    $WM_SETTINGCHANGE = 0x001A
    Add-Type -Name "NativeMethods" -Namespace "Win32" -MemberDefinition @"
        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr SendMessageTimeout(
            IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
            uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
    $null = [Win32.NativeMethods]::SendMessageTimeout(
        $HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, "Environment",
        0x0002, 5000, [ref] [UIntPtr]::Zero)
    Write-Step "宸插箍鎾幆澧冨彉閲忓彉鏇撮€氱煡"
} catch {
    Write-Warn "骞挎挱鍙樻洿澶辫触锛堥噸鍚悗鑷姩鐢熸晥锛? $_"
}

# 7. 楠岃瘉瀹夎
Write-Step "楠岃瘉瀹夎瀹屾暣鎬?.."
$checks = @(
    @{Label="SKILL.md";      Path=Join-Path $INSTALL_DIR "SKILL.md"},
    @{Label="requirements.txt"; Path=Join-Path $INSTALL_DIR "requirements.txt"},
    @{Label="agent_ssh_audit\__init__.py"; Path=Join-Path $INSTALL_DIR "agent_ssh_audit\__init__.py"},
    @{Label="agent_ssh_audit\client.py";   Path=Join-Path $INSTALL_DIR "agent_ssh_audit\client.py"},
    @{Label="agent_ssh_audit\rules.py";    Path=Join-Path $INSTALL_DIR "agent_ssh_audit\rules.py"},
    @{Label="agent_ssh_audit\storage.py";  Path=Join-Path $INSTALL_DIR "agent_ssh_audit\storage.py"},
    @{Label="agent_ssh_audit\replay.py";   Path=Join-Path $INSTALL_DIR "agent_ssh_audit\replay.py"},
    @{Label="agent_ssh_audit\recorder.py"; Path=Join-Path $INSTALL_DIR "agent_ssh_audit\recorder.py"},
    @{Label="bin\agent-ssh-run.py";   Path=Join-Path $INSTALL_DIR "bin\agent-ssh-run.py"},
    @{Label="bin\agent-ssh-shell.py"; Path=Join-Path $INSTALL_DIR "bin\agent-ssh-shell.py"},
    @{Label="bin\agent-ssh-replay.py";Path=Join-Path $INSTALL_DIR "bin\agent-ssh-replay.py"},
    @{Label="demo.py";     Path=Join-Path $INSTALL_DIR "demo.py"},
    @{Label="test_shell.py"; Path=Join-Path $INSTALL_DIR "test_shell.py"}
)

$allOK = $true
foreach ($c in $checks) {
    if (Test-Path $c.Path) {
        Write-Step $c.Label
    } else {
        Write-Err "缂哄皯: $($c.Label)"
        $allOK = $false
    }
}

Write-Host ""
if ($allOK) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  瀹夎瀹屾垚锛? -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  鐜鍙橀噺: AGENT_SSH_AUDIT_HOME=$INSTALL_DIR"
    Write-Host "  鏃ュ織鐩綍: $logsDir"
    Write-Host "  鍑嵁鏂囦欢: $credFile"
    Write-Host ""
    Write-Host "  蹇€熼獙璇?"
    Write-Host "    cd `$env:AGENT_SSH_AUDIT_HOME"
    Write-Host "    python demo.py"
    Write-Host ""
    Write-Host "  鍗歌浇: .\install.ps1 -Uninstall"
} else {
    Write-Err "瀹夎涓嶅畬鏁达紝璇锋鏌ョ己澶辨枃浠跺悗閲嶆柊杩愯銆?
    exit 1
}
