@echo off
echo 正在检查 Python 环境...

python --version >nul 2>&1
if errorlevel 1 (
    echo Python未安装！请先安装Python 3.6或更高版本。
    echo 可以从 https://www.python.org/downloads/ 下载安装。
    pause
    exit
)

echo 正在检查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo FFmpeg未安装！请先安装FFmpeg。
    echo 可以从 https://ffmpeg.org/download.html 下载安装。
    pause
    exit
)

echo 正在安装/更新依赖包...
pip install -r requirements.txt

echo 启动程序...
python main.py

pause 