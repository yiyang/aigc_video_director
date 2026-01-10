#!/usr/bin/env python3
"""
多智能体系统
"""

import json
from models import StoryData, StoryInput, StorySegment
from config import COMIC_STYLES, VOLC_CONFIG, AGENT_CONFIG, VIDEO_CONFIG

from utils import call_volc_api, plan_segment_durations

import textwrap

class BaseAgent:
    """智能体基类"""
    def __init__(self, config):
        self.config = config
    
    def log(self, message):
        """统一的日志输出"""
        print(f"  🤖 {self.__class__.__name__}: {message}")

class ScriptDoctorAgent(BaseAgent):
    """剧本医生智能体 - 将用户粗糙提示词扩写为可执行分镜脚本"""

    def enhance_story_prompts(self, story_input: StoryInput):
        """增强版故事提示词生成（约30秒成片，单镜≥4秒，仅4/5秒混合）"""
        self.log("开始增强故事剧本生成...")

        style_key = getattr(story_input, "style", "cinematic") or "cinematic"
        rhythm_style = getattr(story_input, "rhythm_style", "manju") or "manju"
        user_script_prompt = getattr(story_input, "script_prompt", None)

        theme = getattr(story_input, "theme", "")
        summary = getattr(story_input, "summary", "")
        characters = getattr(story_input, "characters", "") or ""

        style_config = COMIC_STYLES.get(style_key, COMIC_STYLES["cinematic"])

        prefer_more_cuts = (rhythm_style != "movie")
        segment_count, planned_durations, total_duration = plan_segment_durations(
            target_total_sec=VIDEO_CONFIG.get("target_total_duration", 30),
            tolerance_sec=VIDEO_CONFIG.get("target_total_tolerance", 2),
            allowed_durations=VIDEO_CONFIG.get("segment_duration_options", [4, 5]),
            min_duration_sec=VIDEO_CONFIG.get("segment_duration_min", 4),
            max_segments=VIDEO_CONFIG.get("max_segments", VIDEO_CONFIG.get("video_count", 10)),
            prefer_more_cuts=prefer_more_cuts,
        )


        base_story = user_script_prompt.strip() if user_script_prompt else (
            f"主题：{theme}\n梗概：{summary}\n角色：{characters}".strip()
        )

        rhythm_guide = (
            "【节奏风格：漫剧】\n"
            "- 高密度信息：每镜必须有明确动作/表情/关系变化（时长4-5秒）\n"
            "- 分镜感强：多用特写/中景切换，夸张表情与肢体语言\n"
            "- 镜头语言：快速推进、明确运镜（推拉摇移）但不过度晃动\n"
            "- 转场：剧情需要连续时才用 tailframe_continue，其余 hard_cut\n"
        )

        if rhythm_style == "movie":
            rhythm_guide = (
                "【节奏风格：电影】\n"
                "- 连贯叙事：镜头更稳定、运动更克制，信息逐步揭示\n"
                "- 镜头语言：明确景别（远/中/近/特写），光影与调度更讲究\n"
                "- 转场：连续动作/同场景追随可用 tailframe_continue，其余 hard_cut\n"
            )

        strict_no_text_rules = (
            "【硬性约束（必须遵守）】\n"
            "1) 画面中绝对不出现任何文字：字幕/对白框/拟声词/LOGO/水印/UI/招牌/书页文字/屏幕文字等一律禁止\n"
            "2) 仅输出画面描述，不要输出任何解释文字；最终只返回严格JSON\n"
            f"3) 本次分镜数量为{segment_count}镜，总时长约{total_duration}秒（允许合理浮动）\n"
            f"4) 每镜 duration_sec 必须严格等于该镜规划时长：{planned_durations}（只能是4或5，且不得低于4）\n"
            f"5) 风格字段 style_used 必须返回视觉风格 key：\"{style_key}\"（不要返回中文名）\n"
            "6) transition_strategy 只能是：\"tailframe_continue\" 或 \"hard_cut\"\n"
        )


        enhanced_prompt = f"""你是一个专业的短视频分镜编剧。请基于用户提供的粗糙剧本，生成一条总时长约{total_duration}秒的短视频分镜脚本，按{segment_count}个分镜输出（每镜时长见下方规划）。

【用户粗糙剧本】
{base_story}

{rhythm_guide}

【视觉风格参考】
- 视觉风格提示词（仅供参考）：{style_config['prompt']}

{strict_no_text_rules}

【本次时长规划】
- 分镜数量: {segment_count}
- 每镜 duration_sec 依次为: {planned_durations}

请严格按以下JSON格式输出（不要包含任何无关文本，不要用Markdown）：
{{
  "overall_title": "[系列标题]",
  "plot_twist": "[最后的反转/爆点]",
  "segments": [
    {{
      "segment_number": 1,
      "title": "[分镜标题]",
      "golden_hook": "[画面钩子/爆点提示，仅供后期参考，画面里不要出现文字]",
      "visual_prompt": "[用于首帧图片生成的单帧画面描述，强调人物/场景/构图/光影，无字]",
      "video_prompt": "[用于视频生成的动作与运镜描述（动作、表情、景别、运镜、氛围），无字，无配音要求；时长应与 duration_sec 对应]",
      "style_used": "{style_key}",
      "aspect_ratio": "9:16",
      "duration_sec": {planned_durations[0]},
      "transition_strategy": "hard_cut",
      "transition_reason": "[为何用该转场（可简短）]"
    }}
  ]
}}

注意：
- segments 数组必须恰好包含 {segment_count} 个元素（segment_number 依次为 1..{segment_count}）
- 第 i 镜的 duration_sec 必须严格等于上方规划的第 i 个数字（只能4或5，且不得低于4）
- 你可以让某些镜头使用 transition_strategy=tailframe_continue 以便剧情连续（例如同场景连续动作/追随镜头）
- 每个分镜的 visual_prompt/video_prompt 都必须再次强调“无文字纯画面”
"""


        payload = {
            "model": VOLC_CONFIG["chat_model"],
            "messages": [{"role": "user", "content": enhanced_prompt}],
            "temperature": AGENT_CONFIG["script_doctor"]["temperature"],
            "max_tokens": AGENT_CONFIG["script_doctor"]["max_tokens"],
        }

        try:
            result = call_volc_api(payload, "chat")
            content = result["choices"][0]["message"]["content"].strip()

            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                raw = json.loads(json_str)
                self.log("分镜剧本生成完成！")
                return self._convert_to_story_data(
                    raw,
                    desired_count=segment_count,
                    desired_durations=planned_durations,
                    default_style_key=style_key,
                    default_duration=int(VIDEO_CONFIG.get("video_duration", 4)),
                )


            self.log("JSON解析失败，使用备用方案")
            return self._create_fallback_story(
                story_input,
                style_key=style_key,
                style_config=style_config,
                desired_count=segment_count,
                durations=planned_durations,
            )


        except Exception as e:
            self.log(f"剧本生成失败: {e}")
            return self._create_fallback_story(
                story_input,
                style_key=style_key,
                style_config=style_config,
                desired_count=segment_count,
                durations=planned_durations,
            )


    def _normalize_style_key(self, style_used, default_style_key="cinematic"):
        """兼容 style key / 中文名，内部统一返回 key"""
        if not style_used:
            return default_style_key
        if style_used in COMIC_STYLES:
            return style_used
        for k, v in COMIC_STYLES.items():
            if v.get("name") == style_used:
                return k
        return default_style_key

    def _convert_to_story_data(self, raw_data, desired_count=10, desired_durations=None, default_style_key="cinematic", default_duration=4):
        """将原始数据转换为StoryData模型，并保证分镜数量满足 desired_count。

        - 若提供 desired_durations（长度=desired_count），则会强制覆盖每镜 duration_sec
        - 未提供时，会将 duration_sec 归一到 4/5 秒（且不得低于4秒）
        """

        segments = []

        raw_segments = raw_data.get("segments", [])
        self.log(f"原始数据中找到{len(raw_segments)}个分镜")

        # 按 segment_number 排序，缺失则按出现顺序
        def seg_sort_key(s):
            if isinstance(s, dict) and isinstance(s.get("segment_number"), int):
                return s.get("segment_number")
            return 10**9

        if isinstance(raw_segments, list):
            raw_segments_sorted = sorted(raw_segments, key=seg_sort_key)
        else:
            raw_segments_sorted = []

        for seg_idx, seg in enumerate(raw_segments_sorted):
            if not isinstance(seg, dict):
                continue

            if "visual_prompt" not in seg or "video_prompt" not in seg:
                continue

            style_key = self._normalize_style_key(seg.get("style_used"), default_style_key)
            duration_sec = int(seg.get("duration_sec", default_duration) or default_duration)
            # 时长归一：只允许 4/5 秒，且不得低于4秒
            duration_sec = 5 if duration_sec >= 5 else 4
            transition_strategy = seg.get("transition_strategy", "hard_cut")

            if transition_strategy not in ["hard_cut", "tailframe_continue"]:
                transition_strategy = "hard_cut"

            segment = StorySegment(
                segment_number=seg.get("segment_number", seg_idx + 1),
                title=seg.get("title", f"镜头{seg_idx+1:02d}"),
                golden_hook=seg.get("golden_hook", ""),
                visual_prompt=seg.get("visual_prompt", ""),
                video_prompt=seg.get("video_prompt", ""),
                narration=seg.get("narration", []),
                style_used=style_key,
                aspect_ratio=seg.get("aspect_ratio", "9:16"),
                keywords=seg.get("keywords", []),
                duration_sec=duration_sec,
                transition_strategy=transition_strategy,
                transition_reason=seg.get("transition_reason"),
            )
            segments.append(segment)

        # 统一重排为 1..desired_count
        if len(segments) > desired_count:
            segments = segments[:desired_count]

        if len(segments) < desired_count:
            self.log(f"⚠️  有效分镜不足{desired_count}个，补充分镜")
            style_config = COMIC_STYLES.get(default_style_key, COMIC_STYLES["cinematic"])
            for i in range(len(segments), desired_count):
                idx = i + 1
                segments.append(
                    StorySegment(
                        segment_number=idx,
                        title=f"补充分镜{idx:02d}",
                        golden_hook="",
                        visual_prompt=f"{style_config['prompt']}，关键动作瞬间，9:16竖屏构图，绝对无文字，纯画面",
                        video_prompt=f"{default_duration}秒短镜头：明确动作与情绪变化，景别清晰，运镜自然，绝对无文字纯画面",

                        narration=[],
                        style_used=default_style_key,
                        aspect_ratio="9:16",
                        keywords=style_config.get("keywords", [])[:2],
                        duration_sec=default_duration,
                        transition_strategy="hard_cut",
                        transition_reason="补充分镜",
                    )
                )

        for i, seg in enumerate(segments, 1):
            seg.segment_number = i
            if not seg.duration_sec:
                seg.duration_sec = default_duration

        if desired_durations and isinstance(desired_durations, list) and len(desired_durations) == desired_count:
            for i, seg in enumerate(segments, 1):
                try:
                    d = int(desired_durations[i - 1])
                except Exception:
                    d = default_duration
                seg.duration_sec = 5 if d >= 5 else 4


        return StoryData(
            overall_title=raw_data.get("overall_title", "约30秒分镜成片"),

            plot_twist=raw_data.get("plot_twist", ""),
            segments=segments,
        )

    def _create_fallback_story(self, story_input, style_key="cinematic", style_config=None, desired_count=10, durations=None):
        """创建备用故事（保证 desired_count 个分镜）。

        durations: 可选的每镜时长数组（仅允许4/5秒）
        """

        self.log("创建备用分镜脚本...")

        if style_config is None:
            style_config = COMIC_STYLES.get(style_key, COMIC_STYLES["cinematic"])

        base_story = (getattr(story_input, "script_prompt", "") or getattr(story_input, "summary", "") or "").strip()
        if not base_story:
            base_story = getattr(story_input, "theme", "自定义故事")

        segments = []
        for i in range(desired_count):
            idx = i + 1
            transition_strategy = "tailframe_continue" if idx > 1 and idx <= 3 else "hard_cut"

            d = None
            if durations and isinstance(durations, list) and len(durations) >= idx:
                try:
                    d = int(durations[idx - 1])
                except Exception:
                    d = None
            duration_sec = 5 if (d and d >= 5) else 4

            segments.append(
                StorySegment(
                    segment_number=idx,
                    title=f"分镜{idx:02d}",
                    golden_hook="",
                    visual_prompt=f"{style_config['prompt']}，{base_story[:120]}，关键瞬间定格，9:16竖屏构图，绝对无文字纯画面",
                    video_prompt=f"{duration_sec}秒短镜头：推进剧情一小步（动作+表情+环境变化），运镜简洁，绝对无文字纯画面",
                    narration=[],
                    style_used=style_key,
                    aspect_ratio="9:16",
                    keywords=style_config.get("keywords", [])[:2],
                    duration_sec=duration_sec,
                    transition_strategy=transition_strategy,
                    transition_reason="备用脚本默认策略",
                )
            )


        return StoryData(
            overall_title=f"{getattr(story_input, 'theme', '自定义故事')} - 约30秒成片",

            plot_twist="",
            segments=segments,
        )


class VisualDirectorAgent(BaseAgent):
    """视觉导演智能体 - 增强图像生成"""
    
    def enhance_visual_prompt(self, base_prompt, style_key):
        """增强视觉提示词（内部使用 style key）"""
        style_name = COMIC_STYLES.get(style_key, {}).get("name", style_key)
        self.log(f"增强{style_name}风格的视觉提示词...")

        style_enhancements = {
            "cinematic": "电影级光影，浅景深效果，35mm胶片质感，戏剧性构图，绝对无文字",
            "realistic_photo": "照片级真实感，自然光影，细节丰富，专业摄影，绝对无文字",
            "street_photography": "纪实抓拍质感，自然光影，真实细节，绝对无文字",
            "studio_portrait": "专业影棚布光，人物突出，干净背景，绝对无文字",
            "shonen": "动感十足，热血氛围，强烈对比，漫画质感，夸张动作，绝对无文字",
            "shoujo": "柔和色彩，浪漫氛围，华丽细节，少女漫画质感，绝对无文字",
            "seinen": "成熟写实画风，深沉色调，复杂构图，绝对无文字",
            "dark": "黑暗氛围，哥特元素，神秘诡异，强烈对比，绝对无文字",
            "scifi": "赛博朋克霓虹光，未来质感，雨夜反光，绝对无文字",
            "cyberpunk_city": "未来都市霓虹与雨夜氛围，绝对无文字",
            "oil_painting": "古典油画笔触质感，艺术光影，绝对无文字",
            "watercolor": "水彩晕染与纸纹质感，柔和过渡，绝对无文字",
        }

        enhancement = style_enhancements.get(style_key, "高质量视觉，细节丰富，绝对无文字")
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
        
        dur = int(getattr(story_segment, "duration_sec", VIDEO_CONFIG.get("video_duration", 4)) or VIDEO_CONFIG.get("video_duration", 4))

        # 基于场景类型推荐节奏（单镜4/5秒）
        rhythm_patterns = {
            "开场": f"{dur}秒短镜头：开头抓钩子画面，中段动作推进，结尾留下悬念",
            "发展": f"{dur}秒短镜头：开头变化出现，中段冲突升级，结尾切到下一镜",
            "高潮": f"{dur}秒短镜头：开头紧张爆发，中段关键动作，结尾反转定格"
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
        expected = int(VIDEO_CONFIG.get("video_count", 5))
        if len(story_data.segments) < expected:
            score -= 2
            self.log(f"⚠️ 分段数量不足{expected}个")

        
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