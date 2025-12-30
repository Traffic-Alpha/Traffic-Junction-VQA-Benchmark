# Traffic VQA Benchmark 生成总结

生成时间: 2025-12-29  
作者: AI Assistant

## 项目概述

本项目从已生成的交通场景 VQA 问题中进行采样，创建了一个标准化的 benchmark 数据集，用于评估多模态大模型在交通场景理解任务上的性能。

## 数据来源

- **源数据路径**: `/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier`
- **输出路径**: `/mnt/petrelfs/wangmaonan/traffic_vqa_benchmark/benchmark_dataset`
- **采样范围**: Timestep 100-550
- **随机种子**: 42

## 生成的文件

### 1. 主要脚本

| 文件名 | 说明 |
|--------|------|
| `sample_benchmark.py` | 主采样脚本，负责从源数据中采样问题并生成 benchmark |
| `sample_utils.py` | 辅助工具类，包含问题分类、过滤和图片复制功能 |
| `validate_benchmark.py` | 验证脚本，检查 benchmark 数据集的完整性和正确性 |
| `example_use_benchmark.py` | 使用示例，展示如何加载和使用 benchmark 数据集 |

### 2. Benchmark 数据集

位置: `benchmark_dataset/`

```
benchmark_dataset/
├── images/                          # 所有图片 (592张)
│   ├── 100/high_quality_rgb/
│   ├── 101/high_quality_rgb/
│   └── ...
├── l1.1_obj_q1_vehicle_count.jsonl        # 15 questions
├── l1.1_obj_q2_special_vehicle_exist.jsonl # 10 questions
├── l1.1_obj_q3_special_vehicle_type.jsonl  # 10 questions
├── l1.1_obj_q4_special_event_exist.jsonl   # 10 questions
├── l1.1_obj_q5_special_event_type.jsonl    # 10 questions
├── l1.2_topo_q1_incoming_lanes_count.jsonl # 11 questions
├── l1.2_topo_q2_outgoing_lanes_count.jsonl # 11 questions
├── l1.2_topo_q5_incoming_vehicles.jsonl    # 20 questions
├── l1.2_topo_q6_outgoing_vehicles.jsonl    # 20 questions
├── l1.2_topo_q8_special_vehicle_lane.jsonl # 11 questions
├── l1.2_topo_q9_special_event_lane.jsonl   # 11 questions
├── l2.1_view_q1_most_vehicles.jsonl        # 8 questions
├── l2.1_view_q2_special_vehicle_location.jsonl # 8 questions
├── l2.1_view_q4_bev_to_view.jsonl          # 8 questions
├── l2.1_view_q5_view_to_bev.jsonl          # 8 questions
├── l2.2_time_q1_temporal_order.jsonl       # 10 questions
├── l2.2_time_q3_temporal_between.jsonl     # 10 questions
├── l3_dec_q1_phase_most_vehicles.jsonl     # 5 questions
├── l3_dec_q2_phase_accident.jsonl          # 5 questions
├── l3_dec_q3_phase_special_vehicle.jsonl   # 5 questions
├── l3_dec_q4_phase_green_light.jsonl       # 5 questions
├── l3_dec_q5_phase_decision.jsonl          # 5 questions
├── README.md                                # 详细说明文档
└── statistics.json                          # 统计信息
```

## 数据集统计

### 总体统计

- **总问题数**: 216 / 240 (90.0%)
- **总图片数**: 592 张（物理文件）
- **引用图片数**: 374 张（唯一图片）
- **JSONL 文件**: 22 个
- **问题类型**: 22 种

### 按级别统计

| 级别 | 采样数量 | 目标数量 | 完成率 | 状态 |
|------|---------|---------|--------|------|
| **L1.1 Obj** (目标级感知) | 55 | 50 | 110.0% | ✓ 超额完成 |
| **L1.2 Topo** (交通结构理解) | 84 | 99 | 84.8% | ✗ 缺失 15 |
| **L2.1 View** (多视角空间一致性) | 32 | 40 | 80.0% | ✗ 缺失 8 |
| **L2.2 Time** (跨时间理解) | 20 | 26 | 76.9% | ✗ 缺失 6 |
| **L3 Dec** (决策支持) | 25 | 25 | 100.0% | ✓ 完成 |

### 按类别统计

| 类别 | 问题数量 |
|------|---------|
| Vehicle Analysis | 63 |
| Special Vehicles | 39 |
| Special Events | 31 |
| Road Infrastructure | 22 |
| Traffic Phase Analysis | 20 |
| Temporal Reasoning | 20 |
| Scene Understanding | 16 |
| Comprehensive Analysis | 5 |

### 按任务类型统计

| 任务类型 | 问题数量 |
|---------|---------|
| Single Image | 139 |
| Multi Image | 41 |
| Cross-Timestep Multi Image | 36 |

## 未采样到的问题类型

以下问题类型在原始 VQA 生成过程中未被生成，需要后续补充：

1. **L1.2 Q3**: 进口道有多少直行/右转的车道 (目标: 2个)
2. **L1.2 Q4**: 特定车道的功能 (目标: 2个)
3. **L1.2 Q7**: 特定车道上有多少车 (目标: 11个)
4. **L2.1 Q3**: 选出不同view的图片 (目标: 8个)
5. **L2.2 Q2**: 判断排队趋势 (目标: 6个)
6. **L2.2 Q4**: 多帧识别车道功能 (目标: 10个)

**总计缺失**: 39 个问题

## 采样策略

### 1. 问题分类

通过 `QuestionFilter` 类根据问题的 `category`、`task`、`subtask` 和 `question_type` 字段进行自动分类。

### 2. 特殊过滤

- **特殊车辆问题**: 确保答案中包含特殊车辆（police, ambulance, fire truck）
- **特殊事件问题**: 确保答案中包含特殊事件（barrier, collision, accident）

### 3. 随机采样

- 对于可用问题数量超过目标数量的类型，进行随机采样
- 对于可用问题数量少于目标数量的类型，使用所有可用问题
- 使用固定随机种子 (42) 确保可重现性

### 4. 图片管理

- 自动复制所有引用的图片到 `images/` 目录
- 保持原有的目录结构
- 自动更新问题中的图片路径

## 使用方法

### 快速开始

```python
from example_use_benchmark import BenchmarkLoader

# 初始化加载器
loader = BenchmarkLoader("/path/to/benchmark_dataset")

# 加载问题
questions = loader.load_questions('l1.1_obj_q1_vehicle_count')

# 加载问题及图片
for q in questions:
    q_with_images = loader.load_question_with_images(q)
    # 处理问题和图片
```

### 评估示例

```python
# 加载所有问题
all_questions = loader.load_all_questions()

# 对每个问题类型进行评估
for q_type, questions in all_questions.items():
    for q in questions:
        # 调用模型预测
        predicted = your_model(q['question'], q['image_path'])
        
        # 检查答案
        is_correct = (predicted == q['correct_answer'])
```

详细使用方法请参考 `example_use_benchmark.py`。

## JSONL 格式说明

每个 `.jsonl` 文件的每一行是一个 JSON 对象，包含以下字段：

### 必需字段

- `question`: 问题文本
- `answer`: 完整答案文本
- `options`: 选项字典 (A, B, C, D)
- `correct_answer`: 正确选项 (A/B/C/D)
- `category`: 问题类别
- `task`: 任务类型
- `subtask`: 子任务类型
- `capabilities`: 所需能力列表

### 图片字段 (根据问题类型不同而不同)

- `image_path`: 单张图片路径 (单图问题)
- `images`: 多张图片路径列表 (多图问题)
- `bev_image`: BEV 图片路径 (BEV 相关问题)
- `view_image`: View 图片路径 (View 相关问题)
- `option_images`: 选项图片列表 (图片选择题)
- `reference_images`: 参考图片列表 (时序问题)

### 元数据字段

- `direction`: 方向编号 (0/1/2)
- `timestep`: 时间步
- `question_type`: 问题类型标识符

## 验证结果

运行 `validate_benchmark.py` 的验证结果：

```
✓ Total Questions: 216
✓ Total Images Referenced: 374
✓ Total Image Files: 592
✓ Missing Images: 0
✓ JSONL Files: 22
✓ All referenced images exist
```

所有数据完整性检查均已通过。

## 后续工作建议

1. **补充缺失的问题类型**: 在 VQA 生成器中添加以下问题类型的生成逻辑：
   - 车道功能相关问题 (L1.2 Q3, Q4, Q7)
   - 不同视角识别问题 (L2.1 Q3)
   - 排队趋势分析问题 (L2.2 Q2)
   - 多帧车道功能识别 (L2.2 Q4)

2. **扩展数据集**: 如果需要更多问题，可以：
   - 扩大采样范围（当前为 timestep 100-550）
   - 从其他场景中采样
   - 增加每个问题类型的采样数量

3. **质量控制**: 对采样的问题进行人工审核，确保：
   - 问题表述清晰
   - 答案准确无误
   - 图片质量良好

4. **评估基准**: 使用多个基线模型在 benchmark 上进行评估，建立性能基准。

## 文件清单

### 代码文件

- ✓ `sample_benchmark.py` - 主采样脚本
- ✓ `sample_utils.py` - 辅助工具类
- ✓ `validate_benchmark.py` - 验证脚本
- ✓ `example_use_benchmark.py` - 使用示例

### 文档文件

- ✓ `BENCHMARK_SUMMARY.md` - 本文件（项目总结）
- ✓ `benchmark_dataset/README.md` - 数据集说明文档
- ✓ `benchmark_dataset/statistics.json` - 统计信息

### 数据文件

- ✓ 22 个 JSONL 文件 (216 个问题)
- ✓ 592 张图片文件

## 运行命令

```bash
# 1. 生成 benchmark
cd /mnt/petrelfs/wangmaonan/traffic_vqa_benchmark
python sample_benchmark.py

# 2. 验证 benchmark
python validate_benchmark.py

# 3. 查看使用示例
python example_use_benchmark.py
```

## 依赖项

```
- Python 3.7+
- PIL (Pillow)
- json (标准库)
- pathlib (标准库)
- shutil (标准库)
- random (标准库)
```

## 许可和使用

本 benchmark 数据集基于原始交通场景 VQA 数据生成，用于研究和评估目的。

---

生成完成时间: 2025-12-29  
数据集版本: v1.0  
状态: ✓ 已完成并通过验证

