#!/usr/bin/env python3
"""
配置和常量定义
"""

# 火山引擎API配置
VOLC_CONFIG = {
    "api_key": "", # 火山引擎API密钥
    "chat_api_base": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "text_to_image_api_base": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    "video_generate_api_base": "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
    "task_info_api_base": "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
    "chat_model": "doubao-seed-1-6-251015",
    "text_to_image_model": "doubao-seedream-4-5-251128",
    "video_model": "doubao-seedance-1-5-pro-251215"
}

# Nginx服务器配置
NGINX_CONFIG = {
    "local_image_dir": "/var/www/html/comic_frames",
    "server_url": "http://", # Nginx服务器IP
    "sub_path": "comic_frames"
}

# 视频生成参数
VIDEO_CONFIG = {
    "output_dir": "./generated_videos",
    "image_size": "1920x1920",
    "video_duration": 10,
    "video_count": 3,
    "aspect_ratio": "9:16",
    "max_retries": 3,
    "polling_interval": 5,
    "max_polling_attempts": 120
}

# 风格配置 (电影感为首选)
COMIC_STYLES = {
    "cinematic": {
        "name": "电影感",
        "prompt": "电影画面，宽银幕构图，戏剧性光影，电影级调色，氛围感，故事性，摄影机运动感，专业电影镜头，无文字，纯画面",
        "keywords": ["电影", "戏剧光", "宽屏", "氛围", "故事性", "镜头感", "电影摄影", "无字"]
    },
    "realistic_photo": {
        "name": "写实摄影",
        "prompt": "专业摄影，写实风格，超高清画质，真实细节，自然光影，照片级真实感，无文字，纯摄影画面",
        "keywords": ["摄影", "写实", "高清", "自然光", "细节", "无字"]
    },
    "shonen": {
        "name": "少年漫画",
        "prompt": "日本少年漫画风格，动感十足，热血氛围，强烈对比，速度线效果，无文字，纯漫画画面",
        "keywords": ["热血", "战斗", "冒险", "友情", "成长", "漫画", "无字"]
    },
    "shoujo": {
        "name": "少女漫画", 
        "prompt": "日本少女漫画风格，大眼睛，华丽细节，浪漫氛围，柔和色彩，花卉元素，无文字，纯画面",
        "keywords": ["浪漫", "爱情", "校园", "少女", "情感", "漫画", "无字"]
    },
    "seinen": {
        "name": "青年漫画",
        "prompt": "日本青年漫画风格，写实画风，成熟主题，细腻心理描写，复杂构图，深沉色调，无文字，纯画面",
        "keywords": ["现实", "心理", "社会", "人性", "悬疑", "漫画", "无字"]
    },
    "dark": {
        "name": "暗黑幻想",
        "prompt": "暗黑幻想风格，哥特元素，黑暗氛围，神秘诡异，强烈对比，华丽颓废，无文字，纯画面",
        "keywords": ["黑暗", "恐怖", "哥特", "奇幻", "神秘", "无字"]
    },
    "scifi": {
        "name": "赛博朋克",
        "prompt": "赛博朋克风格，未来都市，霓虹灯光，机械义体，雨夜街道，反乌托邦，无文字，纯画面",
        "keywords": ["科幻", "未来", "机械", "霓虹", "反乌托邦", "无字"]
    },
    "oil_painting": {
        "name": "古典油画",
        "prompt": "古典油画风格，笔触感丰富，厚重质感，古典大师用光，深沉色调，艺术感，无文字，纯画面",
        "keywords": ["油画", "古典", "艺术", "笔触", "质感", "无字"]
    },
    "watercolor": {
        "name": "水彩手绘",
        "prompt": "水彩画风格，透明感，色彩晕染，纸纹质感，柔和过渡，艺术手绘感，无文字，纯画面",
        "keywords": ["水彩", "手绘", "柔和", "晕染", "艺术", "无字"]
    },
    "cyberpunk_city": {
        "name": "赛博朋克都市",
        "prompt": "赛博朋克城市景观，霓虹灯光，雨夜街道，未来建筑，高科技与低生活，氛围感，无文字，纯画面",
        "keywords": ["赛博朋克", "都市", "霓虹", "雨夜", "未来", "无字"]
    },
    "street_photography": {
        "name": "街头摄影",
        "prompt": "街头摄影风格，纪实感，捕捉瞬间，城市生活，人文气息，黑白或色彩，无文字，纯画面",
        "keywords": ["街头", "纪实", "人文", "瞬间", "城市", "无字"]
    },
    "studio_portrait": {
        "name": "影棚人像",
        "prompt": "专业影棚人像摄影，studio lighting，纯净背景，突出人物，专业布光，肖像，无文字，纯画面",
        "keywords": ["人像", "影棚", "肖像", "专业", "布光", "无字"]
    }
}

# 智能体配置
AGENT_CONFIG = {
    "script_doctor": {
        "temperature": 0.8,
        "max_tokens": 2000,
        "enhancement_level": "high"
    },
    "visual_director": {
        "quality_preset": "cinematic",
        "max_variants": 3
    }
}