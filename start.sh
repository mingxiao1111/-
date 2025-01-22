#!/bin/bash

echo "正在检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "Python未安装！请先安装Python 3.6或更高版本。"
    echo "可以从 https://www.python.org/downloads/ 下载安装。"
    exit 1
fi

echo "正在检查 FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg未安装！请先安装FFmpeg。"
    echo "Linux用户可以使用: sudo apt-get install ffmpeg"
    echo "Mac用户可以使用: brew install ffmpeg"
    exit 1
fi

echo "正在安装/更新依赖包..."
pip3 install -r requirements.txt

echo "启动程序..."
python3 main.py 