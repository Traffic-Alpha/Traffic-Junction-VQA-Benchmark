# Traffic VQA Benchmark

交通场景视觉问答（Visual Question Answering）数据集和基准测试工具，用于大型多模态模型的微调和评估。

## 📋 目录

- [项目简介](#项目简介)
- [快速开始](#快速开始)
- [完整流程](#完整流程)
  - [步骤0：准备工作](#步骤0准备工作)
  - [步骤1：生成VQA数据](#步骤1生成vqa数据)
  - [步骤2：采样Benchmark数据集](#步骤2采样benchmark数据集)
  - [步骤3：可视化和验证](#步骤3可视化和验证)
- [VQA问题类型](#vqa问题类型)
- [数据格式](#数据格式)
- [模型测试与评估](#模型测试与评估)
- [项目结构](#项目结构)
- [安装依赖](#安装依赖)

---

## 📖 项目简介

本项目基于交通仿真数据，自动生成高质量的视觉问答数据集，用于评估多模态大模型在交通场景理解中的能力。

### 核心特性

- ✅ **多层次问题**：涵盖感知、理解、推理和决策四个层次
- ✅ **多种问题类型**：包括单图VQA、多图VQA、跨时间推理、跨视角匹配等
- ✅ **标准化格式**：支持选择题（MCQ）格式，便于自动评估
- ✅ **完整工具链**：从数据生成、采样、可视化到模型测试的完整流程
- ✅ **高质量数据**：基于真实交通仿真，包含丰富的交通场景和车辆信息

### 数据集制作流程

1. 运行交通仿真，生成场景数据
2. 更新 `global.json` 中的必要信息（相位映射、动作信息等）
3. 使用本工具自动生成 VQA 问题
4. 从生成的问题中采样构建 Benchmark 数据集
5. 可视化验证数据质量
6. 使用 Benchmark 测试评估模型性能

---

## 🚀 快速开始

如果您已有准备好的交通场景数据，可以按照以下三步快速生成 Benchmark：

```bash
# 步骤1：生成 VQA 数据（需要先配置场景路径）
python quick_generate_vqa.py

# 步骤2：采样 Benchmark 数据集（需要先配置源路径和输出路径）
python quick_sample_benchmark.py

# 步骤3：可视化验证结果
python quick_visualize_vqa_data.py benchmark_dataset
```

详细步骤请参考 [完整流程](#完整流程) 章节。

---

## 📝 完整流程

### 步骤0：准备工作

在生成 VQA 数据之前，需要确保 `global.json` 文件包含必要的信息。

#### 0.1 更新 `can_perform_action` 字段

运行 `quick_update_global_info.py` 脚本来更新 `global.json` 中的 `can_perform_action` 字段：

```bash
python quick_update_global_info.py global.json --backup
```

**功能说明**：
- 该脚本会分析场景数据，标记哪些时间步可以进行决策动作
- 结果保存在 `global.json` 的 `can_perform_action` 字段中

#### 0.2 添加 `index2phase` 映射信息

在 `global.json` 中手动添加或更新 `index2phase` 字段，建立图片索引与交通相位的对应关系。该配置只在 easy 模式下使用，可以快速定位相位和图片之间的关系。**示例**：
```json
{
     "index2phase": {
          "0": 2,
          "1": 3,
          "2": 0,
          "3": 1
     },
}
```

#### 0.3 添加 `phaseInfo` 相位信息

在 `global.json` 中添加 `phaseInfo` 字段，描述每个交通相位的详细信息。**示例**：

```json
{
  "phaseInfo": "Phase 0: All lanes of Image 2;\nPhase 1: All lanes of Image 3;\nPhase 2: All lanes of Image 0;\nPhase 3: All lanes of Image 1;\n",
}
```

---

### 步骤1：生成VQA数据

使用 `quick_generate_vqa.py` 为每个 timestep 生成不同类型的 VQA 问题。

#### 1.1 配置场景路径

编辑 `quick_generate_vqa.py`，设置您的场景路径和观测距离：

```python
# 场景路径
scene_path = "/path/to/your/scene/data"

# 定义观测距离映射（需要区分 incoming 和 outgoing）
distance_mapping = {
    0: {'incoming': 65, 'outgoing': 40},  # 方向0的可视范围（米）
    1: {'incoming': 65, 'outgoing': 40},  # 方向1的可视范围（米）
    2: {'incoming': 65, 'outgoing': 40},  # 方向2的可视范围（米）
}
```

**参数说明**：
- `scene_path`: 交通场景数据的根目录
- `distance_mapping`: 每个方向的可视距离（米）
  - `incoming`: 进口车道的观测距离
  - `outgoing`: 出口车道的观测距离

#### 1.2 运行生成脚本

```bash
python quick_generate_vqa.py
```

#### 1.3 生成结果

脚本会为每个 timestep 生成以下文件：

```
scene_name/
├── 0/                              # timestep 0
│   ├── annotations/                # 标注数据
│   │   ├── 0.json                  # 方向 0 的标注
│   │   ├── 1.json                  # 方向 1 的标注
│   │   └── 2.json                  # 方向 2 的标注
│   ├── high_quality_rgb/           # 高质量图片
│   │   ├── 0.png                   # 方向 0 的图片
│   │   ├── 1.png                   # 方向 1 的图片
│   │   ├── 2.png                   # 方向 2 的图片
│   │   └── bev.png                 # 鸟瞰图
│   ├── step_info.json              # 时间步信息
│   └── VQA/                        # 生成的VQA数据
│       ├── single_image_vqa/       # 单图问答
│       │   ├── 0.json
│       │   ├── 1.json
│       │   └── 2.json
│       ├── multi_image_vqa.json    # 多图问答
│       └── all_vqa.json            # 所有问答
├── 10/                             # timestep 10
│   └── ...
└── ...
```

**文件说明**：
- `single_image_vqa/`: 针对单个方向图像的 VQA 问题
- `multi_image_vqa.json`: 需要多个图像的 VQA 问题（比较、推理等）
- `all_vqa.json`: 该 timestep 所有 VQA 问题的汇总

---

### 步骤2：采样Benchmark数据集

使用 `quick_sample_benchmark.py` 从生成的 VQA 问题中采样，构建标准化的 Benchmark 数据集。

#### 2.1 配置路径

编辑 `quick_sample_benchmark.py`，设置源数据路径和输出路径：

```python
# 配置路径
source_root = "/path/to/your/scene/data"  # VQA 数据源根目录
output_root = "/path/to/benchmark_dataset"  # benchmark 输出目录

# 创建生成器
generator = BenchmarkGenerator(
    source_root=source_root,
    output_root=output_root,
    timestep_range=(100, 550),  # 采样的 timestep 范围
    random_seed=42              # 随机种子，保证可复现
)
```

#### 2.2 采样配置

脚本内置了标准的采样配置，根据问题类型定义采样数量：

```python
sampling_config = {
    # L1.1 Obj - 目标级感知
    'l1.1_obj_q1_vehicle_count': 15,
    'l1.1_obj_q2_special_vehicle_exist': 10,
    'l1.1_obj_q3_special_vehicle_type': 10,
    # ... 更多配置
}
```

您可以根据需要修改每个问题类型的采样数量。

#### 2.3 运行采样脚本

```bash
python quick_sample_benchmark.py
```

#### 2.4 采样结果

脚本会在 `output_root` 目录下生成：

```
benchmark_dataset/
├── images/                                  # 复制的图片文件
│   ├── 536/
│   │   └── 1.png
│   └── ...
├── l1.1_obj_q1_vehicle_count.jsonl         # 按问题类型组织的数据文件
├── l1.1_obj_q2_special_vehicle_exist.jsonl
├── l1.2_topo_q1_incoming_lanes_count.jsonl
├── l2.1_view_q1_most_vehicles.jsonl
├── l2.2_time_q1_temporal_order.jsonl
├── l3_dec_q1_phase_most_vehicles.jsonl
└── ...
```

**特点**：
- ✅ 按问题类型分类保存为独立的 JSONL 文件
- ✅ 自动复制相关图片到 `images/` 目录
- ✅ 更新图片路径为相对路径
- ✅ 平衡采样（如存在性问题会平衡"有"和"没有"的样本）

---

### 步骤3：可视化和验证

使用 `quick_visualize_vqa_data.py` 生成美观的可视化页面，方便人工检查数据质量。

#### 3.1 生成HTML可视化

```bash
python quick_visualize_vqa_data.py benchmark_dataset
```

**输出文件**：`benchmark_dataset/vqa_visualization.html`

#### 3.2 查看可视化结果

**使用本地 HTTP 服务器**：

```bash
cd benchmark_dataset
python -m http.server 8000
```

然后在浏览器中访问：`http://localhost:8000/vqa_visualization.html`

**简单方式**：
直接双击 `vqa_visualization.html` 文件在浏览器中打开（某些浏览器可能因安全策略限制图片显示）。


#### 3.3. 打包数据集下载

如需将数据集打包以便下载或分发，可以使用以下命令：

```bash
# 打包整个 benchmark_dataset 目录（包含所有数据和图片）
zip -r traffic_vqa_benchmark.zip benchmark_dataset/

# 仅打包 JSONL 数据文件（不含图片，体积更小）
zip -r traffic_vqa_data_only.zip benchmark_dataset/*.jsonl benchmark_dataset/*.html
```

#### 3.5 可视化特性

HTML 页面包含以下功能：

- 🎨 **美观界面**：紫色渐变主题，卡片式布局
- 🖼️ **图片展示**：直接显示 VQA 图片，支持悬停放大
- 📊 **统计面板**：显示数据集整体统计信息
- 📚 **目录导航**：快速跳转到任意问题类型
- ✅ **高亮答案**：正确选项以绿色标记
- 🔝 **返回顶部**：浮动按钮快速返回页面顶部
- 📱 **响应式设计**：自适应不同屏幕尺寸

#### 3.6 人工验证检查清单

在可视化页面中，重点检查以下内容：

- [ ] **问题表述**：是否清晰、准确、无歧义
- [ ] **选项设置**：选项是否合理，干扰项是否有效
- [ ] **答案正确性**：正确答案是否准确
- [ ] **图片匹配**：图片与问题是否对应
- [ ] **元数据完整性**：类别、任务类型等信息是否完整
- [ ] **能力标签**：所需能力标签是否合理

发现问题后，可以直接修改对应的 JSONL 文件，然后重新生成可视化页面验证。

---

## 🎯 VQA问题类型

本 Benchmark 涵盖多个层次的问题类型：

### L1.1 - 目标级感知（Object-level Perception）

测试模型对基本交通目标的识别和计数能力。

| 问题类型 | 描述 | 样本数 |
|---------|------|--------|
| q1_vehicle_count | 统计图片中的车辆总数 | 15 |
| q2_special_vehicle_exist | 判断是否存在特殊车辆（警车、救护车等） | 10 |
| q3_special_vehicle_type | 识别特殊车辆的类型 | 10 |
| q4_special_event_exist | 判断是否存在特殊事件（事故、障碍物等） | 10 |
| q5_special_event_type | 识别特殊事件的类型 | 10 |

### L1.2 - 交通结构理解（Topology Understanding）

测试模型对道路拓扑结构和车辆分布的理解能力。

| 问题类型 | 描述 | 样本数 |
|---------|------|--------|
| q1_incoming_lanes_count | 统计进口车道总数 | 11 |
| q2_outgoing_lanes_count | 统计出口车道总数 | 11 |
| q3_lane_function_count | 统计不同功能车道的数量 | 2 |
| q4_lane_function | 识别特定车道的功能 | 2 |
| q5_incoming_vehicles | 统计进口车道上的车辆数 | 20 |
| q6_outgoing_vehicles | 统计出口车道上的车辆数 | 20 |
| q7_lane_vehicles | 统计特定车道上的车辆数 | 11 |
| q8_special_vehicle_lane | 定位特殊车辆所在的车道 | 11 |
| q9_special_event_lane | 定位特殊事件影响的车道 | 11 |

### L2.1 - 多视角空间一致性（Multi-view Spatial Consistency）

测试模型在不同视角间的空间理解和匹配能力。

| 问题类型 | 描述 | 样本数 |
|---------|------|--------|
| q1_most_vehicles | 比较多个方向，找出车辆最多的方向 | 8 |
| q2_special_vehicle_location | 在多个方向中定位特殊车辆 | 8 |
| q3_different_view | 匹配不同视角的同一场景 | 8 |
| q4_bev_to_view | 从BEV图匹配对应的方向图 | 8 |
| q5_view_to_bev | 从方向图匹配对应的BEV图 | 8 |

### L2.2 - 跨时间理解（Temporal Understanding）

测试模型对时间序列变化的理解和推理能力。

| 问题类型 | 描述 | 样本数 |
|---------|------|--------|
| q1_temporal_order | 对多个时间点的图片进行排序 | 10 |
| q2_queue_trend | 分析队列长度的变化趋势 | 6 |
| q3_temporal_between | 判断给定图片在时间序列中的位置 | 10 |
| q4_lane_function_multi | 跨时间分析车道功能 | 10 |

### L3 - 决策支持（Decision Support）

测试模型基于视觉信息进行交通决策的能力。

| 问题类型 | 描述 | 样本数 |
|---------|------|--------|
| q1_phase_most_vehicles | 基于车辆数量推荐相位 | 5 |
| q2_phase_accident | 考虑事故情况的相位决策 | 5 |
| q3_phase_special_vehicle | 考虑特殊车辆的相位决策 | 5 |
| q4_phase_green_light | 基于当前绿灯状态的相位决策 | 5 |
| q5_phase_decision | 综合多因素的相位决策 | 5 |

---

## 📊 数据格式

### 单图 VQA 格式

```json
{
  "question": "How many incoming lanes are there in total?",
  "answer": "There are a total of 3 incoming lanes.",
  "options": {
    "A": "1",
    "B": "2",
    "C": "3",
    "D": "4"
  },
  "correct_answer": "C",
  "category": "Road Infrastructure",
  "task": "Single Image",
  "subtask": "Counting",
  "capabilities": ["Lane Detection", "Spatial Understanding"],
  "image_path": "images/536/0.png",
  "direction": 0,
  "timestep": "536"
}
```

### 多图 VQA 格式

```json
{
  "question": "Which direction shows the most vehicles?",
  "answer": "Direction 0 shows the most vehicles with 5 vehicles visible.",
  "options": {
    "A": "Direction 0",
    "B": "Direction 1",
    "C": "Direction 2"
  },
  "correct_answer": "A",
  "category": "Vehicle Analysis",
  "task": "Multi Image",
  "subtask": "Comparison",
  "capabilities": ["Object Detection", "Cross-Image Comparison"],
  "images": [
    "images/536/0.png",
    "images/536/1.png",
    "images/536/2.png"
  ],
  "timestep": "536"
}
```

### 跨视角匹配格式（BEV ↔ View）

```json
{
  "question": "Given the BEV (bird's-eye view) from timestep 100, which directional view (direction 0) corresponds to this BEV?",
  "options": {
    "A": "The view from timestep 50",
    "B": "The view from timestep 100",
    "C": "The view from timestep 150",
    "D": "The view from timestep 200"
  },
  "correct_answer": "B",
  "answer_text": "The view from timestep 100",
  "bev_image": "images/100/bev.png",
  "option_images": [
    "images/50/0.png",
    "images/100/0.png",
    "images/150/0.png",
    "images/200/0.png"
  ],
  "images": [
    "images/100/bev.png",
    "images/50/0.png",
    "images/100/0.png",
    "images/150/0.png",
    "images/200/0.png"
  ],
  "target_timestep": "100",
  "direction": "0",
  "question_type": "bev_to_view"
}
```

### JSONL 文件格式

Benchmark 数据集以 JSONL（JSON Lines）格式保存，每行是一个独立的 JSON 对象：

```jsonl
{"question": "...", "answer": "...", "options": {...}, "correct_answer": "A", ...}
{"question": "...", "answer": "...", "options": {...}, "correct_answer": "B", ...}
{"question": "...", "answer": "...", "options": {...}, "correct_answer": "C", ...}
```

---

## 🧪 模型测试与评估

### 测试工具简介

项目提供了完整的模型测试工具，支持通过 OpenAI API 格式评估多模态模型性能。

测试工具位于 `benchmark_test/` 目录下：

- `vqa_example.py`: 简单测试，快速验证
- `vqa_full_test.py`: 完整测试，支持批量测试和结果保存
- `vqa_compare_models.py`: 模型对比测试，生成对比报告
- `list_api_models.py`: 列出可用的 API 模型

### 快速测试

#### 1. 安装依赖

```bash
pip install openai -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2. 配置 API

编辑测试脚本，配置您的 API 信息：

```python
# API 配置
api_key = "your-api-key"
base_url = "http://your-api-server:port/v1"
model_name = "gpt-4o"  # 或其他模型名称

# 数据路径
vqa_data_path = "benchmark_dataset/l1.1_obj_q1_vehicle_count.jsonl"
base_path = "benchmark_dataset/"
```

#### 3. 运行测试

**简单测试**（随机选择几个问题）：
```bash
python benchmark_test/vqa_example.py
```

**完整测试**（批量测试并保存结果）：
```bash
python benchmark_test/vqa_full_test.py
```

**模型对比测试**：
```bash
python benchmark_test/vqa_compare_models.py
```

### 评估指标

- **总体准确率（Overall Accuracy）**：所有问题的准确率
- **任务类型准确率**：单图 VQA 和多图 VQA 的分别准确率
- **类别准确率**：各个类别的准确率
- **子任务准确率**：各个子任务的准确率

### 测试结果示例

```
============================================================
📊 评估结果
============================================================

总体准确率: 75.50% (163/216)

任务类型准确率:
  - 单图 VQA: 78.20% (125/160)
  - 多图 VQA: 67.86% (38/56)

按类别准确率:
  - Road Infrastructure: 82.00% (41/50)
  - Vehicle Analysis: 75.00% (45/60)
  - Special Vehicles: 70.00% (28/40)
  - Special Events: 72.00% (18/25)
  - Decision Support: 76.00% (19/25)
```

详细使用说明请参考 [`benchmark_test/README.md`](benchmark_test/README.md)。

---

## 📁 项目结构

```
traffic_vqa_benchmark/
├── parse_infos/                      # 核心解析和生成模块
│   ├── single_image_vqa.py           # 单图 VQA 生成器
│   ├── multi_image_vqa.py            # 多图 VQA 生成器
│   ├── cross_timestep_vqa.py         # 跨时间 VQA 生成器
│   └── parse_direction_infos.py      # 方向信息解析
│
├── benchmark_utils/                  # Benchmark 采样工具
│   ├── question_filter.py            # 问题分类和过滤
│   ├── image_copier.py               # 图片复制和路径更新
│   └── benchmark_sampler.py          # 采样器
│
├── benchmark_test/                   # 模型测试工具
│   ├── vqa_example.py                # 简单测试示例
│   ├── vqa_full_test.py              # 完整批量测试
│   ├── vqa_compare_models.py         # 模型对比测试
│   └── README.md                     # 测试工具说明
│
├── benchmark_dataset/                # 采样后的 Benchmark 数据集
│   ├── images/                       # 图片文件
│   ├── *.jsonl                       # 按问题类型分类的数据文件
│   └── vqa_visualization.html        # 可视化页面
│
├── generate_vqa_dataset.py           # VQA 数据集生成器（主类）
├── quick_generate_vqa.py             # 快速生成 VQA 数据（步骤1）
├── quick_sample_benchmark.py         # 快速采样 Benchmark（步骤2）
├── quick_visualize_vqa_data.py       # 快速可视化（步骤3）
├── update_global_info.py             # 更新 global.json 信息
│
├── requirements.txt                  # Python 依赖
├── README.md                         # 本文件
└── TODO.md                           # 开发待办事项
```

---

## 👥 贡献者

- WANG Maonan
- JIANG Kemou
- ZOU Xinchen
- HUANG ZhengYan

---

**祝使用愉快！** 🎉

