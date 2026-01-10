---
name: 30s-3s-segments-auto-ffmpeg-merge
overview: 将现有“3×10秒三连”升级为“最多10×3秒分镜自动生成 + ffmpeg 自动合成为1段30秒成片”。运行时可选“漫剧/电影”节奏风格；默认全自动、严格无字；最终成片强制无音频。分镜间是否使用尾帧续接由分镜的转场策略字段决定。初始剧本提示词由用户在运行时交互输入（可很粗糙），agent 在其基础上补全分镜与提示词。
todos:
  - id: repo-audit
    content: 使用[subagent:code-explorer]梳理3×10秒链路入口与改造点
    status: completed
  - id: cli-runtime-input
    content: 新增30秒模式CLI：一次性剧本输入+漫剧/电影风格选择
    status: completed
    dependencies:
      - repo-audit
  - id: storyboard-planner
    content: 实现30秒分镜规划：3秒单位、≤10镜、输出分镜JSON含转场策略
    status: completed
    dependencies:
      - cli-runtime-input
  - id: prompt-no-text
    content: 完善每镜提示词模板：严格无字负面约束与风格节奏差异
    status: completed
    dependencies:
      - storyboard-planner
  - id: segment-orchestration
    content: 改造生成编排：按转场策略决定尾帧续接或独立生成
    status: completed
    dependencies:
      - prompt-no-text
  - id: ffmpeg-merge-30s
    content: 实现FFmpeg自动归一化+concat合成单段30秒并强制-an
    status: completed
    dependencies:
      - segment-orchestration
  - id: validation-output
    content: 添加产物校验：分镜JSON可复现、成片无音频、时长锁定30秒
    status: completed
    dependencies:
      - ffmpeg-merge-30s
---

## Product Overview

将现有“3×10秒三连”升级为“总时长30秒、按3秒粒度编排的多分镜自动生成与合成”。用户运行时一次性输入粗糙剧本描述，并选择“漫剧/电影”节奏风格；系统自动补全分镜与每镜提示词，输出严格无字画面，最终成片强制无音频。

## Core Features

- **运行时交互输入**：一次性粘贴/输入粗糙剧本，选择节奏风格（漫剧/电影），默认全自动不再二次确认
- **30秒分镜编排**：按3秒为最小粒度自动拆分为不超过10个分镜，保证总时长严格为30秒
- **分镜脚本JSON输出**：生成包含镜头时长、画面要素、负面约束（无字）、以及“转场策略”字段的分镜计划
- **转场策略驱动续接**：按每个分镜的转场策略决定是否使用上一段尾帧续接下一段首帧，剧情需要时才续接
- **自动合成成片**：将所有分镜片段自动合成为单段30秒视频，并强制去除音频轨道

## Tech Stack（沿用现有项目栈）

- 复用仓库当前脚本语言/运行方式与现有生成流程（通过仓库扫描确定入口命令、配置与数据结构）
- 视频合成：FFmpeg（统一转码参数、concat合并、强制 `-an` 去音频）

## Architecture Design

### System Architecture

```mermaid
flowchart LR
U[运行时输入: 粗糙剧本 + 节奏风格] --> P[分镜规划器: 30秒/3秒粒度]
P --> J[分镜JSON: segments + transition]
J --> G[分镜生成编排器: 逐镜生成/续接策略]
G --> V[分镜视频资产: N个片段]
V --> F[FFmpeg合成器: 归一化 + concat + -an]
F --> O[输出: 单段30s无音频成片]
```

### Module Division

- **Runtime Prompt Module**：读取用户一次性输入、选择节奏风格、写入本次任务配置
- **Storyboard Planner Module**：将“粗糙剧本”补全为分镜计划；按“3秒单位”分配，保证总单位数=10
- **Segment Orchestrator Module**：按分镜JSON依次生成；根据 `transition.strategy` 决定是否尾帧续接
- **FFmpeg Composer Module**：对分镜片段统一编码参数后拼接；最终强制移除音频并校验时长为30秒

### Data Flow（关键约束）

- 规划阶段：产生 `totalUnits=10`（1单位=3秒），`sum(segment.units)=10`
- 生成阶段：每镜附带 `noText=true` 的提示词约束；如来源模型可能带配音，合成阶段统一 `-an`
- 合成阶段：若片段规格不一致，先逐段归一化（分辨率/fps/编码）再concat，避免拼接失败

## Implementation Details

### Core Directory Structure（仅展示预计新增/修改）

```
d:/codebase/aigc_video_director/
├── src/
│   ├── storyboard/
│   │   ├── planner.ts            # 新增/改造：30s/3s单位分镜规划
│   │   ├── types.ts              # 新增：分镜JSON与转场策略类型
│   │   └── stylePresets.ts        # 新增：漫剧/电影节奏与提示词模板
│   ├── orchestrator/
│   │   └── segmentRunner.ts       # 修改：按transition执行尾帧续接/独立生成
│   ├── ffmpeg/
│   │   └── composer.ts            # 修改/新增：归一化、concat、强制-an
│   └── cli/
│       └── run30s.ts              # 新增：运行时交互入口（一次性输入+风格选择）
```

### Key Code Structures（核心数据结构）

```ts
export type RhythmStyle = "manju" | "movie";

export type TransitionStrategy = "tailframe_continue" | "hard_cut";

export interface SegmentPlan {
  id: string;              // seg-01...
  units: number;           // 1..10，1单位=3秒
  durationSec: number;     // units * 3
  prompt: string;          // 已补全的正向提示词（严格无字）
  negativePrompt: string;  // 强制无字/无字幕/无水印等
  transition: {
    strategy: TransitionStrategy;
    reason?: string;       // 可选：为何续接/不续接（便于复盘）
  };
}

export interface StoryboardPlan {
  rhythmStyle: RhythmStyle;
  totalDurationSec: 30;
  unitSec: 3;
  segments: SegmentPlan[]; // length <= 10, sum(units)=10
}
```

### Technical Implementation Plan（按难点拆解）

1) **30秒/3秒单位分配**

- Approach：以“单位数=10”为硬约束；根据剧情节拍决定分镜数量与每镜units分配（≥1）
- Testing：断言总时长=30；分镜数≤10；每镜duration为3的倍数

2) **转场策略执行（尾帧续接）**

- Approach：在编排器中读取 `transition.strategy`；当为 `tailframe_continue` 时，将上一镜尾帧路径/参考信息注入下一镜生成输入
- Testing：对比两镜首尾帧连续性；策略为hard_cut时不注入

3) **FFmpeg无音频强制与时长校验**

- Approach：统一转码参数后concat；输出参数强制 `-an`；完成后用ffprobe校验duration≈30s
- Testing：输出无音频流；时长误差在可控范围（必要时做trim到30s）

## Integration Points

- 分镜生成器：复用现有“按提示词生成分镜视频”的接口/脚本调用方式（由仓库扫描对齐参数）
- 合成器输入：分镜片段文件列表（按时间线顺序）
- 输出：单文件30秒成片 + 分镜JSON（可选落盘用于复现）

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 扫描仓库定位现有“3×10秒三连”实现入口、分镜数据结构、以及FFmpeg合成逻辑
- Expected outcome: 输出可修改点清单（文件路径/关键函数/数据流），并给出最小改造方案以复用现有链路