"""
Author: WANG Maonan
Description: VQA 完整测试脚本 - 批量测试、准确率计算、结果保存
"""
import os
import json
import base64
from openai import OpenAI
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import re


class VQABenchmarkFullTest:
    """VQA Benchmark 完整测试类"""
    
    def __init__(self, api_key: str, base_url: str, model_name: str = "gpt-4o"):
        """
        初始化测试类
        
        Args:
            api_key: OpenAI API Key
            base_url: API Base URL
            model_name: 使用的模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        
    def encode_image(self, image_path: str) -> str:
        """
        将图片编码为 base64 格式
        
        Args:
            image_path: 图片路径
            
        Returns:
            base64 编码的图片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def test_single_image_vqa(self, vqa_item: dict, base_path: str) -> dict:
        """
        测试单图 VQA
        
        Args:
            vqa_item: VQA 数据项
            base_path: 图片基础路径
            
        Returns:
            包含预测结果和正确答案的字典
        """
        # 构建完整的图片路径
        image_path = os.path.join(base_path, vqa_item['image_path'])
        
        if not os.path.exists(image_path):
            print(f"⚠️  图片不存在: {image_path}")
            return None
        
        # 编码图片
        base64_image = self.encode_image(image_path)
        
        # 构建提示词
        question = vqa_item['question']
        options = vqa_item.get('options', {})
        
        # 如果有选项，添加到问题中
        if options:
            options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
            prompt = f"{question}\n\nOptions:\n{options_text}\n\nPlease select the correct option (A/B/C/D)."
        else:
            prompt = question
        
        # 调用 API
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            predicted_answer = response.choices[0].message.content.strip()
            
            # 提取选项（A/B/C/D）
            predicted_option = self.extract_option(predicted_answer)
            correct_option = vqa_item.get('correct_answer')
            
            # 判断是否正确
            is_correct = predicted_option == correct_option if correct_option else None
            
            return {
                "question": question,
                "predicted_answer": predicted_answer,
                "predicted_option": predicted_option,
                "correct_option": correct_option,
                "answer_text": vqa_item.get('answer'),
                "options": options,
                "is_correct": is_correct,
                "category": vqa_item.get('category'),
                "subtask": vqa_item.get('subtask'),
                "task": vqa_item.get('task'),
                "image_path": image_path
            }
            
        except Exception as e:
            print(f"❌ API 调用失败: {e}")
            return None
    
    def test_multi_image_vqa(self, vqa_item: dict, base_path: str) -> dict:
        """
        测试多图 VQA
        
        Args:
            vqa_item: VQA 数据项
            base_path: 图片基础路径
            
        Returns:
            包含预测结果和正确答案的字典
        """
        # 构建消息内容（交替插入文本标签和图片）
        content = []
        images = vqa_item.get('images', [])
        question = vqa_item['question']
        options = vqa_item.get('options', {})
        
        # 构建提示词，明确说明图片顺序
        if options:
            options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
            prompt = f"{question}\n\n"
            prompt += f"The images are presented in order below (Image Index 0, Image Index 1, Image Index 2, ...).\n\n"
            prompt += f"Options:\n{options_text}\n\n"
            prompt += f"Please select the correct option (A/B/C/D)."
        else:
            prompt = f"{question}\n\nThe images are presented in order below (Image Index 0, Image Index 1, Image Index 2, ...)."
        
        content.append({"type": "text", "text": prompt})
        
        # 添加图片，每张图片前加上标签
        for idx, image_rel_path in enumerate(images):
            image_path = os.path.join(base_path, image_rel_path)
            
            if not os.path.exists(image_path):
                print(f"⚠️  图片不存在: {image_path}")
                continue
            
            # 添加图片索引标签
            content.append({
                "type": "text",
                "text": f"\n[Image Index {idx}]:"
            })
            
            # 编码并添加图片
            base64_image = self.encode_image(image_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            })
        
        # 调用 API
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=500
            )
            
            predicted_answer = response.choices[0].message.content.strip()
            
            # 提取选项（A/B/C/D）
            predicted_option = self.extract_option(predicted_answer)
            correct_option = vqa_item.get('correct_answer')
            
            # 判断是否正确
            is_correct = predicted_option == correct_option if correct_option else None
            
            return {
                "question": question,
                "predicted_answer": predicted_answer,
                "predicted_option": predicted_option,
                "correct_option": correct_option,
                "answer_text": vqa_item.get('answer'),
                "options": options,
                "is_correct": is_correct,
                "category": vqa_item.get('category'),
                "subtask": vqa_item.get('subtask'),
                "task": vqa_item.get('task'),
                "images": images
            }
            
        except Exception as e:
            print(f"❌ API 调用失败: {e}")
            return None
    
    def extract_option(self, text: str) -> str:
        """
        从文本中提取选项（A/B/C/D）
        
        Args:
            text: 模型输出的文本
            
        Returns:
            提取的选项字母，如果未找到则返回空字符串
        """
        # 尝试多种模式匹配
        patterns = [
            r'(?:^|\s)([A-D])(?:\.|:|\s|$)',  # A: 或 A. 或单独的 A
            r'(?:option|answer|选项)?\s*([A-D])',  # option A 或 answer A
            r'\b([A-D])\b'  # 独立的字母
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return ""
    
    def batch_test(self, vqa_data: List[dict], base_path: str, max_samples: int = None) -> List[dict]:
        """
        批量测试 VQA 数据
        
        Args:
            vqa_data: VQA 数据列表
            base_path: 图片基础路径
            max_samples: 最大测试样本数，None表示测试全部
            
        Returns:
            测试结果列表
        """
        results = []
        
        # 限制测试样本数
        test_data = vqa_data[:max_samples] if max_samples else vqa_data
        total = len(test_data)
        
        print(f"\n📊 开始批量测试，共 {total} 条数据")
        print("-" * 60)
        
        for idx, vqa_item in enumerate(test_data, 1):
            print(f"\n[{idx}/{total}] 测试中...")
            print(f"  类别: {vqa_item.get('category', 'N/A')} - {vqa_item.get('subtask', 'N/A')}")
            print(f"  任务: {vqa_item.get('task', 'N/A')}")
            
            # 显示图片路径
            if vqa_item.get('task') == 'Single Image':
                print(f"  图片: {vqa_item.get('image_path', 'N/A')}")
            elif vqa_item.get('task') == 'Multi Image':
                images = vqa_item.get('images', [])
                print(f"  图片数量: {len(images)}")
                for img_idx, img_path in enumerate(images):
                    print(f"    [{img_idx}] {img_path}")
            
            # 根据任务类型选择测试方法
            if vqa_item.get('task') == 'Single Image':
                result = self.test_single_image_vqa(vqa_item, base_path)
            elif vqa_item.get('task') == 'Multi Image':
                result = self.test_multi_image_vqa(vqa_item, base_path)
            else:
                print(f"  ⚠️ 未知任务类型: {vqa_item.get('task')}")
                continue
            
            if result:
                results.append(result)
                status = "✅" if result.get('is_correct') else "❌"
                print(f"  {status} 预测: {result.get('predicted_option')} | 正确: {result.get('correct_option')}")
        
        return results
    
    def calculate_metrics(self, results: List[dict]) -> dict:
        """
        计算评估指标
        
        Args:
            results: 测试结果列表
            
        Returns:
            包含各种指标的字典
        """
        if not results:
            return {}
        
        # 总体准确率
        correct_count = sum(1 for r in results if r.get('is_correct'))
        total_count = len(results)
        overall_accuracy = correct_count / total_count if total_count > 0 else 0
        
        # 按任务类型分组
        single_image_results = [r for r in results if r.get('task') == 'Single Image']
        multi_image_results = [r for r in results if r.get('task') == 'Multi Image']
        
        single_image_accuracy = (
            sum(1 for r in single_image_results if r.get('is_correct')) / len(single_image_results)
            if single_image_results else 0
        )
        
        multi_image_accuracy = (
            sum(1 for r in multi_image_results if r.get('is_correct')) / len(multi_image_results)
            if multi_image_results else 0
        )
        
        # 按类别分组
        category_accuracy = {}
        for result in results:
            category = result.get('category', 'Unknown')
            if category not in category_accuracy:
                category_accuracy[category] = {'correct': 0, 'total': 0}
            
            category_accuracy[category]['total'] += 1
            if result.get('is_correct'):
                category_accuracy[category]['correct'] += 1
        
        # 计算每个类别的准确率
        for category in category_accuracy:
            stats = category_accuracy[category]
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'overall_accuracy': overall_accuracy,
            'correct_count': correct_count,
            'total_count': total_count,
            'single_image_accuracy': single_image_accuracy,
            'single_image_count': len(single_image_results),
            'multi_image_accuracy': multi_image_accuracy,
            'multi_image_count': len(multi_image_results),
            'category_accuracy': category_accuracy
        }
    
    def save_results(self, results: List[dict], metrics: dict, output_path: str):
        """
        保存测试结果
        
        Args:
            results: 测试结果列表
            metrics: 评估指标
            output_path: 输出文件路径
        """
        output_data = {
            'model': self.model_name,
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics,
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_path}")
    
    def print_metrics(self, metrics: dict):
        """
        打印评估指标
        
        Args:
            metrics: 评估指标字典
        """
        print("\n" + "="*60)
        print("📊 评估结果")
        print("="*60)
        
        print(f"\n总体准确率: {metrics['overall_accuracy']:.2%} ({metrics['correct_count']}/{metrics['total_count']})")
        
        print(f"\n任务类型准确率:")
        print(f"  - 单图 VQA: {metrics['single_image_accuracy']:.2%} ({metrics['single_image_count']} 条)")
        print(f"  - 多图 VQA: {metrics['multi_image_accuracy']:.2%} ({metrics['multi_image_count']} 条)")
        
        print(f"\n按类别准确率:")
        for category, stats in metrics['category_accuracy'].items():
            print(f"  - {category}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})")


def full_test():
    """完整测试：测试所有VQA数据"""
    
    print("\n" + "="*60)
    print("VQA Benchmark - 完整测试")
    print("="*60 + "\n")
    
    # API 配置
    api_key = "sk-2LdDgrUtliwULsFaxUD46XfCqjfpbodbaMtiTZqhOAqtjKbN"
    base_url = "http://35.220.164.252:3888/v1"
    model_name = "gpt-4o"
    
    # 测试数据路径
    vqa_data_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/535/VQA/all_vqa.json"
    base_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/535"
    
    # 输出路径
    output_dir = "/mnt/petrelfs/wangmaonan/traffic_vqa_benchmark/benchmark_test/results"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"vqa_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    # 加载 VQA 数据
    print(f"📂 加载 VQA 数据: {vqa_data_path}")
    with open(vqa_data_path, 'r', encoding='utf-8') as f:
        vqa_data = json.load(f)
    print(f"✅ 加载成功，共 {len(vqa_data)} 条数据\n")
    
    # 创建测试实例
    tester = VQABenchmarkFullTest(api_key, base_url, model_name)
    
    # 批量测试（可以设置 max_samples 限制测试数量，None表示测试全部）
    results = tester.batch_test(vqa_data, base_path, max_samples=10)  # 先测试前10条
    
    # 计算指标
    metrics = tester.calculate_metrics(results)
    
    # 打印结果
    tester.print_metrics(metrics)
    
    # 保存结果
    tester.save_results(results, metrics, output_path)
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == "__main__":
    full_test()

