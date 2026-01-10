---
name: min-4s-shot-and-approx-30s
overview: 将分镜最小时长从3秒提升到4秒，并允许4/5秒混合以生成约30秒成片；同步移除“固定10镜/严格30秒”的写死假设；保持全自动与严格无字；合成阶段默认保留音轨（不刻意去音）。
todos:
  - id: repo-scan-constraints
    content: 使用[subagent:code-explorer]定位3s/10镜/严格30s/去音相关代码
    status: completed
  - id: update-shot-planner
    content: 改造分镜规划：最小4s，允许4/5s混合，目标约30s
    status: completed
    dependencies:
      - repo-scan-constraints
  - id: remove-hardcoded-assumptions
    content: 移除固定10镜与严格30秒校验，改为范围校验与回退
    status: completed
    dependencies:
      - update-shot-planner
  - id: enforce-no-text
    content: 梳理生成与合成链路，确保全流程无字幕/无文字叠加
    status: completed
    dependencies:
      - remove-hardcoded-assumptions
  - id: keep-audio-by-default
    content: 合成阶段默认保留音轨，移除默认静音/去音逻辑或改默认值
    status: completed
    dependencies:
      - repo-scan-constraints
  - id: add-tests-and-samples
    content: 补齐用例：时长分布、总时长范围、音频保留、无字输出
    status: completed
    dependencies:
      - keep-audio-by-default
      - enforce-no-text
  - id: update-config-docs
    content: 更新配置与说明：4s最小、4/5s混合、约30s、默认保留音轨
    status: completed
    dependencies:
      - add-tests-and-samples
---

## Product Overview

一个全自动分镜生成与视频合成流程：分镜时长以4秒为最小单位，允许4/5秒混合拼接，生成约30秒左右的无字成片；合成阶段默认保留原始音轨。

## Core Features

- **分镜时长策略升级**：将分镜最小时长从3秒提升到4秒，并支持4秒与5秒混合分配，整体时长自动贴近30秒（允许小幅浮动）。
- **去除写死假设**：移除“固定10镜/严格30秒”的硬编码限制，镜头数量由时长分配策略自动决定。
- **严格无字输出**：生成与合成全流程保持无字幕/无文字叠加的成片效果。
- **默认保留音轨**：视频合成阶段不再刻意去音，默认保留音频轨道（如有配置项则以“保留”为默认值）。

## Tech Stack

- 沿用现有项目技术栈与工程结构（通过代码扫描定位分镜规划、时长校验、合成渲染与音频处理实现）。

## Architecture & Data Flow (变更相关)

```mermaid
flowchart LR
  A[输入素材/脚本] --> B[分镜规划器\n(4s最小, 4/5s混合, ~30s)]
  B --> C[镜头清单/时间轴]
  C --> D[渲染/合成器\n(默认保留音轨)]
  D --> E[成片输出\n无字, 约30秒, 含音频]
  B -->|校验失败| F[约束与回退策略\n(避免硬编码10镜/严格30s)]
  F --> B
```

## Module Division (聚焦本次改动)

- **Shot Planner / Timeline Builder**：负责镜头数量与每镜时长分配；移除固定10镜与严格30秒校验。
- **Constraint Validator**：统一约束校验（最小时长=4s，总时长≈30s范围内）。
- **Composer / Renderer**：合成阶段默认保留音轨，避免默认静音或强制去音。

## Key Code Structures (示例接口，用于落地改造点)

- `type Shot = { id: string; durationSec: 4 | 5; ... }`
- `planShots(targetSec: number, minSec: 4, allowedSec: number[]): Shot[]`
- `validateTimeline(totalSec: number, range: { min: number; max: number }): void`
- `composeVideo(timeline, { keepAudio: true }): Output`

## Agent Extensions

- **SubAgent: code-explorer**
- Purpose: 全仓检索定位“3秒最小分镜”“固定10镜/严格30秒”“合成去音/静音”等实现与配置入口
- Expected outcome: 输出需修改的文件清单、关键函数/常量位置、调用链路与影响面，确保改动最小且稳定