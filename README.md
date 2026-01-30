# 🎬 视频去重处理器 (Video Dedup Tool)

一款使用 **FFmpeg + GPU 加速** 的智能视频去重工具，通过画面混合、随机裁剪、音频微调等技术，让你的视频"焕然一新"。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ 功能介绍

### 🎨 核心功能：视频混合去重
- **智能透明叠加**：将主视频与干扰视频按可调比例（1%-15%）混合
- **GPU 硬件加速**：自动检测并使用 NVIDIA / AMD / Intel 显卡加速编码
- **高质量输出**：支持自定义 CRF 画质参数（18-28）

### ✂️ 进阶功能：随机裁剪
- **边缘随机裁剪**：从视频四边随机裁剪 2%-10%
- **智能拉伸填充**：裁剪后自动拉伸回原分辨率，肉眼几乎无法察觉
- **每次不同**：每次处理都会生成不同的裁剪参数

### 🎵 进阶功能：音频去重
- **音调微调**：将音频音调调整 ±2%（0.98x - 1.02x）
- **速度补偿**：自动补偿因音调变化产生的速度偏移
- **无感知处理**：微小的变化人耳几乎无法分辨

---

## 🖥️ 界面预览

本工具提供 **现代化深色主题 GUI 界面**，基于 CustomTkinter 构建：

- 📁 可视化文件选择
- 🎚️ 参数滑块调节
- 📊 实时进度显示
- 📋 FFmpeg 日志输出

---

## 📦 安装方法

### 1. 安装 FFmpeg

**Windows:**
```bash
# 使用 Scoop
scoop install ffmpeg

# 或使用 Chocolatey
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 2. 安装 Python 依赖

```bash
pip install customtkinter
```

---

## 🚀 使用方法

### 方式一：图形界面（推荐）

直接运行 GUI 程序：

```bash
python video_dedup_gui.py
```

然后：
1. 选择 **主视频文件**（要处理的视频）
2. 选择 **干扰视频文件**（用于混合的素材）
3. 选择 **输出目录**
4. 调整参数（混合比例、画质等）
5. 根据需要开启 **随机裁剪** 和 **音频去重**
6. 点击 **🚀 开始处理**

### 方式二：命令行

```bash
# 基础用法
python ab.py -a 主视频.mp4 -b 干扰视频.mp4 -o 输出.mp4

# 完整参数
python ab.py \
    -a target.mp4 \
    -b noise.mp4 \
    -o output.mp4 \
    --opacity 0.03 \
    --crf 20 \
    --crop \
    --crop-strength 0.05 \
    --audio-dedup \
    --pitch 1.01
```

### 命令行参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-a`, `--input` | 主视频路径 | `target.mp4` |
| `-b`, `--noise` | 干扰视频路径 | `noise.mp4` |
| `-o`, `--output` | 输出文件路径 | `final_original.mp4` |
| `--opacity` | 干扰视频混合比例 | `0.03` (3%) |
| `--crf` | 画质参数（越小越好） | `20` |
| `--no-gpu` | 禁用 GPU 加速 | - |
| `--crop` | 启用随机裁剪 | - |
| `--crop-strength` | 裁剪强度 | `0.03` (3%) |
| `--audio-dedup` | 启用音频去重 | - |
| `--pitch` | 音调系数 | `1.01` |
| `--tempo` | 速度系数 | `1.0` |

---

## ⚙️ 系统要求

- **操作系统**：Windows 10/11、macOS、Linux
- **Python**：3.8 或更高版本
- **FFmpeg**：需要预先安装并添加到系统 PATH
- **显卡**（可选）：NVIDIA / AMD / Intel 独显或核显，用于硬件加速

---

## 📁 项目结构

```
video-dedup-tool/
├── video_dedup_gui.py    # GUI 图形界面程序
├── ab.py                 # 命令行核心处理程序
├── .gitignore            # Git 忽略文件
└── README.md             # 项目说明文档
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## ⭐ 如果这个项目对你有帮助，请给一个 Star！
