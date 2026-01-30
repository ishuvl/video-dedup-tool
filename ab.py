#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频去重工具 - 进阶版
支持 blend 滤镜透明叠加 + 随机裁剪 + 音频微调
"""

import subprocess
import sys
import os
import shutil
import random
from pathlib import Path
from datetime import datetime


def check_ffmpeg() -> bool:
    """检测系统是否安装了 FFmpeg"""
    return shutil.which('ffmpeg') is not None


def check_file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return Path(filepath).exists()


def detect_gpu_encoder() -> str:
    """
    自动检测可用的 GPU 硬件编码器
    返回最佳可用编码器，如果没有则返回 libx264
    """
    # 按优先级排序的 GPU 编码器
    gpu_encoders = [
        ('h264_nvenc', 'NVIDIA'),   # NVIDIA 显卡
        ('h264_amf', 'AMD'),        # AMD 显卡
        ('h264_qsv', 'Intel'),      # Intel 核显
    ]
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True, text=True, timeout=10
        )
        available_encoders = result.stdout
        
        for encoder, brand in gpu_encoders:
            if encoder in available_encoders:
                # 尝试实际使用该编码器（有些检测到但不能用）
                test_cmd = [
                    'ffmpeg', '-hide_banner', '-f', 'lavfi', 
                    '-i', 'nullsrc=s=256x256:d=0.1', 
                    '-c:v', encoder, '-f', 'null', '-'
                ]
                test_result = subprocess.run(
                    test_cmd, capture_output=True, timeout=10
                )
                if test_result.returncode == 0:
                    return encoder
    except Exception:
        pass
    
    return 'libx264'  # 默认使用 CPU 编码


def smart_ab_deduplicate(
    video_a: str,
    video_b: str,
    output_name: str,
    blend_opacity: float = 0.03,
    crf: int = 20,
    preset: str = 'fast',
    use_gpu: bool = True,
    enable_crop: bool = False,
    crop_strength: float = 0.03,
    enable_audio_dedup: bool = False,
    pitch_factor: float = 1.01,
    tempo_factor: float = 1.0
) -> bool:
    """
    使用 blend 滤镜进行视频去重（正确实现透明叠加）
    支持随机裁剪和音频微调
    
    Args:
        video_a: 主视频路径
        video_b: 干扰素材视频路径
        output_name: 输出文件路径
        blend_opacity: 混合比例 (0.01-0.15，表示 B 视频占比)
        crf: 画质参数 (18-28, 越小画质越好)
        preset: 编码速度
        use_gpu: 是否使用GPU加速
        enable_crop: 是否启用随机裁剪
        crop_strength: 裁剪强度 (0.02-0.10，即2%-10%)
        enable_audio_dedup: 是否启用音频去重
        pitch_factor: 音调系数 (0.98-1.02)
        tempo_factor: 速度系数 (0.98-1.02)
    
    Returns:
        bool: 处理是否成功
    """
    
    # ========== 前置检查 ==========
    if not check_ffmpeg():
        print("❌ 错误：未检测到 FFmpeg")
        return False
    
    if not check_file_exists(video_a):
        print(f"❌ 错误：主视频文件不存在：{video_a}")
        return False
    
    if not check_file_exists(video_b):
        print(f"❌ 错误：干扰视频文件不存在：{video_b}")
        return False
    
    # 限制参数范围
    blend_opacity = max(0.01, min(0.15, blend_opacity))
    main_opacity = 1.0 - blend_opacity  # 主视频的保留比例
    
    # 限制裁剪和音频参数范围
    crop_strength = max(0.02, min(0.10, crop_strength))  # 限制在2%-10%
    pitch_factor = max(0.98, min(1.02, pitch_factor))    # 限制音调变化
    tempo_factor = max(0.98, min(1.02, tempo_factor))    # 限制速度变化
    
    # ========== 选择编码器 ==========
    if use_gpu:
        encoder = detect_gpu_encoder()
    else:
        encoder = 'libx264'
    
    is_gpu = encoder != 'libx264'
    encoder_info = {
        'libx264': '🖥️  CPU (libx264)',
        'h264_nvenc': '🎮 NVIDIA GPU (NVENC)',
        'h264_amf': '🎮 AMD GPU (AMF)',
        'h264_qsv': '🎮 Intel GPU (QSV)'
    }
    
    # ========== 构建视频滤镜命令 ==========
    # 方法：使用 blend 滤镜，将 A 和 B 按比例混合
    # all_expr: 对每个像素，输出 = A * (1-opacity) + B * opacity
    
    # 基础混合滤镜
    filter_parts = []
    filter_parts.append(f"[1:v][0:v]scale2ref=w=iw:h=ih[b_scaled][a_ref]")
    filter_parts.append(f"[a_ref][b_scaled]blend=all_expr='A*{main_opacity}+B*{blend_opacity}'[blended]")
    
    # 如果启用随机裁剪
    final_video_label = "[blended]"
    if enable_crop:
        # 随机生成裁剪参数（在 crop_strength 范围内随机变化）
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
        # crop=w:h:x:y 然后 scale 回原尺寸
        crop_w = 1 - crop_left - crop_right
        crop_h = 1 - crop_top - crop_bottom
        filter_parts.append(
            f"[blended]crop=w=iw*{crop_w:.4f}:h=ih*{crop_h:.4f}:"
            f"x=iw*{crop_left:.4f}:y=ih*{crop_top:.4f},"
            f"scale=iw/{crop_w:.4f}:ih/{crop_h:.4f}:"
            f"flags=lanczos[vout]"
        )
        final_video_label = "[vout]"
    
    filter_cmd = ";".join(filter_parts)
    
    # ========== 构建音频滤镜命令 ==========
    audio_filter_cmd = None
    if enable_audio_dedup:
        # 使用 asetrate + aresample + atempo 组合来调整音调和速度
        # asetrate: 改变采样率来改变音调（会同时改变速度）
        # aresample: 恢复原采样率
        # atempo: 补偿速度变化并应用所需的速度调整
        # 公式：最终速度 = pitch_factor * tempo_factor
        #       atempo 需要设置为 tempo_factor / pitch_factor 来补偿
        
        compensate_tempo = tempo_factor / pitch_factor
        # atempo 有限制 [0.5, 100.0]
        compensate_tempo = max(0.5, min(100.0, compensate_tempo))
        
        audio_filter_cmd = (
            f"asetrate=44100*{pitch_factor},"
            f"aresample=44100,"
            f"atempo={compensate_tempo:.4f}"
        )
    
    # ========== 构建 FFmpeg 命令 ==========
    # 根据是否有音频滤镜来构建完整的 filter_complex
    if enable_audio_dedup and audio_filter_cmd:
        if enable_crop:
            # 视频有输出标签 [vout]
            full_filter = f"{filter_cmd};[0:a]{audio_filter_cmd}[aout]"
        else:
            # 需要让混合输出成为默认视频输出（去掉 [blended] 标签）
            full_filter = filter_cmd.replace("[blended]", "") + f";[0:a]{audio_filter_cmd}[aout]"
    else:
        full_filter = filter_cmd
        if not enable_crop:
            # 去掉 [blended] 标签，让其成为默认输出
            full_filter = filter_cmd.replace("[blended]", "")
    
    cmd = [
        'ffmpeg',
        '-hide_banner',
        '-y',  # 自动覆盖
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
    
    # GPU 编码器使用不同的质量参数
    if is_gpu:
        # GPU 使用 CQ (Constant Quality) 模式
        if encoder == 'h264_nvenc':
            cmd.extend(['-rc', 'constqp', '-qp', str(crf)])
        elif encoder == 'h264_amf':
            cmd.extend(['-rc', 'cqp', '-qp_i', str(crf), '-qp_p', str(crf)])
        elif encoder == 'h264_qsv':
            cmd.extend(['-global_quality', str(crf)])
    else:
        # CPU 使用 CRF + preset
        cmd.extend(['-preset', preset, '-crf', str(crf)])
    
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
    
    # ========== 执行处理 ==========
    print("=" * 50)
    print("🎬 视频去重处理器 - 进阶版")
    print("=" * 50)
    print(f"📥 主视频：{video_a}")
    print(f"🎭 干扰视频：{video_b}")
    print(f"📤 输出文件：{output_name}")
    print(f"⚙️  混合比例：主视频 {main_opacity*100:.1f}% + 干扰 {blend_opacity*100:.1f}%")
    print(f"🔧 编码器：{encoder_info.get(encoder, encoder)}")
    if enable_crop:
        print(f"✂️  随机裁剪：已启用 (强度 {crop_strength*100:.1f}%)")
    else:
        print(f"✂️  随机裁剪：未启用")
    if enable_audio_dedup:
        print(f"🎵 音频去重：已启用 (音调 {pitch_factor:.3f}x, 速度 {tempo_factor:.3f}x)")
    else:
        print(f"🎵 音频去重：未启用")
    print("-" * 50)
    print("🚀 开始处理...")
    
    start_time = datetime.now()
    
    try:
        # 运行 FFmpeg
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        
        for line in process.stdout:
            if 'frame=' in line:
                print(f"\r⏳ {line.strip()[:60]}", end='', flush=True)
        
        process.wait()
        print()
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        output_size = Path(output_name).stat().st_size / (1024 * 1024)
        
        print("-" * 50)
        print(f"✅ 处理完成！")
        print(f"📁 输出文件：{output_name}")
        print(f"📊 文件大小：{output_size:.2f} MB")
        print(f"⏱️  耗时：{duration:.1f} 秒")
        print("=" * 50)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg 处理失败！错误码：{e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='🎬 视频去重处理器 - 进阶版')
    parser.add_argument('-a', '--input', default='target.mp4', help='主视频路径')
    parser.add_argument('-b', '--noise', default='noise.mp4', help='干扰视频路径')
    parser.add_argument('-o', '--output', default='final_original.mp4', help='输出文件路径')
    parser.add_argument('--opacity', type=float, default=0.03, help='干扰视频混合比例 (默认 0.03 即 3%%)')
    parser.add_argument('--crf', type=int, default=20, help='画质参数 (默认 20)')
    parser.add_argument('--preset', default='fast', help='CPU编码速度 (默认 fast)')
    parser.add_argument('--no-gpu', action='store_true', help='禁用GPU加速，强制使用CPU编码')
    
    # 新增随机裁剪参数
    parser.add_argument('--crop', action='store_true', help='启用随机裁剪')
    parser.add_argument('--crop-strength', type=float, default=0.03, 
                        help='裁剪强度 (0.02-0.10，默认 0.03 即 3%%，不超过10%%)')
    
    # 新增音频去重参数
    parser.add_argument('--audio-dedup', action='store_true', help='启用音频去重')
    parser.add_argument('--pitch', type=float, default=1.01,
                        help='音调系数 (0.98-1.02，默认 1.01)')
    parser.add_argument('--tempo', type=float, default=1.0,
                        help='速度系数 (0.98-1.02，默认 1.0)')
    
    args = parser.parse_args()
    
    success = smart_ab_deduplicate(
        args.input,
        args.noise,
        args.output,
        blend_opacity=args.opacity,
        crf=args.crf,
        preset=args.preset,
        use_gpu=not getattr(args, 'no_gpu', False),
        enable_crop=args.crop,
        crop_strength=args.crop_strength,
        enable_audio_dedup=args.audio_dedup,
        pitch_factor=args.pitch,
        tempo_factor=args.tempo
    )
    
    sys.exit(0 if success else 1)

