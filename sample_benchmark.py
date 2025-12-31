'''
Author: WANG Maonan
Date: 2025-12-29
Description: 从生成的 VQA 问题中采样，创建 benchmark 数据集
'''
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from benchmark_utils.question_filter import QuestionFilter
from benchmark_utils.image_copier import ImageCopier
from benchmark_utils.benchmark_sampler import BenchmarkSampler

class BenchmarkGenerator:
    """Benchmark 数据集生成器"""
    
    def __init__(
        self,
        source_root: str,
        output_root: str,
        timestep_range: tuple = (100, 550),
        random_seed: int = 42
    ):
        """初始化
        
        Args:
            source_root: VQA 数据源根目录
            output_root: benchmark 输出根目录
            timestep_range: timestep 采样范围 (start, end)
            random_seed: 随机种子
        """
        self.source_root = Path(source_root)
        self.output_root = Path(output_root)
        self.timestep_range = timestep_range
        
        # 设置随机种子
        random.seed(random_seed)
        
        # 创建输出目录
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_root / 'images'
        self.images_dir.mkdir(exist_ok=True)
        
        # 初始化工具类
        self.filter = QuestionFilter()
        self.image_copier = ImageCopier(self.source_root, self.images_dir)
        self.sampler = BenchmarkSampler()
        
    def collect_all_questions(self) -> Dict[str, List[Dict[str, Any]]]:
        """收集所有 timestep 的 VQA 问题
        
        Returns:
            按问题类型分类的所有问题
        """
        print(f"{'='*60}")
        print(f"Phase 1: Collecting all VQA questions...")
        print(f"{'='*60}\n")
        
        # 按问题类型分类存储
        categorized_questions = defaultdict(list)
        
        # 遍历所有 timestep
        timestep_dirs = sorted(
            [d for d in self.source_root.iterdir() if d.is_dir() and d.name.isdigit()],
            key=lambda x: int(x.name)
        )
        
        collected_count = 0
        for timestep_dir in timestep_dirs:
            timestep = int(timestep_dir.name)
            
            # 只处理指定范围内的 timestep
            if not (self.timestep_range[0] <= timestep <= self.timestep_range[1]):
                continue
            
            # 收集 single image VQA
            single_vqa_dir = timestep_dir / 'VQA' / 'single_image_vqa'
            if single_vqa_dir.exists():
                for json_file in single_vqa_dir.glob('*.json'):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                    
                    for q in questions:
                        q_type = self.filter.classify_question(q)
                        if q_type:
                            categorized_questions[q_type].append(q)
                            collected_count += 1
            
            # 收集 multi image VQA
            multi_vqa_file = timestep_dir / 'VQA' / 'multi_image_vqa.json'
            if multi_vqa_file.exists():
                with open(multi_vqa_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                for q in questions:
                    q_type = self.filter.classify_question(q)
                    if q_type:
                        categorized_questions[q_type].append(q)
                        collected_count += 1
        
        print(f"✓ Collected {collected_count} questions from timestep {self.timestep_range[0]} to {self.timestep_range[1]}")
        print(f"✓ Question types found: {len(categorized_questions)}\n")
        
        # 打印每个类型的数量
        print("Question distribution by type:")
        for q_type, questions in sorted(categorized_questions.items()):
            print(f"  - {q_type}: {len(questions)} questions")
        print()
        
        return dict(categorized_questions)
    
    def sample_questions(
        self,
        categorized_questions: Dict[str, List[Dict[str, Any]]],
        sampling_config: Dict[str, int]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """根据配置采样问题
        
        Args:
            categorized_questions: 按类型分类的所有问题
            sampling_config: 采样配置 {question_type: count}
            
        Returns:
            采样后的问题
        """
        print(f"{'='*60}")
        print(f"Phase 2: Sampling questions according to config...")
        print(f"{'='*60}\n")
        
        sampled_questions = {}
        
        for q_type, target_count in sampling_config.items():
            if target_count == 0 or target_count == '-':
                continue
            
            available_questions = categorized_questions.get(q_type, [])
            
            # 特殊处理：存在性问题需要平衡采样
            if q_type in ['l1.1_obj_q2_special_vehicle_exist', 'l1.1_obj_q4_special_event_exist']:
                # 一半有特殊情况，一半没有
                half_count = target_count // 2
                
                if 'special_vehicle' in q_type:
                    has_special = self.filter.filter_has_special_vehicle(available_questions)
                    no_special = self.filter.filter_no_special_vehicle(available_questions)
                else:
                    has_special = self.filter.filter_has_special_event(available_questions)
                    no_special = self.filter.filter_no_special_event(available_questions)
                
                sampled_has = self.sampler.sample_questions(has_special, half_count, q_type + "_has")
                sampled_no = self.sampler.sample_questions(no_special, target_count - half_count, q_type + "_no")
                
                sampled = sampled_has + sampled_no
                random.shuffle(sampled)  # 打乱顺序
                
                if sampled:
                    sampled_questions[q_type] = sampled
                    print(f"✓ {q_type}: sampled {len(sampled)}/{target_count} (has: {len(sampled_has)}, no: {len(sampled_no)})")
                else:
                    print(f"✗ {q_type}: no questions available (target: {target_count})")
            
            # 类型和定位问题只采样有特殊情况的
            elif q_type in ['l1.1_obj_q3_special_vehicle_type', 'l1.1_obj_q5_special_event_type',
                           'l1.2_topo_q8_special_vehicle_lane', 'l1.2_topo_q9_special_event_lane',
                           'l2.1_view_q2_special_vehicle_location', 'l3_dec_q3_phase_special_vehicle']:
                if 'special_vehicle' in q_type or 'vehicle_location' in q_type:
                    available_questions = self.filter.filter_has_special_vehicle(available_questions)
                else:
                    available_questions = self.filter.filter_has_special_event(available_questions)
                
                sampled = self.sampler.sample_questions(
                    available_questions,
                    target_count,
                    q_type
                )
                
                if sampled:
                    sampled_questions[q_type] = sampled
                    print(f"✓ {q_type}: sampled {len(sampled)}/{target_count} (available: {len(available_questions)})")
                else:
                    print(f"✗ {q_type}: no questions available (target: {target_count})")
            
            # 其他问题正常采样
            else:
                sampled = self.sampler.sample_questions(
                    available_questions,
                    target_count,
                    q_type
                )
                
                if sampled:
                    sampled_questions[q_type] = sampled
                    print(f"✓ {q_type}: sampled {len(sampled)}/{target_count} (available: {len(available_questions)})")
                else:
                    print(f"✗ {q_type}: no questions available (target: {target_count})")
        
        print()
        return sampled_questions
    
    def save_benchmark(
        self,
        sampled_questions: Dict[str, List[Dict[str, Any]]],
        sampling_config: Dict[str, int]
    ):
        """保存 benchmark 数据集
        
        Args:
            sampled_questions: 采样后的问题
            sampling_config: 采样配置（用于生成空文件）
        """
        print(f"{'='*60}")
        print(f"Phase 3: Saving benchmark dataset...")
        print(f"{'='*60}\n")
        
        total_images = 0
        empty_files = []
        
        # 保存已采样的问题
        for q_type, questions in sampled_questions.items():
            # 创建 jsonl 文件
            jsonl_path = self.output_root / f"{q_type}.jsonl"
            
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for q in questions:
                    # 复制图片并更新路径
                    new_q = self.image_copier.copy_and_update_paths(q)
                    
                    # 写入 jsonl
                    f.write(json.dumps(new_q, ensure_ascii=False) + '\n')
                    
                    # 统计图片数量
                    if 'images' in new_q:
                        total_images += len(new_q['images'])
                    elif 'image_path' in new_q:
                        total_images += 1
            
            print(f"✓ Saved {len(questions)} questions to {jsonl_path.name}")
        
        # 为未采样到的问题类型创建空文件
        print(f"\nCreating empty files for missing question types...")
        for q_type, target_count in sampling_config.items():
            if target_count == 0 or target_count == '-':
                continue
            
            if q_type not in sampled_questions:
                jsonl_path = self.output_root / f"{q_type}.jsonl"
                
                # 创建空文件并写入注释
                with open(jsonl_path, 'w', encoding='utf-8') as f:
                    # 写入一个 JSON 注释行（虽然不是标准 JSONL，但方便理解）
                    comment = {
                        "_comment": f"This file is empty. Please manually add {target_count} questions of type {q_type}.",
                        "_target_count": target_count,
                        "_question_type": q_type
                    }
                    f.write(f"# {json.dumps(comment, ensure_ascii=False)}\n")
                
                empty_files.append(jsonl_path.name)
                print(f"✓ Created empty file: {jsonl_path.name} (target: {target_count} questions)")
        
        print(f"\n✓ Total questions: {sum(len(q) for q in sampled_questions.values())}")
        print(f"✓ Total images: {total_images}")
        print(f"✓ Empty files created: {len(empty_files)}")
        print(f"✓ Output directory: {self.output_root}")
        print(f"✓ Images directory: {self.images_dir}")
        print()
    
    def generate(self):
        """生成完整的 benchmark 数据集"""
        # 定义采样配置（根据表格）
        sampling_config = {
            # L1.1 Obj - 目标级感知
            'l1.1_obj_q1_vehicle_count': 15,
            'l1.1_obj_q2_special_vehicle_exist': 10,
            'l1.1_obj_q3_special_vehicle_type': 10,
            'l1.1_obj_q4_special_event_exist': 10,
            'l1.1_obj_q5_special_event_type': 10,
            
            # L1.2 Topo - 交通结构理解
            'l1.2_topo_q1_incoming_lanes_count': 11,
            'l1.2_topo_q2_outgoing_lanes_count': 11,
            'l1.2_topo_q3_lane_function_count': 2,
            'l1.2_topo_q4_lane_function': 2,
            'l1.2_topo_q5_incoming_vehicles': 20,
            'l1.2_topo_q6_outgoing_vehicles': 20,
            'l1.2_topo_q7_lane_vehicles': 11,
            'l1.2_topo_q8_special_vehicle_lane': 11,
            'l1.2_topo_q9_special_event_lane': 11,
            
            # L2.1 View - 多视角空间一致性
            'l2.1_view_q1_most_vehicles': 8,
            'l2.1_view_q2_special_vehicle_location': 8,
            'l2.1_view_q3_different_view': 8,
            'l2.1_view_q4_bev_to_view': 8,
            'l2.1_view_q5_view_to_bev': 8,
            
            # L2.2 Time - 跨时间理解
            'l2.2_time_q1_temporal_order': 10,
            'l2.2_time_q2_queue_trend': 6,
            'l2.2_time_q3_temporal_between': 10,
            'l2.2_time_q4_lane_function_multi': 0, # 根据车流判断车道功能
            'l2.2_time_q5_accident_multi': 0,  # 多帧判断事故类型
            
            # L3 Dec - 决策支持
            'l3_dec_q1_phase_most_vehicles': 5,
            'l3_dec_q2_phase_accident': 5,
            'l3_dec_q3_phase_special_vehicle': 5,
            'l3_dec_q4_phase_green_light': 5,
            'l3_dec_q5_phase_decision': 5,
        }
        
        # 执行生成流程
        categorized_questions = self.collect_all_questions()
        sampled_questions = self.sample_questions(categorized_questions, sampling_config)
        self.save_benchmark(sampled_questions, sampling_config)
        
        print(f"{'='*60}")
        print(f"Benchmark generation completed!")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    # 配置路径
    source_root = "/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier"
    output_root = "/mnt/petrelfs/wangmaonan/traffic_vqa_benchmark/benchmark_dataset"
    
    # 创建生成器
    generator = BenchmarkGenerator(
        source_root=source_root,
        output_root=output_root,
        timestep_range=(100, 550),
        random_seed=42
    )
    
    # 生成 benchmark
    generator.generate()


if __name__ == '__main__':
    main()

