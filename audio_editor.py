from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QSlider, QLabel, QFileDialog, QStyle, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import wave
import os
from pydub import AudioSegment

class AudioEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音频编辑器")
        self.setMinimumSize(1200, 600)
        
        # 初始化播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.setup_ui()
        self.setup_connections()
        
        # 播放控制变量
        self.current_file = None
        self.is_playing = False
        self.playback_speed = 1.0
        
        # 剪切点
        self.cut_start = None
        self.cut_end = None
        
        # 添加剪切点列表
        self.cut_points = []  # 存储多个剪切区间 [(start1, end1), (start2, end2), ...]
        
        # 添加实时计时器
        self.timer = QTimer()
        self.timer.setInterval(100)  # 100ms更新一次
        self.timer.timeout.connect(self.update_real_time_duration)
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)  # 增加边距
        
        # 顶部控制区
        top_layout = QHBoxLayout()
        
        # 文件控制
        self.open_btn = QPushButton("打开音频文件")
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
        
        # 进度条和控制区域
        progress_control_layout = QVBoxLayout()
        progress_control_layout.setSpacing(15)  # 增加间距
        
        # 进度条
        progress_slider_container = QVBoxLayout()
        progress_slider_container.setSpacing(8)  # 调整进度条和时间的间距
        
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
        progress_slider_container.addWidget(self.progress_slider)
        
        # 时间显示
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(10, 0, 10, 0)  # 添加左右边距
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
        
        progress_slider_container.addLayout(time_layout)
        
        # 播放控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)  # 增加按钮间距
        control_layout.setContentsMargins(10, 0, 10, 0)  # 添加左右边距
        
        # 播放控制按钮
        self.backward_3s_btn = QPushButton("后退3秒")
        self.backward_5s_btn = QPushButton("后退5秒")
        self.play_btn = QPushButton("播放/暂停")
        self.forward_5s_btn = QPushButton("前进5秒")
        self.forward_20s_btn = QPushButton("前进20秒")
        self.speed_btn = QPushButton("1.0x")
        
        control_buttons = [
            self.backward_3s_btn,
            self.backward_5s_btn,
            self.play_btn,
            self.forward_5s_btn,
            self.forward_20s_btn,
            self.speed_btn
        ]
        
        for btn in control_buttons:
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
            control_layout.addWidget(btn)
        
        progress_control_layout.addLayout(progress_slider_container)
        progress_control_layout.addLayout(control_layout)
        
        # 剪切控制
        cut_layout = QHBoxLayout()
        cut_layout.setSpacing(15)  # 增加按钮间距
        cut_layout.setContentsMargins(10, 20, 10, 10)  # 添加边距，上边距稍大
        
        # 剪切按钮
        self.set_start_btn = QPushButton("设置起点")
        self.set_end_btn = QPushButton("设置终点")
        self.set_end_new_start_btn = QPushButton("终点同时新建起点")
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
        cut_layout.addStretch()
        
        main_layout.addLayout(progress_control_layout)
        main_layout.addLayout(cut_layout)
        
        self.setLayout(main_layout)
    
    def setup_connections(self):
        self.open_btn.clicked.connect(self.open_audio_file)
        self.play_btn.clicked.connect(self.toggle_play)
        self.speed_btn.clicked.connect(self.toggle_speed)
        
        # 新增的快进快退按钮连接
        self.backward_3s_btn.clicked.connect(lambda: self.seek_relative(-3000))
        self.backward_5s_btn.clicked.connect(lambda: self.seek_relative(-5000))
        self.forward_5s_btn.clicked.connect(lambda: self.seek_relative(5000))
        self.forward_20s_btn.clicked.connect(lambda: self.seek_relative(20000))
        
        self.set_start_btn.clicked.connect(self.set_cut_start)
        self.set_end_btn.clicked.connect(self.set_cut_end)
        self.set_end_new_start_btn.clicked.connect(self.set_end_and_new_start)
        self.save_cut_btn.clicked.connect(self.save_cut)
        
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
    
    def seek_relative(self, offset_ms):
        """相对当前位置移动指定毫秒数"""
        current_pos = self.player.position()
        new_pos = max(0, min(current_pos + offset_ms, self.player.duration()))
        self.player.setPosition(new_pos)
    
    def open_audio_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.wav)"
        )
        if file_name:
            self.current_file = file_name
            self.file_label.setText(f"当前文件: {os.path.basename(file_name)}")
            self.player.setSource(QUrl.fromLocalFile(file_name))
            self.audio_output.setVolume(1.0)
            self.player.play()
            self.is_playing = True
            self.play_btn.setText("暂停")
    
    def toggle_play(self):
        if self.is_playing:
            self.player.pause()
        else:
            self.player.play()
        self.is_playing = not self.is_playing
    
    def toggle_speed(self):
        speeds = [1.0, 1.5, 2.0, 0.5]
        current_index = speeds.index(self.playback_speed)
        self.playback_speed = speeds[(current_index + 1) % len(speeds)]
        self.speed_btn.setText(f"{self.playback_speed}x")
        self.player.setPlaybackRate(self.playback_speed)
    
    def seek_position(self, position):
        self.player.setPosition(position)
    
    def on_position_changed(self, position):
        """只在非拖动状态下更新进度条"""
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)
        self.update_time_label(position, self.player.duration())
    
    def on_duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)
        self.update_time_label(self.player.position(), duration)
    
    def update_time_label(self, position, duration):
        position_str = self.format_time(position)
        duration_str = self.format_time(duration)
        self.time_label.setText(f"{position_str} / {duration_str}")
    
    def format_time(self, ms):
        s = ms // 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}"
    
    def slider_click(self, event):
        """处理进度条点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录当前播放状态
            self.was_playing = self.is_playing
            # 暂停播放
            self.player.pause()
            self.is_playing = False
            
            # 计算并设置新位置
            value = QStyle.sliderValueFromPosition(
                self.progress_slider.minimum(),
                self.progress_slider.maximum(),
                int(event.position().x()),
                self.progress_slider.width()
            )
            self.progress_slider.setValue(value)
            self.player.setPosition(value)
            
            # 如果之前在播放，则恢复播放
            if self.was_playing:
                self.player.play()
                self.is_playing = True
    
    def set_cut_start(self):
        self.cut_start = self.player.position()
        self.update_cut_info()
        self.update_cut_points_display()
        self.timer.start()  # 开始实时计时
    
    def set_cut_end(self):
        self.cut_end = self.player.position()
        self.update_cut_info()
        self.update_cut_points_display()
        self.timer.stop()  # 停止实时计时
    
    def set_end_and_new_start(self):
        current_pos = self.player.position()
        if self.cut_start is not None:
            self.cut_end = current_pos
            self.cut_points.append((self.cut_start, self.cut_end))
            self.update_cut_list()
        self.cut_start = current_pos
        self.cut_end = None
        self.update_cut_info()
        self.update_cut_points_display()
        self.timer.start()  # 重新开始实时计时
    
    def update_cut_info(self):
        if self.cut_start is not None:
            start_str = self.format_time(self.cut_start)
            if self.cut_end is not None:
                duration = abs(self.cut_end - self.cut_start) / 1000  # 转换为秒
                end_str = self.format_time(self.cut_end)
                self.cut_info_label.setText(f"剪切时长: {duration:.1f}秒 ({start_str} - {end_str})")
            else:
                self.cut_info_label.setText(f"起点已设置: {start_str}")
        else:
            self.cut_info_label.setText("剪切时长: 0秒")
    
    def update_cut_points_display(self):
        # 更新剪切点可视化显示
        pass  # TODO: 实现剪切点的可视化显示
    
    def update_cut_list(self):
        """更新剪切片段列表显示"""
        cut_list_text = "剪切片段列表:\n"
        for i, (start, end) in enumerate(self.cut_points, 1):
            duration = (end - start) / 1000
            start_str = self.format_time(start)
            end_str = self.format_time(end)
            cut_list_text += f"{i}. {start_str} - {end_str} (时长: {duration:.1f}秒)\n"
        self.cut_info_label.setText(cut_list_text)
    
    def update_real_time_duration(self):
        """更新实时剪切时长"""
        if self.cut_start is not None and self.cut_end is None:
            current_pos = self.player.position()
            duration = abs(current_pos - self.cut_start) / 1000
            self.real_time_duration_label.setText(f"实时时长: {duration:.1f}秒")
    
    def on_slider_pressed(self):
        """滑块按下时暂停播放"""
        self.was_playing = self.is_playing
        self.player.pause()
        self.is_playing = False
    
    def on_slider_released(self):
        """滑块释放时设置位置并恢复播放状态"""
        position = self.progress_slider.value()
        self.player.setPosition(position)
        if self.was_playing:
            self.player.play()
            self.is_playing = True
    
    def save_cut(self):
        if not self.current_file:
            return
            
        # 保存前暂停播放
        was_playing = self.is_playing
        self.player.pause()
        self.is_playing = False
        
        try:
            if self.cut_start is not None and self.cut_end is not None:
                self.cut_points.append((self.cut_start, self.cut_end))
            
            if not self.cut_points:
                if was_playing:
                    self.player.play()
                    self.is_playing = True
                return
            
            # 先选择保存目录
            save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
            if not save_dir:
                return
            
            # 获取基础文件名
            default_name = os.path.splitext(os.path.basename(self.current_file))[0]
            
            audio = AudioSegment.from_wav(self.current_file)
            
            for i, (start, end) in enumerate(self.cut_points, 1):
                # 为每个片段请求文件名
                file_name, _ = QFileDialog.getSaveFileName(
                    self,
                    f"保存第 {i} 个片段",
                    os.path.join(save_dir, f"{default_name}_cut_{i}.wav"),
                    "WAV文件 (*.wav)"
                )
                
                if file_name:
                    # 提取并保存片段
                    segment = audio[start:end]
                    segment.export(file_name, format="wav")
            
            QMessageBox.information(self, "成功", f"已保存 {len(self.cut_points)} 个音频片段")
            self.cut_points = []
            self.cut_start = None
            self.cut_end = None
            self.timer.stop()
            self.update_cut_info()
            self.update_cut_list()
            self.real_time_duration_label.setText("实时时长: 0.0秒")
        
        finally:
            # 无论保存是否成功，都恢复之前的播放状态
            if was_playing:
                self.player.play()
                self.is_playing = True
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.player.stop()
        self.deleteLater()
        event.accept() 