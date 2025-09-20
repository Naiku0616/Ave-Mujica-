import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QWidget, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QFont

class CustomMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("TEXT")  # 窗口标题
        self.setGeometry(600, 100, 850, 950)  # 窗口位置和大小(x, y, width, height)

        # 移除默认窗口边框（创建无边框窗口）
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 设置窗口背景为半透明（可选）
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 加载背景图像
        # 注意：请将路径替换为您自己的图像路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "丰川祥子.png")
        
        if os.path.exists(image_path):
            self.background = QPixmap(image_path)
        else:
            # 如果没有找到图像，创建一个默认的背景
            self.background = QPixmap(900, 600)
            self.background.fill(Qt.darkGray)
            print(f"警告：未找到背景图像 {image_path}，使用默认背景")

            # 初始化拖动变量
        self.oldPos = self.pos()
        
        # 创建UI
        self.initUI()
    
    def initUI(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

         # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        main_layout.setSpacing(0)  # 移除间距
        
        # 创建自定义标题栏
        title_bar = self.create_title_bar()
        main_layout.addWidget(title_bar)
        
        # 创建内容区域
        content_widget = self.create_content_widget()
        main_layout.addWidget(content_widget)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
            QWidget {
                background: transparent;
            }
        """)
    
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
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        title_layout.addWidget(title_label)
        
        # 添加弹性空间
        title_layout.addStretch()

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
    
    def create_content_widget(self):
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 150);
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        
        # 创建内容布局
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加欢迎文本
        welcome_label = QLabel("客服小祥很不高兴为您服务")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        content_layout.addWidget(welcome_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 100);")
        content_layout.addWidget(separator)
        
        # 添加说明文本
        info_label = QLabel(
            "还真是高高在上啊！\n"
            "曾经那个软弱的我已经死了\n"
            "现在是更软弱的我"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                padding: 20px;
            }
        """)
        content_layout.addWidget(info_label)

        # 添加按钮
        button_layout = QHBoxLayout()
        
        start_btn = QPushButton("点击投诉")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        button_layout.addWidget(start_btn)

        settings_btn = QPushButton("展开重力场")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:pressed {
                background-color: #626567;
            }
        """)
        button_layout.addWidget(settings_btn)
        
        content_layout.addLayout(button_layout)

        # 添加弹性空间
        content_layout.addStretch()
        
        return content_widget
    
    def paintEvent(self, event):
        # 绘制背景图像
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background)
    
    def mousePressEvent(self, event):
        # 记录鼠标按下时的位置
        self.oldPos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        # 实现窗口拖动
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

# 应用程序入口点
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 10)  # 使用微软雅黑字体
    app.setFont(font)
    
    window = CustomMainWindow()
    window.show()
    
    sys.exit(app.exec_())