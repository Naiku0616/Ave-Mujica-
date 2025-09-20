import sys
import os
import math
import pygame
import time
from datetime import datetime
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QWidget, QHBoxLayout, QFrame, 
                             QFileDialog, QSlider, QSpinBox, QGroupBox,
                             QListWidget, QListWidgetItem, QMenu, QAction,
                             QMessageBox, QInputDialog, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QFont, QImageReader, QIcon, QTransform, QKeySequence, QImage

try:
    import piexif
    EXIF_SUPPORT = True
except ImportError:
    EXIF_SUPPORT = False

# 支持的音频格式列表
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

class ImageLoaderThread(QThread):
    """图片加载线程，避免主线程阻塞"""
    image_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, image_paths):
        super().__init__()
        self.image_paths = image_paths
    
    def run(self):
        for path in self.image_paths:
            if not os.path.exists(path):
                continue
                
            # 使用QImage加载图片，效率更高
            image = QImage(path)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                self.image_loaded.emit(path, pixmap)
            # 添加短暂延迟，避免过于频繁的信号发射
            self.msleep(10)

class ImageViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("星泉Naiku")
        self.setGeometry(350, 100, 1200, 800)
        
        # 移除默认窗口边框
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化变量
        self.image_folder = ""
        self.image_list = []
        self.playlists = {}  # 播放列表字典
        self.current_playlist = "默认列表"  # 当前播放列表
        self.current_index = 0
        self.timer = QTimer()
        self.slide_interval = 3  # 默认3秒切换
        self.transition_type = "淡入淡出"  # 过渡效果类型
        self.transition_duration = 500  # 过渡动画持续时间(毫秒)
        self.is_fullscreen = False  # 全屏状态
        self.image_rotation = 0  # 图片旋转角度
        self.image_flip_h = False  # 水平翻转
        self.image_flip_v = False  # 垂直翻转
        
        # 图片缓存
        self.image_cache = {}
        self.cache_size = 10  # 缓存最近10张图片
        
        # 预加载线程
        self.loader_thread = None
        
        # 加载默认背景
        self.background = QPixmap(1200, 800)
        self.background.fill(Qt.darkGray)
        
        # 初始化拖动变量
        self.oldPos = self.pos()
        
        # 音乐状态
        self.music_playing = False
        self.music_file = None
        
        # 创建UI
        self.initUI()
        
        # 连接定时器信号
        self.timer.timeout.connect(self.next_image)
        
        # 创建默认播放列表
        self.playlists[self.current_playlist] = []
        
        # 初始化音乐
        self.init_music()
    
    def find_music_file(self):
        """查找可用的音乐文件"""
        # 首先尝试查找特定的音乐文件
        music_files = [
            "天球(そら)のMúsica - Ave Mujica.flac",
            "天球(そら)のMusica - Ave Mujica.flac",  # 可能的变体
            "background_music.flac",
            "background_music.mp3",
            "music.flac",
            "music.mp3"
        ]
        
        # 检查当前目录
        for file in music_files:
            if os.path.exists(file):
                return file
        
        # 检查程序所在目录
        app_dir = os.path.dirname(os.path.abspath(__file__))
        for file in music_files:
            full_path = os.path.join(app_dir, file)
            if os.path.exists(full_path):
                return full_path
        
        # 如果没有找到特定文件，查找任何支持的音频文件
        for file in os.listdir('.'):
            if any(file.lower().endswith(ext) for ext in SUPPORTED_AUDIO_FORMATS):
                return file
        
        # 检查程序目录中的音频文件
        for file in os.listdir(app_dir):
            if any(file.lower().endswith(ext) for ext in SUPPORTED_AUDIO_FORMATS):
                return os.path.join(app_dir, file)
        
        return None
    
    def init_music(self):
        """初始化背景音乐"""
        try:
            # 查找音乐文件
            self.music_file = self.find_music_file()
            
            if not self.music_file:
                print("警告: 未找到音乐文件，程序将在无声模式下运行")
                print("支持的音频格式:", ", ".join(SUPPORTED_AUDIO_FORMATS))
                return
            
            # 初始化音频 mixer 模块
            pygame.mixer.init()
            
            # 加载音乐文件
            pygame.mixer.music.load(self.music_file)
            
            # 设置音量（0.0 到 1.0）
            pygame.mixer.music.set_volume(0.5)  # 50% 音量
            
            # 循环播放音乐（-1 表示无限循环）
            pygame.mixer.music.play(-1)
            self.music_playing = True
            print(f"背景音乐开始循环播放: {os.path.basename(self.music_file)}")
            
        except Exception as e:
            print(f"播放音乐时出错: {e}")
            # 尝试使用其他方法初始化pygame
            try:
                pygame.init()
                pygame.mixer.init()
                if self.music_file:
                    pygame.mixer.music.load(self.music_file)
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.music_playing = True
                    print(f"背景音乐开始循环播放 (重试): {os.path.basename(self.music_file)}")
            except Exception as ex:
                print(f"音乐播放完全失败: {ex}")
    
    def toggle_music(self):
        """切换音乐播放状态"""
        if not self.music_file:
            QMessageBox.information(self, "音乐", "未找到音乐文件")
            return
            
        try:
            if self.music_playing:
                pygame.mixer.music.pause()
                self.music_playing = False
                print("音乐已暂停")
                self.statusBar().showMessage("音乐已暂停", 2000)
            else:
                pygame.mixer.music.unpause()
                self.music_playing = True
                print("音乐继续播放")
                self.statusBar().showMessage("音乐继续播放", 2000)
        except Exception as e:
            print(f"切换音乐状态时出错: {e}")
            # 尝试重新初始化音乐
            self.init_music()
    
    def initUI(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧播放列表面板
        self.playlist_panel = self.create_playlist_panel()
        main_layout.addWidget(self.playlist_panel, 1)  # 1/5的空间给播放列表
        
        # 创建右侧主内容区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 创建自定义标题栏
        title_bar = self.create_title_bar()
        right_layout.addWidget(title_bar)
        
        # 创建内容区域
        content_widget = self.create_content_widget()
        right_layout.addWidget(content_widget)
        
        main_layout.addWidget(right_panel, 4)  # 4/5的空间给主内容
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
            QWidget {
                background: transparent;
            }
        """)
        
        # 创建状态栏
        self.statusBar().setStyleSheet("color: white; background-color: rgba(40, 40, 40, 180);")
        if self.music_file:
            self.statusBar().showMessage(f"音乐: {os.path.basename(self.music_file)}", 3000)
    
    def create_title_bar(self):
        # 创建标题栏容器
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 180);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        
        # 创建标题栏布局
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加标题
        title_label = QLabel("Ave Mujica")
        title_label.setStyleSheet("""
            QLabel {
                color: red;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        title_layout.addWidget(title_label)
        
        # 添加弹性空间
        title_layout.addStretch()
        
        # 添加全屏按钮
        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(30, 30)
        fullscreen_btn.setToolTip("切换全屏 (F11)")
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """)
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        title_layout.addWidget(fullscreen_btn)
        
        # 添加最小化按钮
        min_btn = QPushButton("—")
        min_btn.setFixedSize(30, 30)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """)
        min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(min_btn)
        
        # 添加关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e81123;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        return title_bar
    
    def create_playlist_panel(self):
        # 创建播放列表面板
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 200);
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 播放列表标题
        playlist_label = QLabel("神人列表")
        playlist_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addWidget(playlist_label)
        
        # 播放列表操作按钮
        btn_layout = QHBoxLayout()
        
        # 新建播放列表按钮
        new_list_btn = QPushButton("新建")
        new_list_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        new_list_btn.clicked.connect(self.create_new_playlist)
        btn_layout.addWidget(new_list_btn)
        
        # 删除播放列表按钮
        del_list_btn = QPushButton("删除")
        del_list_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        del_list_btn.clicked.connect(self.delete_playlist)
        btn_layout.addWidget(del_list_btn)
        
        layout.addLayout(btn_layout)
        
        # 播放列表
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(50, 50, 50, 150);
                border: 1px solid rgba(100, 100, 100, 100);
                border-radius: 5px;
                color: white;
            }
            QListWidget::item:selected {
                background-color: rgba(52, 152, 219, 150);
            }
        """)
        self.playlist_widget.currentItemChanged.connect(self.switch_playlist)
        layout.addWidget(self.playlist_widget)
        
        # 添加当前播放列表项
        self.update_playlist_display()
        
        # 添加图片到播放列表按钮
        add_to_list_btn = QPushButton("添加图片到列表")
        add_to_list_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        add_to_list_btn.clicked.connect(self.add_images_to_playlist)
        layout.addWidget(add_to_list_btn)
        
        return panel
    
    def create_content_widget(self):
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 200);
                border-bottom-right-radius: 10px;
            }
        """)
        
        # 创建内容布局
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建图片显示区域
        self.image_display_widget = QWidget()
        image_display_layout = QVBoxLayout(self.image_display_widget)
        image_display_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建图片标签（用于显示图片）
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 100);
                border: 2px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                min-height: 400px;
            }
        """)
        self.image_label.setText("还真是低低在下呢！")
        self.image_label.setFont(QFont("Arial", 16))
        image_display_layout.addWidget(self.image_label)
        
        # 创建图片信息显示区域
        self.image_info_label = QLabel()
        self.image_info_label.setStyleSheet("color: white; font-size: 12px;")
        self.image_info_label.setAlignment(Qt.AlignCenter)
        self.image_info_label.setText("图片信息将显示在这里")
        image_display_layout.addWidget(self.image_info_label)
        
        content_layout.addWidget(self.image_display_widget, 3)  # 3/4的空间给图片显示
        
        # 创建控制面板
        control_panel = self.create_control_panel()
        content_layout.addWidget(control_panel, 1)  # 1/4的空间给控制面板
        
        return content_widget
    
    def create_control_panel(self):
        # 创建控制面板容器
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        
        # 第一行：文件夹选择和当前图片信息
        folder_row = QHBoxLayout()
        
        # 文件夹选择按钮
        folder_btn = QPushButton("选择图片文件夹")
        folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        folder_btn.clicked.connect(self.select_folder)
        folder_row.addWidget(folder_btn)
        
        # 当前图片信息
        self.info_label = QLabel("未选择文件夹")
        self.info_label.setStyleSheet("color: white; font-size: 12px;")
        folder_row.addWidget(self.info_label)
        
        folder_row.addStretch()
        panel_layout.addLayout(folder_row)
        
        # 第二行：导航控制
        nav_row = QHBoxLayout()
        
        # 上一张按钮
        prev_btn = QPushButton("上一张")
        prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        prev_btn.clicked.connect(self.prev_image)
        prev_btn.setShortcut(QKeySequence("Left"))  # 左箭头快捷键
        nav_row.addWidget(prev_btn)
        
        # 播放/暂停按钮
        self.play_btn = QPushButton("播放")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_slideshow)
        self.play_btn.setShortcut(QKeySequence("Space"))  # 空格键快捷键
        nav_row.addWidget(self.play_btn)
        
        # 下一张按钮
        next_btn = QPushButton("下一张")
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        next_btn.clicked.connect(self.next_image)
        next_btn.setShortcut(QKeySequence("Right"))  # 右箭头快捷键
        nav_row.addWidget(next_btn)
        
        panel_layout.addLayout(nav_row)
        
        # 第三行：图片编辑控制
        edit_row = QHBoxLayout()
        
        # 旋转按钮
        rotate_btn = QPushButton("旋转")
        rotate_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        rotate_btn.clicked.connect(self.rotate_image)
        rotate_btn.setShortcut(QKeySequence("R"))  # R键快捷键
        edit_row.addWidget(rotate_btn)
        
        # 水平翻转按钮
        flip_h_btn = QPushButton("水平翻转")
        flip_h_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        flip_h_btn.clicked.connect(self.flip_horizontal)
        flip_h_btn.setShortcut(QKeySequence("H"))  # H键快捷键
        edit_row.addWidget(flip_h_btn)
        
        # 垂直翻转按钮
        flip_v_btn = QPushButton("垂直翻转")
        flip_v_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        flip_v_btn.clicked.connect(self.flip_vertical)
        flip_v_btn.setShortcut(QKeySequence("V"))  # V键快捷键
        edit_row.addWidget(flip_v_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_btn.clicked.connect(self.reset_image_transform)
        reset_btn.setShortcut(QKeySequence("Ctrl+R"))  # Ctrl+R快捷键
        edit_row.addWidget(reset_btn)
        
        # 音乐控制按钮
        music_btn = QPushButton("音乐")
        music_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        music_btn.clicked.connect(self.toggle_music)
        music_btn.setShortcut(QKeySequence("M"))  # M键快捷键
        edit_row.addWidget(music_btn)
        
        panel_layout.addLayout(edit_row)
        
        # 第四行：播放控制
        control_row = QHBoxLayout()
        
        # 过渡效果选择
        transition_label = QLabel("过渡效果:")
        transition_label.setStyleSheet("color: white; font-size: 12px;")
        control_row.addWidget(transition_label)
        
        # 过渡效果下拉菜单
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["无", "淡入淡出", "从左滑动", "从右滑动", "从上滑动", "从下滑动"])
        self.transition_combo.setCurrentText(self.transition_type)
        self.transition_combo.currentTextChanged.connect(self.change_transition)
        self.transition_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(50, 50, 50, 200);
                color: white;
                border: 1px solid rgba(100, 100, 100, 100);
                border-radius: 3px;
                padding: 5px;
            }
        """)
        control_row.addWidget(self.transition_combo)
        
        # 间隔时间标签
        interval_label = QLabel("切换间隔(秒):")
        interval_label.setStyleSheet("color: white; font-size: 12px;")
        control_row.addWidget(interval_label)
        
        # 间隔时间滑块
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setRange(1, 30)  # 1-30秒
        self.interval_slider.setValue(self.slide_interval)
        self.interval_slider.setTickPosition(QSlider.TicksBelow)
        self.interval_slider.setTickInterval(5)
        self.interval_slider.valueChanged.connect(self.change_interval)
        control_row.addWidget(self.interval_slider)
        
        # 间隔时间数字显示
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 30)
        self.interval_spin.setValue(self.slide_interval)
        self.interval_spin.valueChanged.connect(self.change_interval_spin)
        control_row.addWidget(self.interval_spin)
        
        panel_layout.addLayout(control_row)
        
        return panel
    
    def select_folder(self):
        """选择图片文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择图片文件夹", "", 
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            self.image_folder = folder
            self.load_images_from_folder()
    
    def load_images_from_folder(self):
        """从文件夹加载图片"""
        # 支持的图片格式
        supported_formats = [fmt.data().decode().lower() for fmt in QImageReader.supportedImageFormats()]
        
        # 获取文件夹中的所有图片文件
        image_files = []
        for file in os.listdir(self.image_folder):
            if file.split('.')[-1].lower() in supported_formats:
                image_files.append(os.path.join(self.image_folder, file))
        
        # 更新当前播放列表
        if image_files:
            self.playlists[self.current_playlist] = image_files
            self.image_list = image_files
            self.current_index = 0
            
            # 预加载图片
            self.preload_images()
            
            self.display_current_image()
            self.update_info_label()
            
            # 如果有图片，自动开始播放
            self.start_slideshow()
        else:
            self.image_label.setText("文件夹中没有找到支持的图片")
            self.info_label.setText("未找到图片文件")
    
    def preload_images(self):
        """预加载图片到缓存"""
        if not self.image_list:
            return
        
        # 清空缓存
        self.image_cache.clear()
        
        # 确定预加载范围（当前索引前后各几张）
        start_idx = max(0, self.current_index - 3)
        end_idx = min(len(self.image_list), self.current_index + 4)
        
        preload_paths = []
        for i in range(start_idx, end_idx):
            path = self.image_list[i]
            if path not in self.image_cache:
                preload_paths.append(path)
        
        # 启动预加载线程
        if preload_paths and (self.loader_thread is None or not self.loader_thread.isRunning()):
            self.loader_thread = ImageLoaderThread(preload_paths)
            self.loader_thread.image_loaded.connect(self.add_to_cache)
            self.loader_thread.start()
    
    def add_to_cache(self, path, pixmap):
        """将图片添加到缓存"""
        self.image_cache[path] = pixmap
        
        # 如果缓存超过限制，移除最旧的图片
        if len(self.image_cache) > self.cache_size:
            # 使用LRU策略移除最旧的图片
            oldest_key = next(iter(self.image_cache))
            del self.image_cache[oldest_key]
    
    def add_images_to_playlist(self):
        """添加图片到当前播放列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp)"
        )
        
        if files:
            # 添加到当前播放列表
            self.playlists[self.current_playlist].extend(files)
            self.image_list = self.playlists[self.current_playlist]
            
            # 如果是第一次添加图片，显示第一张
            if len(self.playlists[self.current_playlist]) == len(files):
                self.current_index = 0
                self.preload_images()
                self.display_current_image()
            
            self.update_info_label()
            QMessageBox.information(self, "成功", f"已添加 {len(files)} 张图片到播放列表")
    
    def create_new_playlist(self):
        """创建新的播放列表"""
        name, ok = QInputDialog.getText(self, "新建播放列表", "请输入播放列表名称:")
        
        if ok and name:
            if name in self.playlists:
                QMessageBox.warning(self, "警告", "播放列表已存在!")
                return
            
            self.playlists[name] = []
            self.current_playlist = name
            self.image_list = []
            self.current_index = 0
            self.update_playlist_display()
            self.update_info_label()
            self.image_label.setText("请添加图片到播放列表")
    
    def delete_playlist(self):
        """删除当前播放列表"""
        if self.current_playlist == "默认列表":
            QMessageBox.warning(self, "警告", "不能删除默认播放列表!")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除播放列表 '{self.current_playlist}' 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.playlists[self.current_playlist]
            self.current_playlist = "默认列表"
            self.image_list = self.playlists[self.current_playlist]
            self.current_index = 0
            self.update_playlist_display()
            self.update_info_label()
            self.image_label.setText("请添加图片到播放列表")
    
    def switch_playlist(self, current, previous):
        """切换播放列表"""
        if current is None:
            return
        
        playlist_name = current.text()
        if playlist_name in self.playlists:
            self.current_playlist = playlist_name
            self.image_list = self.playlists[playlist_name]
            self.current_index = 0
            
            if self.image_list:
                self.preload_images()
                self.display_current_image()
            else:
                self.image_label.setText("播放列表为空，请添加图片")
            
            self.update_info_label()
    
    def update_playlist_display(self):
        """更新播放列表显示"""
        self.playlist_widget.clear()
        for playlist_name in self.playlists.keys():
            item = QListWidgetItem(playlist_name)
            item.setSizeHint(QSize(0, 30))  # 设置项目高度
            self.playlist_widget.addItem(item)
            
            # 设置当前播放列表为选中状态
            if playlist_name == self.current_playlist:
                self.playlist_widget.setCurrentItem(item)
    
    def display_current_image(self):
        """显示当前图片"""
        if not self.image_list:
            return
        
        # 停止当前的动画
        if hasattr(self, 'animation') and self.animation:
            self.animation.stop()
        
        # 获取当前图片路径
        image_path = self.image_list[self.current_index]
        
        # 检查图片是否在缓存中
        if image_path in self.image_cache:
            pixmap = self.image_cache[image_path]
        else:
            # 如果不在缓存中，直接加载（会阻塞UI，尽量避免）
            pixmap = QPixmap(image_path)
            # 添加到缓存
            self.image_cache[image_path] = pixmap
        
        # 应用变换（旋转和翻转）
        if not pixmap.isNull():
            transform = QTransform()
            transform.rotate(self.image_rotation)
            if self.image_flip_h:
                transform.scale(-1, 1)
            if self.image_flip_v:
                transform.scale(1, -1)
            
            if not transform.isIdentity():
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            
            # 缩放图片以适应标签大小，保持纵横比
            label_size = self.image_label.size()
            if label_size.width() > 10 and label_size.height() > 10:  # 确保标签有有效大小
                scaled_pixmap = pixmap.scaled(
                    label_size.width() - 20, 
                    label_size.height() - 20,
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                # 根据过渡效果类型显示图片
                if self.transition_type == "无" or not hasattr(self, 'previous_pixmap'):
                    # 直接显示图片
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    # 使用过渡效果
                    self.apply_transition_effect(scaled_pixmap)
                
                # 保存当前图片用于下一次过渡
                self.previous_pixmap = scaled_pixmap
                
                # 更新图片信息
                self.update_image_info(image_path)
        
        # 预加载下一批图片
        self.preload_images()
    
    def apply_transition_effect(self, new_pixmap):
        """应用过渡效果"""
        # 简化过渡效果，减少性能开销
        if self.transition_type == "淡入淡出":
            self.image_label.setPixmap(new_pixmap)
        else:
            # 对于滑动效果，使用简单的设置而不是动画
            self.image_label.setPixmap(new_pixmap)
    
    def update_image_info(self, image_path):
        """更新图片信息显示"""
        try:
            # 获取文件信息
            file_size = os.path.getsize(image_path)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(image_path))
            
            # 格式化文件大小
            size_unit = "B"
            size_value = file_size
            if file_size > 1024:
                size_value = file_size / 1024
                size_unit = "KB"
            if size_value > 1024:
                size_value = size_value / 1024
                size_unit = "MB"
            
            size_str = f"{size_value:.1f} {size_unit}"
            
            # 获取图片尺寸
            pixmap = QPixmap(image_path)
            width, height = pixmap.width(), pixmap.height()
            
            # 尝试获取EXIF信息
            exif_info = ""
            if EXIF_SUPPORT:
                try:
                    exif_data = piexif.load(image_path)
                    if "0th" in exif_data and piexif.ImageIFD.Model in exif_data["0th"]:
                        camera_model = exif_data["0th"][piexif.ImageIFD.Model].decode('utf-8')
                        exif_info = f" | 相机: {camera_model}"
                except:
                    pass  # 忽略EXIF解析错误
            
            # 更新信息标签
            info_text = f"{os.path.basename(image_path)} | {width}×{height} | {size_str}{exif_info}"
            self.image_info_label.setText(info_text)
            
        except Exception as e:
            self.image_info_label.setText(f"无法获取图片信息: {str(e)}")
    
    def next_image(self):
        """显示下一张图片"""
        if not self.image_list:
            return
        
        self.current_index = (self.current_index + 1) % len(self.image_list)
        self.display_current_image()
        self.update_info_label()
    
    def prev_image(self):
        """显示上一张图片"""
        if not self.image_list:
            return
        
        self.current_index = (self.current_index - 1) % len(self.image_list)
        self.display_current_image()
        self.update_info_label()
    
    def update_info_label(self):
        """更新信息标签"""
        if not self.image_list:
            self.info_label.setText("播放列表为空")
            return
        
        self.info_label.setText(f"播放列表: {self.current_playlist} | 共 {len(self.image_list)} 张图片 | 当前: {self.current_index + 1}/{len(self.image_list)}")
    
    def toggle_slideshow(self):
        """切换播放/暂停状态"""
        if self.timer.isActive():
            self.stop_slideshow()
        else:
            self.start_slideshow()
    
    def start_slideshow(self):
        """开始自动播放"""
        if not self.image_list:
            return
        
        self.timer.start(self.slide_interval * 1000)  # 转换为毫秒
        self.play_btn.setText("暂停")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
    
    def stop_slideshow(self):
        """停止自动播放"""
        self.timer.stop()
        self.play_btn.setText("播放")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
    
    def change_interval(self, value):
        """改变播放间隔"""
        self.slide_interval = value
        self.interval_spin.setValue(value)
        
        # 如果正在播放，重新启动定时器
        if self.timer.isActive():
            self.timer.setInterval(self.slide_interval * 1000)
    
    def change_interval_spin(self, value):
        """通过SpinBox改变播放间隔"""
        self.interval_slider.setValue(value)
        self.change_interval(value)
    
    def change_transition(self, transition):
        """改变过渡效果"""
        self.transition_type = transition
    
    def rotate_image(self):
        """旋转图片"""
        self.image_rotation = (self.image_rotation + 90) % 360
        self.display_current_image()
    
    def flip_horizontal(self):
        """水平翻转图片"""
        self.image_flip_h = not self.image_flip_h
        self.display_current_image()
    
    def flip_vertical(self):
        """垂直翻转图片"""
        self.image_flip_v = not self.image_flip_v
        self.display_current_image()
    
    def reset_image_transform(self):
        """重置图片变换"""
        self.image_rotation = 0
        self.image_flip_h = False
        self.image_flip_v = False
        self.display_current_image()
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Space:
            self.toggle_slideshow()
        elif event.key() == Qt.Key_Left:
            self.prev_image()
        elif event.key() == Qt.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key_R:
            self.rotate_image()
        elif event.key() == Qt.Key_H:
            self.flip_horizontal()
        elif event.key() == Qt.Key_V:
            self.flip_vertical()
        elif event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            self.reset_image_transform()
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.toggle_music()  # Ctrl+C 暂停/继续音乐
        elif event.key() == Qt.Key_O and event.modifiers() == Qt.ControlModifier:
            self.toggle_music()  # Ctrl+O 暂停/继续音乐
        elif event.key() == Qt.Key_M:
            self.toggle_music()  # M键控制音乐
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新调整图片大小"""
        super().resizeEvent(event)
        if self.image_list:
            self.display_current_image()
    
    def paintEvent(self, event):
        """绘制背景"""
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self.oldPos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and not self.is_fullscreen:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
    
    def closeEvent(self, event):
        """窗口关闭时停止音乐"""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except:
            pass
        event.accept()

# 应用程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    window = ImageViewerWindow()
    window.show()
    
    sys.exit(app.exec_())