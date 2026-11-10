#!/usr/bin/env python3
"""时长规划器测试 —— 纯本地断言，不调用任何 API。

    python3 test_duration_planner.py

覆盖 README「测试覆盖」一节声明的规则：
  1. 4/5 秒混合，总时长约 30 秒（默认 ±2 秒容差）
  2. 节奏偏好：漫剧（多切）与电影（少切）的取镜差异
  3. 约束边界：最大分镜数、单镜最小时长、非法参数
"""

from utils import plan_segment_durations

CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def test_default_is_about_30s():
    """默认参数下总时长落在 30±2 秒，镜头只用 4/5 秒"""
    n, durations, total = plan_segment_durations()
    assert n == len(durations), "分镜数与时长列表长度不一致"
    assert all(d in (4, 5) for d in durations), f"出现非 4/5 秒镜头: {durations}"
    assert total == sum(durations), "planned_total 与逐镜时长之和不一致"
    assert 28 <= total <= 32, f"总时长 {total}s 超出 30±2 秒"
    assert n <= 10, f"分镜数 {n} 超过上限 10"


@case
def test_five_second_shots_not_bunched():
    """多个 5 秒镜头应分散，而非全堆在片头"""
    n, durations, total = plan_segment_durations(target_total_sec=30)
    k = durations.count(5)
    if k > 1:
        head = durations[:k]
        assert any(d == 4 for d in head), f"5 秒镜头全堆在片头: {durations}"
    assert durations != [], "时长列表为空"


@case
def test_more_cuts_more_segments():
    """漫剧偏好应切得比电影偏好更碎"""
    n_more, _, total_more = plan_segment_durations(prefer_more_cuts=True)
    n_less, _, total_less = plan_segment_durations(prefer_more_cuts=False)
    assert n_more >= n_less, f"多切({n_more}) 应不少于少切({n_less})"
    # 两种节奏都应命中 30±2 秒，差异只体现在镜头数
    assert abs(total_more - 30) <= 2 and abs(total_less - 30) <= 2


@case
def test_max_segments_respected():
    """max_segments 是硬上限，受限时宁可短于目标也不超发"""
    n, durations, total = plan_segment_durations(target_total_sec=30, max_segments=5)
    assert n <= 5, f"分镜数 {n} 超过 max_segments=5"
    assert total == sum(durations)
    # 被上限压住时，取满 5 镜 × 5 秒 = 25 秒，应小于目标而非超发
    assert total <= 30, f"受限时不应超出目标时长，实际 {total}s"


@case
def test_target_duration_scales():
    """目标时长参数应等比缩放结果"""
    for target in (20, 50):
        n, durations, total = plan_segment_durations(target_total_sec=target)
        assert total == sum(durations)
        assert abs(total - target) <= 2, f"目标 {target}s 实际 {total}s"


@case
def test_invalid_segment_duration_rejected():
    """单镜时长不在 [4,5] 内必须显式报错，不能静默生成"""
    try:
        plan_segment_durations(allowed_durations=[3])
    except ValueError:
        return
    raise AssertionError("allowed_durations=[3] 应当抛出 ValueError")


@case
def test_tiny_target_falls_back_to_single_segment():
    """目标低于单镜下限时退化为单镜"""
    n, durations, total = plan_segment_durations(target_total_sec=4)
    assert n == 1 and durations == [4] and total == 4, f"目标 4s 应规划为单镜 4s，实际 {n}, {durations}"


def main():
    failed = 0
    for fn in CASES:
        name = fn.__name__.replace("_", " ")
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"✗ {name}\n    {e}")
        except Exception as e:  # noqa: BLE001 - 用例内任何异常都算失败
            failed += 1
            print(f"✗ {name}\n    {type(e).__name__}: {e}")
        else:
            print(f"✓ {name}")

    print(f"\n{len(CASES) - failed}/{len(CASES)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
