"""
Author: WANG Maonan
Description: VQA 模型对比测试 - 对比多个模型在相同数据集上的表现
"""
import os
import json
from typing import List, Dict
from datetime import datetime
from vqa_full_test import VQABenchmarkFullTest


class VQAModelComparison:
    """VQA 模型对比类"""
    
    def __init__(self, models_config: List[Dict]):
        """
        初始化模型对比
        
        Args:
            models_config: 模型配置列表，每个配置包含 api_key, base_url, model_name
        """
        self.models_config = models_config
        self.testers = []
        
        # 为每个模型创建测试实例
        for config in models_config:
            tester = VQABenchmarkFullTest(
                api_key=config['api_key'],
                base_url=config['base_url'],
                model_name=config['model_name']
            )
            self.testers.append({
                'name': config.get('display_name', config['model_name']),
                'tester': tester,
                'config': config
            })
    
    def compare_models(self, vqa_data: List[dict], base_path: str, max_samples: int = None) -> Dict:
        """
        对比多个模型
        
        Args:
            vqa_data: VQA 数据列表
            base_path: 图片基础路径
            max_samples: 最大测试样本数
            
        Returns:
            包含所有模型结果的字典
        """
        all_results = {}
        
        print("\n" + "="*60)
        print("🔍 模型对比测试")
        print("="*60)
        
        for idx, tester_info in enumerate(self.testers, 1):
            model_name = tester_info['name']
            tester = tester_info['tester']
            
            print(f"\n[{idx}/{len(self.testers)}] 测试模型: {model_name}")
            print("-" * 60)
            
            # 批量测试
            results = tester.batch_test(vqa_data, base_path, max_samples)
            
            # 计算指标
            metrics = tester.calculate_metrics(results)
            
            # 保存结果
            all_results[model_name] = {
                'results': results,
                'metrics': metrics
            }
            
            # 打印简要结果
            print(f"\n✅ {model_name} 测试完成")
            print(f"   总体准确率: {metrics['overall_accuracy']:.2%} ({metrics['correct_count']}/{metrics['total_count']})")
        
        return all_results
    
    def print_comparison(self, all_results: Dict):
        """
        打印对比结果
        
        Args:
            all_results: 所有模型的测试结果
        """
        print("\n" + "="*60)
        print("📊 模型对比结果")
        print("="*60)
        
        # 打印总体准确率对比
        print("\n总体准确率对比:")
        print("-" * 60)
        sorted_models = sorted(
            all_results.items(),
            key=lambda x: x[1]['metrics']['overall_accuracy'],
            reverse=True
        )
        
        for rank, (model_name, data) in enumerate(sorted_models, 1):
            metrics = data['metrics']
            accuracy = metrics['overall_accuracy']
            count = f"{metrics['correct_count']}/{metrics['total_count']}"
            print(f"{rank}. {model_name:20s}: {accuracy:6.2%} ({count})")
        
        # 打印任务类型准确率对比
        print("\n单图 VQA 准确率对比:")
        print("-" * 60)
        sorted_single = sorted(
            all_results.items(),
            key=lambda x: x[1]['metrics']['single_image_accuracy'],
            reverse=True
        )
        
        for rank, (model_name, data) in enumerate(sorted_single, 1):
            metrics = data['metrics']
            accuracy = metrics['single_image_accuracy']
            count = metrics['single_image_count']
            print(f"{rank}. {model_name:20s}: {accuracy:6.2%} ({count} 条)")
        
        # 如果有多图 VQA 数据
        if any(data['metrics']['multi_image_count'] > 0 for data in all_results.values()):
            print("\n多图 VQA 准确率对比:")
            print("-" * 60)
            sorted_multi = sorted(
                all_results.items(),
                key=lambda x: x[1]['metrics']['multi_image_accuracy'],
                reverse=True
            )
            
            for rank, (model_name, data) in enumerate(sorted_multi, 1):
                metrics = data['metrics']
                accuracy = metrics['multi_image_accuracy']
                count = metrics['multi_image_count']
                print(f"{rank}. {model_name:20s}: {accuracy:6.2%} ({count} 条)")
        
        # 打印类别准确率对比
        print("\n按类别准确率对比:")
        print("-" * 60)
        
        # 收集所有类别
        all_categories = set()
        for data in all_results.values():
            all_categories.update(data['metrics']['category_accuracy'].keys())
        
        for category in sorted(all_categories):
            print(f"\n{category}:")
            category_results = []
            for model_name, data in all_results.items():
                cat_stats = data['metrics']['category_accuracy'].get(category, {'accuracy': 0, 'total': 0})
                category_results.append((model_name, cat_stats['accuracy'], cat_stats['total']))
            
            # 按准确率排序
            category_results.sort(key=lambda x: x[1], reverse=True)
            
            for rank, (model_name, accuracy, total) in enumerate(category_results, 1):
                if total > 0:
                    print(f"  {rank}. {model_name:20s}: {accuracy:6.2%} ({total} 条)")
    
    def save_comparison(self, all_results: Dict, output_path: str):
        """
        保存对比结果
        
        Args:
            all_results: 所有模型的测试结果
            output_path: 输出文件路径
        """
        output_data = {
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'models': list(all_results.keys()),
            'comparison': all_results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 对比结果已保存到: {output_path}")
    
    def generate_comparison_report(self, all_results: Dict, output_path: str):
        """
        生成对比报告（Markdown格式）
        
        Args:
            all_results: 所有模型的测试结果
            output_path: 输出文件路径
        """
        report_lines = []
        
        # 标题
        report_lines.append("# VQA 模型对比报告\n")
        report_lines.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 模型列表
        report_lines.append("## 测试模型\n")
        for idx, model_name in enumerate(all_results.keys(), 1):
            report_lines.append(f"{idx}. {model_name}\n")
        report_lines.append("\n")
        
        # 总体准确率对比表格
        report_lines.append("## 总体准确率对比\n\n")
        report_lines.append("| 排名 | 模型 | 准确率 | 正确数/总数 |\n")
        report_lines.append("|------|------|--------|-------------|\n")
        
        sorted_models = sorted(
            all_results.items(),
            key=lambda x: x[1]['metrics']['overall_accuracy'],
            reverse=True
        )
        
        for rank, (model_name, data) in enumerate(sorted_models, 1):
            metrics = data['metrics']
            accuracy = metrics['overall_accuracy']
            count = f"{metrics['correct_count']}/{metrics['total_count']}"
            report_lines.append(f"| {rank} | {model_name} | {accuracy:.2%} | {count} |\n")
        
        report_lines.append("\n")
        
        # 任务类型准确率对比
        report_lines.append("## 任务类型准确率对比\n\n")
        report_lines.append("### 单图 VQA\n\n")
        report_lines.append("| 排名 | 模型 | 准确率 | 样本数 |\n")
        report_lines.append("|------|------|--------|--------|\n")
        
        sorted_single = sorted(
            all_results.items(),
            key=lambda x: x[1]['metrics']['single_image_accuracy'],
            reverse=True
        )
        
        for rank, (model_name, data) in enumerate(sorted_single, 1):
            metrics = data['metrics']
            accuracy = metrics['single_image_accuracy']
            count = metrics['single_image_count']
            report_lines.append(f"| {rank} | {model_name} | {accuracy:.2%} | {count} |\n")
        
        report_lines.append("\n")
        
        # 多图 VQA（如果有）
        if any(data['metrics']['multi_image_count'] > 0 for data in all_results.values()):
            report_lines.append("### 多图 VQA\n\n")
            report_lines.append("| 排名 | 模型 | 准确率 | 样本数 |\n")
            report_lines.append("|------|------|--------|--------|\n")
            
            sorted_multi = sorted(
                all_results.items(),
                key=lambda x: x[1]['metrics']['multi_image_accuracy'],
                reverse=True
            )
            
            for rank, (model_name, data) in enumerate(sorted_multi, 1):
                metrics = data['metrics']
                accuracy = metrics['multi_image_accuracy']
                count = metrics['multi_image_count']
                report_lines.append(f"| {rank} | {model_name} | {accuracy:.2%} | {count} |\n")
            
            report_lines.append("\n")
        
        # 类别准确率对比
        report_lines.append("## 按类别准确率对比\n\n")
        
        all_categories = set()
        for data in all_results.values():
            all_categories.update(data['metrics']['category_accuracy'].keys())
        
        for category in sorted(all_categories):
            report_lines.append(f"### {category}\n\n")
            report_lines.append("| 排名 | 模型 | 准确率 | 样本数 |\n")
            report_lines.append("|------|------|--------|--------|\n")
            
            category_results = []
            for model_name, data in all_results.items():
                cat_stats = data['metrics']['category_accuracy'].get(
                    category,
                    {'accuracy': 0, 'total': 0}
                )
                category_results.append((model_name, cat_stats['accuracy'], cat_stats['total']))
            
            category_results.sort(key=lambda x: x[1], reverse=True)
            
            for rank, (model_name, accuracy, total) in enumerate(category_results, 1):
                if total > 0:
                    report_lines.append(f"| {rank} | {model_name} | {accuracy:.2%} | {total} |\n")
            
            report_lines.append("\n")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)
        
        print(f"📄 对比报告已生成: {output_path}")


def compare_test():
    """模型对比测试示例"""
    
    print("\n" + "="*60)
    print("VQA Benchmark - 模型对比测试")
    print("="*60 + "\n")
    
    # 配置多个模型（示例：这里只配置一个模型，实际使用时可以配置多个）
    models_config = [
        {
            'api_key': 'sk-2LdDgrUtliwULsFaxUD46XfCqjfpbodbaMtiTZqhOAqtjKbN',
            'base_url': 'http://35.220.164.252:3888/v1',
            'model_name': 'gpt-4o',
            'display_name': 'GPT-4o'
        },
        # 可以添加更多模型
        # {
        #     'api_key': 'another-api-key',
        #     'base_url': 'http://another-server:port/v1',
        #     'model_name': 'qwen-vl-max',
        #     'display_name': 'Qwen-VL-Max'
        # },
    ]
    
    # 测试数据路径
    vqa_data_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/535/VQA/all_vqa.json"
    base_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/535"
    
    # 输出路径
    output_dir = "/mnt/petrelfs/wangmaonan/traffic_vqa_benchmark/benchmark_test/results"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_output = os.path.join(output_dir, f"model_comparison_{timestamp}.json")
    md_output = os.path.join(output_dir, f"model_comparison_{timestamp}.md")
    
    # 加载 VQA 数据
    print(f"📂 加载 VQA 数据: {vqa_data_path}")
    with open(vqa_data_path, 'r', encoding='utf-8') as f:
        vqa_data = json.load(f)
    print(f"✅ 加载成功，共 {len(vqa_data)} 条数据\n")
    
    # 创建对比测试实例
    comparator = VQAModelComparison(models_config)
    
    # 对比测试（先测试前10条）
    all_results = comparator.compare_models(vqa_data, base_path, max_samples=10)
    
    # 打印对比结果
    comparator.print_comparison(all_results)
    
    # 保存结果
    comparator.save_comparison(all_results, json_output)
    
    # 生成报告
    comparator.generate_comparison_report(all_results, md_output)
    
    print("\n" + "="*60)
    print("✅ 模型对比测试完成")
    print("="*60)


if __name__ == "__main__":
    compare_test()

