#!/usr/bin/env python3
"""
多智能体系统
"""

import json
from models import StoryData, StoryInput, StorySegment
from config import COMIC_STYLES, VOLC_CONFIG, AGENT_CONFIG
from utils import call_volc_api
import textwrap

class BaseAgent:
    """智能体基类"""
    def __init__(self, config):
        self.config = config
    
    def log(self, message):
        """统一的日志输出"""
        print(f"  🤖 {self.__class__.__name__}: {message}")

class ScriptDoctorAgent(BaseAgent):
    """剧本医生智能体 - 增强故事生成"""
    
    def enhance_story_prompts(self, story_input):
        """增强版故事提示词生成"""
        self.log("开始增强故事剧本生成...")
        
        theme = story_input.theme
        summary = story_input.summary
        characters = story_input.characters or ""
        style_preference = story_input.style
        
        style_config = COMIC_STYLES.get(style_preference, COMIC_STYLES["cinematic"])
        
        # 增强的提示词设计
        enhanced_prompt = f"""你是一个专业的影视编剧。请为以下故事创作3个连续的10秒短视频，采用专业的三幕剧结构：

【故事主题】{theme}
【详细情节】{summary}
【角色设定】{characters}

【专业要求】
1. 第一幕（0-10秒）：建立冲突，3秒黄金钩子必须吸引眼球
2. 第二幕（10-20秒）：冲突升级，制造悬念转折点  
3. 第三幕（20-30秒）：高潮反转，留下深刻印象

【黄金钩子设计】
- 每个视频前3秒必须有强力钩子
- 使用疑问、震惊、悬念等手法
- 长度控制在15-30字

【视觉要求】
- {style_config['prompt']}
- 绝对无文字纯画面
- 电影级镜头语言


请严格按照以下JSON格式返回结果，确保包含所有必要字段：
{{
  "overall_title": "[视频系列整体标题]",
  "plot_twist": "[剧情反转点描述]",
  "segments": [
    {{
      "segment_number": 1,
      "title": "[第一幕标题]",
      "golden_hook": "[第一幕黄金钩子，15-30字]",
      "visual_prompt": "[第一幕视觉提示词]",
      "video_prompt": "[第一幕视频制作提示词]",
      "style_used": "[使用的风格名称]",
      "aspect_ratio": "9:16"
    }},
    {{
      "segment_number": 2,
      "title": "[第二幕标题]",
      "golden_hook": "[第二幕黄金钩子，15-30字]",
      "visual_prompt": "[第二幕视觉提示词]",
      "video_prompt": "[第二幕视频制作提示词]",
      "style_used": "[使用的风格名称]",
      "aspect_ratio": "9:16"
    }},
    {{
      "segment_number": 3,
      "title": "[第三幕标题]",
      "golden_hook": "[第三幕黄金钩子，15-30字]",
      "visual_prompt": "[第三幕视觉提示词]",
      "video_prompt": "[第三幕视频制作提示词]",
      "style_used": "[使用的风格名称]",
      "aspect_ratio": "9:16"
    }}
  ]
}}

注意：
1. 必须包含所有字段，不要添加额外字段
2. 确保JSON格式严格正确，不包含任何无关文本
3. segments数组必须包含3个元素，对应三幕剧结构"""

        payload = {
            "model": VOLC_CONFIG["chat_model"],
            "messages": [{"role": "user", "content": enhanced_prompt}],
            "temperature": AGENT_CONFIG["script_doctor"]["temperature"],
            "max_tokens": AGENT_CONFIG["script_doctor"]["max_tokens"]
        }
        
        try:
            result = call_volc_api(payload, "chat")
            content = result['choices'][0]['message']['content'].strip()
            
            # 提取JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                story_data = json.loads(json_str)
                self.log("故事剧本增强完成！")
                return self._convert_to_story_data(story_data)
            else:
                self.log("JSON解析失败，使用备用方案")
                return self._create_fallback_story(story_input, style_config)
                
        except Exception as e:
            self.log(f"剧本生成失败: {e}")
            return self._create_fallback_story(story_input, style_config)
    
    def _convert_to_story_data(self, raw_data):
        """将原始数据转换为StoryData模型"""
        segments = []
        
        # 处理大模型返回的segments
        raw_segments = raw_data.get('segments', [])
        self.log(f"原始数据中找到{len(raw_segments)}个分段")
        
        for seg_idx, seg in enumerate(raw_segments):
            if not isinstance(seg, dict):
                self.log(f"⚠️  分段{seg_idx+1}不是字典类型，跳过")
                continue
            
            # 检查必要字段
            has_required_fields = all(key in seg for key in ['golden_hook', 'visual_prompt', 'video_prompt'])
            if not has_required_fields:
                self.log(f"⚠️  分段{seg_idx+1}缺少必要字段，跳过")
                continue
            
            # 创建StorySegment
            segment = StorySegment(
                segment_number=seg.get('segment_number', seg_idx + 1),
                title=seg.get('title', f"第{seg_idx+1}段"),
                golden_hook=seg.get('golden_hook', ''),
                visual_prompt=seg.get('visual_prompt', ''),
                video_prompt=seg.get('video_prompt', ''),
                narration=seg.get('narration', ["注意看！", "事情不简单", "继续往下看"]),
                style_used=seg.get('style_used', 'cinematic'),
                aspect_ratio=seg.get('aspect_ratio', '9:16'),
                keywords=seg.get('keywords', [])
            )
            segments.append(segment)
        
        # 确保至少有一个有效分段
        if not segments:
            self.log("⚠️  没有获取到有效分段，创建默认分段")
            # 创建3个默认分段，确保有完整的三幕结构
            for i in range(3):
                segment_title = ["开场", "发展", "高潮"][i]
                segment = StorySegment(
                    segment_number=i + 1,
                    title=f"默认{segment_title}",
                    golden_hook=["眼前的一幕让人震惊！", "危险正在悄悄靠近！", "最后的真相竟然是这样！"][i],
                    visual_prompt=f"{segment_title}画面，建立场景和氛围，9:16竖屏构图，无文字纯画面",
                    video_prompt=f"0-3秒展示震撼的{segment_title}画面，3-7秒情节发展，7-10秒悬念铺垫，纯画面无文字",
                    narration=["注意看！", "事情不简单", "继续往下看"],
                    style_used='cinematic',
                    aspect_ratio='9:16',
                    keywords=[segment_title, '震撼']
                )
                segments.append(segment)
        elif len(segments) < 3:
            self.log(f"⚠️  只有{len(segments)}个有效分段，补充到3个")
            # 补充到3个分段
            for i in range(len(segments), 3):
                segment_title = ["开场", "发展", "高潮"][i]
                segment = StorySegment(
                    segment_number=i + 1,
                    title=f"补充{segment_title}",
                    golden_hook=["眼前的一幕让人震惊！", "危险正在悄悄靠近！", "最后的真相竟然是这样！"][i],
                    visual_prompt=f"{segment_title}画面，建立场景和氛围，9:16竖屏构图，无文字纯画面",
                    video_prompt=f"0-3秒展示震撼的{segment_title}画面，3-7秒情节发展，7-10秒悬念铺垫，纯画面无文字",
                    narration=["注意看！", "事情不简单", "继续往下看"],
                    style_used='cinematic',
                    aspect_ratio='9:16',
                    keywords=[segment_title, '震撼']
                )
                segments.append(segment)
        
        return StoryData(
            overall_title=raw_data.get('overall_title', '默认视频系列'),
            plot_twist=raw_data.get('plot_twist', '最后的真相完全出乎意料！'),
            segments=segments
        )
    
    def _create_fallback_story(self, story_input, style_config):
        """创建备用故事"""
        self.log("创建备用故事剧本...")
        
        segments = []
        segment_titles = [
            f"{story_input.theme} - 开场",
            f"{story_input.theme} - 发展", 
            f"{story_input.theme} - 高潮"
        ]
        
        golden_hooks = [
            f"眼前的一幕让所有人惊呆了！{story_input.summary[:20]}...",
            f"危险正在悄悄靠近，你还不知道！",
            f"最后的真相竟然是这样..."
        ]
        
        for i in range(3):
            visual_prompt = f"{style_config['prompt']}，{story_input.summary}，"
            video_prompt = f"0-3秒展示黄金钩子: {golden_hooks[i]}，3-7秒情节发展，7-10秒悬念铺垫，纯画面无文字"
            
            if i == 0:
                visual_prompt += f"开场画面，建立场景和氛围，包含黄金钩子元素，9:16竖屏构图，无文字纯画面"
            elif i == 1:
                visual_prompt += f"情节发展画面，动作进行中，保持紧张感，9:16竖屏构图，无文字纯画面"
            else:
                visual_prompt += f"高潮转折画面，紧张时刻，为反转做准备，9:16竖屏构图，无文字纯画面"
            
            segments.append(StorySegment(
                segment_number=i + 1,
                title=segment_titles[i],
                golden_hook=golden_hooks[i],
                visual_prompt=visual_prompt,
                video_prompt=video_prompt,
                narration=["注意看！", "事情不简单", "继续往下看"],
                style_used=style_config['name'],
                aspect_ratio="9:16",
                keywords=style_config['keywords'][:2]
            ))
        
        return StoryData(
            overall_title=f"{story_input.theme} - 三连视频",
            plot_twist=f"{story_input.theme}的真相竟然完全出乎意料！",
            segments=segments
        )

class VisualDirectorAgent(BaseAgent):
    """视觉导演智能体 - 增强图像生成"""
    
    def enhance_visual_prompt(self, base_prompt, style_name):
        """增强视觉提示词"""
        self.log(f"增强{style_name}风格的视觉提示词...")
        
        style_enhancements = {
            "电影感": "电影级光影，浅景深效果，35mm胶片质感，戏剧性构图，无文字",
            "写实摄影": "照片级真实感，自然光影，细节丰富，专业摄影，无文字",
            "少年漫画": "动感十足，热血氛围，强烈对比，漫画质感，无文字",
            "少女漫画": "柔和色彩，浪漫氛围，华丽细节，漫画风格，无文字",
            "暗黑幻想": "黑暗氛围，哥特元素，神秘诡异，强烈对比，无文字"
        }
        
        enhancement = style_enhancements.get(style_name, "高质量视觉，细节丰富，无文字")
        enhanced_prompt = f"{base_prompt}，{enhancement}"
        
        self.log(f"提示词增强完成: {len(enhanced_prompt)}字符")
        return enhanced_prompt
    
    def recommend_camera_shots(self, scene_type):
        """推荐镜头语言"""
        shot_recommendations = {
            "开场": ["定场镜头", "缓慢推进", "环境展示"],
            "冲突": ["中景对话", "特写表情", "多角度切换"],
            "高潮": ["快速剪辑", "特写细节", "动态运镜"],
            "结尾": ["缓慢拉远", "意境镜头", "留白处理"]
        }
        
        return shot_recommendations.get(scene_type, ["标准镜头", "平稳运镜"])

class RhythmDesignerAgent(BaseAgent):
    """节奏设计师智能体 - 节奏和音乐匹配"""
    
    def design_rhythm_pattern(self, story_segment):
        """设计节奏模式"""
        self.log(f"为'{story_segment.title}'设计节奏模式...")
        
        # 基于场景类型推荐节奏
        rhythm_patterns = {
            "开场": "缓慢建立，0-3秒强力钩子，3-7秒平稳发展，7-10秒悬念铺垫",
            "发展": "中等节奏，0-3秒新悬念，3-7秒冲突升级，7-10秒推向高潮", 
            "高潮": "快速节奏，0-3秒紧张感，3-7秒爆发，7-10秒反转收尾"
        }
        
        # 根据标题判断场景类型
        scene_type = "发展"  # 默认
        if "开场" in story_segment.title or "开始" in story_segment.title:
            scene_type = "开场"
        elif "高潮" in story_segment.title or "结局" in story_segment.title:
            scene_type = "高潮"
        
        pattern = rhythm_patterns.get(scene_type, "标准节奏")
        self.log(f"节奏模式: {pattern}")
        return pattern
    
    def recommend_music_tempo(self, emotional_tone):
        """推荐音乐节奏"""
        tempo_mapping = {
            "紧张": "120-140BPM，急促节奏，适合动作场景",
            "浪漫": "60-80BPM，柔和旋律，适合情感叙事",
            "史诗": "80-100BPM，宏大配乐，适合壮观场景",
            "神秘": "90-110BPM，悬疑音效，适合推理剧情"
        }
        
        return tempo_mapping.get(emotional_tone, "100BPM，通用节奏")

class QualityInspectorAgent(BaseAgent):
    """质量检测官智能体 - 质量评估和优化"""
    
    def evaluate_story_quality(self, story_data):
        """评估故事质量"""
        self.log("评估故事剧本质量...")
        
        score = 10  # 基础分
        
        # 检查分段数量
        if len(story_data.segments) < 3:
            score -= 2
            self.log("⚠️ 分段数量不足3个")
        
        # 检查黄金钩子质量
        for i, segment in enumerate(story_data.segments):
            hook = segment.golden_hook
            if len(hook) < 10:
                score -= 1
                self.log(f"⚠️ 第{i+1}段钩子过短: {hook}")
            elif len(hook) > 50:
                score -= 0.5
                self.log(f"⚠️ 第{i+1}段钩子过长: {hook[:30]}...")
            
            # 检查钩子吸引力
            if not any(keyword in hook for keyword in ['?', '？', '震惊', '惊呆', '竟然', '秘密', '真相']):
                score -= 0.5
                self.log(f"⚠️ 第{i+1}段钩子缺乏吸引力元素")
        
        # 检查剧情反转
        if not story_data.plot_twist or len(story_data.plot_twist) < 10:
            score -= 1
            self.log("⚠️ 剧情反转描述不足")
        
        # 确保分数在合理范围
        score = max(5, min(10, score))
        
        quality_levels = {
            10: "优秀",
            9: "很好", 
            8: "良好",
            7: "一般",
            6: "需要改进",
            5: "较差"
        }
        
        level = quality_levels.get(int(score), "一般")
        self.log(f"📊 质量评分: {score:.1f}/10 ({level})")
        
        return {
            "score": score,
            "level": level,
            "suggestions": self._generate_suggestions(story_data, score)
        }
    
    def _generate_suggestions(self, story_data, score):
        """生成改进建议"""
        suggestions = []
        
        if score < 8:
            suggestions.append("💡 建议加强黄金钩子的吸引力")
        
        if len(story_data.segments) < 3:
            suggestions.append("💡 建议确保有完整的3段结构")
        
        if not story_data.plot_twist or len(story_data.plot_twist) < 15:
            suggestions.append("💡 建议强化剧情反转的意外性")
        
        return suggestions
    
    def select_best_variant(self, variants):
        """选择最佳变体"""
        self.log(f"从{len(variants)}个变体中选择最佳版本...")
        
        if not variants:
            return None
        
        # 简单的评分选择（实际可以更复杂）
        best_variant = max(variants, key=lambda x: x.get('quality_score', 0))
        self.log(f"✅ 选择最佳变体: 评分{best_variant.get('quality_score', 0)}")
        
        return best_variant

class VideoDirectorAgent:
    """视频导演智能体 - 协调所有智能体"""
    
    def __init__(self, config):
        self.config = config
        self.script_doctor = ScriptDoctorAgent(config)
        self.visual_director = VisualDirectorAgent(config)
        self.rhythm_designer = RhythmDesignerAgent(config)
        self.quality_inspector = QualityInspectorAgent(config)
    
    def create_video_plan(self, user_input):
        """创建完整的视频制作计划"""
        print("🎬 视频导演开始制定制作计划...")
        
        # 1. 剧本创作
        print("\n📝 第一步：剧本创作")
        story_data = self.script_doctor.enhance_story_prompts(user_input)
        
        # 确保至少有一个有效分段
        if not story_data.segments:
            self.log("⚠️  故事数据中没有有效分段，创建备用故事")
            style_config = COMIC_STYLES.get(user_input.style, COMIC_STYLES["cinematic"])
            story_data = self.script_doctor._create_fallback_story(user_input, style_config)
        
        # 2. 质量评估
        print("\n📊 第二步：质量评估")
        quality_report = self.quality_inspector.evaluate_story_quality(story_data)
        
        # 3. 视觉规划
        print("\n🎨 第三步：视觉规划")
        visual_plan = self._create_visual_plan(story_data)
        
        # 4. 节奏设计
        print("\n⏱️ 第四步：节奏设计")
        rhythm_plan = self._create_rhythm_plan(story_data)
        
        return {
            "story_data": story_data,
            "quality_report": quality_report,
            "visual_plan": visual_plan,
            "rhythm_plan": rhythm_plan,
            "director_notes": self._generate_director_notes(story_data, quality_report)
        }
    
    def _create_visual_plan(self, story_data):
        """创建视觉规划"""
        visual_plan = {}
        
        for segment in story_data.segments:
            enhanced_prompt = self.visual_director.enhance_visual_prompt(
                segment.visual_prompt, segment.style_used
            )
            camera_shots = self.visual_director.recommend_camera_shots(
                self._classify_scene_type(segment.title)
            )
            
            visual_plan[segment.segment_number] = {
                "enhanced_prompt": enhanced_prompt,
                "camera_shots": camera_shots,
                "style": segment.style_used
            }
        
        return visual_plan
    
    def _create_rhythm_plan(self, story_data):
        """创建节奏规划"""
        rhythm_plan = {}
        
        for segment in story_data.segments:
            rhythm_pattern = self.rhythm_designer.design_rhythm_pattern(segment)
            music_tempo = self.rhythm_designer.recommend_music_tempo(
                self._classify_emotional_tone(segment.title)
            )
            
            rhythm_plan[segment.segment_number] = {
                "rhythm_pattern": rhythm_pattern,
                "music_tempo": music_tempo
            }
        
        return rhythm_plan
    
    def _classify_scene_type(self, title):
        """根据标题分类场景类型"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['开场', '开始', '引入', '建立']):
            return "开场"
        elif any(word in title_lower for word in ['高潮', '结局', '结尾', '解决']):
            return "高潮"
        else:
            return "发展"
    
    def _classify_emotional_tone(self, title):
        """根据标题分类情感基调"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['紧张', '危险', '冲突', '战斗']):
            return "紧张"
        elif any(word in title_lower for word in ['浪漫', '爱情', '温馨', '感人']):
            return "浪漫"
        elif any(word in title_lower for word in ['神秘', '悬疑', '秘密', '真相']):
            return "神秘"
        else:
            return "史诗"
    
    def _generate_director_notes(self, story_data, quality_report):
        """生成导演指导说明"""
        notes = [
            f"🎯 总体指导: {story_data.overall_title}",
            f"📊 质量评分: {quality_report['score']:.1f}/10 ({quality_report['level']})",
            "📝 分段指导:"
        ]
        
        for segment in story_data.segments:
            notes.append(f"  - 第{segment.segment_number}段: {segment.title}")
            notes.append(f"    黄金钩子: {segment.golden_hook}")
        
        notes.append(f"🔄 剧情反转: {story_data.plot_twist}")
        
        if quality_report['suggestions']:
            notes.append("💡 改进建议:")
            for suggestion in quality_report['suggestions']:
                notes.append(f"  - {suggestion}")
        
        return notes