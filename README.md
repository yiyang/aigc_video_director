# 智能视频导演系统 (AIGC Video Director)

基于火山引擎的多智能体视频生成系统，用于制作专业级三连视频。

## 核心特性

- 多智能体协作架构，包括剧本创作、视觉设计、节奏规划和质量检测
- 专业三连视频制作：3个10秒连续视频，尾帧自动衔接
- 支持12种专业视觉风格（电影感、写实摄影、漫画风格等）
- 纯视觉叙事，无任何文字元素

## 快速开始

### 环境要求

- Python 3.7+
- FFmpeg（用于视频处理）
- Nginx（可选，用于图片服务器）

### 安装步骤

1. 克隆项目
   ```bash
   git clone https://github.com/yiyang/aigc_video_director.git
   cd aigc_video_director
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 安装系统依赖
   - Ubuntu/Debian：
     ```bash
     sudo apt update
     sudo apt install ffmpeg nginx
     ```
   - macOS：
     ```bash
     brew install ffmpeg nginx
     ```

4. 配置API密钥
   在`config.py`中配置火山引擎API密钥：
   ```python
   VOLC_CONFIG = {
       "api_key": "your-api-key-here",
       # 其他配置
   }
   ```

5. 运行系统
   ```bash
   python main.py
   ```

## 使用方法

### 交互式运行

1. 启动系统后选择运行模式（交互模式、示例模式或快速测试）
2. 输入故事信息（主题、梗概、角色描述、视觉风格）
3. 确认生成设置，系统将自动生成视频

### 代码调用

```python
from video_generator import VideoGenerator
from models import StoryInput

# 初始化生成器
generator = VideoGenerator()

# 准备输入数据
story_input = StoryInput(
    theme="故事主题",
    summary="故事描述",
    characters="角色信息",
    style="cinematic",  # 视觉风格
    output_name="输出名称"
)

# 生成视频系列
result = generator.generate_continuous_series(story_input)
```

## 项目结构

```
aigc_video_director/
├── config.py              # 配置和常量定义
├── models.py              # 数据模型定义
├── utils.py               # 工具函数集合
├── agents.py              # 多智能体系统
├── video_generator.py     # 视频生成核心
├── main.py                # 主程序入口
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
```

## 许可证

本项目采用 Apache2 许可证。