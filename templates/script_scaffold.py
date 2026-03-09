"""
Math Video Scene Scaffold
数学教学视频场景脚手架

根据分镜脚本和音频信息生成完整动画

使用方式：
1. 复制此文件为 script.py
2. 根据题目实现 TODO 部分
3. 运行 manim -pqh script.py MathScene

常见问题：
- 渲染卡住：通常是音频文件问题，尝试禁用 add_scene_audio
- deepcopy 错误：不要存储 self 引用到 Mobject 中
- 视频未生成：检查 copy_video_to_root 路径是否正确
"""

from manim import *
import json
import os


class MathScene(Scene):
    """
    数学教学视频场景

    核心原则：
    1. 数学先行 - 先建立正确的数学模型
    2. 音画同步 - 用 wait_for_narration() 对齐高亮与读白
    3. 高亮对应 - 配音提到什么，画面高亮什么
    4. 最小验证 - assert_geometry 只验证关键事实和画布范围
    """

    # ========== 1. 配置参数 ==========
    config.pixel_width = 1920
    config.pixel_height = 1080
    config.frame_rate = 60

    COLORS = {
        'background': '#1a1a2e',
        'primary': '#4ecca3',
        'secondary': '#e94560',
        'highlight': '#ffc107',
        'text': '#ffffff',
        'text_secondary': '#aaaaaa',
        'grid': '#2a2a4e',
        'axis': '#444466',
    }

    # ========== 2. 幕信息数组（从分镜读取） ==========
    SCENES = [
        # (幕号, 幕名, 音频文件名, 时长秒数)
        # 时长从 audio/audio_info.json 读取
        # TODO: 根据分镜脚本填写
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_dir = "audio"
        self.audio_info_file = os.path.join(self.audio_dir, "audio_info.json")
        self._current_scene_num = None
        self._current_scene_name = ""
        self._scene_start_time = 0.0
        self._audio_safety_margin = 0.2
        self._audio_data = self._load_audio_data()
        self._sync_points = {}  # {scene_num: [{idx, text, time}, ...]}

    # ========== 3. 音频管理 ==========
    def _load_audio_data(self):
        """从 audio_info.json 加载音频时长和同步点"""
        if not os.path.exists(self.audio_info_file):
            return {}

        try:
            with open(self.audio_info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load audio info: {e}")
            return {}

        timings = {}
        for item in data.get('files', []):
            scene_num = item.get('scene')
            duration = item.get('duration')
            if scene_num and duration:
                timings[scene_num] = duration

            sp = item.get('sync_points', [])
            if scene_num and sp:
                self._sync_points[scene_num] = sp

        for i, (scene_num, name, audio_file, _) in enumerate(self.SCENES):
            if scene_num in timings:
                self.SCENES[i] = (scene_num, name, audio_file, timings[scene_num])

        return timings

    def add_scene_audio(self, scene_num, play_audio=True):
        """添加指定幕的音频"""
        for sn, name, audio_file, duration in self.SCENES:
            if sn == scene_num:
                audio_path = os.path.join(self.audio_dir, audio_file)
                if os.path.exists(audio_path):
                    if play_audio:
                        self.add_sound(audio_path)
                    return duration
                else:
                    print(f"Warning: Audio file not found: {audio_path}")
                    return 0
        return 0

    def start_scene_with_audio(self, scene_num):
        """
        开始一幕并播放该幕音频（防重叠入口）

        返回：float - 该幕音频时长（秒）
        """
        self._current_scene_num = scene_num
        self._scene_start_time = self.time

        for sn, name, _, duration in self.SCENES:
            if sn == scene_num:
                self._current_scene_name = name
                expected = float(duration or 0)
                break
        else:
            self._current_scene_name = f"Scene {scene_num}"
            expected = 0.0

        self.add_scene_audio(scene_num, play_audio=True)
        print(
            f"\n▶ Scene {scene_num}: {self._current_scene_name} | "
            f"audio={expected:.2f}s | t={self._scene_start_time:.2f}s"
        )
        return expected

    def end_scene_with_audio(self, expected_duration=None, safety_margin=None):
        """结束一幕并补足等待，确保不抢跑到下一幕导致音频重叠。"""
        if expected_duration is None:
            expected_duration = 0.0
        if safety_margin is None:
            safety_margin = self._audio_safety_margin

        elapsed = self.time - self._scene_start_time
        target = max(0.0, float(expected_duration)) + max(0.0, float(safety_margin))
        remaining = target - elapsed

        if remaining > 1e-3:
            self.wait(remaining)
            elapsed = self.time - self._scene_start_time

        if elapsed + 1e-3 < target:
            print(
                f"⚠ Scene {self._current_scene_num} timeline short: "
                f"elapsed={elapsed:.2f}s < target={target:.2f}s"
            )
        else:
            print(
                f"✓ Scene {self._current_scene_num} done: "
                f"elapsed={elapsed:.2f}s / target={target:.2f}s"
            )

    # ========== 4. 幕内同步工具（核心） ==========
    def wait_until_scene_time(self, target_time):
        """
        等待到当前幕内的指定时刻（相对于幕开始的秒数）。

        如果动画已超过目标时刻，打印警告但不回退。
        用法：self.wait_until_scene_time(3.7)  # 等到幕开始后 3.7s
        """
        elapsed = self.time - self._scene_start_time
        remaining = target_time - elapsed
        if remaining > 0.05:
            self.wait(remaining)
        elif remaining < -0.3:
            print(
                f"  ⚠ 幕{self._current_scene_num} 动画超时 {abs(remaining):.2f}s"
                f"（目标 {target_time:.1f}s，实际已 {elapsed:.1f}s）"
            )

    def wait_for_narration(self, keyword):
        """
        等待到读白说出包含 keyword 的那句话的起始时刻。

        从当前幕的 sync_points 中查找第一个 text 包含 keyword 的条目，
        然后调用 wait_until_scene_time() 对齐。

        用法：
            self.wait_for_narration("内切圆")
            self.play(FadeIn(incircle))
        """
        target = self.get_sync_time(keyword)
        if target is not None:
            self.wait_until_scene_time(target)
        else:
            print(
                f"  ⚠ 幕{self._current_scene_num} 未找到同步点 '{keyword}'，"
                f"跳过等待（检查 audio_info.json 的 sync_points）"
            )

    def get_sync_time(self, keyword):
        """
        查找当前幕中包含 keyword 的同步点时间。

        返回：float 秒数，未找到返回 None
        """
        points = self._sync_points.get(self._current_scene_num, [])
        for sp in points:
            if keyword in sp.get("text", ""):
                return sp["time"]
        return None

    def get_sync_time_by_index(self, sentence_idx):
        """
        按句子序号获取同步点时间（第 0 句、第 1 句...）。

        返回：float 秒数，未找到返回 None
        """
        points = self._sync_points.get(self._current_scene_num, [])
        for sp in points:
            if sp.get("idx") == sentence_idx:
                return sp["time"]
        return None

    # ========== 5. 几何计算（必须实现） ==========
    def calculate_geometry(self):
        """
        计算所有几何元素的位置和属性

        坐标系说明：
        - 所有点的格式：(x, y) - z 坐标始终为 0
        - 建议将几何图形放在 (-5, 5) x (-4, 4) 区域内

        返回：dict 包含所有几何对象的数据
        """
        geometry = {
            'points': {},
            'lines': {},
            'circles': {},
            'arcs': {},
            'polygons': {},
        }
        # TODO: 【必须实现】根据题目几何关系计算所有点的坐标
        return geometry

    # ========== 6. 几何验证（必须实现） ==========
    def assert_geometry(self, geometry):
        """
        验证几何计算的正确性（最小验证原则）

        验证内容：
        1. 题目给定的事实（如：两条边相等）
        2. 精度问题：使用相对误差比较
        3. 画布范围检查：确保图形在可视区域内
        """
        def approx_equal(a, b, epsilon=1e-4):
            return abs(a - b) < epsilon

        # TODO: 【必须实现】验证几何计算的正确性

        def check_canvas_bounds(geometry):
            all_points = list(geometry['points'].values())
            for circle in geometry['circles'].values():
                cx, cy = circle['center']
                r = circle['radius']
                all_points.extend([(cx+r, cy), (cx-r, cy), (cx, cy+r), (cx, cy-r)])

            if not all_points:
                return True

            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            CANVAS_MIN_X, CANVAS_MAX_X = -6, 6
            CANVAS_MIN_Y, CANVAS_MAX_Y = -5, 5
            MARGIN = 0.5

            assert min_x >= CANVAS_MIN_X + MARGIN, f"图形超出左边界：{min_x}"
            assert max_x <= CANVAS_MAX_X - MARGIN, f"图形超出右边界：{max_x}"
            assert min_y >= CANVAS_MIN_Y + MARGIN, f"图形超出下边界：{min_y}"
            assert max_y <= CANVAS_MAX_Y - MARGIN, f"图形超出上边界：{max_y}"

            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            assert abs(center_x) < 1.5, f"图形中心偏离 x 轴：{center_x}"
            assert abs(center_y) < 1.0, f"图形中心偏离 y 轴：{center_y}"
            return True

        check_canvas_bounds(geometry)
        print("Geometry validation passed!")

    # ========== 7. 图形元素定义 ==========
    def define_elements(self, geometry):
        """定义 Manim 图形对象（但不创建动画）"""
        elements = {
            'points': {},
            'lines': {},
            'circles': {},
            'labels': {},
        }

        def to_3d(p):
            return (p[0], p[1], 0.0)

        # TODO: 根据分镜需求定义图形元素
        return elements

    # ========== 8. 字幕工具 ==========
    def create_subtitle(self, text, position=DOWN * 3.5):
        """创建字幕对象"""
        subtitle = Text(text, font_size=36, color=self.COLORS['text'])
        subtitle.to_edge(position)
        return subtitle

    def fade_in(self, mobject, run_time=0.5):
        return FadeIn(mobject, run_time=run_time)

    def fade_out(self, mobject, run_time=0.5):
        return FadeOut(mobject, run_time=run_time)

    def show_subtitle_timed(self, text, duration, position=DOWN * 3.5,
                            fade_in_time=0.5, fade_out_time=0.5):
        """显示字幕并在指定时间后自动退场"""
        subtitle = self.create_subtitle(text, position)
        self.play(self.fade_in(subtitle), run_time=fade_in_time)
        hold_time = max(0.0, duration - fade_in_time - fade_out_time)
        self.wait(hold_time)
        self.play(self.fade_out(subtitle), run_time=fade_out_time)
        return subtitle

    def show_subtitle_with_audio(self, text, audio_duration, position=DOWN * 3.5):
        """显示字幕并持续到音频结束"""
        subtitle = self.create_subtitle(text, position)
        self.play(self.fade_in(subtitle), run_time=0.5)
        self.wait(max(0.0, audio_duration - 1.0))
        self.play(self.fade_out(subtitle), run_time=0.5)
        return subtitle

    # ========== 9. 高亮工具 ==========
    def highlight_element(self, element, color=None, scale=1.3, duration=0.8):
        """高亮指定元素"""
        color = color or self.COLORS['highlight']
        original_color = element.get_color()
        self.play(
            element.animate.scale(scale).set_color(color),
            run_time=0.4
        )
        self.wait(duration - 0.4)
        self.play(
            element.animate.scale(1/scale).set_color(original_color),
            run_time=0.4
        )

    def indicate_equal_lines(self, line1, line2, duration=1.2):
        """指示两条线段相等（同时高亮）"""
        self.play(
            line1.animate.set_color(self.COLORS['highlight']).set_stroke(width=6),
            line2.animate.set_color(self.COLORS['highlight']).set_stroke(width=6),
            run_time=0.5
        )
        self.wait(duration - 0.8)
        self.play(
            line1.animate.set_color(self.COLORS['primary']).set_stroke(width=3),
            line2.animate.set_color(self.COLORS['primary']).set_stroke(width=3),
            run_time=0.5
        )

    # ========== 10. 主流程 ==========
    def construct(self):
        """主构造流程"""
        self.camera.background_color = self.COLORS['background']

        geometry = self.calculate_geometry()
        self.assert_geometry(geometry)
        elements = self.define_elements(geometry)

        for scene_num, scene_name, audio_file, duration in self.SCENES:
            method_name = f"play_scene_{scene_num}"
            if hasattr(self, method_name):
                expected_duration = self.start_scene_with_audio(scene_num)
                getattr(self, method_name)(elements, geometry)
                self.end_scene_with_audio(expected_duration)
            else:
                print(f"Warning: play_scene_{scene_num} not implemented")

        self.copy_video_to_root()

    def copy_video_to_root(self):
        """渲染完成后拷贝视频到项目根目录"""
        import shutil
        from pathlib import Path

        scene_name = self.__class__.__name__
        possible_paths = [
            Path(f"media/videos/script/1920p60/{scene_name}.mp4"),
            Path(f"media/videos/script/1080p60/{scene_name}.mp4"),
            Path(f"media/videos/script/720p30/{scene_name}.mp4"),
        ]

        video_src = None
        for path in possible_paths:
            if path.exists():
                video_src = path
                break

        if video_src:
            video_dst = Path(f"{scene_name}.mp4")
            try:
                shutil.copy2(video_src, video_dst)
                print(f"\n✓ 视频已拷贝到：{video_dst.absolute()}")
            except Exception as e:
                print(f"\n⚠️ 视频拷贝失败：{e}")
        else:
            print(f"\n⚠️ 未找到视频文件")


# ========== 使用说明 ==========
"""
关键提醒：
1. 所有几何计算必须在 calculate_geometry() 中完成
2. assert_geometry() 必须检查画布范围
3. 每幕必须通过 start_scene_with_audio()/end_scene_with_audio() 统一收口
4. 配音提到什么，画面就高亮什么
5. 使用 wait_for_narration("关键词") 对齐读白和高亮时机——不要用 duration - N 手动估算
6. 使用 wait_until_scene_time(秒数) 精确定位幕内时间点
7. 使用 create_subtitle() 创建字幕，不要用 Subtitle 类
8. 幕末收尾统一由 end_scene_with_audio() 自动补足，play_scene_X() 内不需要手动兜底
9. 所有点坐标使用 2D (x, y)，define_elements 中用 to_3d() 转换
10. 字幕退场：使用 show_subtitle_timed() 或 show_subtitle_with_audio() 确保文字退场

同步对齐示例（推荐写法）：
    def play_scene_2(self, elements, geometry):
        # 读白第1句："首先，我们来看三角形ABC"
        self.wait_for_narration("三角形ABC")
        self.play(Create(triangle, run_time=1.0))

        # 读白第2句："它的内切圆I，分别切三条边"
        self.wait_for_narration("内切圆")
        self.play(FadeIn(incircle, run_time=0.5))

        # 无需手动兜底——end_scene_with_audio() 会自动补齐
"""
