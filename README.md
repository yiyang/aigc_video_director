🎬 智能视频导演系统 (AIGC Video Director)

基于火山引擎的多智能体视频生成系统 | 专业级三连视频制作工具

✨ 核心特性

🤖 多智能体协作架构

• 剧本医生: 专业故事创作，三幕剧结构

• 视觉导演: 电影级镜头语言，风格化提示词增强  

• 节奏设计师: 智能节奏规划，音乐节奏匹配

• 质量检测官: 多维度质量评估，自动优化建议

🎯 专业视频制作

• 三连视频: 3个10秒连续视频，尾帧自动衔接

• 黄金钩子: 每个视频前3秒强力吸引观众

• 剧情反转: 专业叙事结构，高潮反转设计

• 无文字画面: 严格保证纯视觉叙事，无任何文字元素

🎨 丰富视觉风格

支持12种专业视觉风格，包括电影感、写实摄影、少年漫画、少女漫画、暗黑幻想、赛博朋克等。

🚀 快速开始

环境要求

• Python 3.7+

• FFmpeg (用于视频处理)

• Nginx (用于图片服务器，可选)

安装步骤

1. 克隆项目
git clone <repository-url>
cd aigc_video_director


2. 安装依赖
pip install -r requirements.txt


3. 安装系统依赖
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg nginx

# macOS
brew install ffmpeg nginx


4. 配置API密钥
在 config.py 中配置您的火山引擎API密钥：
VOLC_CONFIG = {
    "api_key": "your-api-key-here",
    # ... 其他配置
}


5. 运行系统
python main.py


📁 项目结构


aigc_video_director/
├── config.py              # 配置和常量定义
├── models.py              # 数据模型定义
├── utils.py               # 工具函数集合
├── agents.py              # 多智能体系统
├── video_generator.py     # 视频生成核心
├── main.py                # 主程序入口
├── requirements.txt       # Python依赖
└── README.md             # 项目说明


🎮 使用方法

交互式运行

1. 启动系统
python main.py


2. 选择运行模式
   • 🎭 交互模式: 输入自定义故事

   • 🧪 示例模式: 运行预定义示例

   • ⚡ 快速测试: 快速验证功能

3. 输入故事信息
   • 故事主题 (如: "魔法学院的秘密")

   • 故事梗概 (如: "学生在古书中发现失传魔法")

   • 角色描述 (可选)

   • 视觉风格选择

4. 确认生成
   • 系统会显示剧本详情供确认

   • 确认黄金钩子设计

   • 确认首帧图片质量

代码调用

from video_generator import VideoGenerator
from models import StoryInput

# 初始化生成器
generator = VideoGenerator()

# 准备输入数据
story_input = StoryInput(
    theme="你的故事主题",
    summary="详细的故事描述",
    characters="角色信息",
    style="cinematic",  # 视觉风格
    output_name="自定义输出名称"
)

# 生成视频系列
result = generator.generate_continuous_series(story_input)

# 处理结果
if result.status == "completed":
    print(f"生成成功！视频保存在: {result.series_dir}")
    print(f"成功生成: {result.successful_videos}个视频")


⚙️ 配置说明

API配置 (config.py)

VOLC_CONFIG = {
    "api_key": "your-volc-engine-api-key",
    "chat_api_base": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "text_to_image_api_base": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    "video_generate_api_base": "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
    "chat_model": "doubao-seed-1-6-250615",
    "text_to_image_model": "doubao-seedream-4-5-251128",
    "video_model": "doubao-seedance-1-5-pro-251215"
}


视频参数配置

VIDEO_CONFIG = {
    "output_dir": "./generated_videos",  # 输出目录
    "image_size": "1920x1920",          # 图片尺寸
    "video_duration": 10,               # 每段视频时长(秒)
    "video_count": 3,                   # 视频段数
    "aspect_ratio": "9:16",             # 画面比例
    "max_retries": 3,                   # 重试次数
}


🎨 视觉风格库

系统内置12种专业视觉风格：

风格名称 特点描述 适用场景

电影感 戏剧性光影，宽银幕构图 剧情片，电影感内容

写实摄影 照片级真实感，自然光影 纪录片，真实场景

少年漫画 热血动感，强烈对比 动作，冒险内容

少女漫画 浪漫柔和，华丽细节 爱情，校园故事

暗黑幻想 哥特元素，神秘氛围 奇幻，恐怖题材

赛博朋克 霓虹灯光，未来科技 科幻，未来世界

古典油画 厚重质感，古典用光 艺术，历史题材

水彩手绘 透明感，色彩晕染 文艺，清新内容

赛博都市 未来建筑，雨夜街道 城市，建筑展示

街头摄影 纪实感，捕捉瞬间 人文，纪实内容

影棚人像 专业布光，纯净背景 人物，肖像拍摄

📊 输出结果

生成的文件结构


generated_videos/你的系列名称/
├── production_script.json     # 完整剧本文件
├── merge_instructions.txt    # 视频合并说明
├── production_report.txt     # 详细生成报告
├── part_01_视频名称.mp4      # 第一段视频
├── part_02_视频名称.mp4      # 第二段视频  
├── part_03_视频名称.mp4      # 第三段视频
├── last_frame_part01.jpg    # 第一段尾帧
└── last_frame_part02.jpg    # 第二段尾帧


视频规格

• 格式: MP4 (H.264)

• 分辨率: 1920x1920 (1:1) 或适配比例

• 时长: 每段10秒，总30秒

• 帧率: 25fps

• 特点: 无文字纯画面，专业级质量

🔧 高级功能

自定义智能体

from agents import BaseAgent

class CustomAgent(BaseAgent):
    def process(self, input_data):
        # 实现你的自定义逻辑
        enhanced_data = self.enhance_content(input_data)
        return enhanced_data


扩展视觉风格

# 在 config.py 中添加新风格
COMIC_STYLES["your_style"] = {
    "name": "你的风格名称",
    "prompt": "风格描述提示词",
    "keywords": ["关键词1", "关键词2"]
}


🐛 故障排除

常见问题

1. API调用失败
   • 检查API密钥是否正确

   • 确认网络连接正常

   • 查看火山引擎服务状态

2. 图片部署失败
   • 检查Nginx服务是否运行

   • 确认目录权限设置正确

   • 验证服务器配置

3. 视频生成超时
   • 增加 max_polling_attempts 参数

   • 检查网络稳定性

   • 联系火山引擎技术支持

4. FFmpeg错误
   • 确认FFmpeg已正确安装

   • 检查系统PATH设置

   • 尝试重新安装FFmpeg

🤝 贡献指南

我们欢迎各种形式的贡献！

开发环境设置

1. Fork 项目仓库
2. 创建特性分支 (git checkout -b feature/AmazingFeature)
3. 提交更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 开启Pull Request

📄 许可证

本项目采用 MIT 许可证。

🙏 致谢

• https://www.volcengine.com/ - 提供强大的AIGC API支持

• https://ffmpeg.org/ - 视频处理工具

• https://python-pillow.org/ - 图像处理库

⭐ 如果这个项目对你有帮助，请给个星星！