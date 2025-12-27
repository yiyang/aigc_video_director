#!/usr/bin/env python3
"""
智能视频导演系统 - 主入口文件
集成多智能体系统
"""

import sys
import subprocess
from datetime import datetime

from config import VOLC_CONFIG, NGINX_CONFIG, VIDEO_CONFIG, COMIC_STYLES
from models import StoryInput
from video_generator import VideoGenerator

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    # 检查必要库
    try:
        import PIL
        import urllib
        import json
        print("✅ 必要库已安装")
    except ImportError as e:
        print(f"❌ 缺少必要库: {e}")
        return False
    
    # 检查FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg已安装")
        else:
            print("⚠️  FFmpeg检查失败，尾帧提取功能可能受限")
    except:
        print("⚠️  FFmpeg未安装，尾帧提取功能将使用备用方案")
    
    return True

def display_welcome():
    """显示欢迎信息"""
    print("\n" + "="*80)
    print("🎬 智能视频导演系统 v4.0")
    print("="*80)
    print("特点:")
    print("  • 🤖 多智能体协作：剧本医生 + 视觉导演 + 节奏设计师 + 质量检测官")
    print("  • 🎯 专业三幕剧结构：开场 → 发展 → 高潮反转")
    print("  • 🎨 多种视觉风格：电影感、漫画、摄影等12种风格")
    print("  • 📹 连续视频生成：3个10秒视频，尾帧自动衔接")
    print("  • 🚫 无文字纯画面：所有画面严格保证无任何文字")
    print("  • 👤 智能交互：用户确认环节确保质量")
    print("  • 📊 质量评估：自动评分和改进建议")
    print("="*80)

def display_system_info():
    """显示系统信息"""
    print(f"\n📋 系统配置:")
    print(f"  服务器IP: {NGINX_CONFIG['server_url']}")
    print(f"  图片目录: {NGINX_CONFIG['local_image_dir']}")
    print(f"  输出目录: {VIDEO_CONFIG['output_dir']}")
    print(f"  图片尺寸: {VIDEO_CONFIG['image_size']}")
    print(f"  视频时长: {VIDEO_CONFIG['video_duration']}秒/段")
    print(f"  视频数量: {VIDEO_CONFIG['video_count']}个")
    print(f"  总时长: {VIDEO_CONFIG['video_duration'] * VIDEO_CONFIG['video_count']}秒")
    print(f"  画面要求: 无文字纯画面")
    print(f"  API模型: {VOLC_CONFIG['video_model']}")

def display_styles():
    """显示可用风格"""
    print(f"\n🎨 可用视觉风格 ({len(COMIC_STYLES)}种):")
    for i, (key, style) in enumerate(COMIC_STYLES.items(), 1):
        print(f"  {i:2d}. {style['name']} - {style['prompt']}")

def run_interactive_mode():
    """交互式运行模式"""
    print("\n" + "="*70)
    print("🎭 交互模式 - 创建您的视频故事")
    print("="*70)
    
    # 获取用户输入
    print("\n📖 请输入故事信息:")
    
    theme = input("故事主题 (例如：魔法学院的秘密): ").strip()
    if not theme:
        print("❌ 主题不能为空")
        return None
    
    summary = input("故事梗概 (例如：学生在古书中发现失传魔法): ").strip()
    if not summary:
        print("❌ 梗概不能为空")
        return None
    
    characters = input("角色描述 (可选，直接回车跳过): ").strip()
    
    # 选择风格
    print("\n🎨 选择视觉风格:")
    display_styles()
    
    style_keys = list(COMIC_STYLES.keys())
    try:
        choice = input(f"选择风格 (1-{len(style_keys)}，默认1): ").strip()
        if choice and choice.isdigit():
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(style_keys):
                selected_style = style_keys[choice_idx]
            else:
                selected_style = "cinematic"
        else:
            selected_style = "cinematic"
    except:
        selected_style = "cinematic"
    
    output_name = input("\n📁 输出系列名称 (可选，默认自动生成): ").strip()
    
    # 创建输入对象
    story_input = StoryInput(
        theme=theme,
        summary=summary,
        characters=characters if characters else None,
        style=selected_style,
        output_name=output_name
    )
    
    print(f"\n✅ 输入确认:")
    print(f"  主题: {theme}")
    print(f"  风格: {COMIC_STYLES[selected_style]['name']}")
    print(f"  画面: 无文字纯画面")
    print(f"  时长: 3×10秒 = 30秒")
    
    return story_input

def run_example_mode():
    """示例模式"""
    print("\n" + "="*70)
    print("🧪 示例模式 - 暗黑幻想故事")
    print("="*70)
    
    story_input = StoryInput(
        theme="吸血鬼城堡的诅咒",
        summary="年轻的探险家艾琳在废弃的吸血鬼城堡中发现了一面古老的镜子，镜中映出的不是她的倒影，而是一个沉睡百年的吸血鬼灵魂",
        characters="艾琳（22岁，勇敢的考古学学生），镜中的吸血鬼领主",
        style="dark",
        output_name="vampire_castle_series"
    )
    
    print(f"📖 示例故事:")
    print(f"  主题: {story_input.theme}")
    print(f"  梗概: {story_input.summary}")
    print(f"  风格: {COMIC_STYLES[story_input.style]['name']}")
    print(f"  画面: 无文字纯画面")
    
    return story_input

def run_quick_test():
    """快速测试模式"""
    print("\n" + "="*70)
    print("⚡ 快速测试模式")
    print("="*70)
    
    story_input = StoryInput(
        theme="魔法少女的日常",
        summary="一个普通的女孩在图书馆发现了一本会说话的古书，从此踏上了魔法之旅",
        characters="小樱（15岁，普通中学生），魔法古书",
        style="cinematic",
        output_name="quick_test_series"
    )
    
    print(f"🔧 测试配置:")
    print(f"  主题: {story_input.theme}")
    print(f"  风格: {COMIC_STYLES[story_input.style]['name']}")
    print(f"  视频: 3个10秒视频")
    print(f"  画面: 无文字纯画面")
    
    return story_input

def main():
    """主函数"""
    try:
        # 环境检查
        if not check_environment():
            print("❌ 环境检查失败，请安装必要依赖")
            return
        
        # 显示欢迎信息
        display_welcome()
        display_system_info()
        
        # 选择运行模式
        print("\n🎯 请选择运行模式:")
        print("1. 🎭 交互模式 (输入您的故事)")
        print("2. 🧪 示例模式 (运行预定义示例)") 
        print("3. ⚡ 快速测试 (快速验证功能)")
        print("4. 🔧 环境检查")
        print("5. 🚪 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        story_input = None
        
        if choice == "1":
            story_input = run_interactive_mode()
        elif choice == "2":
            story_input = run_example_mode()
        elif choice == "3":
            story_input = run_quick_test()
        elif choice == "4":
            print("\n🔧 环境检查完成")
            return
        elif choice == "5":
            print("👋 再见！")
            return
        else:
            print("❌ 无效选择")
            return
        
        if not story_input:
            return
        
        # 确认开始生成
        print("\n" + "="*70)
        confirm = input("🚀 确认开始生成视频？(y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消了生成")
            return
        
        # 初始化视频生成器
        print("\n" + "="*70)
        print("🚀 初始化视频导演系统...")
        generator = VideoGenerator({
            "volc_config": VOLC_CONFIG,
            "nginx_config": NGINX_CONFIG, 
            "video_config": VIDEO_CONFIG,
            "comic_styles": COMIC_STYLES
        })
        
        # 生成视频系列
        print("🎬 开始生成三连视频系列...")
        result = generator.generate_continuous_series(story_input)
        
        # 显示最终结果
        print("\n" + "="*70)
        if result.status == "completed":
            print("🎉 生成任务完成！")
            print(f"📁 结果目录: {result.series_dir}")
            print(f"📊 成功视频: {result.successful_videos}/{result.total_segments}")
            
            print(f"\n💡 下一步:")
            print(f"  1. 查看目录: {result.series_dir}")
            print(f"  2. 阅读说明: {result.merge_instructions}")
            print(f"  3. 使用剪映编辑视频")
            print(f"  4. 手动添加字幕和音效")
            print(f"  5. 享受您的专业级视频！")
            
        elif result.status == "cancelled":
            print("❌ 用户取消了生成")
        else:
            print(f"❌ 生成失败: {result.reason}")
        
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断了程序")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()