#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频去重工具 - GUI版本
使用 CustomTkinter 构建现代化深色主题界面
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import shutil
import random
import re
import os
from pathlib import Path
from datetime import datetime


class VideoDeduplicatorApp(ctk.CTk):
    """视频去重工具主界面"""
    
    def __init__(self):
        super().__init__()
        
        # 窗口基本设置
        self.title("🎬 视频去重处理器 - GPU加速版")
        self.geometry("850x950")  # 增加窗口高度
        self.minsize(750, 800)    # 增加最小高度
        
        # 设置深色主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 状态变量
        self.is_processing = False
        self.total_frames = 0
        self.process = None
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建所有界面组件"""
        
        # 创建可滚动的主容器
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 主容器（在滚动区域内）
        self.main_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ========== 标题区域 ==========
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🎬 视频去重处理器",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="使用 FFmpeg + GPU 加速，智能混合去重",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # ========== 文件选择区域 ==========
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", pady=(0, 15))
        
        file_title = ctk.CTkLabel(
            file_frame,
            text="📁 文件设置",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        file_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 主视频输入
        self.video_a_entry = self._create_file_input(
            file_frame, "主视频文件", "选择主视频 (video_a)", self._select_video_a
        )
        
        # 干扰视频输入
        self.video_b_entry = self._create_file_input(
            file_frame, "干扰视频文件", "选择干扰视频 (video_b)", self._select_video_b
        )
        
        # 输出目录
        self.output_dir_entry = self._create_file_input(
            file_frame, "输出目录", "选择输出目录", self._select_output_dir
        )
        
        # ========== 参数设置区域 ==========
        param_frame = ctk.CTkFrame(self.main_frame)
        param_frame.pack(fill="x", pady=(0, 15))
        
        param_title = ctk.CTkLabel(
            param_frame,
            text="⚙️ 参数设置",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        param_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 参数内容容器
        param_content = ctk.CTkFrame(param_frame, fg_color="transparent")
        param_content.pack(fill="x", padx=15, pady=(0, 15))
        
        # 左侧参数
        left_params = ctk.CTkFrame(param_content, fg_color="transparent")
        left_params.pack(side="left", fill="x", expand=True)
        
        # 混合比例滑动条
        blend_frame = ctk.CTkFrame(left_params, fg_color="transparent")
        blend_frame.pack(fill="x", pady=5)
        
        self.blend_label = ctk.CTkLabel(
            blend_frame,
            text="🎨 混合比例: 0.03 (3.0%)",
            font=ctk.CTkFont(size=13)
        )
        self.blend_label.pack(anchor="w")
        
        self.blend_slider = ctk.CTkSlider(
            blend_frame,
            from_=0.01,
            to=0.15,
            number_of_steps=14,
            command=self._on_blend_change
        )
        self.blend_slider.set(0.03)
        self.blend_slider.pack(fill="x", pady=(5, 0))
        
        # 视频质量滑动条
        crf_frame = ctk.CTkFrame(left_params, fg_color="transparent")
        crf_frame.pack(fill="x", pady=(15, 5))
        
        self.crf_label = ctk.CTkLabel(
            crf_frame,
            text="🎞️ 视频质量 (CRF): 20 (越小质量越高)",
            font=ctk.CTkFont(size=13)
        )
        self.crf_label.pack(anchor="w")
        
        self.crf_slider = ctk.CTkSlider(
            crf_frame,
            from_=18,
            to=28,
            number_of_steps=10,
            command=self._on_crf_change
        )
        self.crf_slider.set(20)
        self.crf_slider.pack(fill="x", pady=(5, 0))
        
        # 右侧参数
        right_params = ctk.CTkFrame(param_content, fg_color="transparent")
        right_params.pack(side="right", fill="x", expand=True, padx=(30, 0))
        
        # 编码器选择
        encoder_frame = ctk.CTkFrame(right_params, fg_color="transparent")
        encoder_frame.pack(fill="x", pady=5)
        
        encoder_label = ctk.CTkLabel(
            encoder_frame,
            text="🔧 编码器选择",
            font=ctk.CTkFont(size=13)
        )
        encoder_label.pack(anchor="w")
        
        self.encoder_var = ctk.StringVar(value="自动检测")
        self.encoder_combo = ctk.CTkComboBox(
            encoder_frame,
            values=["自动检测", "CPU (libx264)", "NVIDIA (NVENC)", "AMD (AMF)", "Intel (QSV)"],
            variable=self.encoder_var,
            width=200
        )
        self.encoder_combo.pack(fill="x", pady=(5, 0))
        
        # ========== 进阶功能区域 ==========
        advanced_frame = ctk.CTkFrame(self.main_frame)
        advanced_frame.pack(fill="x", pady=(0, 15))
        
        advanced_title = ctk.CTkLabel(
            advanced_frame,
            text="🚀 进阶去重功能",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 进阶功能内容容器
        advanced_content = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        advanced_content.pack(fill="x", padx=15, pady=(0, 15))
        
        # 左侧：随机裁剪功能
        left_advanced = ctk.CTkFrame(advanced_content, fg_color="transparent")
        left_advanced.pack(side="left", fill="x", expand=True)
        
        # 随机裁剪开关
        crop_switch_frame = ctk.CTkFrame(left_advanced, fg_color="transparent")
        crop_switch_frame.pack(fill="x", pady=5)
        
        self.crop_var = ctk.BooleanVar(value=False)
        self.crop_switch = ctk.CTkSwitch(
            crop_switch_frame,
            text="✂️ 开启随机裁剪",
            variable=self.crop_var,
            font=ctk.CTkFont(size=13),
            command=self._on_crop_toggle
        )
        self.crop_switch.pack(anchor="w")
        
        # 裁剪强度滑动条
        crop_slider_frame = ctk.CTkFrame(left_advanced, fg_color="transparent")
        crop_slider_frame.pack(fill="x", pady=(10, 5))
        
        self.crop_strength_label = ctk.CTkLabel(
            crop_slider_frame,
            text="裁剪强度: 3.0% (范围 2%-10%)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.crop_strength_label.pack(anchor="w")
        
        self.crop_strength_slider = ctk.CTkSlider(
            crop_slider_frame,
            from_=0.02,
            to=0.10,
            number_of_steps=8,
            command=self._on_crop_strength_change,
            state="disabled"
        )
        self.crop_strength_slider.set(0.03)
        self.crop_strength_slider.pack(fill="x", pady=(5, 0))
        
        # 右侧：音频去重功能
        right_advanced = ctk.CTkFrame(advanced_content, fg_color="transparent")
        right_advanced.pack(side="right", fill="x", expand=True, padx=(30, 0))
        
        # 音频去重开关
        audio_switch_frame = ctk.CTkFrame(right_advanced, fg_color="transparent")
        audio_switch_frame.pack(fill="x", pady=5)
        
        self.audio_dedup_var = ctk.BooleanVar(value=False)
        self.audio_dedup_switch = ctk.CTkSwitch(
            audio_switch_frame,
            text="🎵 开启音频去重",
            variable=self.audio_dedup_var,
            font=ctk.CTkFont(size=13),
            command=self._on_audio_dedup_toggle
        )
        self.audio_dedup_switch.pack(anchor="w")
        
        # 音调滑动条
        pitch_slider_frame = ctk.CTkFrame(right_advanced, fg_color="transparent")
        pitch_slider_frame.pack(fill="x", pady=(10, 5))
        
        self.pitch_label = ctk.CTkLabel(
            pitch_slider_frame,
            text="音调系数: 1.01x (范围 0.98-1.02)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.pitch_label.pack(anchor="w")
        
        self.pitch_slider = ctk.CTkSlider(
            pitch_slider_frame,
            from_=0.98,
            to=1.02,
            number_of_steps=40,
            command=self._on_pitch_change,
            state="disabled"
        )
        self.pitch_slider.set(1.01)
        self.pitch_slider.pack(fill="x", pady=(5, 0))
        
        # ========== 控制按钮 ==========
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))
        
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 开始处理",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._start_processing
        )
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹️ 停止",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            fg_color="#8B0000",
            hover_color="#5C0000",
            state="disabled",
            command=self._stop_processing
        )
        self.stop_btn.pack(side="right", expand=True, fill="x", padx=(10, 0))
        
        # ========== 进度显示区域 ==========
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", pady=(0, 15))
        
        progress_title = ctk.CTkLabel(
            progress_frame,
            text="📊 处理进度",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        progress_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_bar.set(0)
        
        # 进度文字
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="就绪",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(anchor="w", padx=15, pady=(0, 15))
        
        # ========== 日志输出区域 ==========
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 FFmpeg 输出日志",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            height=150
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def _create_file_input(self, parent, label_text, placeholder, browse_command):
        """创建文件输入组件"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=5)
        
        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=13))
        label.pack(anchor="w")
        
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(5, 0))
        
        entry = ctk.CTkEntry(
            input_frame,
            placeholder_text=placeholder,
            height=35
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            input_frame,
            text="浏览...",
            width=80,
            height=35,
            command=browse_command
        )
        browse_btn.pack(side="right")
        
        return entry
    
    def _select_video_a(self):
        """选择主视频"""
        filepath = filedialog.askopenfilename(
            title="选择主视频",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv"),
                ("所有文件", "*.*")
            ]
        )
        if filepath:
            self.video_a_entry.delete(0, "end")
            self.video_a_entry.insert(0, filepath)
            self._log(f"✅ 已选择主视频: {filepath}")
    
    def _select_video_b(self):
        """选择干扰视频"""
        filepath = filedialog.askopenfilename(
            title="选择干扰视频",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv"),
                ("所有文件", "*.*")
            ]
        )
        if filepath:
            self.video_b_entry.delete(0, "end")
            self.video_b_entry.insert(0, filepath)
            self._log(f"✅ 已选择干扰视频: {filepath}")
    
    def _select_output_dir(self):
        """选择输出目录"""
        dirpath = filedialog.askdirectory(title="选择输出目录")
        if dirpath:
            self.output_dir_entry.delete(0, "end")
            self.output_dir_entry.insert(0, dirpath)
            self._log(f"✅ 已选择输出目录: {dirpath}")
    
    def _on_blend_change(self, value):
        """混合比例滑块变化"""
        self.blend_label.configure(
            text=f"🎨 混合比例: {value:.2f} ({value*100:.1f}%)"
        )
    
    def _on_crf_change(self, value):
        """视频质量滑块变化"""
        self.crf_label.configure(
            text=f"🎞️ 视频质量 (CRF): {int(value)} (越小质量越高)"
        )
    
    def _on_crop_toggle(self):
        """随机裁剪开关变化"""
        if self.crop_var.get():
            self.crop_strength_slider.configure(state="normal")
            self._log("✅ 已开启随机裁剪功能")
        else:
            self.crop_strength_slider.configure(state="disabled")
            self._log("❌ 已关闭随机裁剪功能")
    
    def _on_crop_strength_change(self, value):
        """裁剪强度滑块变化"""
        self.crop_strength_label.configure(
            text=f"裁剪强度: {value*100:.1f}% (范围 2%-10%)"
        )
    
    def _on_audio_dedup_toggle(self):
        """音频去重开关变化"""
        if self.audio_dedup_var.get():
            self.pitch_slider.configure(state="normal")
            self._log("✅ 已开启音频去重功能")
        else:
            self.pitch_slider.configure(state="disabled")
            self._log("❌ 已关闭音频去重功能")
    
    def _on_pitch_change(self, value):
        """音调滑块变化"""
        self.pitch_label.configure(
            text=f"音调系数: {value:.3f}x (范围 0.98-1.02)"
        )
    
    def _log(self, message):
        """添加日志"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
    
    def _check_ffmpeg(self) -> bool:
        """检测 FFmpeg"""
        return shutil.which('ffmpeg') is not None
    
    def _get_video_frame_count(self, video_path: str) -> int:
        """获取视频总帧数"""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-count_packets',
                '-show_entries', 'stream=nb_read_packets',
                '-of', 'csv=p=0',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return int(result.stdout.strip())
        except:
            pass
        return 0
    
    def _detect_gpu_encoder(self) -> str:
        """检测可用的GPU编码器"""
        encoder_choice = self.encoder_var.get()
        
        if encoder_choice == "CPU (libx264)":
            return 'libx264'
        elif encoder_choice == "NVIDIA (NVENC)":
            return 'h264_nvenc'
        elif encoder_choice == "AMD (AMF)":
            return 'h264_amf'
        elif encoder_choice == "Intel (QSV)":
            return 'h264_qsv'
        
        # 自动检测
        gpu_encoders = [
            ('h264_nvenc', 'NVIDIA'),
            ('h264_amf', 'AMD'),
            ('h264_qsv', 'Intel'),
        ]
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=10
            )
            available_encoders = result.stdout
            
            for encoder, brand in gpu_encoders:
                if encoder in available_encoders:
                    test_cmd = [
                        'ffmpeg', '-hide_banner', '-f', 'lavfi',
                        '-i', 'nullsrc=s=256x256:d=0.1',
                        '-c:v', encoder, '-f', 'null', '-'
                    ]
                    test_result = subprocess.run(test_cmd, capture_output=True, timeout=10)
                    if test_result.returncode == 0:
                        self._log(f"🎮 检测到 {brand} GPU 编码器: {encoder}")
                        return encoder
        except Exception as e:
            self._log(f"⚠️ GPU 检测异常: {e}")
        
        self._log("🖥️ 使用 CPU 编码器: libx264")
        return 'libx264'
    
    def _start_processing(self):
        """开始处理"""
        # 验证输入
        video_a = self.video_a_entry.get().strip()
        video_b = self.video_b_entry.get().strip()
        output_dir = self.output_dir_entry.get().strip()
        
        if not video_a:
            messagebox.showerror("错误", "请选择主视频文件！")
            return
        if not video_b:
            messagebox.showerror("错误", "请选择干扰视频文件！")
            return
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录！")
            return
        if not Path(video_a).exists():
            messagebox.showerror("错误", f"主视频文件不存在：\n{video_a}")
            return
        if not Path(video_b).exists():
            messagebox.showerror("错误", f"干扰视频文件不存在：\n{video_b}")
            return
        if not self._check_ffmpeg():
            messagebox.showerror("错误", "未检测到 FFmpeg！请先安装 FFmpeg。")
            return
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(video_a).stem
        output_name = Path(output_dir) / f"{original_name}_dedup_{timestamp}.mp4"
        
        # 更新UI状态
        self.is_processing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="正在准备...")
        self.log_text.delete("1.0", "end")
        
        # 在后台线程中执行处理
        thread = threading.Thread(
            target=self._process_video,
            args=(video_a, video_b, str(output_name)),
            daemon=True
        )
        thread.start()
    
    def _process_video(self, video_a, video_b, output_name):
        """在后台线程中处理视频"""
        try:
            # 获取基础参数
            blend_opacity = self.blend_slider.get()
            crf = int(self.crf_slider.get())
            main_opacity = 1.0 - blend_opacity
            
            # 获取进阶功能参数
            enable_crop = self.crop_var.get()
            crop_strength = self.crop_strength_slider.get()
            enable_audio_dedup = self.audio_dedup_var.get()
            pitch_factor = self.pitch_slider.get()
            tempo_factor = 1.0  # 默认速度
            
            # 检测编码器
            self._log("=" * 50)
            self._log("🎬 视频去重处理器 - 进阶版")
            self._log("=" * 50)
            
            encoder = self._detect_gpu_encoder()
            is_gpu = encoder != 'libx264'
            
            encoder_info = {
                'libx264': '🖥️ CPU (libx264)',
                'h264_nvenc': '🎮 NVIDIA GPU (NVENC)',
                'h264_amf': '🎮 AMD GPU (AMF)',
                'h264_qsv': '🎮 Intel GPU (QSV)'
            }
            
            # 获取总帧数用于进度计算
            self._log("📊 正在分析视频信息...")
            self.total_frames = self._get_video_frame_count(video_a)
            if self.total_frames > 0:
                self._log(f"📊 视频总帧数: {self.total_frames}")
            else:
                self._log("⚠️ 无法获取帧数，进度将以时间估算")
            
            # ========== 构建视频滤镜命令 ==========
            filter_parts = []
            filter_parts.append(f"[1:v][0:v]scale2ref=w=iw:h=ih[b_scaled][a_ref]")
            filter_parts.append(f"[a_ref][b_scaled]blend=all_expr='A*{main_opacity}+B*{blend_opacity}'[blended]")
            
            # 如果启用随机裁剪
            if enable_crop:
                # 随机生成裁剪参数
                crop_left = random.uniform(0, crop_strength)
                crop_right = random.uniform(0, crop_strength)
                crop_top = random.uniform(0, crop_strength)
                crop_bottom = random.uniform(0, crop_strength)
                
                # 确保总裁剪不超过限制
                total_horizontal = crop_left + crop_right
                total_vertical = crop_top + crop_bottom
                
                if total_horizontal > crop_strength:
                    scale = crop_strength / total_horizontal
                    crop_left *= scale
                    crop_right *= scale
                    
                if total_vertical > crop_strength:
                    scale = crop_strength / total_vertical
                    crop_top *= scale
                    crop_bottom *= scale
                
                # crop 滤镜：从边缘裁剪，然后拉伸回原分辨率
                crop_w = 1 - crop_left - crop_right
                crop_h = 1 - crop_top - crop_bottom
                filter_parts.append(
                    f"[blended]crop=w=iw*{crop_w:.4f}:h=ih*{crop_h:.4f}:"
                    f"x=iw*{crop_left:.4f}:y=ih*{crop_top:.4f},"
                    f"scale=iw/{crop_w:.4f}:ih/{crop_h:.4f}:"
                    f"flags=lanczos[vout]"
                )
            
            filter_cmd = ";".join(filter_parts)
            
            # ========== 构建音频滤镜命令 ==========
            audio_filter_cmd = None
            if enable_audio_dedup:
                # 限制参数范围
                pitch_factor = max(0.98, min(1.02, pitch_factor))
                compensate_tempo = tempo_factor / pitch_factor
                compensate_tempo = max(0.5, min(100.0, compensate_tempo))
                
                audio_filter_cmd = (
                    f"asetrate=44100*{pitch_factor},"
                    f"aresample=44100,"
                    f"atempo={compensate_tempo:.4f}"
                )
            
            # ========== 构建完整的 filter_complex ==========
            if enable_audio_dedup and audio_filter_cmd:
                if enable_crop:
                    full_filter = f"{filter_cmd};[0:a]{audio_filter_cmd}[aout]"
                else:
                    full_filter = filter_cmd.replace("[blended]", "") + f";[0:a]{audio_filter_cmd}[aout]"
            else:
                full_filter = filter_cmd
                if not enable_crop:
                    full_filter = filter_cmd.replace("[blended]", "")
            
            # ========== 构建 FFmpeg 命令 ==========
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-y',
                '-i', video_a,
                '-i', video_b,
                '-filter_complex', full_filter,
            ]
            
            # 添加视频输出映射（如果有标签）
            if enable_crop:
                cmd.extend(['-map', '[vout]'])
            
            # 添加音频输出映射
            if enable_audio_dedup:
                cmd.extend(['-map', '[aout]'])
            
            cmd.extend(['-c:v', encoder])
            
            # 添加编码器参数
            if is_gpu:
                if encoder == 'h264_nvenc':
                    cmd.extend(['-rc', 'constqp', '-qp', str(crf)])
                elif encoder == 'h264_amf':
                    cmd.extend(['-rc', 'cqp', '-qp_i', str(crf), '-qp_p', str(crf)])
                elif encoder == 'h264_qsv':
                    cmd.extend(['-global_quality', str(crf)])
            else:
                cmd.extend(['-preset', 'fast', '-crf', str(crf)])
            
            # 音频编码设置
            if enable_audio_dedup:
                cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            else:
                cmd.extend(['-c:a', 'copy'])
            
            cmd.extend([
                '-shortest',
                '-movflags', '+faststart',
                output_name
            ])
            
            # 输出处理信息
            self._log(f"📥 主视频：{video_a}")
            self._log(f"🎭 干扰视频：{video_b}")
            self._log(f"📤 输出文件：{output_name}")
            self._log(f"⚙️ 混合比例：主视频 {main_opacity*100:.1f}% + 干扰 {blend_opacity*100:.1f}%")
            self._log(f"🔧 编码器：{encoder_info.get(encoder, encoder)}")
            if enable_crop:
                self._log(f"✂️ 随机裁剪：已启用 (强度 {crop_strength*100:.1f}%)")
            else:
                self._log(f"✂️ 随机裁剪：未启用")
            if enable_audio_dedup:
                self._log(f"🎵 音频去重：已启用 (音调 {pitch_factor:.3f}x)")
            else:
                self._log(f"🎵 音频去重：未启用")
            self._log("-" * 50)
            self._log("🚀 开始处理...")
            
            start_time = datetime.now()
            
            # 执行 FFmpeg
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 读取输出并更新进度
            for line in self.process.stdout:
                if not self.is_processing:
                    break
                    
                line = line.strip()
                
                # 解析帧进度
                frame_match = re.search(r'frame=\s*(\d+)', line)
                if frame_match:
                    current_frame = int(frame_match.group(1))
                    if self.total_frames > 0:
                        progress = min(current_frame / self.total_frames, 1.0)
                        self.after(0, lambda p=progress: self.progress_bar.set(p))
                        self.after(0, lambda f=current_frame, t=self.total_frames: 
                            self.progress_label.configure(text=f"处理中: {f}/{t} 帧 ({f/t*100:.1f}%)"))
                    else:
                        self.after(0, lambda f=current_frame:
                            self.progress_label.configure(text=f"处理中: {f} 帧"))
                    
                    # 只记录关键进度信息
                    if current_frame % 100 == 0:
                        speed_match = re.search(r'speed=\s*([\d.]+)x', line)
                        speed = speed_match.group(1) if speed_match else "N/A"
                        self.after(0, lambda l=f"⏳ frame={current_frame} speed={speed}x": self._log(l))
                elif line and not line.startswith('frame='):
                    self.after(0, lambda l=line: self._log(l))
            
            self.process.wait()
            
            if self.process.returncode == 0:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                output_size = Path(output_name).stat().st_size / (1024 * 1024)
                
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.progress_label.configure(text="✅ 处理完成！"))
                
                self._log("-" * 50)
                self._log(f"✅ 处理完成！")
                self._log(f"📁 输出文件：{output_name}")
                self._log(f"📊 文件大小：{output_size:.2f} MB")
                self._log(f"⏱️ 耗时：{duration:.1f} 秒")
                self._log("=" * 50)
                
                self.after(0, lambda: messagebox.showinfo(
                    "处理完成",
                    f"✅ 视频处理成功！\n\n"
                    f"输出文件：{output_name}\n"
                    f"文件大小：{output_size:.2f} MB\n"
                    f"处理耗时：{duration:.1f} 秒"
                ))
            else:
                self._log(f"❌ FFmpeg 处理失败！错误码：{self.process.returncode}")
                self.after(0, lambda: self.progress_label.configure(text="❌ 处理失败"))
                self.after(0, lambda: messagebox.showerror(
                    "处理失败",
                    f"FFmpeg 返回错误码：{self.process.returncode}\n请查看日志了解详情。"
                ))
                
        except Exception as e:
            self._log(f"❌ 发生错误：{e}")
            self.after(0, lambda: self.progress_label.configure(text=f"❌ 错误: {e}"))
            self.after(0, lambda err=str(e): messagebox.showerror("错误", f"处理过程中发生错误：\n{err}"))
        finally:
            self.is_processing = False
            self.process = None
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))
    
    def _stop_processing(self):
        """停止处理"""
        if self.process:
            self.is_processing = False
            self.process.terminate()
            self._log("⚠️ 用户取消了处理")
            self.progress_label.configure(text="已取消")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")


def main():
    """主函数"""
    app = VideoDeduplicatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
