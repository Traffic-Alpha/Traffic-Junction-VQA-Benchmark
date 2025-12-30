'''
Author: WANG Maonan
Date: 2025-12-12
LastEditors: WANG Maonan
Description: 生成一个指定场景的 VQA 数据
LastEditTime: 2025-12-30
'''
import os
from generate_vqa_dataset import VQADatasetGenerator

def main():
    """生成指定场景的 VQA 数据"""
    
    print("\n" + "="*60)
    print("Traffic VQA Benchmark - Quick Start")
    print("="*60 + "\n")
    
    # 示例场景路径
    scene_path = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier"
    
    # 检查路径是否存在
    if not os.path.exists(scene_path):
        print(f"❌ Error: Scene path does not exist: {scene_path}")
        print("\nPlease update the 'scene_path' variable in this script to point to your data.")
        return
    
    print(f"📁 Scene: {os.path.basename(scene_path)}")
    print(f"📍 Path: {scene_path}\n")
    
    # 定义观测距离映射（需要区分 incoming 和 outgoing）
    distance_mapping = {
        0: {'incoming': 65, 'outgoing': 40},  # 方向 0 的可视范围（米）
        1: {'incoming': 65, 'outgoing': 40},  # 方向 1 的可视范围（米）
        2: {'incoming': 65, 'outgoing': 40},  # 方向 2 的可视范围（米）
    }
    
    print("⚙️  Configuration:")
    print(f"   - Observation distances:")
    for direction, distances in distance_mapping.items():
        print(f"      Direction {direction}: incoming={distances['incoming']}m, outgoing={distances['outgoing']}m")
    print()
    
    # 创建生成器
    print("🚀 Starting VQA dataset generation...\n")
    generator = VQADatasetGenerator(scene_path, distance_mapping)
    
    # 生成数据集
    generator.generate_dataset()
    
    print("\n" + "="*60)
    print("✅ VQA Dataset Generation Completed!")
    print("="*60)
    
    # 显示生成的文件
    print("\n📊 Generated files:")
    print("   For each timestep, you'll find:")
    print("   - single_image_vqa/    : 单图问答数据")
    print("   - multi_image_vqa.json : 多图问答数据")
    print("   - all_vqa.json        : 所有问答数据")

if __name__ == "__main__":
    main()