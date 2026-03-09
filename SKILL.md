---
name: MathLens
description: |
  专业的数学老师辅导技能，用于深入浅出的解答数学题，生成HTML讲解文档和带配音的Manim动画视频， 解答细致，深入浅出，浅显易懂，比较适合一般学情的学生。
  核心工作流：数学分析 → HTML可视化 → 分镜脚本 → TTS音频 → 验证更新 → 脚手架 → Manim代码 → 渲染验证
  触发条件：学生粘贴数学题图片、需要教学视频、需要HTML讲解资料
---

# 数学分析

## 核心工作流

```python
WORKFLOW = [
    # 步骤1: 数学建模
    {
        "step": 1,
        "name": "analyze_problem",
        "input": "题目图片/文本",
        "output": "math_analysis.md",
        "tasks": ["推导数学事实", "建立几何模型", "确定图形构建方法"]
    },

    # 步骤2: HTML可视化
    {
        "step": 2,
        "name": "html_visualization",
        "input": "math_analysis.md",
        "output": "数学_{日期}_{题目}.html",
        "tasks": ["SVG画图形", "展示画图过程", "标注关键要素"]
    },

    # 步骤3: 分镜脚本
    {
        "step": 3,
        "name": "storyboard",
        "input": "HTML内容",
        "output": "{日期}_{题目}_分镜.md",
        "tasks": ["定义幕结构(不限制幕数)", "设计画面/字幕/读白", "音频清单(时长留空)"]
    },

    # 步骤4: TTS生成（含句级同步点）
    {
        "step": 4,
        "name": "generate_tts",
        "input": "分镜脚本",
        "output": "audio/audio_{三位幕号}_{幕名}.wav + audio_info.json(含sync_points)",
        "command": "python scripts/generate_tts.py audio_list.csv ./audio --voice xiaoxiao"
    },

    # 步骤5: 验证更新（含同步点摘要）
    {
        "step": 5,
        "name": "validate_audio",
        "input": "分镜.md + audio/",
        "output": "更新后的分镜.md(填充时长) + 同步点摘要(供步骤7参考)",
        "command": "python scripts/validate_audio.py 分镜.md ./audio",
        "check": ["音频存在性", "时长>0", "数量匹配", "sync_points完整性"]
    },

    # 步骤6: 脚手架
    {
        "step": 6,
        "name": "scaffold",
        "input": "分镜.md + audio_info.json(含sync_points)",
        "output": "script.py (伪代码框架)",
        "template": "templates/script_scaffold.py",
        "must_include": [
            "calculate_geometry() - 几何建模",
            "assert_geometry() - 几何验证(题目条件+精度) + 画布范围检查(边界+中心)",
            "COLORS - 颜色定义",
            "SCENES[] - 幕信息数组(从audio_info.json加载时长)",
            "start_scene_with_audio(scene_num) - 每幕起点（播放音频+记录起始时间）",
            "end_scene_with_audio(expected_duration, safety_margin=0.2) - 每幕收尾（自动补齐等待）",
            "wait_for_narration(keyword) - 等到读白说出关键词时刻再触发动画",
            "wait_until_scene_time(seconds) - 等到幕内指定时刻",
        ]
    },

    # 步骤7: 生成代码
    {
        "step": 7,
        "name": "implement",
        "input": "script.py脚手架 + 分镜.md + audio_info.json(含sync_points)",
        "output": "完整的script.py",
        "rules": [
            "根据分镜实现每幕动画",
            "使用 wait_for_narration(keyword) 对齐读白和高亮",
            "禁止 self.wait(max(..., duration - N)) 手动兜底",
            "画面时长由 end_scene_with_audio() 自动补齐",
            "calculate_geometry()必须完整实现"
        ]
    },

    # 步骤8: 检查与渲染
    {
        "step": 8,
        "name": "check_and_render",
        "input": "script.py",
        "output": "视频文件 + 关键帧截图",
        "command": "python scripts/render.py",
        "check": ["代码结构检查(check.py)", "几何正确性", "高亮同步", "字幕清晰", "动画流畅"],
        "on_fail": "回到步骤7修改代码"
    }
]

# 工作流状态转换
# step1 → step2 → step3 → step4 → step5 → step6 → step7 → step8
#                                          ↑____________↓ (失败时循环)
```

---

## 步骤1：分析题目，推导数学事实

**目标**：建立正确的数学计算方法和流程，形成画出符合数学的图形的方法。

### 输出格式
```markdown
## 数学事实分析

### 已知条件
- 条件1：...
- 条件2：...

### 推导的事实
1. **事实名称**: 描述
   - 计算过程: ...
   - 数学表达: ...

### 图形构建方法
- 点的坐标: ...
- 边的关系: ...
- 圆/弧的定义: ...

### 需要证明的结论
- 结论1: ...
```

**注意**：所有证明题需要证明的结论，在分镜中都可以作为已确立的**事实**来使用。

---

## 步骤2：HTML + SVG 可视化

**目标**：用 HTML + SVG 画出图形，展示画图过程和解答流程，为分镜做规划。
**补充**：如果用户已经提供了准确的HTML文件，描述了画图过程，可以按文件名要求复制一份，跳过生成文件。

### 输出要求
- 文件命名：`数学_{日期}_{题目简述}.html`
- 包含：题目陈述、SVG 图形、分步解答、关键要素标注
- SVG 需要展示**画图过程**（如：先画三角形 → 再画圆 → 标注点）

---

## 步骤3：生成分镜脚本

**目标**：定义视频结构，不限制幕数，结尾预留音频文件名（时长为空）。

### 文件命名
`{日期}_{题目}_分镜.md`

### 分镜脚本结构
```markdown
# 分镜脚本 - {题目名称}

## 分镜设计

### 第1幕：{幕名}
**画面**: ...
**字幕**: ...（简洁，≤20字）
**读白**: ...（详细，口语化，容易理解，适合普通学情的学生）
**动画**: ...
**目的**: ...

---

## 音频生成清单（步骤4填写）

| 幕号 | 文件名 | 读白文本 | 时长 | 说话人 | 情感 |
|------|--------|----------|------|--------|------|
| 1 | audio_001_{幕名}.wav | "读白文本" | | xiaoxiao | 热情 |
| 2 | audio_002_{幕名}.wav | "读白文本" | | xiaoxiao | 平和 |
```

### 关键规范
- 幕号从1开始连续编号
- 文件名格式：`audio_{三位幕号}_{幕名}.wav`
- **时长列为空**，由步骤5填充
- 不限制幕数，根据内容需要决定
- 每幕读白建议 1~3 句，每句 8~20 字，避免单幕文本过长导致动画拥挤
- 动作节奏采用「句子拍点」：每句读白对应 1~2 个核心动画，不要一口气堆叠大量 Create/Transform

### 动画描述：使用读白关键词锚点（重要）

分镜的**动画**部分使用 `@[关键词]` 锚定读白中的句子，步骤4 TTS 生成后会自动产生每句话的精确时间戳（sync_points），步骤7中代码通过 `wait_for_narration("关键词")` 精确对齐。

**不要写硬编码秒数**（如 `0.0s`, `3.0s`），因为 TTS 生成前无法预知准确时刻。

```markdown
**动画**:
- @[勾股定理]: 字幕"勾股定理"淡入
- @[正方形]: 正方形高亮 → 字幕退场
- @[所以]: 结论公式淡入，持续到幕末
```

**`@[关键词]` 规则**：
1. 关键词取自**读白文本**中某句话的特征词（2~6字）
2. 同一幕内关键词不要重复
3. 步骤5验证后，可在同步点摘要中确认每个关键词的实际时间
4. 如果某动画不需要对齐读白（如幕首淡入），可以省略锚点

### 字幕退场约定

为了避免动画中文字忘记退场，在**动画**部分使用退场标记：

**退场标记方式**（三选一）：
1. `→` 箭头符号表示退场（推荐，最简洁）
2. `退场:` 或 `淡出:` 显式标记
3. `持续X秒` 指定显示时长

**示例**：
```markdown
**动画**:
- @[正方形性质]: 字幕淡入，持续3秒 → 自动退场
- @[勾股定理]: 标题淡入 → @[所以] 时退场
- 幕末：所有文字退场
```

### 参考示例
见 `references/storyboard_sample.md` - 第九十九题：证明四点共圆

### 音画节奏预算（必填）

每一幕必须包含节奏预算（写在分镜的**动画**末尾）：

```markdown
**节奏预算**:
- 音频时长 D: ___s（步骤5回填）
- 读白句数: 3 句
- 核心动画数: 3 个（每句读白对应 1~2 个动画）
- 关键同步词: "三角形ABC", "内切圆", "切点"
```

**执行原则**：
- 单幕内重动画（Create/Transform 大对象）连续不超过 3 个
- 每个关键结论后至少留 `0.2~0.4s` 的视觉停顿
- 幕末收尾由 `end_scene_with_audio()` 自动补齐，不需要手动兜底
- **禁止** `self.wait(max(..., duration - N))` 模式

---

## 步骤4：TTS 生成语音文件（含句级同步点）

**使用脚本**：`scripts/generate_tts.py`（Edge TTS）

脚本通过 Edge TTS 的 `WordBoundary` 事件自动捕获每句话的起始时间，生成 `sync_points`。

### 执行命令
```bash
python scripts/generate_tts.py audio_list.csv ./audio --voice xiaoxiao
```

### 输出文件
```
audio/
├── audio_001_开场.wav
├── audio_002_展示图形.wav
├── audio_003_定理证明.wav
├── ...
└── audio_info.json          ← 含 sync_points
```

### audio_info.json 格式（含 sync_points）
```json
{
  "files": [
    {
      "scene": 1,
      "file": "audio_001_开场.wav",
      "duration": 8.5,
      "sync_points": [
        {"idx": 0, "text": "大家好，今天我们来讲解一道经典的平面几何问题", "time": 0.0},
        {"idx": 1, "text": "证明四点共圆", "time": 3.2},
        {"idx": 2, "text": "这道题综合运用了切线长定理和双曲线的性质", "time": 4.8}
      ]
    },
    {
      "scene": 2,
      "file": "audio_002_展示图形.wav",
      "duration": 15.2,
      "sync_points": [
        {"idx": 0, "text": "首先，我们来看题目给出的图形", "time": 0.0},
        {"idx": 1, "text": "三角形 ABC 的内切圆 I", "time": 2.1},
        {"idx": 2, "text": "三角形内一点 K", "time": 7.4}
      ]
    }
  ]
}
```

**sync_points 说明**：
- `idx`：句子在本幕中的序号（从 0 开始）
- `text`：句子前 40 字（用于关键词匹配）
- `time`：该句话在音频中的起始秒数（由 TTS WordBoundary 精确计算）
- 在步骤7中通过 `self.wait_for_narration("关键词")` 查找 text 包含关键词的条目

---

## 步骤5：验证音频并查看同步点

**使用脚本**：`scripts/validate_audio.py`

### 功能
1. 读取 `audio/audio_info.json` 获取音频时长
2. 验证所有音频文件存在且时长正常（>0秒）
3. 更新分镜脚本的"音频生成清单"中的时长列
4. **打印同步点摘要**：列出每幕的句级同步点及其时间戳
5. 如果缺少音频或时长异常，报错提醒

### 执行命令
```bash
python scripts/validate_audio.py 分镜.md ./audio
```

### 输出示例（含同步点摘要）
```
🎯 同步点摘要（用于 wait_for_narration）
==================================================

  第1幕 (8.5s):
     0.00s │ "大家好，今天我们来讲解一道经典的平面几何问题"
     3.20s │ "证明四点共圆"
     4.80s │ "这道题综合运用了切线长定理和双曲线的性质"

  第2幕 (15.2s):
     0.00s │ "首先，我们来看题目给出的图形"
     2.10s │ "三角形 ABC 的内切圆 I"
     7.40s │ "三角形内一点 K"
```

**此摘要是步骤7中选择 `wait_for_narration()` 关键词的依据。**

### 验证失败情况
- 缺少音频文件 → 报错："缺少第X幕音频文件"
- 时长为0或异常 → 报错："第X幕音频时长异常，请检查格式"
- 分镜与音频数量不匹配 → 报错："分镜X幕，音频Y个，数量不匹配"

---

## 步骤6：生成 script.py 脚手架

**使用模板**：`templates/script_scaffold.py`

**输出**：`script.py`（伪代码框架，由 AI 在步骤7完善）

### 脚手架核心方法一览

| 方法 | 作用 | 调用位置 |
|------|------|---------|
| `calculate_geometry()` | 几何建模 | construct() |
| `assert_geometry()` | 几何验证 + 画布范围 | construct() |
| `define_elements()` | 定义 Manim 图形对象 | construct() |
| `start_scene_with_audio(n)` | 播放音频 + 记录起始时间 | construct() 循环 |
| `end_scene_with_audio(d)` | 自动补齐等待 | construct() 循环 |
| `wait_for_narration(keyword)` | **等到读白说出关键词** | play_scene_X() |
| `wait_until_scene_time(sec)` | 等到幕内指定时刻 | play_scene_X() |
| `get_sync_time(keyword)` | 查找关键词时间（不等待） | play_scene_X() |

### 脚手架必须包含的部分

```python
from manim import *
import json
import os

class MathScene(Scene):
    """
    数学教学视频场景 - 脚手架
    根据分镜脚本和音频信息生成完整动画
    """

    # ========== 1. 颜色定义 ==========
    COLORS = {
        'background': '#1a1a2e',      # 深蓝背景
        'primary': '#4ecca3',          # 主色（青色）
        'secondary': '#e94560',        # 辅助色（红色）
        'highlight': '#ffc107',        # 高亮色（黄色）
        'text': '#ffffff',             # 文字白色
        'grid': '#2a2a4e',             # 网格线
    }

    # ========== 1b. 画布分区（防遮挡核心） ==========
    # 默认分区，可根据题目图形大小微调坐标，但必须保证各区互不重叠
    ZONES = {
        'title':    {'y_min': 3.0,  'y_max': 3.8,  'x_min': -6.5, 'x_max': 6.5,  'desc': '标题区（顶部）'},
        'geometry': {'y_min': -2.2, 'y_max': 2.8,  'x_min': -5.0, 'x_max': 3.0,  'desc': '几何图形主区域（中偏左）'},
        'subtitle': {'y_min': -3.8, 'y_max': -2.8, 'x_min': -6.5, 'x_max': 6.5,  'desc': '字幕区（底部）'},
        'formula':  {'y_min': -2.2, 'y_max': 2.8,  'x_min': 3.5,  'x_max': 6.5,  'desc': '公式/结论区（右侧）'},
    }

    # ========== 1c. z_index 层级定义（防遮挡核心） ==========
    # 数值越大越靠前（遮挡数值小的）
    Z_LAYERS = {
        'bg_grid':     0,   # 背景辅助线、网格
        'fill':        1,   # 填充色块（如三角形内部着色）
        'geometry':    2,   # 几何图形（线段、圆、多边形边框）
        'label':       3,   # 点标签、角标注（必须在图形之上）
        'highlight':   4,   # 高亮效果（闪烁、变色）
        'subtitle':    5,   # 字幕文字
        'formula':     5,   # 公式、推导步骤
        'title':       6,   # 标题
    }

    # ========== 2. 幕信息数组（供AI参考） ==========
    # 格式: (幕号, 幕名, 音频文件名, 时长秒数)
    # 注意：时长从 audio_info.json 读取，确保画面等待音频原则
    SCENES = [
        (1, "开场", "audio_001_开场.wav", None),
        (2, "展示图形", "audio_002_展示图形.wav", None),
        # ... 根据分镜动态生成
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 加载音频时长信息
        self.audio_timings = self._load_audio_timings()

    def _load_audio_timings(self):
        """从 audio_info.json 加载音频时长"""
        # TODO: AI实现 - 读取JSON并填充 SCENES 的时长
        pass

    # ========== 3. 几何计算函数 ==========
    def calculate_geometry(self):
        """
        计算所有几何元素的位置和属性

        从步骤2的HTML画图中提取信息，建立数学模型：
        - 所有点的坐标 (x, y) - ⚠️ 始终使用2D，z坐标始终为0
        - 边的长度和方程
        - 圆/弧的圆心和半径
        - 交点计算
        - 切线、法线等辅助线

        返回: dict 包含所有几何对象的数据
        """
        # TODO: AI根据题目几何关系实现
        geometry = {
            'points': {},      # {'A': (x, y), 'B': (x, y), ...}
            'lines': {},       # {'AB': {'start': A, 'end': B, 'length': L}, ...}
            'circles': {},     # {'circle1': {'center': O, 'radius': r}, ...}
            'arcs': {},        # 圆弧定义
        }
        return geometry

    # ========== 4. 几何验证函数 ==========
    def assert_geometry(self, geometry):
        """
        验证几何计算的正确性（最小验证原则）

        验证内容：
        1. 题目给定的事实（如：两条边相等，谁是谁的一半）
        2. 精度问题：使用相对误差比较，而非绝对相等
        3. 画布范围检查：确保图形在可视区域内
        4. 错误提示：所有assert必须用中文描述问题，包含具体数值和修复建议

        === 几何条件验证 ===
        基于题目给定的条件，编写最小但关键的验证：
        - 如果题目说 AB = BC，验证 |AB - BC| < epsilon
        - 如果题目说 E 是中点，验证 AE = EB（考虑浮点误差）
        - 如果题目说某角是直角，验证向量点积接近0
        - 如果题目给具体数值（如边长为5），验证计算结果匹配

        精度建议：
        - 相对误差：1e-6 或绝对误差 1e-4
        - 示例：assert abs(len_AB - len_BC) < 1e-4, "中文错误提示：AB长度不等于BC长度"

        === 画布范围验证算法 ===
        目标：确保整个图形在画布内，且位于视觉中心区域

        算法步骤（AI需要根据几何数据实现）：
        1. 计算所有几何元素的外接矩形 bounding_box
           - 遍历所有点、线、圆的边界点
           - 取最小x, 最大x, 最小y, 最大y

        2. 验证矩形在画布范围内（考虑边距）
           - 画布默认范围：FRAME_WIDTH=14.2, FRAME_HEIGHT=8
           - 建议边距：四周各留 0.5-1.0 单位
           - 验证：min_x > -7+margin 且 max_x < 7-margin
                   min_y > -4+margin 且 max_y < 4-margin

        3. 验证矩形中心在视觉中心区域
           - 画布中心：(0, 0)
           - 视觉中心区域：中心 ±20%（即 x∈[-1.4, 1.4], y∈[-0.8, 0.8]）
           - 计算矩形中心：(center_x, center_y) = ((min_x+max_x)/2, (min_y+max_y)/2)
           - 验证：center_x ∈ [-1.4, 1.4] 且 center_y ∈ [-0.8, 0.8]

        4. 如果图形超出范围，AI需要调整几何计算的缩放或平移
        """
        # === TODO: AI实现 - 基于题目条件的验证（失败时用中文报错）===
        # 示例代码（根据实际题目修改）：
        # epsilon = 1e-4
        # len_ab = geometry['lines']['AB']['length']
        # len_bc = geometry['lines']['BC']['length']
        # assert abs(len_ab - len_bc) < epsilon, f"几何验证失败：AB长度({len_ab:.4f})不等于BC长度({len_bc:.4f})，题目要求两边相等"
        #
        # len_ae = geometry['lines']['AE']['length']
        # len_ab = geometry['lines']['AB']['length']
        # assert abs(len_ae * 2 - len_ab) < epsilon, f"几何验证失败：E不是AB中点，AE({len_ae:.4f})*2={len_ae*2:.4f} != AB({len_ab:.4f})"

        # === TODO: AI实现 - 画布范围检查（失败时用中文报错）===
        # 1. 计算bounding_box
        #    all_points = list(geometry['points'].values())
        #    min_x = min(p[0] for p in all_points)
        #    max_x = max(p[0] for p in all_points)
        #    min_y = min(p[1] for p in all_points)
        #    max_y = max(p[1] for p in all_points)
        #
        # 2. 验证画布边界（失败时报具体数值）
        #    margin = 0.5
        #    assert min_x > -7 + margin, f"画布验证失败：图形左边界(min_x={min_x:.2f})超出安全区域(>{-7+margin})，需要向右平移或缩小"
        #    assert max_x < 7 - margin, f"画布验证失败：图形右边界(max_x={max_x:.2f})超出安全区域(<{7-margin})，需要向左平移或缩小"
        #    assert min_y > -4 + margin, f"画布验证失败：图形下边界(min_y={min_y:.2f})超出安全区域(>{-4+margin})，需要向上平移或缩小"
        #    assert max_y < 4 - margin, f"画布验证失败：图形上边界(max_y={max_y:.2f})超出安全区域(<{4-margin})，需要向下平移或缩小"
        #
        # 3. 验证视觉中心（失败时报具体偏移）
        #    center_x = (min_x + max_x) / 2
        #    center_y = (min_y + max_y) / 2
        #    assert -1.4 <= center_x <= 1.4, f"视觉中心验证失败：图形中心X={center_x:.2f}超出视觉中心区域[-1.4, 1.4]，建议调整几何计算使图形居中"
        #    assert -0.8 <= center_y <= 0.8, f"视觉中心验证失败：图形中心Y={center_y:.2f}超出视觉中心区域[-0.8, 0.8]，建议调整几何计算使图形居中"

        pass

    # ========== 5. 图形元素定义 ==========
    def define_elements(self, geometry):
        """
        定义 Manim 图形对象（但不创建动画）
        ⚠️ 必须遵守步骤7「防遮挡规范」：z_index层级、标签偏移、分区放置
        """
        # TODO: AI根据分镜需求定义
        elements = {
            'points': {},      # Mobject 点对象
            'lines': {},       # Mobject 线对象
            'circles': {},     # Mobject 圆对象
            'labels': {},      # 标签文字
        }
        return elements

    # ========== 6. 构造主流程 ==========
    def construct(self):
        """主构造流程"""
        # 计算几何
        geometry = self.calculate_geometry()
        self.assert_geometry(geometry)
        elements = self.define_elements(geometry)

        # 设置背景
        self.camera.background_color = self.COLORS['background']

        # 按幕执行
        for scene_num, scene_name, audio_file, duration in self.SCENES:
            self.play_scene(scene_num, scene_name, audio_file, duration, elements, geometry)

    def play_scene(self, scene_num, scene_name, audio_file, duration, elements, geometry):
        """
        播放单幕动画 - 必须与统一时间轴护栏配合

        ========== 音频集成（强制要求） ==========
        每幕必须添加对应的音频文件，否则视频将没有声音。
        但推荐在 construct() 中统一调用 start_scene_with_audio(scene_num)，
        不要在每个 play_scene_X() 里重复散落 add_sound 逻辑。

        统一入口：
            expected_duration = self.start_scene_with_audio(scene_num)
            self.play_scene_X(...)
            self.end_scene_with_audio(expected_duration, safety_margin=0.2)

        注意：
        - audio_file 参数已经包含文件名（如 "audio_001_开场.wav"）
        - 音频文件位于 audio/ 目录下
        - 不要手工估算“本幕动画共几秒”，以 self.time 实际耗时为准

        ========== 画面等待音频原则 ==========
        - 动画总时长由 end_scene_with_audio 自动兜底到 >= 音频时长
        - 可以画面多等待（多出静音部分，后期可剪辑）
        - 不能画面比音频短（会导致音频被截断）

        ========== 高亮规范（必须在读白提到时同步） ==========
        - 提到某个边等于某个边 → 用动画高亮两条边
        - 提到某个点/圆 → 闪烁或放大高亮
        - 提到证明结论 → 用框或颜色强调

        ========== 绘制策略 ==========
        - 简单图形：直接显示，然后高亮关键部分
        - 复杂图形：逐步绘制，边画边讲解
        """
        # TODO: AI实现 - 只写本幕视觉动作，音频起止由统一护栏方法负责
        pass

    # ========== 7. 同步对齐工具（核心新增） ==========
    def wait_until_scene_time(self, target_time):
        """等待到当前幕内指定时刻（相对于幕开始的秒数）"""
        # 脚手架已实现，见 templates/script_scaffold.py
        pass

    def wait_for_narration(self, keyword):
        """
        等到读白说出包含 keyword 的那句话时刻。
        从 audio_info.json 的 sync_points 中查找匹配。
        
        用法示例：
            self.wait_for_narration("内切圆")
            self.play(FadeIn(incircle))
        """
        # 脚手架已实现，见 templates/script_scaffold.py
        pass

    def get_sync_time(self, keyword):
        """查找关键词的时间戳（不等待），返回 float 或 None"""
        pass
```

---

## 步骤7：AI 生成最终代码

**输入**：
- 分镜脚本（已更新时长）
- `audio/audio_info.json`（含 sync_points）
- `script.py` 脚手架
- 步骤5输出的同步点摘要

**输出**：完整的 `script.py`

**AI 生成指导**：
1. 根据分镜的"动画"描述实现具体动画代码
2. **使用 `wait_for_narration("关键词")` 对齐读白和高亮**（参考步骤5的同步点摘要选择关键词）
3. 实现 `calculate_geometry()` 的具体计算
4. 实现 `assert_geometry()` 的验证逻辑
5. 为每幕实现 `play_scene_X()` 方法
6. **音频集成（必须，防重叠）**：
   - 在 `construct()` 的每幕循环中统一执行：
     - `expected_duration = self.start_scene_with_audio(scene_num)`
     - `play_scene_X(...)`
     - `self.end_scene_with_audio(expected_duration, safety_margin=0.2)`
   - `play_scene_X()` 内专注视觉动作，不手工累计总时长
7. 验证音频文件路径正确：`audio/audio_001_XXX.wav`
8. **字幕显示与退场（关键）**：
   - 使用 `show_subtitle_timed(text, duration)` 或 `show_subtitle_with_audio(text, audio_duration)`
   - 分镜中的 `→` 或 `退场:` 标记表示文字退场
   - **必须确保所有文字元素都有退场动画**

### 禁止事项（步骤7）

| 禁止 | 替代方案 |
|------|---------|
| `self.wait(max(..., duration - N))` | 删除手动兜底，由 `end_scene_with_audio()` 自动补齐 |
| 硬编码 `self.wait(3.7)` 对齐读白 | 使用 `self.wait_for_narration("关键词")` |
| 在 `play_scene_X()` 中调用 `add_sound()` | 由 `start_scene_with_audio()` 统一管理 |
| 手动估算 `animation_time` 判断切幕 | 由 `end_scene_with_audio()` 自动处理 |

### 防遮挡规范（步骤7必须遵守）

动画元素相互遮挡是最常见的视觉问题。以下规则**必须严格执行**。

#### 规则1：画布分区 — 不同类型元素各归其位

脚手架中的 `ZONES` 定义了默认分区（可根据题目微调坐标，但**必须保证各区互不重叠**）：

| 区域 | 放置内容 | 核心约束 |
|------|---------|---------|
| **标题区**（顶部） | 幕标题 | 幕切换时替换旧标题 |
| **几何区**（中偏左） | 图形、点、线、圆、标签 | 主图形区，偏左留出右侧公式空间 |
| **字幕区**（底部） | 字幕文字 | 字幕**必须**在底部（y ≈ -3.3），**禁止**放画布中央 |
| **公式区**（右侧） | 公式、推导、结论 | **禁止**与几何图形重叠；图形偏右时可将公式区换到左侧 |

#### 规则2：z_index 层级 — 每个 Mobject 必须设置

使用脚手架 `Z_LAYERS` 常量，创建后**立即**调用 `set_z_index()`：

```python
line_AB = Line(A, B, color=WHITE)
line_AB.set_z_index(self.Z_LAYERS['geometry'])     # 层级2

label_A = Text("A", font_size=28).next_to(dot_A, UR, buff=0.15)
label_A.set_z_index(self.Z_LAYERS['label'])         # 层级3，在线段之上
# ❌ 忘记 set_z_index → 标签可能被后绘制的线段遮挡
```

**层级从后到前**：背景(0) → 填充(1) → 几何(2) → 标签(3) → 高亮(4) → 字幕/公式(5) → 标题(6)

#### 规则3：点标签防碰撞

1. **方向偏移**：`next_to(dot, 方向, buff=0.15~0.25)`，**禁止**把标签放在点的精确坐标
2. **方向选择**：标签朝远离密集线段/元素的方向（如三角形内角处标签朝外）
3. **背景衬底**：标签可能与线段接近时，加 `label.add_background_rectangle(color=bg_color, opacity=0.85, buff=0.06)`
4. **间距检查**：两标签间距 < 0.3 时，调整方向或增大 buff

#### 规则4：元素生命周期 — 及时退场防堆叠

```python
# 字幕：必须配对退场
self.play(FadeIn(subtitle))
self.wait_for_narration("关键词")
self.play(FadeOut(subtitle))          # ❌ 漏掉这行 → 字幕堆叠

# 公式替换：先退旧再入新
self.play(FadeOut(old_formula), FadeIn(new_formula))

# 高亮：不再需要时恢复原色（如果需要持续高亮则可保留，但确保不遮挡后续元素）
self.play(line_AB.animate.set_color(YELLOW))
# ...讲解完毕后...
self.play(line_AB.animate.set_color(WHITE))
```

**幕末清理**：每幕结束前，将不需要带入下一幕的元素统一 FadeOut。

#### 规则5：同区域冲突预防

1. **多公式纵向排列**：`VGroup(...).arrange(DOWN, buff=0.3)`
2. **字幕排队**：多条字幕**依次显示**（先退场再入场），禁止同时可见
3. **同一位置禁止堆叠** 2 个及以上可见文字元素

---

## 步骤8：代码检查与渲染

### 8.1 代码结构检查（必须）

**使用脚本**：`scripts/check.py`

在渲染之前，必须先检查代码是否包含必要的函数和结构：

```bash
# 检查 script.py（默认）
python scripts/check.py

# 检查指定文件
python scripts/check.py my_script.py
```

**检查内容**：
1. ✅ `calculate_geometry()` - 几何计算函数是否存在
2. ✅ `assert_geometry()` - 几何验证函数是否存在
3. ✅ `define_elements()` - 图形元素定义函数是否存在
4. ✅ 字幕类 `Subtitle` / `TitleSubtitle` 是否存在
5. ✅ 是否有 `add_sound()` 调用（音频集成）
6. ✅ 是否有继承 `Scene` 的类
7. ✅ 是否使用了 `wait_for_narration()` 或 `wait_until_scene_time()` 同步方法
8. ✅ 是否存在 `self.wait(max(..., duration - N))` 反模式
9. ⚠️ 防遮挡（需人工审查代码）：Mobject 是否设置了 `set_z_index()`、字幕是否在底部、字幕是否配对 FadeOut、标签是否用 `next_to()` 偏移

**检查结果**：
- ❌ 错误：必须修复，否则无法渲染
- ⚠️ 警告：建议修复，但不会阻止渲染

### 8.2 渲染视频

#### 方式1：使用渲染脚本（推荐，包含检查）

```bash
# 完整流程：检查 -> 渲染 -> 拷贝到根目录
python scripts/render.py

# 指定文件和场景
python scripts/render.py -f script.py -s MathScene

# 指定渲染质量
python scripts/render.py -q h    # 1080p60 (默认)
python scripts/render.py -q k    # 4K
python scripts/render.py -q m    # 720p30

# 跳过检查（不推荐，仅用于快速测试）
python scripts/render.py --no-check
```

#### 方式2：直接使用 manim（跳过检查，不推荐）

```bash
manim -pqh script.py MathScene
```

### 提取关键帧验证
```bash
python scripts/extract_frames.py media/videos/script/1080p60/MathScene.mp4 --interval 5
```

### 验证内容
1. 几何图形是否正确（点、线、圆位置）
2. 高亮是否与讲解同步
3. 字幕是否清晰可读
4. 动画是否流畅
5. **防遮挡检查**（关键帧逐帧确认）：
   - 点标签是否被线段/圆弧遮挡？
   - 字幕是否与几何图形重叠？
   - 多个文字元素是否堆叠在同一位置？
   - 公式/结论是否侵入几何区域？
5. **音频是否正确添加**：
   - 每幕都有声音（没有静音幕）
   - 音频与分镜中的读白内容一致
   - 每幕末 `elapsed >= audio_duration + safety_margin`（没有抢跑切幕）
   - 没有出现上一幕音频未结束就进入下一幕的重叠

### 渲染后必须执行
```python
# 在construct()最后添加：拷贝视频到根目录
import shutil
import os
from pathlib import Path

# 渲染完成后拷贝到根目录
video_src = Path("media/videos/script/1920p60/SquareTriangleProblem.mp4")
video_dst = Path("最终视频.mp4")
if video_src.exists():
    shutil.copy2(video_src, video_dst)
    print(f"✓ 视频已拷贝到: {video_dst}")
```

**规则：渲染完成后必须将视频拷贝到项目根目录**，不要留在media/深处。

### 如果发现问题
- 回到步骤7修改代码
- 重新渲染验证

---

## 数学解题原则（绝对重要）

### ❌ 禁止使用坐标系
**绝不用坐标系来求解**，应该用各种定义和推理。

**错误示例**（坐标法）：
```
设B=(0,0), C=(5,0), A=(1.8, 2.4)...
面积 = ½ × 底 × 高
```

**正确示例**（几何推理）：
```
1. 由勾股定理：BC = √(AB² + AC²) = 5
2. 正方形性质：BE = BC = 5
3. 等积变换：S△ABE = S△ABC × (EB/BC) × sin(∠ABE)/sin(∠ABC)
4. 或用向量叉积、海伦公式等纯几何方法
```

**允许的可视化辅助**：
- 为了动画展示可以显示坐标，但解题过程不能用坐标计算
- 可以用几何画板的思路：旋转、平移、对称等变换

### 推荐的几何推理方法
1. **等积变换** - 同底等高、等底同高
2. **相似三角形** - 比例关系
3. **勾股定理** - 边长关系
4. **向量/叉积** - 纯几何意义的运算
5. **旋转/对称** - 几何变换

---

## 文件结构

```
tutor/
├── SKILL.md                          # 本文件 - 工作流程定义
├── requirements.txt                  # Python 依赖
├── references/
│   └── storyboard_sample.md          # 分镜脚本示例（参考）
├── templates/
│   └── script_scaffold.py            # Manim 脚手架模板（含字幕类）
├── scripts/
│   ├── generate_tts.py               # TTS 生成脚本
│   ├── validate_audio.py             # 音频验证脚本
│   ├── check.py                      # 代码结构检查脚本（渲染前必执行）
│   └── render.py                     # 渲染流水线脚本（检查+渲染+拷贝）
└── sample/                           # 示例项目（保留参考）
    └── geometry_proof/
```

---

## 依赖管理

使用 `uv` 管理依赖：

```bash
# 创建虚拟环境
uv venv .venv

# 安装依赖
uv pip install -r requirements.txt

# 激活环境
source .venv/bin/activate
```

---

## 绕过LaTeX依赖（重要）

Manim默认需要LaTeX来渲染数学公式。如果不想安装LaTeX，**全部使用Text替代MathTex**：

```python
# ❌ 需要LaTeX
MathTex(r"BC^2 = AB^2 + AC^2")
MathTex(r"\frac{1}{2} \times 5")
MathTex("A")  # 甚至连字母都需要LaTeX

# ✅ 不需要LaTeX
Text("BC² = AB² + AC²", font_size=36)
Text("½ × 5", font_size=30)
Text("A", font_size=32)  # 用Text直接显示字母
```

**常用替换对照表**：

| 数学符号 | LaTeX写法 | 无LaTeX写法 |
|---------|----------|------------|
| 上标 | `x^2` | `x²` (直接输入Unicode) |
| 分数 | `\frac{1}{2}` | `½` 或 `1/2` |
| 度数 | `90^\circ` | `90°` |
| 平方厘米 | `\text{cm}^2` | `cm²` |
| 根号 | `\sqrt{25}` | `√25` |
| 角度 | `\angle A` | `∠A` |

**脚手架默认不使用MathTex**，如需数学公式请直接输入Unicode字符。

---

## 关键原则总结

| 原则 | 说明 |
|------|------|
| **数学先行** | 先建立正确的数学模型，再画图 |
| **音频必填** | 每幕必须调用 `self.add_sound()`，否则视频无声音 |
| **句级同步** | 使用 `wait_for_narration("关键词")` 精确对齐读白和高亮（精度 ±0.3s） |
| **高亮对应** | 配音提到什么，画面高亮什么 |
| **自动补齐** | 幕末由 `end_scene_with_audio()` 自动补齐，禁止 `duration - N` 手动兜底 |
| **最小验证** | `assert_geometry` 验证题目条件(带精度) + 画布范围(边界+中心) |
| **防遮挡** | 画布分区(标题/几何/字幕/公式) + z_index层级 + 标签偏移 + 及时退场 |
| **逐步抽象** | 从 HTML 可视化 → 分镜脚本 → Manim 代码 |
