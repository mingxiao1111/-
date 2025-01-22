import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QGroupBox, QProgressDialog, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from video_processor import VideoProcessor
from audio_editor import AudioEditor
from video_editor import VideoEditor

class VideoConverterThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    
    def __init__(self, video_file, video_processor):
        super().__init__()
        self.video_file = video_file
        self.video_processor = video_processor
        
    def run(self):
        try:
            # 实际的转换操作
            output_file = self.video_file.rsplit('.', 1)[0] + '.wav'
            # 模拟转换进度
            for i in range(101):
                if i < 90:  # 前90%用于显示转换进度
                    self.progress.emit(i)
                    self.msleep(20)  # 稍微延迟一下，让进度条显示更平滑
            
            # 执行实际转换
            self.video_processor.convert_to_wav(self.video_file, output_file)
            
            # 完成最后的进度
            self.progress.emit(100)
            self.finished.emit(output_file)
        except Exception as e:
            print(f"转换失败: {str(e)}")
            self.finished.emit("")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音视频处理工具")
        self.setMinimumSize(800, 600)
        
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        layout.setSpacing(30)  # 增加间距
        layout.setContentsMargins(40, 40, 40, 40)  # 增加边距
        
        # 标题
        title_label = QLabel("音视频处理工具")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 视频处理部分
        video_group = QGroupBox("视频处理")
        video_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 5px;
            }
        """)
        video_layout = QVBoxLayout()
        video_layout.setSpacing(15)
        
        self.video_btn = QPushButton("视频转音频")
        self.video_editor_btn = QPushButton("打开视频编辑器")
        
        for btn in [self.video_btn, self.video_editor_btn]:
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    padding: 5px 15px;
                    background-color: #2196F3;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        
        self.video_btn.clicked.connect(self.open_video_file)
        self.video_editor_btn.clicked.connect(self.open_video_editor)
        
        video_layout.addWidget(self.video_btn)
        video_layout.addWidget(self.video_editor_btn)
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # 音频处理部分
        audio_group = QGroupBox("音频处理")
        audio_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 5px;
            }
        """)
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(15)
        
        self.audio_btn = QPushButton("打开音频编辑器")
        self.audio_btn.setMinimumHeight(50)
        self.audio_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 5px 15px;
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        self.audio_btn.clicked.connect(self.open_audio_editor)
        
        audio_layout.addWidget(self.audio_btn)
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        layout.addStretch()  # 添加弹性空间
        main_widget.setLayout(layout)
        
        self.video_processor = VideoProcessor()
        self.audio_editor = None
        self.video_editor = None

    def open_video_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "视频转音频",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_name:
            # 创建进度对话框
            progress = QProgressDialog("正在转换视频...", "取消", 0, 100, self)
            progress.setWindowTitle("转换进度")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            
            # 创建转换线程
            self.converter = VideoConverterThread(file_name, self.video_processor)
            self.converter.progress.connect(progress.setValue)
            self.converter.finished.connect(self.conversion_finished)
            
            # 开始转换
            self.converter.start()
            
    def conversion_finished(self, output_file):
        if output_file:
            # 选择保存位置
            save_file, _ = QFileDialog.getSaveFileName(
                self,
                "保存音频文件",
                output_file,
                "WAV文件 (*.wav)"
            )
            if save_file:
                import shutil
                shutil.move(output_file, save_file)
                QMessageBox.information(self, "成功", "视频已成功转换为音频！")
        else:
            QMessageBox.critical(self, "错误", "转换失败，请检查视频文件！")

    def open_audio_editor(self):
        if self.audio_editor is not None and not self.audio_editor.isVisible():
            self.audio_editor = None
            
        if self.audio_editor is None:
            self.audio_editor = AudioEditor()
            self.audio_editor.destroyed.connect(lambda: setattr(self, 'audio_editor', None))
        self.audio_editor.show()
        self.audio_editor.raise_()
        
    def open_video_editor(self):
        if self.video_editor is not None and not self.video_editor.isVisible():
            self.video_editor = None
            
        if self.video_editor is None:
            self.video_editor = VideoEditor()
            self.video_editor.destroyed.connect(lambda: setattr(self, 'video_editor', None))
        self.video_editor.show()
        self.video_editor.raise_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 