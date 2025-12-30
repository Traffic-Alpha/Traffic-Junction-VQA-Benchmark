#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VQA数据可视化工具 - 将JSONL格式转换为美观的HTML页面
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import argparse


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """加载JSONL文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"   ⚠️ 警告: 第 {line_num} 行解析失败: {e}")
                continue
    return data


def get_task_name(filename: str) -> str:
    """从文件名提取任务名称"""
    return filename.replace('.jsonl', '').replace('_', ' ').title()


def generate_html_header() -> str:
    """生成HTML头部"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic VQA Benchmark - 数据可视化</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .header .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-card .number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-card .label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .task-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            transition: transform 0.3s ease;
        }
        
        .task-section:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        }
        
        .task-header {
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        
        .task-title {
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .task-meta {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            color: #666;
            font-size: 0.95em;
        }
        
        .task-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .badge {
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .qa-item {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .qa-item:hover {
            background: #e9ecef;
            border-left-width: 6px;
        }
        
        .qa-number {
            background: #667eea;
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .question {
            font-size: 1.15em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        
        .question-text {
            flex: 1;
            line-height: 1.5;
        }
        
        .answer {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 2px solid #e0e0e0;
        }
        
        .answer-label {
            font-weight: 600;
            color: #28a745;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .answer-label::before {
            content: "✓";
            background: #28a745;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
        }
        
        .answer-text {
            color: #495057;
            line-height: 1.6;
        }
        
        .options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 12px;
            margin: 15px 0;
        }
        
        .option {
            background: white;
            padding: 12px 15px;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .option:hover {
            border-color: #667eea;
            transform: translateX(5px);
        }
        
        .option.correct {
            border-color: #28a745;
            background: #d4edda;
        }
        
        .option-key {
            display: inline-block;
            width: 28px;
            height: 28px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .option.correct .option-key {
            background: #28a745;
        }
        
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
        }
        
        .metadata-item {
            font-size: 0.9em;
            color: #6c757d;
        }
        
        .metadata-item strong {
            color: #495057;
            display: block;
            margin-bottom: 3px;
        }
        
        .capabilities {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        
        .capability-tag {
            background: #e7f1ff;
            color: #004085;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            border: 1px solid #b8daff;
        }
        
        .images-container {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }
        
        .image-item {
            flex: 1;
            min-width: 250px;
            max-width: 500px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .image-display {
            width: 100%;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .image-display:hover {
            border-color: #667eea;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
            transform: scale(1.02);
        }
        
        .image-path {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 5px;
            color: #495057;
            font-size: 0.85em;
            word-break: break-all;
            border-left: 3px solid #667eea;
        }
        
        .image-error {
            background: #fff3cd;
            border: 2px dashed #ffc107;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
            color: #856404;
        }
        
        .toc {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .toc h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        
        .toc ul {
            list-style: none;
        }
        
        .toc li {
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
            transition: all 0.3s ease;
        }
        
        .toc li:last-child {
            border-bottom: none;
        }
        
        .toc li:hover {
            background: #f8f9fa;
            padding-left: 20px;
        }
        
        .toc a {
            color: #495057;
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .toc a:hover {
            color: #667eea;
        }
        
        .item-count {
            background: #e7f1ff;
            color: #004085;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .options {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-template-columns: 1fr;
            }
        }
        
        .back-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            text-decoration: none;
            font-size: 1.5em;
        }
        
        .back-to-top:hover {
            background: #764ba2;
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <div class="container">
"""


def generate_html_footer() -> str:
    """生成HTML尾部"""
    return """
    </div>
    <a href="#top" class="back-to-top">↑</a>
    <script>
        // 点击选项高亮显示
        document.querySelectorAll('.option').forEach(option => {
            option.addEventListener('click', function() {
                this.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 200);
            });
        });
        
        // 返回顶部按钮
        window.addEventListener('scroll', function() {
            const backToTop = document.querySelector('.back-to-top');
            if (window.pageYOffset > 300) {
                backToTop.style.display = 'flex';
            } else {
                backToTop.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""


def generate_task_html(filename: str, data: List[Dict[str, Any]], task_id: int) -> str:
    """生成单个任务的HTML"""
    if not data:
        return ""
    
    task_name = get_task_name(filename)
    first_item = data[0]
    
    html = f"""
        <div class="task-section" id="task-{task_id}">
            <div class="task-header">
                <div class="task-title">
                    <span>📋</span>
                    <span>{task_name}</span>
                    <span class="badge">{len(data)} 条数据</span>
                </div>
                <div class="task-meta">
                    <span>📁 <strong>文件:</strong> {filename}</span>
                    <span>🏷️ <strong>类别:</strong> {first_item.get('category', 'N/A')}</span>
                    <span>📊 <strong>任务:</strong> {first_item.get('task', 'N/A')}</span>
                    <span>🎯 <strong>子任务:</strong> {first_item.get('subtask', 'N/A')}</span>
                </div>
            </div>
"""
    
    for idx, item in enumerate(data, 1):
        # 问题
        question = item.get('question', '')
        answer = item.get('answer', '')
        options = item.get('options', {})
        correct_answer = item.get('correct_answer', '')
        capabilities = item.get('capabilities', [])
        
        # 图片路径
        image_path = item.get('image_path', '')
        images = item.get('images', [])
        bev_image = item.get('bev_image', '')
        view_image = item.get('view_image', '')
        reference_images = item.get('reference_images', [])
        option_images = item.get('option_images', [])
        
        html += f"""
            <div class="qa-item">
                <div class="question">
                    <span class="qa-number">{idx}</span>
                    <span class="question-text">{question}</span>
                </div>
"""
        
        # 根据不同类型显示问题相关图片
        # 1. BEV to View: 只显示BEV图
        if bev_image:
            html += """
                <div class="images-container">
"""
            html += f"""
                    <div class="image-item">
                        <img src="{bev_image}" alt="BEV Image" class="image-display" 
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" 
                             loading="lazy">
                        <div class="image-error" style="display:none;">
                            ⚠️ 图片加载失败<br>
                            <small>请检查图片路径是否正确</small>
                        </div>
                        <div class="image-path">📁 {bev_image}</div>
                    </div>
"""
            html += """
                </div>
"""
        # 2. View to BEV: 只显示View图
        elif view_image:
            html += """
                <div class="images-container">
"""
            html += f"""
                    <div class="image-item">
                        <img src="{view_image}" alt="View Image" class="image-display" 
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" 
                             loading="lazy">
                        <div class="image-error" style="display:none;">
                            ⚠️ 图片加载失败<br>
                            <small>请检查图片路径是否正确</small>
                        </div>
                        <div class="image-path">📁 {view_image}</div>
                    </div>
"""
            html += """
                </div>
"""
        # 3. Temporal Between: 只显示参考图片（2张）
        elif reference_images:
            html += """
                <div class="images-container">
"""
            for ref_idx, ref_img in enumerate(reference_images, 1):
                html += f"""
                    <div class="image-item">
                        <img src="{ref_img}" alt="Reference Image {ref_idx}" class="image-display" 
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" 
                             loading="lazy">
                        <div class="image-error" style="display:none;">
                            ⚠️ 图片加载失败<br>
                            <small>请检查图片路径是否正确</small>
                        </div>
                        <div class="image-path">📁 {ref_img}</div>
                    </div>
"""
            html += """
                </div>
"""
        # 4. 普通单图或多图
        elif image_path or (images and not option_images):
            html += """
                <div class="images-container">
"""
            if image_path:
                html += f"""
                    <div class="image-item">
                        <img src="{image_path}" alt="VQA Image" class="image-display" 
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" 
                             loading="lazy">
                        <div class="image-error" style="display:none;">
                            ⚠️ 图片加载失败<br>
                            <small>请检查图片路径是否正确</small>
                        </div>
                        <div class="image-path">📁 {image_path}</div>
                    </div>
"""
            elif images:
                for img_idx, img in enumerate(images, 1):
                    html += f"""
                    <div class="image-item">
                        <img src="{img}" alt="VQA Image {img_idx}" class="image-display" 
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" 
                             loading="lazy">
                        <div class="image-error" style="display:none;">
                            ⚠️ 图片加载失败<br>
                            <small>请检查图片路径是否正确</small>
                        </div>
                        <div class="image-path">📁 {img}</div>
                    </div>
"""
            html += """
                </div>
"""
        
        # 选项
        if options:
            html += """
                <div class="options">
"""
            for key_idx, key in enumerate(sorted(options.keys())):
                value = options[key]
                is_correct = key == correct_answer
                correct_class = ' correct' if is_correct else ''
                
                # 如果有选项图片，只显示图片+字母标签，不显示文字
                if option_images and key_idx < len(option_images):
                    option_img = option_images[key_idx]
                    html += f"""
                    <div class="option{correct_class}" style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                        <img src="{option_img}" alt="Option {key}" class="image-display" 
                             style="max-width: 200px;"
                             onerror="this.style.display='none';" 
                             loading="lazy">
                        <div class="option-key" style="margin: 0;">{key}</div>
                    </div>
"""
                else:
                    html += f"""
                    <div class="option{correct_class}">
                        <span class="option-key">{key}</span>
                        <span>{value}</span>
                    </div>
"""
            html += """
                </div>
"""
        
        # 答案
        if answer:
            html += f"""
                <div class="answer">
                    <div class="answer-label">正确答案 ({correct_answer})</div>
                    <div class="answer-text">{answer}</div>
                </div>
"""
        
        # 元数据
        metadata_items = []
        for key, value in item.items():
            if key not in ['question', 'answer', 'options', 'correct_answer', 
                          'capabilities', 'image_path', 'images', 'category', 
                          'task', 'subtask']:
                metadata_items.append((key, value))
        
        if metadata_items or capabilities:
            html += """
                <div class="metadata">
"""
            for key, value in metadata_items:
                html += f"""
                    <div class="metadata-item">
                        <strong>{key}:</strong> {value}
                    </div>
"""
            html += """
                </div>
"""
            
            if capabilities:
                html += """
                <div class="capabilities">
                    <strong style="width: 100%; color: #495057;">所需能力:</strong>
"""
                for cap in capabilities:
                    html += f"""
                    <span class="capability-tag">💡 {cap}</span>
"""
                html += """
                </div>
"""
        
        html += """
            </div>
"""
    
    html += """
        </div>
"""
    
    return html


def generate_statistics(all_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """生成统计信息"""
    total_items = sum(len(data) for data in all_data.values())
    total_files = len(all_data)
    
    categories = set()
    tasks = set()
    
    for data in all_data.values():
        for item in data:
            if 'category' in item:
                categories.add(item['category'])
            if 'task' in item:
                tasks.add(item['task'])
    
    return {
        'total_items': total_items,
        'total_files': total_files,
        'total_categories': len(categories),
        'total_tasks': len(tasks)
    }


def visualize_vqa_dataset(dataset_dir: str, output_file: str = None):
    """
    可视化VQA数据集
    
    Args:
        dataset_dir: JSONL文件所在目录
        output_file: 输出HTML文件路径，默认为 dataset_dir/vqa_visualization.html
    """
    dataset_path = Path(dataset_dir)
    
    if output_file is None:
        output_file = dataset_path / 'vqa_visualization.html'
    
    # 查找所有JSONL文件
    jsonl_files = sorted(dataset_path.glob('*.jsonl'))
    
    if not jsonl_files:
        print(f"❌ 在 {dataset_dir} 目录下没有找到JSONL文件")
        return
    
    print(f"📁 找到 {len(jsonl_files)} 个JSONL文件")
    
    # 加载所有数据
    all_data = {}
    for jsonl_file in jsonl_files:
        filename = jsonl_file.name
        print(f"📖 加载: {filename}")
        data = load_jsonl(jsonl_file)
        all_data[filename] = data
        print(f"   ✓ 加载了 {len(data)} 条数据")
    
    # 生成统计信息
    stats = generate_statistics(all_data)
    
    # 开始生成HTML
    html_content = generate_html_header()
    
    # 添加头部
    html_content += f"""
        <div class="header" id="top">
            <h1>🚦 Traffic VQA Benchmark</h1>
            <p class="subtitle">交通视觉问答基准数据集 - 数据可视化</p>
            <div class="stats">
                <div class="stat-card">
                    <div class="number">{stats['total_items']}</div>
                    <div class="label">总问题数</div>
                </div>
                <div class="stat-card">
                    <div class="number">{stats['total_files']}</div>
                    <div class="label">数据文件</div>
                </div>
                <div class="stat-card">
                    <div class="number">{stats['total_categories']}</div>
                    <div class="label">问题类别</div>
                </div>
                <div class="stat-card">
                    <div class="number">{stats['total_tasks']}</div>
                    <div class="label">任务类型</div>
                </div>
            </div>
        </div>
"""
    
    # 添加目录
    html_content += """
        <div class="toc">
            <h2>📚 目录导航</h2>
            <ul>
"""
    for idx, (filename, data) in enumerate(all_data.items(), 1):
        task_name = get_task_name(filename)
        html_content += f"""
                <li>
                    <a href="#task-{idx}">
                        <span>{task_name}</span>
                        <span class="item-count">{len(data)} 条</span>
                    </a>
                </li>
"""
    html_content += """
            </ul>
        </div>
"""
    
    # 添加每个任务的内容
    for idx, (filename, data) in enumerate(all_data.items(), 1):
        html_content += generate_task_html(filename, data, idx)
    
    # 添加尾部
    html_content += generate_html_footer()
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ 可视化文件已生成: {output_file}")
    print(f"📊 共生成 {stats['total_items']} 个问答对的可视化")
    print(f"💡 在浏览器中打开该文件即可查看")


def main():
    parser = argparse.ArgumentParser(
        description='将VQA JSONL数据转换为美观的HTML可视化页面',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 可视化benchmark_dataset目录下的所有JSONL文件
  python visualize_vqa_data.py benchmark_dataset
  
  # 指定输出文件
  python visualize_vqa_data.py benchmark_dataset -o my_visualization.html
  
  # 使用绝对路径
  python visualize_vqa_data.py /path/to/dataset -o /path/to/output.html
        """
    )
    
    parser.add_argument(
        'dataset_dir',
        type=str,
        help='包含JSONL文件的数据集目录'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出HTML文件路径（默认: dataset_dir/vqa_visualization.html）'
    )
    
    args = parser.parse_args()
    
    visualize_vqa_dataset(args.dataset_dir, args.output)


if __name__ == '__main__':
    main()

