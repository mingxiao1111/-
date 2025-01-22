from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QSlider, QLabel, QFileDialog, QStyle, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QSize, QSizeF
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink, QVideoFrame
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl
import os
import subprocess

class VideoEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频编辑器")
        self.setMinimumSize(1200, 800)  # 视频编辑器窗口稍大
        
        # 初始化播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # 视频输出
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        
        self.setup_ui()
        self.setup_connections()
        
        # 播放控制变量
        self.current_file = None
        self.is_playing = False
        self.playback_speed = 1.0
        
        # 剪切点
        self.cut_start = None
        self.cut_end = None
        self.cut_points = []
        
        # 添加实时计时器
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_real_time_duration)
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)  # 添加边距
        
        # 顶部控制区
        top_layout = QHBoxLayout()
        
        # 文件控制
        self.open_btn = QPushButton("打开视频文件")
        self.open_btn.setMinimumHeight(40)
        self.open_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 5px 15px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        top_layout.addWidget(self.open_btn)
        top_layout.addStretch()
        
        # 当前文件显示
        self.file_label = QLabel("当前文件: 未选择")
        self.file_label.setStyleSheet("font-size: 14px; color: #666;")
        top_layout.addWidget(self.file_label)
        
        main_layout.addLayout(top_layout)
        
        # 视频预览区域
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加点击事件支持
        self.video_widget.mousePressEvent = self.video_click
        self.video_widget.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标指针变为手型
        self.video_widget.setMinimumHeight(400)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setStyleSheet("""
            background-color: #000000;
            border-radius: 5px;
        """)
        video_layout.addWidget(self.video_widget)
        
        main_layout.addWidget(video_container)
        
        # 播放控制
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # 播放控制按钮（移除播放/暂停按钮）
        self.backward_3s_btn = QPushButton("后退3秒")
        self.backward_5s_btn = QPushButton("后退5秒")
        self.forward_5s_btn = QPushButton("前进5秒")
        self.forward_20s_btn = QPushButton("前进20秒")
        self.speed_btn = QPushButton("1.0x")
        
        control_buttons = [
            (self.backward_3s_btn, self.backward_3s),
            (self.backward_5s_btn, self.backward_5s),
            (self.forward_5s_btn, self.forward_5s),
            (self.forward_20s_btn, self.forward_20s),
            (self.speed_btn, self.speed_change)
        ]
        
        for btn, func in control_buttons:
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(100)
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
            btn.clicked.connect(func)
            control_layout.addWidget(btn)
        
        main_layout.addLayout(control_layout)
        
        # 进度条和时间显示
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)
        
        # 时间显示
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-size: 14px;")
        time_layout.addWidget(self.time_label)
        
        self.real_time_duration_label = QLabel("实时时长: 0.0秒")
        self.real_time_duration_label.setStyleSheet("""
            font-size: 14px;
            color: #FF5722;
            font-weight: bold;
        """)
        time_layout.addWidget(self.real_time_duration_label)
        time_layout.addStretch()
        
        progress_layout.addLayout(time_layout)
        
        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimumHeight(50)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 18px;
                background: #ffffff;
                margin: 0px;
                border-radius: 9px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 2px solid #1976D2;
                width: 36px;
                height: 36px;
                margin: -9px 0;
                border-radius: 18px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3;
                border-radius: 9px;
            }
            QSlider::add-page:horizontal {
                background: #E0E0E0;
                border-radius: 9px;
            }
        """)
        self.progress_slider.mousePressEvent = self.slider_click
        progress_layout.addWidget(self.progress_slider)
        
        main_layout.addLayout(progress_layout)
        
        # 剪切控制
        cut_layout = QHBoxLayout()  # 改为水平布局
        cut_layout.setSpacing(10)
        
        # 创建按钮
        self.set_start_btn = QPushButton("设置起点")
        self.set_end_btn = QPushButton("设置终点")
        self.set_end_new_start_btn = QPushButton("设置终点并新建起点")
        self.save_cut_btn = QPushButton("保存片段")
        
        cut_buttons = [
            self.set_start_btn,
            self.set_end_btn,
            self.set_end_new_start_btn,
            self.save_cut_btn
        ]
        
        for btn in cut_buttons:
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(120)
            btn.setStyleSheet("""
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
            cut_layout.addWidget(btn)
        
        # 剪切信息显示
        self.cut_info_label = QLabel("剪切时长: 0秒")
        self.cut_info_label.setStyleSheet("""
            font-size: 14px;
            margin-left: 20px;
            color: #FF5722;
            font-weight: bold;
        """)
        cut_layout.addWidget(self.cut_info_label)
        cut_layout.addStretch()  # 添加弹性空间
        
        main_layout.addLayout(cut_layout)
        
        self.setLayout(main_layout)
        
    def setup_connections(self):
        self.open_btn.clicked.connect(self.open_file)
        self.backward_3s_btn.clicked.connect(self.backward_3s)
        self.backward_5s_btn.clicked.connect(self.backward_5s)
        self.forward_5s_btn.clicked.connect(self.forward_5s)
        self.forward_20s_btn.clicked.connect(self.forward_20s)
        self.speed_btn.clicked.connect(self.speed_change)
        self.set_start_btn.clicked.connect(self.set_start)
        self.set_end_btn.clicked.connect(self.set_end)
        self.set_end_new_start_btn.clicked.connect(self.set_end_new_start)
        self.save_cut_btn.clicked.connect(self.save_cut)
        
        # 添加播放器信号连接
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_name:
            self.current_file = file_name
            self.file_label.setText(f"当前文件: {os.path.basename(file_name)}")
            self.player.setSource(QUrl.fromLocalFile(file_name))
            
            # 设置视频窗口大小
            self.video_widget.setMinimumHeight(400)
            # 设置一个合理的宽高比（16:9）
            self.video_widget.setMinimumWidth(int(400 * 16/9))
            
            # 设置视频窗口策略，使其能够自适应缩放
            self.video_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
            
            self.play()
            self.cut_start = None
            self.cut_end = None
            self.cut_points = []
            self.cut_info_label.setText("剪切时长: 0秒")
            self.real_time_duration_label.setText("实时时长: 0.0秒")
        
    def video_click(self, event):
        """处理视频点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_play()

    def toggle_play(self):
        """切换播放/暂停状态"""
        if not self.current_file:
            return
            
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """开始播放"""
        self.player.play()
        self.is_playing = True
    
    def pause(self):
        """暂停播放"""
        self.player.pause()
        self.is_playing = False
    
    def backward_3s(self):
        self.player.setPosition(self.player.position() - 3000)
        
    def backward_5s(self):
        self.player.setPosition(self.player.position() - 5000)
        
    def forward_5s(self):
        self.player.setPosition(self.player.position() + 5000)
        
    def forward_20s(self):
        self.player.setPosition(self.player.position() + 20000)
        
    def speed_change(self):
        speeds = [0.5, 1.0, 1.5, 2.0]
        current_index = speeds.index(self.playback_speed) if self.playback_speed in speeds else 0
        self.playback_speed = speeds[(current_index + 1) % len(speeds)]
        self.speed_btn.setText(f"{self.playback_speed}x")
        self.player.setPlaybackRate(self.playback_speed)
        
    def set_start(self):
        self.cut_start = self.player.position()
        self.cut_end = None  # 清除之前的终点
        start_str = self.format_time(self.cut_start)
        self.cut_info_label.setText(f"起点: {start_str}")
        self.real_time_duration_label.setText("实时时长: 0.0秒")
        self.timer.start()  # 开始实时计时
        
    def set_end(self):
        if self.cut_start is not None:
            self.cut_end = self.player.position()
            if self.cut_end < self.cut_start:
                # 如果终点在起点之前，交换它们
                self.cut_start, self.cut_end = self.cut_end, self.cut_start
            start_str = self.format_time(self.cut_start)
            end_str = self.format_time(self.cut_end)
            duration = (self.cut_end - self.cut_start) / 1000.0
            self.cut_info_label.setText(f"剪切: {start_str} - {end_str} (时长: {duration:.1f}秒)")
            self.cut_points.append((self.cut_start, self.cut_end))
            self.cut_start = None
            self.cut_end = None
            self.timer.stop()
            self.real_time_duration_label.setText("实时时长: 0.0秒")
        
    def set_end_new_start(self):
        """设置终点并新建起点"""
        if self.cut_start is not None:
            # 先设置终点
            self.set_end()
            # 然后设置新的起点
            self.set_start()
        
    def save_cut(self):
        if not self.current_file:
            return
            
        # 保存前暂停播放
        was_playing = self.is_playing
        self.pause()
            
        if self.cut_start is not None and self.cut_end is not None:
            self.cut_points.append((self.cut_start, self.cut_end))
            
        if not self.cut_points:
            if was_playing:
                self.play()
            return
            
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not save_dir:
            if was_playing:
                self.play()
            return
            
        default_name = os.path.splitext(os.path.basename(self.current_file))[0]
        
        for i, (start, end) in enumerate(self.cut_points, 1):
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                f"保存第 {i} 个片段",
                os.path.join(save_dir, f"{default_name}_cut_{i}.mp4"),
                "视频文件 (*.mp4)"
            )
            
            if file_name:
                # 使用ffmpeg进行视频剪切
                start_time = start / 1000.0  # 转换为秒
                duration = (end - start) / 1000.0
                
                try:
                    subprocess.run([
                        'ffmpeg', '-i', self.current_file,
                        '-ss', str(start_time),
                        '-t', str(duration),
                        '-c', 'copy',  # 使用复制模式，速度更快
                        file_name
                    ], check=True)
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(self, "错误", f"保存视频片段时出错：{str(e)}")
                    continue
        
        QMessageBox.information(self, "成功", f"已保存 {len(self.cut_points)} 个视频片段")
        self.cut_points = []
        self.cut_start = None
        self.cut_end = None
        self.timer.stop()
        self.cut_info_label.setText("剪切时长: 0秒")
        self.real_time_duration_label.setText("实时时长: 0.0秒")
        
        # 如果之前在播放，则恢复播放
        if was_playing:
            self.play()
        
    def update_real_time_duration(self):
        """更新实时剪切时长"""
        if self.cut_start is not None and self.cut_end is None:
            current_pos = self.player.position()
            duration = abs(current_pos - self.cut_start) / 1000.0
            self.real_time_duration_label.setText(f"实时时长: {duration:.1f}秒")
        
    def update_cut_info(self):
        if self.cut_start is not None and self.cut_end is not None:
            self.cut_info_label.setText(f"剪切时长: {(self.cut_end - self.cut_start) / 1000.0:.2f}秒")
        else:
            self.cut_info_label.setText("剪切时长: 0秒")
        
    def slider_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 计算点击位置对应的值
            value = QStyle.sliderValueFromPosition(
                self.progress_slider.minimum(),
                self.progress_slider.maximum(),
                int(event.position().x()),
                self.progress_slider.width()
            )
            self.progress_slider.setValue(value)
            self.player.setPosition(value)
            
    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # 媒体加载完成后设置初始状态
            self.progress_slider.setRange(0, self.player.duration())
            self.update_time_label(0, self.player.duration())
            self.player.play()
            self.is_playing = True
            
    def on_position_changed(self, position):
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)
        self.update_time_label(position, self.player.duration())
        
    def on_duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)
        
    def on_slider_pressed(self):
        self.player.pause()
        
    def on_slider_released(self):
        self.player.setPosition(self.progress_slider.value())
        if self.is_playing:
            self.player.play()
            
    def update_time_label(self, position, duration):
        position_str = self.format_time(position)
        duration_str = self.format_time(duration)
        self.time_label.setText(f"{position_str} / {duration_str}")
        
    def format_time(self, ms):
        """格式化时间显示"""
        s = ms // 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}"
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.player.stop()
        self.deleteLater()
        event.accept()
    