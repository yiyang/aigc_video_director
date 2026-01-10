# 智能视频导演系统 (AIGC Video Director)

基于火山引擎的多智能体视频生成系统，用于制作约30秒短视频成片（分镜拼接自动合成）。


## 核心特性

- **多智能体协作架构**：剧本创作、视觉设计、节奏规划和质量检测智能体协同工作
- **约30秒成片制作**：
  - 单镜时长：最少4秒，仅允许4/5秒混合（避免过短镜头）
  - 总时长：目标30秒±2秒容差，系统自动优化镜头数与时长分配
  - 分镜数量：最多10镜，按节奏风格智能规划
  - 转场策略：按剧情决定是否尾帧续接
  - 自动合成：ffmpeg单段合成，默认保留音轨（可配置去音）
- **12种专业视觉风格**：电影感、写实摄影、漫画风格等
- **纯视觉叙事**：画面严格无任何文字元素（无字幕/对白框/水印/UI）

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
├── config.py                  # 配置和常量定义
├── models.py                  # 数据模型定义
├── utils.py                   # 工具函数集合（含时长规划器、ffmpeg合成）
├── agents.py                  # 多智能体系统
├── video_generator.py         # 视频生成核心（含无字兜底校验）
├── main.py                    # 主程序入口
├── test_duration_planner.py   # 单元测试（时长分布、音频保留、无字输出）
├── requirements.txt           # Python依赖
└── README.md                  # 项目说明
```

## 配置说明

关键配置项（`config.py` 中 `VIDEO_CONFIG`）：

- `target_total_duration`: 目标总时长（秒），默认30
- `target_total_tolerance`: 容差范围（秒），默认±2
- `segment_duration_min`: 单镜最小时长（秒），默认4
- `segment_duration_options`: 允许的单镜时长选项，默认 `[4, 5]`
- `max_segments`: 最多分镜数，默认10
- `force_no_audio`: 合成时是否去音轨，默认 `False`（保留音轨）

## 测试

运行单元测试：
```bash
python test_duration_planner.py
```

测试覆盖：
- 时长规划器：验证4/5秒混合、总时长约30秒、节奏偏好（漫剧/电影）
- 音频保留：验证默认保留音轨、可配置去音（需本机安装ffmpeg/ffprobe）
- 无字输出：验证提示词兜底补齐"无文字/无字幕/纯画面"约束

## 许可证

本项目采用 Apache2 许可证。