'''
Author: WANG Maonan
Date: 2025-12-12
LastEditors: WANG Maonan
Description: 生成完整的 VQA 数据集，包括单图和多图 VQA，以及问答和选择题两种格式
LastEditTime: 2025-12-12
'''
import os
import json
from typing import Dict, List, Any
from parse_infos.single_image_vqa import SingleImageVQA
from parse_infos.multi_image_vqa import MultiImageVQA
from parse_infos.cross_timestep_vqa import CrossTimestepVQA

class VQADatasetGenerator:
    """VQA数据集生成器"""
    
    def __init__(self, root_dir: str, distance_mapping: Dict[int, Dict[str, float]]):
        """初始化生成器
        
        Args:
            root_dir: 场景根目录（包含多个 timestep 子目录）
            distance_mapping: 不同方向的观测距离映射，需要区分 incoming 和 outgoing
                例如: {
                    0: {'incoming': 90, 'outgoing': 30},
                    1: {'incoming': 90, 'outgoing': 30},
                    2: {'incoming': 90, 'outgoing': 30},
                    3: {'incoming': 90, 'outgoing': 30}
                }
        """
        self.root_dir = root_dir
        self.distance_mapping = distance_mapping
        
        # 加载 global.json（只加载一次）
        self.global_data = {}
        global_json_path = os.path.join(root_dir, 'global.json')
        if os.path.exists(global_json_path):
            with open(global_json_path, 'r') as f:
                self.global_data = json.load(f)
        
    def generate_dataset(self):
        """生成完整的 VQA 数据集"""
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(self.root_dir)}")
        print(f"{'='*60}\n")
        
        # 获取所有 timestep 目录
        timesteps = self._get_timesteps()
        
        # 收集所有 timesteps 的数据（用于生成跨 timestep 问题）
        print("Phase 1: Collecting timestep data for cross-timestep reasoning...")
        all_timesteps_data = self._collect_all_timesteps_data(timesteps)
        print(f"  ✓ Collected data for {len(all_timesteps_data)} timesteps\n")
        
        # 为每个 timestep 生成 VQA
        print("Phase 2: Generating VQA for each timestep...")
        for timestep in timesteps:
            print(f"Processing timestep: {timestep}")
            timestep_path = os.path.join(self.root_dir, timestep)
            
            # 1. 生成 Single Image VQA（已包含 MCQ 格式）
            single_image_vqa = self._generate_single_image_vqa(timestep_path)
            
            # 2. 生成 Multi Image VQA（已包含 MCQ 格式）
            multi_image_vqa = self._generate_multi_image_vqa(timestep_path)
            
            # 3. 为当前 timestep 生成跨时间空间推理选择题
            timestep_spatial_mcq = self._generate_spatial_mcq_for_timestep(
                timestep, all_timesteps_data, num_questions=4
            )
            
            # 将跨时间空间推理问题添加到多图VQA中
            multi_image_vqa_with_spatial = multi_image_vqa + timestep_spatial_mcq
            
            # 4. 保存结果
            self._save_results(timestep_path, {
                'single_image_vqa': single_image_vqa,
                'multi_image_vqa': multi_image_vqa_with_spatial
            })
            
            print(f"  ✓ Generated {sum(len(v) for v in single_image_vqa.values())} single-image VQA pairs")
            print(f"  ✓ Generated {len(multi_image_vqa)} multi-image VQA pairs")
            print(f"  ✓ Generated {len(timestep_spatial_mcq)} cross-timestep VQA pairs")
            print(f"  ✓ Completed timestep: {timestep}\n")
    
    def _get_timesteps(self) -> List[str]:
        """获取所有 timestep 目录"""
        timesteps = []
        for item in os.listdir(self.root_dir):
            item_path = os.path.join(self.root_dir, item)
            if os.path.isdir(item_path):
                # 检查是否包含 annotations 目录
                if os.path.exists(os.path.join(item_path, 'annotations')):
                    timesteps.append(item)
        return sorted(timesteps, key=lambda x: int(x) if x.isdigit() else float('inf'))
    
    def _collect_all_timesteps_data(self, timesteps: List[str]) -> Dict[str, Dict]:
        """收集所有 timesteps 的数据
        
        Args:
            timesteps: 所有 timestep 列表
            
        Returns:
            所有 timesteps 的数据字典
        """
        collected_data = {}
        
        for timestep in timesteps:
            timestep_path = os.path.join(self.root_dir, timestep)
            
            # 收集方向和 BEV 图片信息
            timestep_info = {}
            annotations_dir = os.path.join(timestep_path, 'annotations')
            
            if os.path.exists(annotations_dir):
                for json_file in sorted(os.listdir(annotations_dir)):
                    if json_file.endswith('.json'):
                        direction_num = int(os.path.splitext(json_file)[0])
                        timestep_info[f'direction_{direction_num}'] = {
                            'image_path': f"{timestep}/high_quality_rgb/{direction_num}.png"
                        }
                
                # 添加 BEV
                timestep_info['bev'] = {
                    'image_path': f"{timestep}/high_quality_rgb/bev.png"
                }
                
                if timestep_info:  # 只添加有效数据
                    collected_data[timestep] = timestep_info
        
        return collected_data

    # #######################
    # 生成单图 VQA (QA 和 MCQ)
    # #######################
    def _generate_single_image_vqa(self, timestep_path: str) -> Dict[str, List[Dict]]:
        """生成特定 timestep 的单图 VQA (QA 和 MCQ)
        
        Returns:
            Dict[direction, List[qa_pairs]]
        """
        annotations_dir = os.path.join(timestep_path, 'annotations')
        if not os.path.exists(annotations_dir):
            return {}
        
        # 从路径中提取 timestep 编号
        timestep = os.path.basename(timestep_path)
        
        single_image_qa = {}
        
        # 处理每个方向的 annotation
        for json_file in sorted(os.listdir(annotations_dir)):
            if not json_file.endswith('.json'):
                continue
            
            # 获取方向编号
            direction_num = int(os.path.splitext(json_file)[0])
            
            # 获取该方向的 incoming 和 outgoing 可视范围
            direction_distances = self.distance_mapping.get(
                direction_num, 
                {'incoming': 90, 'outgoing': 30}  # 默认值
            )
            max_incoming_distance = direction_distances.get('incoming', 90)
            max_outgoing_distance = direction_distances.get('outgoing', 30)
            
            # 加载 annotation 数据
            json_path = os.path.join(annotations_dir, json_file)
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # 生成 VQA
            vqa_generator = SingleImageVQA(
                data=data, 
                max_incoming_distance=max_incoming_distance,
                max_outgoing_distance=max_outgoing_distance
            )
            qa_pairs = vqa_generator.generate_all_questions()
            
            # 添加图片路径和元数据信息
            for qa in qa_pairs:
                qa['image_path'] = f"{timestep}/high_quality_rgb/{direction_num}.png"
                qa['direction'] = direction_num
                qa['timestep'] = timestep
            
            single_image_qa[f'direction_{direction_num}'] = qa_pairs
        
        return single_image_qa

    # #######################
    # 生成多图 VQA (QA 和 MCQ)
    # #######################
    def _generate_multi_image_vqa(self, timestep_path: str) -> List[Dict]:
        """生成特定 timestep 的多图 VQA
        
        Returns:
            List[qa_pairs]
        """
        annotations_dir = os.path.join(timestep_path, 'annotations')
        timestep = os.path.basename(timestep_path)

        if not os.path.exists(annotations_dir):
            return []
        
        # 收集所有方向的数据
        timestep_data = {}
        for json_file in sorted(os.listdir(annotations_dir)):
            if not json_file.endswith('.json'):
                continue
            
            direction_num = int(os.path.splitext(json_file)[0])
            json_path = os.path.join(annotations_dir, json_file)
            
            with open(json_path, 'r') as f:
                annotation = json.load(f)
            
            timestep_data[f'direction_{direction_num}'] = {
                'annotation': annotation,
                'image_path': f"{timestep}/high_quality_rgb/{direction_num}.png"
            }
        
        # 添加 BEV 图片信息
        timestep_data['bev'] = {
            'image_path': f'{timestep}/high_quality_rgb/bev.png'
        }
        
        # 加载 step_info
        step_info_path = os.path.join(timestep_path, 'step_info.json')
        if os.path.exists(step_info_path):
            with open(step_info_path, 'r') as f:
                step_info = json.load(f)
        else:
            step_info = {}
        
        # 从 global.json 中获取当前 timestep 的信息
        current_timestep = os.path.basename(timestep_path)
        
        # 将 global.json 中的 index2phase 添加到 step_info 中
        if 'index2phase' in self.global_data:
            step_info['index2phase'] = self.global_data['index2phase']
        
        # 将 global.json 中的 phaseInfo 添加到 step_info 中
        if 'phaseInfo' in self.global_data:
            step_info['phaseInfo'] = self.global_data['phaseInfo']

        # 将 global.json 中的 can_perform_action 替换 step_info 中的值
        if 'can_perform_action' in self.global_data:
            global_can_perform = self.global_data['can_perform_action']
            if current_timestep in global_can_perform:
                step_info['can_perform_action'] = global_can_perform[current_timestep]
        
        timestep_data['step_info'] = step_info
        
        # 生成多图 VQA
        multi_vqa_generator = MultiImageVQA(timestep_data, self.distance_mapping)
        qa_pairs = multi_vqa_generator.generate_all_questions()
        
        # 添加图片路径信息
        for qa in qa_pairs:
            qa['images'] = [
                v['image_path'] 
                for k, v in timestep_data.items() 
                if k.startswith('direction_')
            ]
            qa['timestep'] = timestep
        
        return qa_pairs

    # #######################
    # 生成跨时间空间推理选择题
    # #######################
    def _generate_spatial_mcq_for_timestep(
        self, 
        target_timestep: str, 
        all_timesteps_data: Dict[str, Dict],
        num_questions: int = 4
    ) -> List[Dict]:
        """为单个 timestep 生成跨时间空间推理选择题
        
        Args:
            target_timestep: 目标 timestep
            all_timesteps_data: 所有 timesteps 的数据
            num_questions: 要生成的问题数量（默认 2 个）
            
        Returns:
            该 timestep 的跨时间空间推理选择题列表
        """
        if len(all_timesteps_data) < 4:
            return []  # 至少需要 4 个 timesteps 才能生成选择题
        
        if target_timestep not in all_timesteps_data:
            return []
        
        # 使用 CrossTimestepVQA 生成问题
        cross_vqa = CrossTimestepVQA(all_timesteps_data)
        
        # 为当前 timestep 生成指定数量的问题
        mcq_list = []
        for i in range(num_questions):
            if i % 4 == 0:
                # 生成 BEV → View 问题
                mcq = cross_vqa._bev_to_view_mcq_for_specific_timestep(target_timestep)
            elif i % 4 == 1:
                # 生成 View → BEV 问题
                mcq = cross_vqa._view_to_bev_mcq_for_specific_timestep(target_timestep)
            elif i % 4 == 2:
                # 生成时间顺序问题
                mcq = cross_vqa._temporal_order_mcq_for_specific_timestep(target_timestep)
            elif i % 4 == 3:
                # 生成时间间隔问题
                mcq = cross_vqa._temporal_between_mcq_for_specific_timesteps(target_timestep, str(int(target_timestep) + 2))
            
            if mcq and mcq.get('question'):  # 只添加有效问题
                mcq_list.append(mcq)
        
        return mcq_list
    

    # 保存 VQA 结果
    def _save_results(self, timestep_path: str, results: Dict[str, Any]):
        """保存 VQA 结果
        
        Args:
            timestep_path: timestep 目录路径
            results: 包含所有 VQA 结果的字典
        """
        # 创建输出目录
        vqa_dir = os.path.join(timestep_path, 'VQA')
        os.makedirs(vqa_dir, exist_ok=True)
        
        # 1. 保存单图 VQA（按方向分别保存）
        single_vqa_dir = os.path.join(vqa_dir, 'single_image_vqa')
        os.makedirs(single_vqa_dir, exist_ok=True)
        for direction, vqa_pairs in results['single_image_vqa'].items():
            direction_num = direction.split('_')[1]
            output_path = os.path.join(single_vqa_dir, f'{direction_num}.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(vqa_pairs, f, indent=2, ensure_ascii=False)
        
        # 2. 保存多图 VQA
        multi_vqa_path = os.path.join(vqa_dir, 'multi_image_vqa.json')
        with open(multi_vqa_path, 'w', encoding='utf-8') as f:
            json.dump(results['multi_image_vqa'], f, indent=2, ensure_ascii=False)
        
        # 3. 保存汇总的所有 VQA（用于训练和评估）
        all_vqa = []
        for vqa_pairs in results['single_image_vqa'].values():
            all_vqa.extend(vqa_pairs)
        all_vqa.extend(results['multi_image_vqa'])
        
        all_vqa_path = os.path.join(vqa_dir, 'all_vqa.json')
        with open(all_vqa_path, 'w', encoding='utf-8') as f:
            json.dump(all_vqa, f, indent=2, ensure_ascii=False)