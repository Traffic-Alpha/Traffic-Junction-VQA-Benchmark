'''
Author: WANG Maonan
Date: 2025-12-29
Description: 从生成的 VQA 问题中采样，创建 benchmark 数据集
Example of usage:
python quick_sample_benchmark.py \
    --source_root /path/to/source \
    --output_root /path/to/output \
    --timestep_start 200 \
    --timestep_end 550 \
    --random_seed 123
'''
import argparse
from sample_benchmark import BenchmarkGenerator


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从生成的 VQA 问题中采样，创建 benchmark 数据集'
    )
    
    parser.add_argument(
        '--source_root',
        type=str,
        help='源数据根目录路径'
    )
    
    parser.add_argument(
        '--output_root',
        type=str,
        help='输出根目录路径'
    )
    
    parser.add_argument(
        '--timestep_start',
        type=int,
        default=100,
        help='时间步范围起始值'
    )
    
    parser.add_argument(
        '--timestep_end',
        type=int,
        default=550,
        help='时间步范围结束值'
    )
    
    parser.add_argument(
        '--random_seed',
        type=int,
        default=42,
        help='随机种子'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 创建生成器
    generator = BenchmarkGenerator(
        source_root=args.source_root,
        output_root=args.output_root,
        timestep_range=(args.timestep_start, args.timestep_end),
        random_seed=args.random_seed
    )
    
    # 生成 benchmark
    generator.generate()


if __name__ == '__main__':
    main()

