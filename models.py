#!/usr/bin/env python3
"""
数据模型定义
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class StorySegment:
    """故事分段数据模型"""
    segment_number: int
    title: str
    golden_hook: str
    visual_prompt: str
    video_prompt: str
    narration: List[str]
    style_used: str
    aspect_ratio: str
    keywords: List[str]

@dataclass
class StoryData:
    """完整故事数据模型"""
    overall_title: str
    plot_twist: str
    segments: List[StorySegment]

@dataclass
class StoryInput:
    """用户输入数据模型"""
    theme: str
    summary: str
    characters: Optional[str] = None
    style: str = "cinematic"
    output_name: Optional[str] = None

@dataclass
class VideoResult:
    """视频生成结果模型"""
    task_id: Optional[str] = None
    video_url: Optional[str] = None
    local_path: Optional[str] = None
    series_path: Optional[str] = None
    status: str = "pending"
    reason: Optional[str] = None
    video_info: Optional[Dict] = None

@dataclass
class SegmentResult:
    """分段生成结果模型"""
    segment_number: int
    title: str
    golden_hook: str
    visual_prompt: str
    video_prompt: str
    image_url: str
    video_result: VideoResult
    last_frame_path: Optional[str] = None

@dataclass
class ImageResult:
    """图片生成结果模型"""
    image: Any = None
    local_path: str = ""
    prompt_used: str = ""
    size: tuple = (1920, 1920)
    file_size_kb: float = 0
    style: str = ""
    is_fallback: bool = False

@dataclass
class GenerationResult:
    """完整生成结果模型"""
    status: str = "pending"
    successful_videos: int = 0
    total_segments: int = 0
    series_dir: str = ""
    merge_instructions: str = ""
    detailed_report: str = ""
    all_results: List[SegmentResult] = None
    reason: Optional[str] = None
    
    def __post_init__(self):
        if self.all_results is None:
            self.all_results = []