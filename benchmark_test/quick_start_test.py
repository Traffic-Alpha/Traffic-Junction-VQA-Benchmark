"""
Author: WANG Maonan
Description: VQA 测试快速开始 - 演示所有测试功能
"""
import os
import json
from vqa_full_test import VQABenchmarkFullTest
from vqa_compare_models import VQAModelComparison


def main():
    """快速开始测试"""
    
    print("\n" + "="*70)
    print(" "*20 + "VQA 测试工具 - 快速开始")
    print("="*70 + "\n")
    
    # ========== 配置部分 ==========
    print("📝 配置测试参数...")
    
    # API 配置
    api_key = "sk-2LdDgrUtliwULsFaxUD46XfCqjfpbodbaMtiTZqhOAqtjKbN"
    base_url = "http://35.220.164.252:3888/v1"
    model_name = "gpt-4o"
    
    # 数据路径
    vqa_data_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/535/VQA/all_vqa.json"
    base_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/535"
    
    # 输出目录
    output_dir = "/mnt/petrelfs/wangmaonan/traffic_vqa_benchmark/benchmark_test/results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试样本数量（设置为较小的数字进行快速测试）
    test_samples = 5
    
    print(f"  ✓ 模型: {model_name}")
    print(f"  ✓ 测试样本数: {test_samples}")
    print(f"  ✓ 输出目录: {output_dir}\n")
    
    # ========== 加载数据 ==========
    print("📂 加载 VQA 数据...")
    with open(vqa_data_path, 'r', encoding='utf-8') as f:
        vqa_data = json.load(f)
    print(f"  ✓ 加载成功，共 {len(vqa_data)} 条数据\n")
    
    # ========== 功能演示菜单 ==========
    while True:
        print("\n" + "="*70)
        print("请选择要测试的功能：")
        print("="*70)
        print("1. 测试单个 VQA 问题（单图）")
        print("2. 测试单个 VQA 问题（多图）")
        print("3. 批量测试并计算准确率")
        print("4. 模型对比测试（需要配置多个模型）")
        print("5. 查看所有 VQA 问题类型统计")
        print("6. 退出")
        print("-"*70)
        
        choice = input("请输入选项 (1-6): ").strip()
        
        if choice == "1":
            # 测试单个单图 VQA
            test_single_image_vqa(vqa_data, base_path, api_key, base_url, model_name)
        
        elif choice == "2":
            # 测试单个多图 VQA
            test_multi_image_vqa(vqa_data, base_path, api_key, base_url, model_name)
        
        elif choice == "3":
            # 批量测试
            batch_test_vqa(vqa_data, base_path, api_key, base_url, model_name, 
                          test_samples, output_dir)
        
        elif choice == "4":
            # 模型对比测试
            compare_models_test(vqa_data, base_path, test_samples, output_dir)
        
        elif choice == "5":
            # 统计信息
            show_statistics(vqa_data)
        
        elif choice == "6":
            print("\n👋 感谢使用！\n")
            break
        
        else:
            print("\n⚠️  无效选项，请重新选择。")


def test_single_image_vqa(vqa_data, base_path, api_key, base_url, model_name):
    """测试单个单图 VQA"""
    print("\n" + "-"*70)
    print("📸 单图 VQA 测试")
    print("-"*70)
    
    # 筛选单图 VQA
    single_image_data = [item for item in vqa_data if item.get('task') == 'Single Image']
    
    if not single_image_data:
        print("⚠️  没有找到单图 VQA 数据")
        return
    
    # 显示前5个问题
    print("\n可用的问题：")
    for idx, item in enumerate(single_image_data[:5], 1):
        print(f"{idx}. [{item.get('category')}] {item['question'][:60]}...")
    
    idx = int(input(f"\n请选择问题编号 (1-{min(5, len(single_image_data))}): ").strip())
    
    if 1 <= idx <= min(5, len(single_image_data)):
        vqa_item = single_image_data[idx-1]
        
        print(f"\n问题: {vqa_item['question']}")
        print(f"类别: {vqa_item.get('category')} - {vqa_item.get('subtask')}")
        
        if vqa_item.get('options'):
            print("\n选项:")
            for key, value in vqa_item['options'].items():
                print(f"  {key}: {value}")
        
        print(f"\n正确答案: {vqa_item.get('correct_answer')} - {vqa_item.get('answer')}")
        
        print("\n🔄 正在调用 API...")
        tester = VQABenchmarkFullTest(api_key, base_url, model_name)
        result = tester.test_single_image_vqa(vqa_item, base_path)
        
        if result:
            print(f"\n模型回答: {result['predicted_answer']}")
            print(f"提取选项: {result['predicted_option']}")
            status = "✅ 正确" if result['is_correct'] else "❌ 错误"
            print(f"判断结果: {status}")


def test_multi_image_vqa(vqa_data, base_path, api_key, base_url, model_name):
    """测试单个多图 VQA"""
    print("\n" + "-"*70)
    print("📸📸 多图 VQA 测试")
    print("-"*70)
    
    # 筛选多图 VQA
    multi_image_data = [item for item in vqa_data if item.get('task') == 'Multi Image']
    
    if not multi_image_data:
        print("⚠️  没有找到多图 VQA 数据")
        return
    
    # 显示前5个问题
    print("\n可用的问题：")
    for idx, item in enumerate(multi_image_data[:5], 1):
        print(f"{idx}. [{item.get('category')}] {item['question'][:60]}...")
    
    idx = int(input(f"\n请选择问题编号 (1-{min(5, len(multi_image_data))}): ").strip())
    
    if 1 <= idx <= min(5, len(multi_image_data)):
        vqa_item = multi_image_data[idx-1]
        
        print(f"\n问题: {vqa_item['question']}")
        print(f"类别: {vqa_item.get('category')} - {vqa_item.get('subtask')}")
        print(f"图片数量: {len(vqa_item.get('images', []))}")
        
        if vqa_item.get('options'):
            print("\n选项:")
            for key, value in vqa_item['options'].items():
                print(f"  {key}: {value}")
        
        print(f"\n正确答案: {vqa_item.get('correct_answer')} - {vqa_item.get('answer')}")
        
        print("\n🔄 正在调用 API...")
        tester = VQABenchmarkFullTest(api_key, base_url, model_name)
        result = tester.test_multi_image_vqa(vqa_item, base_path)
        
        if result:
            print(f"\n模型回答: {result['predicted_answer']}")
            print(f"提取选项: {result['predicted_option']}")
            status = "✅ 正确" if result['is_correct'] else "❌ 错误"
            print(f"判断结果: {status}")


def batch_test_vqa(vqa_data, base_path, api_key, base_url, model_name, test_samples, output_dir):
    """批量测试 VQA"""
    print("\n" + "-"*70)
    print("📊 批量测试")
    print("-"*70)
    
    print(f"\n将测试前 {test_samples} 条数据")
    confirm = input("是否继续？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("已取消测试")
        return
    
    # 创建测试实例
    tester = VQABenchmarkFullTest(api_key, base_url, model_name)
    
    # 批量测试
    results = tester.batch_test(vqa_data, base_path, max_samples=test_samples)
    
    # 计算指标
    metrics = tester.calculate_metrics(results)
    
    # 打印结果
    tester.print_metrics(metrics)
    
    # 保存结果
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f"batch_test_{timestamp}.json")
    tester.save_results(results, metrics, output_path)


def compare_models_test(vqa_data, base_path, test_samples, output_dir):
    """模型对比测试"""
    print("\n" + "-"*70)
    print("🔍 模型对比测试")
    print("-"*70)
    
    print("\n⚠️  注意：此功能需要配置多个模型")
    print("当前仅配置了一个模型，无法进行对比")
    print("\n如需使用此功能，请在代码中配置多个模型：")
    print("编辑 vqa_compare_models.py 文件中的 models_config")


def show_statistics(vqa_data):
    """显示统计信息"""
    print("\n" + "-"*70)
    print("📈 VQA 数据统计")
    print("-"*70)
    
    # 总数
    total = len(vqa_data)
    print(f"\n总问题数: {total}")
    
    # 按任务类型统计
    task_stats = {}
    for item in vqa_data:
        task = item.get('task', 'Unknown')
        task_stats[task] = task_stats.get(task, 0) + 1
    
    print("\n按任务类型:")
    for task, count in sorted(task_stats.items()):
        percentage = count / total * 100
        print(f"  - {task:20s}: {count:3d} ({percentage:5.1f}%)")
    
    # 按类别统计
    category_stats = {}
    for item in vqa_data:
        category = item.get('category', 'Unknown')
        category_stats[category] = category_stats.get(category, 0) + 1
    
    print("\n按类别:")
    for category, count in sorted(category_stats.items()):
        percentage = count / total * 100
        print(f"  - {category:25s}: {count:3d} ({percentage:5.1f}%)")
    
    # 按子任务统计
    subtask_stats = {}
    for item in vqa_data:
        subtask = item.get('subtask', 'Unknown')
        subtask_stats[subtask] = subtask_stats.get(subtask, 0) + 1
    
    print("\n按子任务:")
    for subtask, count in sorted(subtask_stats.items()):
        percentage = count / total * 100
        print(f"  - {subtask:20s}: {count:3d} ({percentage:5.1f}%)")


if __name__ == "__main__":
    main()

