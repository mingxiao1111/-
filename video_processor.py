import os
from pydub import AudioSegment
from PyQt6.QtWidgets import QMessageBox
import subprocess

class VideoProcessor:
    def __init__(self):
        self.current_video = None
    
    def convert_to_wav(self, input_file, output_file):
        """将视频文件转换为WAV音频文件"""
        try:
            # 使用 ffmpeg 进行转换
            subprocess.run([
                'ffmpeg',
                '-i', input_file,  # 输入文件
                '-vn',  # 不处理视频
                '-acodec', 'pcm_s16le',  # 设置音频编码
                '-ar', '44100',  # 设置采样率
                '-ac', '2',  # 设置声道数
                '-y',  # 覆盖已存在的文件
                output_file
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"转换失败: {e.stderr.decode()}")
            raise Exception("视频转换失败")

    def convert_to_wav_pydub(self, video_path):
        try:
            # 生成输出文件名
            output_path = os.path.splitext(video_path)[0] + ".wav"
            
            # 使用 pydub 转换视频到音频
            audio = AudioSegment.from_file(video_path)
            audio.export(output_path, format="wav")
            
            QMessageBox.information(None, "成功", f"音频已保存至：{output_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"处理视频时出错：{str(e)}") 