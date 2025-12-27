#!/usr/bin/env python3
"""
工具函数集合
"""

import os
import json
import urllib.request
import base64
import io
from PIL import Image, ImageDraw, ImageEnhance
import shutil
import urllib.parse
import subprocess
import time
from datetime import datetime
import glob
import textwrap

from config import VOLC_CONFIG, VIDEO_CONFIG, NGINX_CONFIG

def call_volc_api(payload, api_type="chat", method="POST"):
    """调用火山引擎API - 完整实现"""
    api_url_map = {
        "chat": VOLC_CONFIG["chat_api_base"],
        "text_to_image": VOLC_CONFIG["text_to_image_api_base"],
        "video_generate": VOLC_CONFIG["video_generate_api_base"],
        "task_info": f"{VOLC_CONFIG['task_info_api_base']}/",
    }
    
    api_url = api_url_map.get(api_type, VOLC_CONFIG["chat_api_base"])
    
    headers = {
        "content-Type": "application/json",
        "Authorization": f"Bearer {VOLC_CONFIG['api_key']}"
    }
    
    for attempt in range(VIDEO_CONFIG["max_retries"]):
        try:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                url=api_url,
                data=data,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)
                return result
                
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            print(f"  ❌❌ HTTP错误 {e.code} (尝试 {attempt+1}/{VIDEO_CONFIG['max_retries']}): {error_msg[:200]}")
            
            if attempt < VIDEO_CONFIG["max_retries"] - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"  ⏳⏳⏳ 等待{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            raise Exception(f"HTTP {e.code}: {error_msg[:200]}")
            
        except Exception as e:
            print(f"  ❌❌ 网络错误 (尝试 {attempt+1}/{VIDEO_CONFIG['max_retries']}): {str(e)}")
            
            if attempt < VIDEO_CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            raise Exception(f"网络错误: {str(e)}")
    
    raise Exception("超过最大重试次数")

def compress_image_to_target(image_path, target_size_kb=512):
    """将图片压缩到指定大小（KB）以内 - 完整实现"""
    print(f"  📦📦 压缩图片到{target_size_kb}KB以内...")
    
    try:
        original_img = Image.open(image_path)
    except Exception as e:
        print(f"    ❌❌ 无法打开图片: {e}")
        return image_path
    
    original_size_kb = os.path.getsize(image_path) / 1024
    
    print(f"    原始大小: {original_size_kb:.1f}KB")
    
    if original_size_kb <= target_size_kb:
        print(f"    ✅ 图片已小于{target_size_kb}KB，无需压缩")
        return image_path
    
    base_name = os.path.splitext(image_path)[0]
    
    # 策略1: PNG压缩
    print(f"    🔄🔄 策略1: PNG质量压缩")
    
    compressed_path = f"{base_name}_compressed.png"
    quality = 95
    
    while quality >= 30:
        buffer = io.BytesIO()
        
        if original_img.mode == 'RGBA':
            rgb_img = Image.new('RGB', original_img.size, (255, 255, 255))
            rgb_img.paste(original_img, mask=original_img.split()[3] if original_img.mode == 'RGBA' else None)
            current_img = rgb_img
        else:
            current_img = original_img
        
        current_img.save(buffer, format='PNG', optimize=True, compress_level=9)
        buffer_size_kb = buffer.tell() / 1024
        
        if buffer_size_kb <= target_size_kb:
            current_img.save(compressed_path, format='PNG', optimize=True, compress_level=9)
            final_size_kb = os.path.getsize(compressed_path) / 1024
            print(f"    ✅ PNG压缩完成: {original_size_kb:.1f}KB → {final_size_kb:.1f}KB")
            return compressed_path
        
        quality -= 15
    
    # 策略2: JPEG压缩
    print(f"    🔄🔄 策略2: JPEG压缩")
    
    jpeg_path = f"{base_name}_compressed.jpg"
    
    if original_img.mode != 'RGB':
        jpeg_img = original_img.convert('RGB')
    else:
        jpeg_img = original_img
    
    quality = 85
    while quality >= 30:
        buffer = io.BytesIO()
        jpeg_img.save(buffer, format='JPEG', optimize=True, quality=quality)
        buffer_size_kb = buffer.tell() / 1024
        
        if buffer_size_kb <= target_size_kb:
            jpeg_img.save(jpeg_path, format='JPEG', optimize=True, quality=quality)
            final_size_kb = os.path.getsize(jpeg_path) / 1024
            print(f"    ✅ JPEG压缩完成: {original_size_kb:.1f}KB → {final_size_kb:.1f}KB (质量{quality}%)")
            return jpeg_path
        
        quality -= 10
    
    # 策略3: 调整尺寸
    print(f"    🔄🔄 策略3: 调整图片尺寸")
    
    current_size_kb = os.path.getsize(image_path) / 1024
    scale_factor = (target_size_kb / current_size_kb) ** 0.5
    scale_factor = max(scale_factor, 0.3)
    scale_factor = min(scale_factor, 0.9)
    
    new_width = int(original_img.width * scale_factor)
    new_height = int(original_img.height * scale_factor)
    new_width = max(new_width, 1024)
    new_height = max(new_height, 1024)
    
    print(f"    调整尺寸: {original_img.width}x{original_img.height} → {new_width}x{new_height}")
    
    resized_img = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    if original_img.mode != 'RGB':
        resized_img = resized_img.convert('RGB')
    
    final_path = f"{base_name}_resized.jpg"
    resized_img.save(final_path, format='JPEG', optimize=True, quality=75)
    
    final_size_kb = os.path.getsize(final_path) / 1024
    print(f"    ✅ 尺寸调整完成: {final_size_kb:.1f}KB")
    
    return final_path

def deploy_to_nginx(image_path, story_title):
    """部署图片到Nginx服务器 - 完整实现"""
    print("🌐🌐 部署图片到Nginx...")
    
    compressed_path = compress_image_to_target(image_path, target_size_kb=512)
    
    if compressed_path != image_path:
        print(f"   使用压缩版本: {os.path.basename(compressed_path)}")
        image_path = compressed_path
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(compressed_path)[1]
    filename = f"comic_{timestamp}{file_ext}"
    
    target_path = os.path.join(NGINX_CONFIG["local_image_dir"], filename)
    
    try:
        shutil.copy2(image_path, target_path)
        os.chmod(target_path, 0o644)
        
        safe_filename = urllib.parse.quote(filename)
        image_url = f"{NGINX_CONFIG['server_url']}/{NGINX_CONFIG['sub_path']}/{safe_filename}"
        
        if os.path.exists(target_path):
            file_size = os.path.getsize(target_path) / 1024
            
            print(f"  ✅ 部署成功")
            print(f"     📁📁 文件: {filename}")
            print(f"     📁📁 路径: {target_path}")
            print(f"     🌐🌐 URL: {image_url}")
            print(f"     📦📦 大小: {file_size:.1f} KB")
            
            return {
                "local_path": image_path,
                "compressed_path": compressed_path,
                "nginx_path": target_path,
                "public_url": image_url,
                "filename": filename,
                "file_size_kb": file_size,
                "is_compressed": compressed_path != image_path
            }
        else:
            raise Exception("文件复制失败")
            
    except PermissionError as e:
        print(f"  ❌❌ 权限错误: {e}")
        print(f"  请运行: sudo chown -R $USER:$USER {NGINX_CONFIG['local_image_dir']}")
        raise
    except Exception as e:
        print(f"  ❌❌ 部署失败: {e}")
        raise

def extract_last_frame(video_path, output_image_path):
    """使用FFmpeg提取视频的最后一帧 - 完整实现"""
    print(f"  🎞🎞🎞️  提取尾帧: {os.path.basename(video_path)}")
    
    try:
        # 获取视频时长
        cmd_duration = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            video_path
        ]
        
        result = subprocess.run(cmd_duration, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise Exception(f"获取视频时长失败: {result.stderr}")
        
        duration = float(result.stdout.strip())
        
        # 提取最后一帧（在结束前0.1秒）
        seek_time = max(0, duration - 0.1)
        
        cmd_extract = [
            'ffmpeg', '-y',
            '-ss', str(seek_time),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',  # 高质量
            output_image_path
        ]
        
        print(f"     视频时长: {duration:.2f}秒，提取时间: {seek_time:.2f}秒")
        
        result = subprocess.run(cmd_extract, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"提取尾帧失败: {result.stderr}")
        
        if os.path.exists(output_image_path):
            file_size_kb = os.path.getsize(output_image_path) / 1024
            print(f"     ✅ 尾帧提取成功: {output_image_path}")
            print(f"        大小: {file_size_kb:.1f} KB")
            return output_image_path
        else:
            raise Exception("尾帧文件未生成")
            
    except FileNotFoundError:
        raise Exception("未找到ffmpeg或ffprobe，请确保已安装FFmpeg")
    except Exception as e:
        print(f"     ❌❌ 尾帧提取失败: {e}")
        # 创建备用图片
        return create_fallback_last_frame(output_image_path)

def create_fallback_last_frame(output_path):
    """创建备用尾帧图片 - 完整实现"""
    print("     ⚠⚠⚠️  创建备用尾帧...")
    
    # 创建简单的渐变图片（无文字）
    width, height = 1920, 1920
    img = Image.new('RGB', (width, height), color=(30, 30, 50))
    draw = ImageDraw.Draw(img)
    
    # 添加渐变
    for y in range(height):
        color_val = int(30 + (y / height) * 50)
        draw.line([(0, y), (width, y)], fill=(color_val, color_val, color_val + 20))
    
    # 不添加任何文字
    img.save(output_path, "PNG", quality=90)
    return output_path

def get_video_info(video_path):
    """获取视频文件信息 - 完整实现"""
    try:
        if not os.path.exists(video_path):
            return {"error": "文件不存在"}
        
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        
        info = {"file_size_mb": round(file_size_mb, 2)}
        
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=duration,width,height,codec_name',
                '-of', 'json', video_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                video_data = json.loads(result.stdout)
                if 'streams' in video_data and len(video_data['streams']) > 0:
                    stream = video_data['streams'][0]
                    info.update({
                        "duration": float(stream.get('duration', 0)),
                        "width": int(stream.get('width', 0)),
                        "height": int(stream.get('height', 0)),
                        "codec": stream.get('codec_name', 'unknown')
                    })
        except:
            pass
        
        return info
        
    except Exception as e:
        return {"error": str(e)}

def download_video(video_url, output_name):
    """下载生成的视频 - 完整实现"""
    print(f"  ⬇⬇⬇️  下载视频...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in output_name if c.isalnum() or c in ('_', '-')).rstrip()
    safe_name = safe_name.replace(' ', '_')[:50]
    
    filename = f"{safe_name}_{timestamp}.mp4"
    video_path = os.path.join(VIDEO_CONFIG["output_dir"], filename)
    
    try:
        req = urllib.request.Request(video_url)
        
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            print(f"     开始下载到: {video_path}")
            
            with open(video_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        print(f"     进度: {percent:6.1f}% ({mb_downloaded:.1f} MB)", end='\r')
        
        if os.path.exists(video_path):
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"\n  ✅ 视频下载完成")
            print(f"     📁📁 保存路径: {video_path}")
            print(f"     📦📦 文件大小: {file_size_mb:.2f} MB")
            
            return video_path
        else:
            raise Exception("文件下载后未找到")
            
    except Exception as e:
        print(f"\n  ❌❌ 视频下载失败: {e}")
        return None

def poll_video_task(task_id):
    """轮询视频任务状态 - 完整实现"""
    print(f"  🔄🔄 开始轮询任务状态...")
    
    query_url = f"{VOLC_CONFIG['task_info_api_base']}/{task_id}"
    
    start_time = time.time()
    last_status = ""
    
    status_translation = {
        "queued": "排队中",
        "running": "运行中", 
        "succeeded": "成功",
        "failed": "失败",
        "pending": "等待中",
        "processing": "处理中",
        "completed": "已完成",
        "success": "成功"
    }
    
    print(f"     轮询地址: {query_url}")
    
    for attempt in range(VIDEO_CONFIG["max_polling_attempts"]):
        try:
            elapsed = int(time.time() - start_time)
            remaining_attempts = VIDEO_CONFIG["max_polling_attempts"] - attempt - 1
            
            headers = {
                "Authorization": f"Bearer {VOLC_CONFIG['api_key']}",
                "Content-Type": "application/json"
            }
            
            req = urllib.request.Request(query_url, headers=headers, method='GET')
            with urllib.request.urlopen(req, timeout=30) as response:
                task_result = json.loads(response.read().decode('utf-8'))
            
            raw_status = task_result.get("status", "").lower()
            
            progress = task_result.get("progress", 0)
            if isinstance(progress, (int, float)):
                progress_display = f"{progress}%"
            else:
                progress_display = "未知"
            
            if raw_status != last_status:
                chinese_status = status_translation.get(raw_status, raw_status)
                
                status_info = f"     [{elapsed:3d}s] 状态: {chinese_status} ({raw_status})"
                if progress_display != "未知":
                    status_info += f" - 进度: {progress_display}"
                status_info += f" - 剩余轮询: {remaining_attempts}次"
                
                print(status_info)
                
                if raw_status in ["succeeded", "completed", "success"]:
                    video_url = None
                    
                    possible_locations = [
                        task_result.get("video_url"),
                        task_result.get("result_url"),
                        task_result.get("output_url"),
                        task_result.get("url"),
                        task_result.get("data", {}).get("video_url"),
                        task_result.get("data", {}).get("result_url"),
                        task_result.get("data", {}).get("output_url"),
                        task_result.get("data", {}).get("url"),
                        task_result.get("result", {}).get("video_url"),
                        task_result.get("result", {}).get("result_url"),
                        task_result.get("result", {}).get("output_url"),
                        task_result.get("result", {}).get("url"),
                    ]
                    
                    for url in possible_locations:
                        if url and isinstance(url, str) and url.startswith(("http://", "https://")):
                            video_url = url
                            break
                    
                    if video_url:
                        print(f"     ✅ 视频生成成功!")
                        print(f"         📹📹 视频URL: {video_url[:80]}...")
                        return video_url
                    else:
                        import re
                        response_str = json.dumps(task_result)
                        url_pattern = r'https?://[^\s<>"\'{}|\\^`]+'
                        urls = re.findall(url_pattern, response_str)
                        
                        if urls:
                            video_url = urls[0]
                            print(f"         找到URL: {video_url[:80]}...")
                            return video_url
                        else:
                            print(f"         ❌❌ 未找到任何视频URL")
                            return None
                
                elif raw_status == "failed":
                    error_msg = task_result.get("error_message", 
                                              task_result.get("error", 
                                                           task_result.get("message", "未知错误")))
                    print(f"     ❌❌ 任务失败: {error_msg}")
                    return None
                
                elif raw_status in ["running", "processing"]:
                    print(f"     🔄🔄 视频生成中...")
                
                elif raw_status in ["queued", "pending"]:
                    print(f"     ⏳⏳⏳ 任务排队中...")
                
                else:
                    print(f"     ? 未知状态，继续轮询...")
            
            last_status = raw_status
            
            if raw_status in ["succeeded", "completed", "success", "failed"]:
                break
            elif raw_status in ["running", "processing"]:
                time.sleep(5)
            elif raw_status in ["queued", "pending"]:
                time.sleep(10)
            else:
                time.sleep(15)
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"     ❌❌ 任务ID不存在或已过期: {task_id}")
                return None
            elif e.code == 429:
                print(f"     ⚠⚠⚠️  请求过于频繁，等待30秒...")
                time.sleep(30)
            else:
                print(f"     ⚠⚠⚠️  HTTP错误 {e.code}: {e.reason}")
                time.sleep(10)
                
        except Exception as e:
            print(f"     ⚠⚠⚠️  轮询出错: {str(e)}")
            time.sleep(10)
    
    print(f"  ⏰⏰⏰ 轮询超时 (超过{VIDEO_CONFIG['max_polling_attempts'] * VIDEO_CONFIG['polling_interval']}秒)")
    return None

def setup_directories():
    """创建必要的目录结构 - 完整实现"""
    print("📁📁 检查目录结构...")
    
    try:
        os.makedirs(NGINX_CONFIG["local_image_dir"], exist_ok=True)
        print(f"  ✅ Nginx目录: {NGINX_CONFIG['local_image_dir']}")
        os.chmod(NGINX_CONFIG["local_image_dir"], 0o755)
    except PermissionError:
        print(f"  ❌❌ 无法创建Nginx目录，权限不足")
        print(f"  请运行: sudo mkdir -p {NGINX_CONFIG['local_image_dir']}")
        print(f"         sudo chown -R $USER:$USER {NGINX_CONFIG['local_image_dir']}")
        return False
    except Exception as e:
        print(f"  ❌❌ 创建目录失败: {e}")
        return False
    
    os.makedirs(VIDEO_CONFIG["output_dir"], exist_ok=True)
    print(f"  ✅ 视频输出目录: {VIDEO_CONFIG['output_dir']}")
    
    return True

def cleanup_temp_files():
    """清理临时文件 - 完整实现"""
    print("🧹🧹 清理临时文件...")
    
    temp_patterns = [
        "*_compressed.png",
        "*_compressed.jpg", 
        "*_resized.jpg",
        "comic_frame_*.png",
        "fallback_*.png",
        "direct_test_*.png"
    ]
    
    cleaned_count = 0
    
    for pattern in temp_patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    cleaned_count += 1
            except Exception as e:
                pass
    
    print(f"  ✅ 清理完成，删除了 {cleaned_count} 个临时文件")

def confirm_with_user(prompt, options=None, default=None):
    """与用户确认的通用函数 - 完整实现"""
    print("\n" + "="*60)
    print("❓❓ 用户确认环节")
    print("="*60)
    
    if options:
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            choice = input(f"\n请选择 (1-{len(options)}){' [默认:' + str(default) + ']' if default else ''}: ").strip()
            if not choice and default:
                return options[default-1] if isinstance(default, int) else default
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice)-1]
            print(f"⚠️  请输入1-{len(options)}之间的数字")
    else:
        print(f"\n{prompt}")
        while True:
            response = input("请输入 'y' 确认继续，'n' 重新生成: ").strip().lower()
            if response in ['y', 'yes', '是']:
                return True
            elif response in ['n', 'no', '否']:
                return False
            print("⚠️  请输入 y/n")

def display_storyboard(story_data):
    """显示剧本详情供用户确认 - 修复版"""
    print("\n" + "="*60)
    print("📋📋 剧本详情确认")
    print("="*60)
    
    # 处理不同类型的 story_data
    if hasattr(story_data, 'overall_title'):  # StoryData对象
        overall_title = story_data.overall_title
        plot_twist = story_data.plot_twist
        segments = story_data.segments
    elif isinstance(story_data, dict):  # 字典
        overall_title = story_data.get('overall_title', '未指定')
        plot_twist = story_data.get('plot_twist', '')
        segments = story_data.get('segments', [])
    else:  # 其他类型
        print("❌ 无法识别的故事数据类型")
        return confirm_with_user("\n❌ 数据类型错误，是否继续生成？")
    
    print(f"\n🎬🎬 整体标题: {overall_title}")
    print(f"📊📊 分段数量: {len(segments)}")
    
    for i, segment in enumerate(segments, 1):
        print(f"\n{'─'*50}")
        
        # 处理不同类型的segment
        if hasattr(segment, 'title'):  # StorySegment对象
            segment_title = segment.title
            golden_hook = segment.golden_hook
            narration = segment.narration
            video_prompt = segment.video_prompt
            visual_prompt = segment.visual_prompt
        elif isinstance(segment, dict):  # 字典
            segment_title = segment.get('title', '未命名')
            golden_hook = segment.get('golden_hook', '')
            narration = segment.get('narration', [])
            video_prompt = segment.get('video_prompt', '')
            visual_prompt = segment.get('visual_prompt', '')
        else:
            continue
        
        print(f"🎬🎬 第{i}段: {segment_title}")
        print(f"{'─'*20}")
        
        # 显示黄金钩子
        if golden_hook:
            print(f"🎯🎯 3秒黄金钩子: {golden_hook}")
        
        # 显示解说词
        if narration:
            print(f"💬💬 解说词:")
            for j, line in enumerate(narration, 1):
                print(f"   镜头{j}: \"{line}\"")
        
        # 显示视频引导词
        if video_prompt:
            print(f"\n🎥🎥 视频引导词:")
            wrapped_text = textwrap.fill(video_prompt, width=70)
            for line in wrapped_text.split('\n'):
                print(f"   {line}")
        
        # 显示首图描述
        if visual_prompt:
            print(f"\n🖼🖼🖼️ 首图描述:")
            wrapped_visual = textwrap.fill(visual_prompt, width=70)
            for line in wrapped_visual.split('\n'):
                print(f"   {line}")
    
    # 显示剧情反转
    if plot_twist:
        print(f"\n{'─'*50}")
        print(f"🔄🔄 剧情反转:")
        print(f"   {plot_twist}")
    
    return confirm_with_user("\n✅ 剧本确认完成，是否继续生成？")

def display_first_image(compressed_image_path, original_image_path, segment_info):
    """显示压缩后的首图并让用户确认 - 完整实现"""
    print("\n" + "="*60)
    print("🖼🖼🖼️ 首图确认环节 (使用压缩版本)")
    print("="*60)
    
    # 优先使用压缩后的图片路径
    display_path = compressed_image_path if os.path.exists(compressed_image_path) else original_image_path
    
    try:
        # 在Jupyter中直接显示图片
        from IPython.display import Image as IPImage, display
        print(f"\n📁📁 图片文件: {os.path.basename(display_path)}")
        print(f"🎬🎬 所属分段: 第{segment_info.get('segment_number', 1)}段 - {segment_info.get('title', '未命名')}")
        
        # 显示图片描述
        if 'visual_prompt' in segment_info:
            print(f"\n📝📝 图片描述:")
            wrapped_desc = textwrap.fill(segment_info['visual_prompt'], width=70)
            for line in wrapped_desc.split('\n'):
                print(f"   {line}")
        
        # 显示文件对比信息
        if os.path.exists(original_image_path) and os.path.exists(compressed_image_path):
            original_size = os.path.getsize(original_image_path) / 1024
            compressed_size = os.path.getsize(compressed_image_path) / 1024
            
            print(f"\n📊📊 压缩对比:")
            print(f"   原始大小: {original_size:.1f} KB")
            print(f"   压缩大小: {compressed_size:.1f} KB")
            
            # 防止除零错误
            if original_size > 0:
                compression_ratio = (1 - compressed_size/original_size) * 100
                print(f"   压缩比例: {compression_ratio:.1f}%")
            else:
                print(f"   压缩比例: 0.0%")
                
            print(f"   ✅ 使用压缩版本生成视频，加载更快")
        
        # 显示当前文件信息
        file_size_kb = os.path.getsize(display_path) / 1024
        print(f"\n📦📦 当前文件大小: {file_size_kb:.1f} KB")
        
        # 检查是否符合视频生成要求
        if file_size_kb > 512:
            print(f"⚠️  警告: 文件大小超过512KB，可能影响视频生成速度")
        else:
            print(f"✅ 文件大小符合要求 (≤512KB)")
        
        # 检查图片是否包含文字
        print(f"\n🔍🔍 无字画面检查:")
        try:
            img = Image.open(display_path)
            # 简单检查：如果图片是纯色或简单图形，可能不会有明显文字
            # 这里只是提示用户检查
            print(f"   ✅ 图片已加载")
            print(f"   📏📏 图片尺寸: {img.size}")
            print(f"   💡💡 请确认画面中无任何文字元素")
        except Exception as e:
            print(f"   ⚠⚠⚠️  无法分析图片: {e}")
        
        # 在Jupyter中直接显示图片
        print("\n🖼🖼🖼️ 图片预览:")
        print("-"*50)
        
        # 显示图片
        display(IPImage(filename=display_path))
        
        print("-"*50)
        
    except ImportError:
        # 如果不在Jupyter环境中，回退到PIL显示
        print("⚠️  不在Jupyter环境中，使用简化预览")
        try:
            img = Image.open(display_path)
            print(f"\n📁📁 图片文件: {os.path.basename(display_path)}")
            print(f"📏📏 图片尺寸: {img.size}")
            print(f"🎬🎬 所属分段: 第{segment_info.get('segment_number', 1)}段 - {segment_info.get('title', '未命名')}")
        except:
            pass
    except Exception as e:
        print(f"⚠️  无法显示图片: {e}")
        print(f"📁📁 图片文件: {display_path}")
    
    # 让用户确认
    print("\n🔍🔍 请查看压缩后的图片文件确认质量:")
    print(f"   压缩文件: {os.path.abspath(compressed_image_path) if os.path.exists(compressed_image_path) else '未找到'}")
    print(f"   原始文件: {os.path.abspath(original_image_path) if os.path.exists(original_image_path) else '未找到'}")
    
    return confirm_with_user("✅ 压缩后的首图质量是否满意，是否继续生成视频？")

def display_golden_hook_confirmation(story_data):
    """显示并确认黄金钩子 - 完整实现"""
    print("\n" + "="*60)
    print("🎯🎯 黄金钩子确认环节")
    print("="*60)
    
    # 处理不同类型的 story_data
    if hasattr(story_data, 'segments'):  # StoryData对象
        segments = story_data.segments
        plot_twist = getattr(story_data, 'plot_twist', '')
    elif isinstance(story_data, dict):  # 字典
        segments = story_data.get('segments', [])
        plot_twist = story_data.get('plot_twist', '')
    else:  # 其他类型
        print("❌ 无法识别的故事数据类型")
        return confirm_with_user("\n❌ 数据类型错误，是否继续生成？")
    
    print(f"\n📊📊 黄金钩子检查 (前3秒吸引观众):")
    print("-"*50)
    
    all_hooks_valid = True
    
    for i, segment in enumerate(segments, 1):
        print(f"\n🎬🎬 第{i}段:")
        
        # 处理不同类型的segment
        if hasattr(segment, 'title'):  # StorySegment对象
            segment_title = segment.title
            golden_hook = getattr(segment, 'golden_hook', '')
        elif isinstance(segment, dict):  # 字典
            segment_title = segment.get('title', '未命名')
            golden_hook = segment.get('golden_hook', '')
        else:
            continue
            
        print(f"   🎬🎬 标题: {segment_title}")
        
        if golden_hook:
            hook = golden_hook
            # 检查钩子质量
            hook_length = len(hook)
            has_question = '？' in hook or '?' in hook
            has_emotional = any(word in hook for word in ['震惊', '惊呆', '没想到', '竟然', '原来', '秘密', '真相'])
            has_urgency = any(word in hook for word in ['紧急', '危险', '小心', '注意', '快看', '马上'])
            
            print(f"   🎯🎯🎯 黄金钩子: \"{hook}\"")
            print(f"   📊📊 分析:")
            print(f"     长度: {hook_length}字符 (建议15-30字)")
            print(f"     包含疑问: {'✅' if has_question else '⚠️'}")
            print(f"     情绪张力: {'✅' if has_emotional else '⚠️'}")
            print(f"     紧迫感: {'✅' if has_urgency else '⚠️'}")
            
            if hook_length < 10 or hook_length > 50:
                print(f"   ⚠⚠⚠️  提示: 钩子长度建议15-30字")
                all_hooks_valid = False
            if not (has_question or has_emotional or has_urgency):
                print(f"   ⚠⚠⚠️  提示: 建议增加疑问、情绪或紧迫感")
                all_hooks_valid = False
        else:
            print(f"   ❌❌ 未找到黄金钩子")
            all_hooks_valid = False
    
    # 检查剧情反转
    if plot_twist:
        print(f"\n🔄🔄 剧情反转:")
        print(f"   \"{plot_twist}\"")
        
        twist_length = len(plot_twist)
        is_surprising = any(word in plot_twist for word in ['反转', '意外', '没想到', '竟然', '原来', '真相', '秘密'])
        
        print(f"   📊📊 分析:")
        print(f"     长度: {twist_length}字符")
        print(f"     意外性: {'✅' if is_surprising else '⚠️'}")
        
        if twist_length < 10:
            print(f"   ⚠⚠⚠️  提示: 反转描述过短")
            all_hooks_valid = False
    else:
        print(f"\n⚠️  未找到剧情反转描述")
        all_hooks_valid = False
    
    if not all_hooks_valid:
        print(f"\n⚠️  部分钩子需要优化，是否继续？")
        return confirm_with_user("继续生成视频？")
    
    return confirm_with_user("\n✅ 黄金钩子检查完成，是否继续？")