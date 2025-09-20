# Ave-Mujica-
适合看过Band Dream Ave Mujica和Band Dream it's My Go!!!的同学
以下是为这个程序编写的 GitHub README.md 文件内容：

---

# Ave Mujica - 星泉Naiku 图片幻灯片播放器

![](https://img.shields.io/badge/Python-3.7%2B-blue)
![](https://img.shields.io/badge/PyQt5-5.15-green)
![](https://img.shields.io/badge/Pygame-2.0-orange)
![](https://img.shields.io/badge/License-MIT-lightgrey)

> 一个优雅、功能丰富的图片幻灯片播放器，支持播放列表管理、背景音乐、过渡动画与图片编辑。

## ✨ 功能特点

- 🖼️ **多格式支持**：支持 JPG、PNG、BMP、GIF、TIFF、WEBP 等常见图片格式
- 🎵 **背景音乐**：自动查找并循环播放背景音乐（支持 MP3、WAV、OGG、FLAC、M4A）
- 📂 **播放列表管理**：支持创建、删除多个播放列表，灵活管理图片集合
- 🎞️ **过渡效果**：提供淡入淡出、左右上下滑动等多种切换动画
- 🔧 **图片编辑**：支持旋转、水平/垂直翻转、重置变换等操作
- ⌨️ **快捷键支持**：空格播放/暂停、方向键切换、R旋转、H/V翻转等
- 🖥️ **无边框设计**：半透明背景，支持拖拽移动，可全屏显示
- ⚡ **智能预加载**：多线程预加载图片，提升浏览流畅度

## 🛠 安装依赖

确保你已安装 Python 3.7+，然后使用以下命令安装依赖：

```bash
pip install PyQt5 pygame piexif
```

> `piexif` 为可选依赖，用于读取图片 EXIF 信息。

## 🚀 使用方法

1. 运行程序：
```bash
python Ave_Mujica.py
```

2. 点击“选择图片文件夹”导入图片，或直接拖拽图片到播放列表中
3. 使用底部控制栏或快捷键控制播放：
   - `空格`：播放/暂停
   - `←/→`：上一张/下一张
   - `R`：旋转图片
   - `H`：水平翻转
   - `V`：垂直翻转
   - `Ctrl+R`：重置变换
   - `M`：切换音乐播放
   - `F11`：切换全屏

4. 可在左侧“神人列表”中管理多个播放列表

## 🎶 音乐支持

程序会自动查找以下名称的音乐文件作为背景音乐：

- `天球(そら)のMúsica - Ave Mujica.flac`
- `background_music.flac` / `.mp3`
- `music.flac` / `.mp3`

也可将任意音频文件放在程序同目录下，程序会自动识别并播放。

## 📁 项目结构

```
Ave_Mujica/
├── Ave_Mujica.py      # 主程序文件
├── requirements.txt   # 依赖列表
├── README.md          # 说明文档
└── (可选音乐文件)
```

## 📄 许可证

本项目基于 MIT 许可证开源。详情请见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

如果程序中有使用到外部资源（如图标、默认音乐等），请确保这些资源也符合对应的开源许可要求，并在 README 中予以说明。
