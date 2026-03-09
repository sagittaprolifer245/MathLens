#!/usr/bin/env python3
"""
Manim 教学视频代码检查脚本
验证 script.py 是否包含必要的函数和结构

使用方法:
    python scripts/check.py [script_file]

默认检查 script.py，也可以指定其他文件
"""

import ast
import sys
import os
from pathlib import Path


class CodeChecker:
    """代码结构检查器"""

    # 必须包含的函数
    REQUIRED_FUNCTIONS = [
        'calculate_geometry',
        'assert_geometry',
        'define_elements',
    ]

    # 推荐包含的函数（警告但不阻止）
    RECOMMENDED_FUNCTIONS = [
        'play_scene',
    ]

    # 必须包含的类（内部类也算）
    REQUIRED_CLASSES = [
        'Subtitle',
        'TitleSubtitle',
    ]

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.errors = []
        self.warnings = []
        self.tree = None
        self.classes = {}  # 类名 -> 方法列表
        self.class_method_calls = {}  # 类名 -> {方法名: set(调用名)}
        self.scene_classes = set()  # 继承自 Scene 的类名

    def parse(self):
        """解析 Python 文件"""
        if not self.file_path.exists():
            self.errors.append(f"文件不存在: {self.file_path}")
            return False

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.tree = ast.parse(content)
            return True
        except SyntaxError as e:
            self.errors.append(f"语法错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"解析失败: {e}")
            return False

    def analyze(self):
        """分析代码结构"""
        if not self.tree:
            return

        # 遍历顶层定义
        for node in ast.iter_child_nodes(self.tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                methods = []
                method_calls = {}
                inner_classes = []
                is_scene_class = False

                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'Scene':
                        is_scene_class = True
                    elif isinstance(base, ast.Attribute) and base.attr == 'Scene':
                        is_scene_class = True
                if is_scene_class:
                    self.scene_classes.add(class_name)

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                        calls = set()
                        for sub in ast.walk(item):
                            if isinstance(sub, ast.Call):
                                if isinstance(sub.func, ast.Attribute):
                                    calls.add(sub.func.attr)
                                elif isinstance(sub.func, ast.Name):
                                    calls.add(sub.func.id)
                        method_calls[item.name] = calls
                    elif isinstance(item, ast.ClassDef):
                        inner_classes.append(item.name)
                        # 也记录内部类的方法
                        inner_methods = [n.name for n in item.body
                                        if isinstance(n, ast.FunctionDef)]
                        self.classes[f"{class_name}.{item.name}"] = inner_methods

                self.classes[class_name] = methods
                self.class_method_calls[class_name] = method_calls

    def check_required_functions(self):
        """检查必需函数是否存在"""
        all_methods = set()
        for class_name, methods in self.classes.items():
            all_methods.update(methods)

        for func_name in self.REQUIRED_FUNCTIONS:
            if func_name not in all_methods:
                self.errors.append(
                    f"缺少必需函数: {func_name}()\n"
                    f"  请在 MathScene 类中实现此方法\n"
                    f"  作用: {self._get_function_description(func_name)}"
                )

    def check_recommended_functions(self):
        """检查推荐函数"""
        all_methods = set()
        for class_name, methods in self.classes.items():
            all_methods.update(methods)

        for func_name in self.RECOMMENDED_FUNCTIONS:
            if func_name not in all_methods:
                self.warnings.append(
                    f"缺少推荐函数: {func_name}()\n"
                    f"  建议实现以更好地控制每幕动画"
                )

    def check_subtitle_classes(self):
        """检查字幕类是否存在"""
        # 检查 Subtitle 和 TitleSubtitle 是否作为内部类定义
        found_subtitle = False
        found_title = False

        for class_name in self.classes.keys():
            if '.' in class_name:
                outer, inner = class_name.split('.')
                if inner == 'Subtitle':
                    found_subtitle = True
                if inner == 'TitleSubtitle':
                    found_title = True

        if not found_subtitle:
            self.warnings.append(
                "未找到 Subtitle 类\n"
                "  建议: 从 templates/script_scaffold.py 复制 Subtitle 类定义\n"
                "  作用: 避免忘记渲染/退场导致的文字残留问题"
            )

        if not found_title:
            self.warnings.append(
                "未找到 TitleSubtitle 类\n"
                "  建议: 从 templates/script_scaffold.py 复制 TitleSubtitle 类定义"
            )

    def check_scene_class(self):
        """检查是否有场景类继承自 Scene"""
        found_scene = False
        for node in ast.iter_child_nodes(self.tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'Scene':
                        found_scene = True
                        break
                    elif isinstance(base, ast.Attribute):
                        if base.attr == 'Scene':
                            found_scene = True
                            break

        if not found_scene:
            self.errors.append(
                "未找到继承自 Scene 的类\n"
                "  必须有一个类继承自 Scene，例如: class MathScene(Scene):"
            )

    def check_add_sound(self):
        """检查是否有 add_sound 调用（音频集成）"""
        has_add_sound = False

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'add_sound':
                        has_add_sound = True
                        break
                elif isinstance(node.func, ast.Name):
                    if node.func.id == 'add_sound':
                        has_add_sound = True
                        break

        if not has_add_sound:
            self.warnings.append(
                "未检测到 add_sound() 调用\n"
                "  提醒: 每幕动画应该添加对应的音频文件\n"
                "  示例: self.add_sound('audio/audio_001_开场.wav')"
            )

    def check_audio_timeline_guards(self):
        """
        检查音频时间轴护栏，避免出现音频重叠：
        - 有分幕时，应使用 start_scene_with_audio / end_scene_with_audio
        - 如果直接 add_sound，也应有明确的 wait_for_audio 或 end_scene_with_audio 兜底
        """
        for class_name in self.scene_classes:
            methods = self.class_method_calls.get(class_name, {})
            if not methods:
                continue

            method_names = set(methods.keys())
            all_calls = set()
            for calls in methods.values():
                all_calls.update(calls)

            has_play_scene_methods = any(name.startswith("play_scene_") for name in method_names)
            has_start_guard = "start_scene_with_audio" in all_calls
            has_end_guard = ("end_scene_with_audio" in all_calls) or ("wait_for_audio" in all_calls)
            has_add_sound = "add_sound" in all_calls

            if has_play_scene_methods and not has_start_guard:
                self.warnings.append(
                    f"{class_name} 检测到 play_scene_* 分幕方法，但未使用 start_scene_with_audio()\n"
                    "  建议: 在 construct() 中统一从 start_scene_with_audio() 开始每幕"
                )

            if has_play_scene_methods and not has_end_guard:
                self.errors.append(
                    f"{class_name} 检测到分幕结构，但未找到 end_scene_with_audio()/wait_for_audio() 收尾\n"
                    "  风险: 下一幕可能提前开始，导致上一幕音频与下一幕音频重叠"
                )

            if has_add_sound and not has_end_guard:
                self.errors.append(
                    f"{class_name} 使用了 add_sound()，但缺少音频收尾等待机制\n"
                    "  建议: 使用 end_scene_with_audio(expected_duration) 或 wait_for_audio()"
                )

    def check_sync_methods(self):
        """
        检查是否使用了同步对齐方法（wait_for_narration / wait_until_scene_time）。
        如果有 play_scene_* 方法但未使用任何同步方法，给出建议。
        """
        for class_name in self.scene_classes:
            methods = self.class_method_calls.get(class_name, {})
            if not methods:
                continue

            play_scene_methods = {
                name: calls for name, calls in methods.items()
                if name.startswith("play_scene_")
            }

            if not play_scene_methods:
                continue

            has_any_sync = False
            for name, calls in play_scene_methods.items():
                if "wait_for_narration" in calls or "wait_until_scene_time" in calls:
                    has_any_sync = True
                    break

            if not has_any_sync:
                self.warnings.append(
                    f"{class_name} 的 play_scene_* 方法未使用 wait_for_narration() 或 wait_until_scene_time()\n"
                    "  建议: 使用同步方法精确对齐读白和画面，而非 self.wait(duration - N) 手动估算\n"
                    "  示例: self.wait_for_narration('内切圆') 会等到读白说到该关键词时刻"
                )

    def check_duration_minus_antipattern(self):
        """
        检测 duration - N 反模式：在 play_scene_* 中使用
        self.wait(max(..., duration - N)) 手动兜底。
        """
        if not self.file_path.exists():
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception:
            return

        import re
        pattern = re.compile(
            r'self\.wait\s*\(\s*max\s*\(.+?duration\s*-',
            re.DOTALL
        )
        matches = pattern.findall(source)
        if matches:
            self.warnings.append(
                f"检测到 {len(matches)} 处 self.wait(max(..., duration - N)) 反模式\n"
                "  问题: 手动计算剩余时长容易出错，增删动画时需重算\n"
                "  建议: 删除手动兜底，改用 end_scene_with_audio() 自动补齐\n"
                "  参考: play_scene_X() 内专注视觉动作，不需要手动兜底"
            )

    def _get_function_description(self, func_name):
        """获取函数描述"""
        descriptions = {
            'calculate_geometry': '计算所有几何元素（点、线、圆）的坐标和属性',
            'assert_geometry': '验证几何计算的正确性和画布范围',
            'define_elements': '定义 Manim 图形对象（点、线、圆等）',
        }
        return descriptions.get(func_name, '未知功能')

    def run(self):
        """运行所有检查"""
        print(f"🔍 检查文件: {self.file_path}")
        print("=" * 50)

        # 解析
        if not self.parse():
            return False

        # 分析
        self.analyze()

        # 各项检查
        self.check_scene_class()
        self.check_required_functions()
        self.check_recommended_functions()
        self.check_subtitle_classes()
        self.check_add_sound()
        self.check_audio_timeline_guards()
        self.check_sync_methods()
        self.check_duration_minus_antipattern()

        # 输出结果
        return self.report()

    def report(self):
        """输出检查报告"""
        success = len(self.errors) == 0

        # 错误
        if self.errors:
            print("\n❌ 错误 (必须修复):")
            for i, error in enumerate(self.errors, 1):
                print(f"\n  {i}. {error}")

        # 警告
        if self.warnings:
            print("\n⚠️  警告 (建议修复):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n  {i}. {warning}")

        # 成功信息
        if success and not self.warnings:
            print("\n✅ 所有检查通过！可以开始渲染。")
        elif success:
            print("\n✅ 必要检查通过，但有警告建议处理。")

        print("\n" + "=" * 50)

        if success:
            print("🎬 下一步: 运行渲染命令")
            print(f"   manim -pqh {self.file_path} MathScene")
        else:
            print("⛔ 检查失败，请修复错误后重试。")

        return success


def main():
    """主函数"""
    # 获取要检查的文件
    if len(sys.argv) > 1:
        script_file = sys.argv[1]
    else:
        script_file = "script.py"

    # 检查文件路径
    script_path = Path(script_file)

    # 运行检查
    checker = CodeChecker(script_path)
    success = checker.run()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
