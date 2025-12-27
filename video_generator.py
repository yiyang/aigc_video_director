#!/usr/bin/env python3
"""
视频生成器核心
集成智能体系统
"""

import os
import json
import shutil
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageEnhance
import base64
import io

from config import VOLC_CONFIG, NGINX_CONFIG, VIDEO_CONFIG, COMIC_STYLES
from models import StoryInput, StoryData, ImageResult, VideoResult, SegmentResult, GenerationResult
from utils import (call_volc_api, compress_image_to_target, deploy_to_nginx, 
                  extract_last_frame, get_video_info, download_video, poll_video_task,
                  setup_directories, cleanup_temp_files, confirm_with_user,
                  display_storyboard, display_first_image, display_golden_hook_confirmation)
from agents import VideoDirectorAgent

class VideoGenerator:
    """视频生成器核心类"""
    
    def __init__(self, config):
        self.config = config
        self.director = VideoDirectorAgent(config)
        self.setup_completed = False
    
    def setup_environment(self):
        """设置生成环境"""
        print("🔧 设置视频生成环境...")
        
        if not setup_directories():
            return False
        
        # 检查FFmpeg
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg已安装")
            else:
                print("⚠️  FFmpeg检查失败")
        except:
            print("⚠️  FFmpeg未安装，尾帧提取功能可能受限")
        
        self.setup_completed = True
        return True
    
    def generate_continuous_series(self, user_input):
        """生成连续视频系列 - 主入口函数"""
        if not self.setup_completed and not self.setup_environment():
            return GenerationResult(status="failed", reason="环境设置失败")
        
        print("\n" + "="*70)
        print("🎬 开始生成三连视频系列")
        print("="*70)
        
        try:
            # 1. 智能导演制定计划
            production_plan = self.director.create_video_plan(user_input)
            story_data = production_plan["story_data"]
            
            # 2. 用户确认环节
            if not self._user_confirmation_workflow(story_data, production_plan):
                return GenerationResult(status="cancelled", reason="用户取消生成")
            
            # 3. 生成视频系列
            result = self._generate_video_series(story_data, user_input)
            
            # 4. 清理和总结
            self._cleanup_and_report(result, user_input)
            
            return result
            
        except Exception as e:
            print(f"❌ 视频生成失败: {e}")
            return GenerationResult(status="failed", reason=str(e))
    
    def _user_confirmation_workflow(self, story_data, production_plan):
        """用户确认工作流"""
        print("\n" + "="*60)
        print("👤 用户确认工作流")
        print("="*60)
        
        # 显示导演计划
        print("\n🎬 导演制作计划:")
        for note in production_plan.get("director_notes", []):
            print(f"  {note}")
        
        # 剧本确认
        if not display_storyboard(story_data):
            print("❌ 用户取消了剧本")
            return False
        
        # 黄金钩子确认
        if not display_golden_hook_confirmation(story_data):
            print("❌ 用户取消了生成")
            return False
        
        return True
    
    def _generate_video_series(self, story_data, user_input):
        """生成视频系列核心逻辑"""
        print("\n" + "="*60)
        print("🚀 开始生成视频系列")
        print("="*60)
        
        # 检查是否有有效分段
        if not story_data.segments:
            print("❌ 没有有效分段，无法生成视频")
            return GenerationResult(status="failed", reason="故事数据中没有有效分段")
        
        # 创建系列目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        series_name = user_input.output_name or f"video_series_{timestamp}"
        series_dir = os.path.join(VIDEO_CONFIG["output_dir"], series_name)
        os.makedirs(series_dir, exist_ok=True)
        
        print(f"📁 创建系列目录: {series_dir}")
        
        # 保存剧本
        script_path = os.path.join(series_dir, "production_script.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump({
                "overall_title": story_data.overall_title,
                "plot_twist": story_data.plot_twist,
                "segments": [{
                    "segment_number": seg.segment_number,
                    "title": seg.title,
                    "golden_hook": seg.golden_hook,
                    "visual_prompt": seg.visual_prompt,
                    "video_prompt": seg.video_prompt,
                    "narration": seg.narration,
                    "style_used": seg.style_used
                } for seg in story_data.segments]
            }, f, ensure_ascii=False, indent=2)
        
        # 逐个生成分段视频
        all_results = []
        last_frame_path = None
        
        for segment in story_data.segments[:3]:  # 只生成前3段
            print(f"\n🎬 生成第{segment.segment_number}段: {segment.title}")
            
            segment_result = self._generate_single_segment(
                segment, segment.segment_number, last_frame_path, series_dir
            )
            
            if segment_result:
                all_results.append(segment_result)
                last_frame_path = segment_result.last_frame_path
                
                # 显示进度
                total_segments = min(3, len(story_data.segments)) if len(story_data.segments) > 0 else 1
                progress = len(all_results) / total_segments * 100
                print(f"📊 进度: {progress:.0f}% ({len(all_results)}/3)")
            else:
                print(f"❌ 第{segment.segment_number}段生成失败")
        
        # 生成合并说明
        merge_instructions = self._generate_merge_instructions(all_results, series_dir, story_data)
        
        # 生成详细报告
        detailed_report = self._generate_detailed_report(user_input, story_data, all_results, series_dir, merge_instructions)
        
        # 统计成功视频数
        successful_videos = sum(1 for r in all_results if r.video_result.status == "success")
        
        return GenerationResult(
            status="completed",
            successful_videos=successful_videos,
            total_segments=len(all_results),
            series_dir=series_dir,
            merge_instructions=merge_instructions,
            detailed_report=detailed_report,
            all_results=all_results
        )
    
    def _generate_single_segment(self, segment, segment_number, last_frame_path, series_dir):
        """生成单个分段视频"""
        print(f"\n📹 生成第{segment_number}段视频...")
        
        # 生成或使用首图
        if segment_number == 1 or last_frame_path is None or not os.path.exists(last_frame_path):
            print("🖼️ 生成首帧图片...")
            image_result = self.generate_comic_image(segment.visual_prompt, segment.style_used)
            
            if not image_result or not image_result.local_path:
                print("❌ 图片生成失败，使用备用方案")
                image_result = self.create_fallback_image(segment.visual_prompt, segment.style_used)
            
            # 用户确认图片
            compressed_path = compress_image_to_target(image_result.local_path)
            if not display_first_image(compressed_path, image_result.local_path, {
                "segment_number": segment_number,
                "title": segment.title,
                "visual_prompt": segment.visual_prompt
            }):
                print("❌ 用户取消了图片")
                return None
            
            image_to_use = compressed_path
        else:
            print("🔄 使用上一段的尾帧作为首图")
            image_to_use = last_frame_path
        
        # 部署图片到Nginx
        print("🌐 部署图片到服务器...")
        try:
            deploy_result = deploy_to_nginx(image_to_use, segment.title)
            image_url = deploy_result["public_url"]
        except Exception as e:
            print(f"❌ 图片部署失败: {e}")
            return None
        
        # 生成视频
        print("🎥 生成视频...")
        output_name = f"part_{segment_number:02d}_{segment.title.replace(' ', '_')}"
        video_result = self.generate_video_from_image(image_url, segment.video_prompt, output_name)
        
        # 移动视频到系列目录
        if video_result.status == "success" and video_result.local_path:
            new_video_path = os.path.join(
                series_dir, 
                f"part_{segment_number:02d}_{os.path.basename(video_result.local_path)}"
            )
            
            try:
                shutil.move(video_result.local_path, new_video_path)
                video_result.series_path = new_video_path
                video_result.video_info = get_video_info(new_video_path)
                print(f"✅ 视频已保存: {new_video_path}")
            except Exception as e:
                print(f"⚠️ 移动视频失败: {e}")
                video_result.series_path = video_result.local_path
        
        # 提取尾帧（如果不是最后一段）
        last_frame_path = None
        if segment_number < 3 and video_result.status == "success" and video_result.series_path:
            print("🎞️ 提取尾帧...")
            frame_name = f"last_frame_part{segment_number:02d}.jpg"
            frame_path = os.path.join(series_dir, frame_name)
            
            try:
                extracted_frame = extract_last_frame(video_result.series_path, frame_path)
                if extracted_frame:
                    last_frame_path = extracted_frame
                    print(f"✅ 尾帧已保存: {frame_path}")
            except Exception as e:
                print(f"⚠️ 尾帧提取失败: {e}")
        
        return SegmentResult(
            segment_number=segment_number,
            title=segment.title,
            golden_hook=segment.golden_hook,
            visual_prompt=segment.visual_prompt,
            video_prompt=segment.video_prompt,
            image_url=image_url,
            video_result=video_result,
            last_frame_path=last_frame_path
        )
    
    def generate_comic_image(self, visual_prompt, style_name):
        """生成漫画图片 - 基于原脚本重构"""
        print(f"🎨 生成{style_name}风格图片...")
        
        style_config = COMIC_STYLES.get(style_name, COMIC_STYLES["cinematic"])
        
        # 根据风格调整提示词
        if style_name == "电影感":
            full_prompt = f"{visual_prompt}，电影画面，电影感，电影摄影，电影级画质，专业电影镜头，宽银幕构图，无文字，纯画面"
        elif "摄影" in style_name:
            full_prompt = f"{visual_prompt}，专业摄影，写实风格，照片级真实感，自然光影，摄影作品，无文字，纯画面"
        elif "漫画" in style_name:
            full_prompt = f"{visual_prompt}，漫画风格，漫画质感，日本漫画，无文字，纯画面，无对话框"
        else:
            full_prompt = f"{visual_prompt}，高质量视觉，细节丰富，4K分辨率，无文字，纯画面"
        
        width, height = map(int, VIDEO_CONFIG["image_size"].split('x'))
        
        payload = {
            "model": VOLC_CONFIG["text_to_image_model"],
            "prompt": full_prompt,
            "size": VIDEO_CONFIG["image_size"],
            "n": 1,
            "response_format": "b64_json",
            "watermark": False
        }
        
        # 负面提示词
        if style_name == "电影感":
            payload["negative_prompt"] = "文字，字幕，对话框，漫画，卡通，动画，低质量，模糊，业余，手机拍摄，水印"
        elif "摄影" in style_name:
            payload["negative_prompt"] = "文字，字幕，对话框，绘画，漫画，动画，卡通，艺术滤镜，低质量，模糊"
        else:
            payload["negative_prompt"] = "文字，字幕，对话框，低质量，模糊，变形，畸形，水印"
        
        try:
            result = call_volc_api(payload, "text_to_image")
            
            if "data" in result and len(result["data"]) > 0:
                image_b64 = result["data"][0]["b64_json"]
                image_bytes = base64.b64decode(image_b64)
                
                image = Image.open(io.BytesIO(image_bytes))
                
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # 图像增强
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.15)
                
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.3)
                
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(1.1)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                local_filename = f"comic_frame_{timestamp}.png"
                local_path = os.path.join(".", local_filename)
                
                image.save(local_path, "PNG", optimize=True, quality=95)
                
                file_size_kb = os.path.getsize(local_path) / 1024
                
                print(f"✅ 图片生成成功: {file_size_kb:.1f}KB")
                
                return ImageResult(
                    image=image,
                    local_path=local_path,
                    prompt_used=full_prompt,
                    size=image.size,
                    file_size_kb=file_size_kb,
                    style=style_name
                )
            else:
                raise Exception("API响应中没有图片数据")
                
        except Exception as e:
            print(f"❌ 图片生成失败: {e}")
            return self.create_fallback_image(visual_prompt, style_name)
    
    def create_fallback_image(self, prompt, style_name="电影感"):
        """创建备用图片 - 基于原脚本重构"""
        print("⚠️ 创建备用图片...")
        
        width, height = map(int, VIDEO_CONFIG["image_size"].split('x'))
        
        # 根据风格创建不同的背景
        if style_name == "电影感":
            image = Image.new('RGB', (width, height), color=(20, 20, 30))
            draw = ImageDraw.Draw(image)
            
            for y in range(height):
                color_value = int(20 + (y / height) * 30)
                r = color_value
                g = color_value
                b = color_value + 20
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        elif "摄影" in style_name:
            image = Image.new('RGB', (width, height), color=(50, 50, 50))
            draw = ImageDraw.Draw(image)
            
            for y in range(height):
                color_value = int(40 + (y / height) * 40)
                draw.line([(0, y), (width, y)], fill=(color_value, color_value, color_value))
        
        elif "漫画" in style_name:
            image = Image.new('RGB', (width, height), color=(240, 240, 250))
            draw = ImageDraw.Draw(image)
            
            for y in range(height):
                color_value = int(230 + (y / height) * 20)
                draw.line([(0, y), (width, y)], fill=(color_value, color_value, 255))
        
        else:
            image = Image.new('RGB', (width, height), color=(40, 40, 60))
            draw = ImageDraw.Draw(image)
            
            for y in range(height):
                color_value = int(40 + (y / height) * 20)
                draw.line([(0, y), (width, y)], fill=(color_value, color_value, color_value + 20))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fallback_{timestamp}.png"
        local_path = os.path.join(".", filename)
        image.save(local_path, "PNG", quality=90)
        
        return ImageResult(
            image=image,
            local_path=local_path,
            prompt_used=prompt,
            size=(width, height),
            is_fallback=True,
            file_size_kb=os.path.getsize(local_path) / 1024,
            style=style_name
        )
    
    def generate_video_from_image(self, image_url, prompt_text, output_name):
        """从图片生成视频 - 基于原脚本重构"""
        print(f"🎬 生成视频: {output_name}")
        
        video_prompt = f"{prompt_text} --ratio {VIDEO_CONFIG['aspect_ratio']} --dur {VIDEO_CONFIG['video_duration']}"
        
        payload = {
            "model": VOLC_CONFIG["video_model"],
            "content": [
                {
                    "type": "text",
                    "text": video_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
        
        try:
            submit_result = call_volc_api(payload, "video_generate", "POST")
            
            task_id = None
            if "task_id" in submit_result:
                task_id = submit_result["task_id"]
            elif "id" in submit_result:
                task_id = submit_result["id"]
            elif "data" in submit_result and "task_id" in submit_result["data"]:
                task_id = submit_result["data"]["task_id"]
            
            if not task_id:
                return VideoResult(status="failed", reason="无法获取任务ID")
            
            print(f"✅ 任务提交成功: {task_id}")
            
            # 轮询任务状态
            video_url = poll_video_task(task_id)
            
            if video_url:
                video_path = download_video(video_url, output_name)
                video_info = get_video_info(video_path) if video_path else {}
                
                return VideoResult(
                    task_id=task_id,
                    video_url=video_url,
                    local_path=video_path,
                    status="success",
                    video_info=video_info
                )
            else:
                return VideoResult(
                    task_id=task_id,
                    status="failed",
                    reason="视频生成超时或失败"
                )
                
        except Exception as e:
            print(f"❌ 视频生成失败: {e}")
            return VideoResult(status="failed", reason=str(e))
    
    def _generate_merge_instructions(self, all_results, series_dir, story_data):
        """生成合并说明文件"""
        instructions_path = os.path.join(series_dir, "merge_instructions.txt")
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write("🎬 三连视频合并说明\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"故事标题: {story_data.overall_title}\n")
            f.write(f"剧情反转: {story_data.plot_twist}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"视频数量: {len(all_results)}个 (每个10秒)\n")
            f.write(f"总时长: {len(all_results) * VIDEO_CONFIG['video_duration']}秒\n")
            f.write(f"画面要求: 无文字纯画面\n")
            f.write(f"目录路径: {series_dir}\n\n")
            
            f.write("📁 视频文件列表:\n")
            f.write("-"*40 + "\n")
            
            for i, result in enumerate(all_results, 1):
                video_path = result.video_result.series_path or result.video_result.local_path
                if video_path and os.path.exists(video_path):
                    size_mb = os.path.getsize(video_path) / (1024 * 1024)
                    f.write(f"{i}. {os.path.basename(video_path)} ({size_mb:.1f} MB)\n")
                else:
                    f.write(f"{i}. part_{i:02d}_*.mp4 (文件未找到)\n")
            
            f.write("\n🎯 黄金钩子列表:\n")
            f.write("-"*40 + "\n")
            for i, result in enumerate(all_results, 1):
                f.write(f"第{i}段 (0-3秒): \"{result.golden_hook}\"\n")
            
            f.write("\n🎬 合并顺序:\n")
            f.write("-"*40 + "\n")
            f.write("1. 打开剪映（或其他视频编辑软件）\n")
            f.write("2. 导入视频，按以下顺序排列:\n")
            for i in range(1, len(all_results) + 1):
                f.write(f"   ├── part_{i:02d}_*.mp4\n")
            f.write("   └── (按顺序排列)\n\n")
            
            f.write("💡 编辑建议:\n")
            f.write("-"*40 + "\n")
            f.write("• 每个视频前3秒为黄金钩子时段\n")
            f.write("• 视频天然连续，无需额外调整\n")
            f.write("• 所有画面均为无文字纯画面\n")
            f.write("• 手动添加字幕和音效增强效果\n")
            f.write("• 在最后揭示剧情反转\n\n")
            
            f.write("🔧 技术说明:\n")
            f.write("-"*40 + "\n")
            f.write(f"• 图片尺寸: {VIDEO_CONFIG['image_size']}\n")
            f.write(f"• 视频时长: {VIDEO_CONFIG['video_duration']}秒/段\n")
            f.write(f"• 画面比例: {VIDEO_CONFIG['aspect_ratio']}\n")
            f.write("• 尾帧衔接: 自动处理\n")
            f.write("• 无字画面: 严格保证\n")
        
        print(f"✅ 合并说明已保存: {instructions_path}")
        return instructions_path
    
    def _generate_detailed_report(self, user_input, story_data, all_results, series_dir, merge_instructions):
        """生成详细报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(series_dir, f"production_report_{timestamp}.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("🎬 视频生成详细报告\n")
            f.write("="*70 + "\n\n")
            
            f.write("📋 基本信息\n")
            f.write("-"*40 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"故事主题: {user_input.theme}\n")
            f.write(f"总体标题: {story_data.overall_title}\n")
            f.write(f"剧情反转: {story_data.plot_twist}\n")
            f.write(f"画面要求: 无文字纯画面\n")
            f.write(f"系列目录: {series_dir}\n\n")
            
            f.write("📊 生成统计\n")
            f.write("-"*40 + "\n")
            successful_videos = sum(1 for r in all_results if r.video_result.status == "success")
            total_videos = len(all_results)
            f.write(f"计划视频: {total_videos}个\n")
            f.write(f"成功生成: {successful_videos}个\n")
            if total_videos > 0:
                f.write(f"成功率: {successful_videos/total_videos*100:.1f}%\n")
            else:
                f.write(f"成功率: 0.0%\n")
            f.write(f"总时长: {successful_videos * VIDEO_CONFIG['video_duration']}秒\n\n")
            
            f.write("🎨 风格信息\n")
            f.write("-"*40 + "\n")
            if all_results:
                style_name = all_results[0].video_prompt
                f.write(f"视觉风格: {user_input.style}\n")
                f.write(f"画面比例: {VIDEO_CONFIG['aspect_ratio']}\n")
                f.write(f"每段时长: {VIDEO_CONFIG['video_duration']}秒\n\n")
            
            f.write("📝 分段详情\n")
            f.write("="*70 + "\n")
            
            for i, result in enumerate(all_results, 1):
                f.write(f"\n第{i}段: {result.title}\n")
                f.write("-"*40 + "\n")
                
                f.write(f"黄金钩子: {result.golden_hook}\n")
                f.write(f"视觉提示: {result.visual_prompt[:100]}...\n")
                f.write(f"视频引导: {result.video_prompt[:100]}...\n")
                
                video_result = result.video_result
                f.write(f"生成状态: {'✅ 成功' if video_result.status == 'success' else '❌ 失败'}\n")
                
                if video_result.status == "success":
                    if video_result.video_info:
                        info = video_result.video_info
                        if "file_size_mb" in info:
                            f.write(f"文件大小: {info['file_size_mb']} MB\n")
                        if "duration" in info:
                            f.write(f"视频时长: {info['duration']:.1f}秒\n")
                    f.write(f"文件路径: {video_result.series_path or video_result.local_path}\n")
                else:
                    f.write(f"失败原因: {video_result.reason}\n")
                
                f.write(f"图片URL: {result.image_url}\n\n")
            
            f.write("💡 使用说明\n")
            f.write("="*70 + "\n")
            f.write("重要提示: 所有生成的视频均为无文字纯画面\n")
            f.write("字幕、标题等文字元素需后期手动添加\n\n")
            
            f.write("编辑步骤:\n")
            f.write("1. 查看合并说明: {merge_instructions}\n")
            f.write("2. 使用剪映按顺序导入视频文件\n")
            f.write("3. 在0-3秒位置手动添加黄金钩子字幕\n")
            f.write("4. 添加转场效果、背景音乐和音效\n")
            f.write("5. 根据需要添加其他字幕\n")
            f.write("6. 在最后揭示剧情反转\n")
            f.write("7. 导出最终视频\n")
        
        print(f"✅ 详细报告已保存: {report_path}")
        return report_path
        
    def _cleanup_and_report(self, result, user_input):
        """清理和生成总结报告"""
        print("\n" + "="*70)
        print("🧹 清理和总结")
        print("="*70)
        
        # 清理临时文件
        cleanup_temp_files()
        
        # 输出总结
        if result.status == "completed":
            print(f"🎉 视频生成完成！")
            print(f"📊 统计信息:")
            print(f"   • 成功视频: {result.successful_videos}/{result.total_segments}")
            print(f"   • 总时长: {result.successful_videos * VIDEO_CONFIG['video_duration']}秒")
            print(f"   • 保存目录: {result.series_dir}")
            print(f"   • 合并说明: {result.merge_instructions}")
            print(f"   • 详细报告: {result.detailed_report}")
            
            print(f"\n💡 重要提示:")
            print(f"   • 所有视频均为无文字纯画面")
            print(f"   • 字幕需要后期手动添加")
            print(f"   • 请查看合并说明进行编辑")
            
        elif result.status == "cancelled":
            print("❌ 用户取消了生成")
        else:
            print(f"❌ 生成失败: {result.reason}")
        
        return result