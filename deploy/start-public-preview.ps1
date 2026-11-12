$ErrorActionPreference = "Stop"

$Branch = "feature/v42-unified-exhibit-search-20261029"
$RepoZip = "https://codeload.github.com/ProfMonkey/museum-/zip/refs/heads/$Branch"
$CloudflaredUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$Root = Join-Path $env:LOCALAPPDATA "WonderAtlas"
$Source = Join-Path $Root "source"
$Tools = Join-Path $Root "tools"
$Temp = Join-Path $env:TEMP "WonderAtlas-V42"
$PythonEnv = Join-Path $Source ".venv"
$Port = 8000
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host ""
Write-Host "==============================================" -ForegroundColor DarkYellow
Write-Host "       万物博物馆 V42.0 公网预览启动器" -ForegroundColor Yellow
Write-Host "==============================================" -ForegroundColor DarkYellow
Write-Host "网站在本机电脑运行，再通过 Cloudflare 临时网址访问。"
Write-Host "数据保存在本机：$Source\data"
Write-Host "请保持这个窗口开启；关闭窗口后公网网址会失效。"
Write-Host ""

New-Item -ItemType Directory -Force -Path $Root,$Tools | Out-Null

$PythonLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
$PythonExe = Get-Command python.exe -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    & py -3.12 --version *> $null
    if ($LASTEXITCODE -eq 0) { $PythonCommand = "py"; $PythonArgs = @("-3.12") }
    else { $PythonCommand = "py"; $PythonArgs = @("-3") }
} elseif ($PythonExe) {
    $PythonCommand = $PythonExe.Source
    $PythonArgs = @()
} else {
    throw "没有找到 Python。请先安装 Python 3.12（安装时勾选 Add Python to PATH），然后重新双击启动器。"
}

# Download V42 source. Keep the data folder so code updates do not delete the database.
if (Test-Path $Temp) { Remove-Item $Temp -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Temp | Out-Null
$Zip = Join-Path $Temp "museum-v42.zip"
Write-Host "[1/5] 下载万物博物馆 V42.0 源码……" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RepoZip -OutFile $Zip
Expand-Archive -Path $Zip -DestinationPath $Temp -Force
$Extracted = Get-ChildItem -Path $Temp -Directory | Select-Object -First 1
if (-not $Extracted -or -not (Test-Path (Join-Path $Extracted.FullName "server.py"))) {
    throw "源码压缩包解压失败，未找到 server.py。"
}
New-Item -ItemType Directory -Force -Path $Source | Out-Null
Copy-Item -Path (Join-Path $Extracted.FullName "*") -Destination $Source -Recurse -Force

Write-Host "[2/5] 准备 Python 环境并安装依赖……" -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $PythonEnv "Scripts\python.exe"))) {
    & $PythonCommand @PythonArgs -m venv $PythonEnv
    if ($LASTEXITCODE -ne 0) { throw "创建 Python 环境失败。" }
}
$VenvPython = Join-Path $PythonEnv "Scripts\python.exe"
& $VenvPython -m pip install --disable-pip-version-check -i "https://pypi.tuna.tsinghua.edu.cn/simple" -r (Join-Path $Source "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Host "清华镜像安装失败，尝试官方 PyPI……" -ForegroundColor Yellow
    & $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $Source "requirements.txt")
}
if ($LASTEXITCODE -ne 0) { throw "依赖安装失败。请检查网络后重新运行启动器。" }

$Cloudflared = Join-Path $Tools "cloudflared.exe"
if (-not (Test-Path $Cloudflared)) {
    Write-Host "[3/5] 下载 Cloudflare 公网连接程序……" -ForegroundColor Cyan
    Invoke-WebRequest -Uri $CloudflaredUrl -OutFile $Cloudflared
}
if ((Get-Item $Cloudflared).Length -lt 10000000) {
    throw "cloudflared.exe 文件异常，请删除 $Cloudflared 后重试。"
}

$Data = Join-Path $Source "data"
New-Item -ItemType Directory -Force -Path $Data | Out-Null
$env:WONDER_DATA_DIR = $Data
$env:WONDER_COOKIE_SECURE = "1"

try {
    $Existing = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2 -UseBasicParsing
    if ($Existing.StatusCode -eq 200) {
        throw "端口 $Port 已有网站在运行。请先关闭旧的网站窗口，再双击启动器。"
    }
} catch {
    if ($_.Exception.Message -like "*端口 $Port 已有网站在运行*") { throw }
}

Write-Host "[4/5] 启动万物博物馆本地服务……" -ForegroundColor Cyan
$Stdout = Join-Path $Root "server.log"
$Stderr = Join-Path $Root "server-error.log"
$Server = Start-Process -FilePath $VenvPython -ArgumentList @("-m","uvicorn","server:app","--host","127.0.0.1","--port","$Port","--proxy-headers") -WorkingDirectory $Source -PassThru -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr

$Ready = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    if ($Server.HasExited) {
        Get-Content $Stderr -Tail 40 -ErrorAction SilentlyContinue
        throw "网站服务启动失败。错误日志：$Stderr"
    }
    try {
        $Health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
        $Ready = $true
        break
    } catch {}
}
if (-not $Ready) {
    Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
    throw "网站 60 秒内没有启动成功。请查看日志：$Stderr"
}

Write-Host ""
Write-Host "本机网站已启动：http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "[5/5] 正在创建临时公网 HTTPS 网址……" -ForegroundColor Cyan
Write-Host "看到 https://xxxx.trycloudflare.com 后，就可以用这个网址访问。" -ForegroundColor Yellow
Write-Host "任何拿到网址的人都能访问；网站允许访客注册。请勿放入敏感资料。" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 结束公网预览。" -ForegroundColor Yellow
Write-Host ""

try {
    & $Cloudflared tunnel --url "http://127.0.0.1:$Port" 2>&1 | ForEach-Object {
        $Line = "$_"
        Write-Host $Line
        if ($Line -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
            $PublicUrl = $Matches[0]
            Write-Host ""
            Write-Host "万物博物馆公网地址：" -ForegroundColor Green
            Write-Host $PublicUrl -ForegroundColor Yellow
            Write-Host ""
            try { Set-Clipboard $PublicUrl } catch {}
            try { Start-Process $PublicUrl } catch {}
        }
    }
} finally {
    if ($Server -and -not $Server.HasExited) {
        Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "公网预览已停止。下次启动会生成新的临时网址。" -ForegroundColor DarkYellow
}
