# -*- coding: utf-8 -*-
"""居家管家 - 窗口识别与相对坐标点击逻辑测试（不依赖真实窗口）"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import actions  # noqa: E402


def test_resolve_point():
    # 窗口位于 (100, 200) - (1000, 800)，即 900x600
    actions.window_rect = lambda hwnd: (100, 200, 1000, 800)
    x, y = actions.resolve_point({"rx": 0.5, "ry": 0.5, "x": 1, "y": 1}, 1234)
    assert (x, y) == (550, 500), (x, y)
    # 一条龙比例点
    x, y = actions.resolve_point({"rx": 47 / 900, "ry": 221 / 600}, 1234)
    assert (x, y) == (147, 421), (x, y)
    # 无窗口句柄时回退绝对坐标
    x, y = actions.resolve_point({"rx": 0.5, "ry": 0.5, "x": 333, "y": 222}, None)
    assert (x, y) == (333, 222), (x, y)
    print("[OK] 窗口相对坐标换算/绝对回退")


def test_run_steps_relative():
    clicked = []
    actions.find_window = lambda title: 999 if title == "BetterGI" else None
    actions.focus_window = lambda hwnd: True
    actions.window_rect = lambda hwnd: (100, 200, 1000, 800)
    actions.click = lambda x, y, double=False: clicked.append((x, y, double))
    actions.time.sleep = lambda s: None
    task = {
        "window_title": "BetterGI", "wait_window": 30,
        "clicks": [
            {"delay": 0, "x": 0, "y": 0, "rx": 47 / 900, "ry": 221 / 600},
            {"delay": 0, "x": 0, "y": 0, "rx": 326 / 900, "ry": 65 / 600},
        ],
    }
    actions._run_steps(task)
    assert clicked == [(147, 421, False), (426, 265, False)], clicked

    # 窗口移动到 (500,0)，相对点击应跟随移动
    clicked.clear()
    actions.window_rect = lambda hwnd: (500, 0, 1400, 600)
    actions._run_steps(task)
    assert clicked == [(547, 221, False), (826, 65, False)], clicked
    print("[OK] 多步点击随窗口位置换算")


def test_launch_idempotent():
    calls = []
    actions.find_window = lambda title: 999  # 窗口已存在
    actions.focus_window = lambda hwnd: True
    class FakePopen:
        def __init__(self, *a, **k):
            calls.append(a)
    actions.subprocess.Popen = FakePopen
    actions.launch_task({"exe": r"C:\x.exe", "window_title": "BetterGI",
                         "clicks": []})
    assert calls == [], "窗口已存在时不应重复启动程序"

    # 窗口不存在才启动
    actions.find_window = lambda title: None
    actions.os.path.exists = lambda p: True
    actions.launch_task({"exe": r"C:\x.exe", "window_title": "BetterGI",
                         "clicks": []})
    assert len(calls) == 1, calls
    print("[OK] 已运行则激活、未运行才启动")


def test_missing_exe_raises():
    actions.find_window = lambda title: None
    actions.os.path.exists = lambda p: False
    try:
        actions.launch_task({"exe": r"C:\nope.exe", "window_title": "",
                             "clicks": []})
        raise AssertionError("应当抛出 FileNotFoundError")
    except FileNotFoundError:
        pass
    print("[OK] 程序路径缺失时报错")


if __name__ == "__main__":
    test_resolve_point()
    test_run_steps_relative()
    test_launch_idempotent()
    test_missing_exe_raises()
    print("全部通过")
