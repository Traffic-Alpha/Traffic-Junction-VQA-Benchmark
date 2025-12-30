# VQA Benchmark 测试工具

本目录包含用于测试 VQA (Visual Question Answering) 数据集的工具脚本，支持使用 OpenAI API 对单图和多图 VQA 进行评估。

## 📁 文件说明

- `vqa_example.py`: 简单测试脚本，快速验证 API 连接和基本功能
- `vqa_full_test.py`: 完整测试脚本，支持批量测试、准确率计算和结果保存
- `vqa_compare_models.py`: 模型对比测试脚本，支持多个模型的性能对比和报告生成
- `list_api_models.py`: 列出可用的 API 模型
- `results/`: 测试结果保存目录
- `README.md`: 本说明文档

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install openai -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 运行简单测试

简单测试会随机选择几个 VQA 问题进行测试，快速验证功能是否正常：

```bash
python benchmark_test/vqa_example.py
```

**输出示例：**
```
============================================================
VQA Benchmark - 简单测试
============================================================

📂 加载 VQA 数据: .../all_vqa.json
✅ 加载成功，共 38 条数据

📸 测试单图 VQA
------------------------------------------------------------

[1] 问题: How many incoming lanes are there in total?
    类别: Road Infrastructure - Counting
    正确答案: D - There are a total of 3 incoming lanes.
    模型回答: D: 3
```

### 3. 运行完整测试

完整测试支持批量测试、准确率统计和结果保存：

```bash
python benchmark_test/vqa_full_test.py
```

**输出示例：**
```
============================================================
VQA Benchmark - 完整测试
============================================================

📊 开始批量测试，共 10 条数据
------------------------------------------------------------

[1/10] 测试中...
  类别: Road Infrastructure - Counting
  任务: Single Image
  ✅ 预测: D | 正确: D

...

============================================================
📊 评估结果
============================================================

总体准确率: 80.00% (8/10)

任务类型准确率:
  - 单图 VQA: 80.00% (10 条)
  - 多图 VQA: 0.00% (0 条)

按类别准确率:
  - Road Infrastructure: 50.00% (1/2)
  - Vehicle Analysis: 66.67% (2/3)
  - Special Vehicles: 100.00% (3/3)
  - Special Events: 100.00% (2/2)
```

### 4. 运行模型对比测试

对比多个模型在同一数据集上的表现：

```bash
python benchmark_test/vqa_compare_models.py
```

**输出示例：**
```
============================================================
🔍 模型对比测试
============================================================

[1/2] 测试模型: GPT-4o
[2/2] 测试模型: Qwen-VL-Max

============================================================
📊 模型对比结果
============================================================

总体准确率对比:
1. GPT-4o              : 80.00% (8/10)
2. Qwen-VL-Max         : 70.00% (7/10)

单图 VQA 准确率对比:
1. GPT-4o              : 80.00% (10 条)
2. Qwen-VL-Max         : 70.00% (10 条)
```

模型对比测试会自动生成：
- JSON 格式的详细结果文件
- Markdown 格式的对比报告

## 🔧 配置说明

### API 配置

在脚本中修改以下参数：

```python
# API 配置
api_key = "your-api-key"
base_url = "http://your-api-server:port/v1"
model_name = "gpt-4o"  # 或其他模型名称
```

### 测试数据路径

```python
# VQA 数据文件路径
vqa_data_path = "/path/to/vqa/all_vqa.json"

# 图片基础路径（通常是 VQA 数据的上级目录）
base_path = "/path/to/timestep_dir/"
```

### 测试样本数量

在 `vqa_full_test.py` 中可以限制测试样本数量：

```python
# 测试前 10 条数据
results = tester.batch_test(vqa_data, base_path, max_samples=10)

# 测试全部数据
results = tester.batch_test(vqa_data, base_path, max_samples=None)
```

### 模型对比配置

在 `vqa_compare_models.py` 中配置多个模型进行对比：

```python
models_config = [
    {
        'api_key': 'your-api-key-1',
        'base_url': 'http://server1:port/v1',
        'model_name': 'gpt-4o',
        'display_name': 'GPT-4o'
    },
    {
        'api_key': 'your-api-key-2',
        'base_url': 'http://server2:port/v1',
        'model_name': 'qwen-vl-max',
        'display_name': 'Qwen-VL-Max'
    },
    # 添加更多模型...
]
```

## 📊 测试结果

测试结果会自动保存到 `results/` 目录下，文件名格式为：`vqa_test_results_YYYYMMDD_HHMMSS.json`

### 结果文件结构

```json
{
  "model": "gpt-4o",
  "test_time": "2025-12-19 15:11:49",
  "metrics": {
    "overall_accuracy": 0.8,
    "correct_count": 8,
    "total_count": 10,
    "single_image_accuracy": 0.8,
    "single_image_count": 10,
    "multi_image_accuracy": 0.0,
    "multi_image_count": 0,
    "category_accuracy": {
      "Road Infrastructure": {
        "correct": 1,
        "total": 2,
        "accuracy": 0.5
      },
      ...
    }
  },
  "results": [
    {
      "question": "...",
      "predicted_answer": "...",
      "predicted_option": "D",
      "correct_option": "D",
      "answer_text": "...",
      "options": {...},
      "is_correct": true,
      "category": "Road Infrastructure",
      "subtask": "Counting",
      "task": "Single Image",
      "image_path": "..."
    },
    ...
  ]
}
```

## 📝 VQA 数据格式

### 单图 VQA

```json
{
  "question": "How many incoming lanes are there in total?",
  "answer": "There are a total of 3 incoming lanes.",
  "options": {
    "A": "5",
    "B": "2",
    "C": "1",
    "D": "3"
  },
  "correct_answer": "D",
  "category": "Road Infrastructure",
  "task": "Single Image",
  "subtask": "Counting",
  "capabilities": ["Lane Detection", "Spatial Understanding"],
  "image_path": "high_quality_rgb/0.png",
  "direction": 0,
  "timestep": "535"
}
```

### 多图 VQA

```json
{
  "question": "Which direction has the most vehicles?",
  "answer": "Image indices 0, 1 have the same number of vehicles.",
  "options": {
    "A": "Image Index 0",
    "B": "Image Index 1",
    "C": "Image Index 2"
  },
  "correct_answer": "A",
  "category": "Vehicle Analysis",
  "task": "Multi Image",
  "subtask": "Counting",
  "capabilities": ["Object Detection", "Cross-Image Comparison"],
  "images": [
    "high_quality_rgb/0.png",
    "high_quality_rgb/1.png",
    "high_quality_rgb/2.png"
  ],
  "timestep": "535"
}
```

## 🎯 支持的任务类型

### 单图 VQA
- **道路基础设施 (Road Infrastructure)**
  - 进出口车道数量统计
  - 车道配置分析

- **车辆分析 (Vehicle Analysis)**
  - 车辆数量统计
  - 车辆分布分析

- **特殊车辆 (Special Vehicles)**
  - 特殊车辆存在性判断
  - 特殊车辆识别
  - 特殊车辆定位

- **特殊事件 (Special Events)**
  - 事故/障碍物存在性判断
  - 事件类型识别
  - 事件定位

### 多图 VQA
- **比较类问题**
  - 车辆数量比较
  - 特殊车辆定位
  - 特殊事件定位

- **推理类问题**
  - 交通流模式分析
  - BEV 与方向图关系
  - 跨视角推理

## 🔍 评估指标

- **总体准确率 (Overall Accuracy)**: 所有问题的准确率
- **任务类型准确率**: 单图 VQA 和多图 VQA 的分别准确率
- **类别准确率**: 各个类别（Road Infrastructure, Vehicle Analysis 等）的准确率
- **子任务准确率**: 各个子任务（Counting, Localization 等）的准确率

## 📞 使用示例

### 测试单个 VQA 问题

```python
from vqa_full_test import VQABenchmarkFullTest

# 创建测试实例
tester = VQABenchmarkFullTest(
    api_key="your-api-key",
    base_url="http://your-api-server:port/v1",
    model_name="gpt-4o"
)

# 单图 VQA
vqa_item = {
    "question": "How many incoming lanes are there?",
    "options": {"A": "2", "B": "3", "C": "4", "D": "5"},
    "correct_answer": "B",
    "image_path": "high_quality_rgb/0.png"
}

result = tester.test_single_image_vqa(vqa_item, "/path/to/base")
print(f"预测: {result['predicted_option']}, 正确答案: {result['correct_option']}")
```

### 批量测试

```python
# 加载数据
with open('all_vqa.json', 'r') as f:
    vqa_data = json.load(f)

# 批量测试
results = tester.batch_test(vqa_data, base_path, max_samples=50)

# 计算指标
metrics = tester.calculate_metrics(results)

# 打印结果
tester.print_metrics(metrics)

# 保存结果
tester.save_results(results, metrics, "results.json")
```

### 模型对比测试

```python
from vqa_compare_models import VQAModelComparison

# 配置多个模型
models_config = [
    {
        'api_key': 'key1',
        'base_url': 'http://server1:port/v1',
        'model_name': 'gpt-4o',
        'display_name': 'GPT-4o'
    },
    {
        'api_key': 'key2',
        'base_url': 'http://server2:port/v1',
        'model_name': 'qwen-vl-max',
        'display_name': 'Qwen-VL-Max'
    }
]

# 创建对比测试
comparator = VQAModelComparison(models_config)

# 加载数据
with open('all_vqa.json', 'r') as f:
    vqa_data = json.load(f)

# 对比测试
all_results = comparator.compare_models(vqa_data, base_path, max_samples=50)

# 打印对比结果
comparator.print_comparison(all_results)

# 保存结果
comparator.save_comparison(all_results, "comparison.json")

# 生成报告
comparator.generate_comparison_report(all_results, "comparison.md")
```

## ⚠️ 注意事项

1. **API 密钥安全**: 请不要将 API 密钥提交到版本控制系统
2. **图片路径**: 确保图片路径正确，相对路径基于 `base_path`
3. **测试规模**: 大规模测试可能需要较长时间和API调用费用
4. **错误处理**: 脚本会自动处理 API 调用失败的情况

## 📈 性能优化建议

1. **并行测试**: 可以实现多线程/多进程并行调用 API
2. **缓存结果**: 对已测试的问题进行缓存，避免重复调用
3. **批量测试**: 根据 API 限制调整批次大小
4. **断点续传**: 保存中间结果，支持从断点继续测试

## 🐛 常见问题

### Q: ModuleNotFoundError: No module named 'openai'
A: 请先安装 openai 库：`pip install openai`

### Q: 图片不存在错误
A: 检查 `base_path` 和 `image_path` 的组合是否正确

### Q: API 调用失败
A: 检查 API 密钥、base_url 和网络连接

### Q: 准确率为 0
A: 检查答案提取逻辑是否正确匹配模型输出格式

## 📄 许可证

请参考项目根目录的许可证文件。

