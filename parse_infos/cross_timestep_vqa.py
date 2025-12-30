'''
Author: WANG Maonan
Date: 2025-12-12
LastEditors: WANG Maonan
Description: 跨时间步 VQA 生成器 - 生成选择题格式的空间推理问题
LastEditTime: 2025-12-12
'''
import random
from typing import Dict, Any

class CrossTimestepVQA:
    def __init__(self, all_timesteps_data: Dict[str, Any]):
        """初始化跨时间步 VQA 生成器
        
        Args:
            all_timesteps_data: 包含多个 timesteps 的数据
                格式: {
                    'timestep_0': {
                        'direction_0': {'image_path': '...'},
                        'direction_1': {'image_path': '...'},
                        'bev': {'image_path': '...'}
                    },
                    'timestep_10': {...},
                    ...
                }
        """
        self.all_timesteps_data = all_timesteps_data
        self.timestep_keys = sorted(all_timesteps_data.keys(), key=lambda x: int(x))
    
    def _bev_to_view_mcq_for_specific_timestep(self, target_timestep: str) -> Dict[str, Any]:
        """为指定的 timestep 生成 BEV → View 选择题
        
        Args:
            target_timestep: 目标 timestep
            
        Returns:
            选择题字典
        """
        if target_timestep not in self.all_timesteps_data:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        if len(self.timestep_keys) < 2:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        target_data = self.all_timesteps_data[target_timestep]
        
        # 获取目标 timestep 的所有方向
        target_directions = [k for k in target_data.keys() if k.startswith('direction_')]
        if len(target_directions) < 3:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 从目标 timestep 的方向中选择 3 个（如果超过 3 个就选 3 个）
        selected_directions = random.sample(target_directions, 3)
        
        # 从其他 timesteps 中选择 1 个作为不对应的选项
        other_timesteps = [t for t in self.timestep_keys if t != target_timestep]
        if not other_timesteps:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        distractor_timestep = random.choice(other_timesteps)
        distractor_data = self.all_timesteps_data[distractor_timestep]
        
        # 从干扰 timestep 中选择一个方向
        distractor_directions = [k for k in distractor_data.keys() if k.startswith('direction_')]
        if not distractor_directions:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        distractor_direction = random.choice(distractor_directions)
        
        # 构建选项：3 个来自 target_timestep（对应的），1 个来自其他 timestep（不对应的）
        option_images = []
        option_sources = []  # 记录每个选项的来源
        
        # 添加 3 个对应的 views
        for direction in selected_directions:
            view_path = target_data[direction]['image_path']
            option_images.append(view_path)
            direction_num = direction.split('_')[1]
            option_sources.append(('target', direction_num))
        
        # 添加 1 个不对应的 view
        distractor_view_path = distractor_data[distractor_direction]['image_path']
        option_images.append(distractor_view_path)
        distractor_direction_num = distractor_direction.split('_')[1]
        option_sources.append(('distractor', distractor_direction_num))
        
        # 打乱选项顺序
        combined = list(zip(option_images, option_sources))
        random.shuffle(combined)
        option_images, option_sources = zip(*combined)
        
        # 构建选项字典
        options = {}
        correct_answer = ''
        option_labels = ['A', 'B', 'C', 'D']
        
        for i, (img_path, (source_type, direction_num)) in enumerate(zip(option_images, option_sources)):
            label = option_labels[i]
            if source_type == 'target':
                options[label] = f"View from direction {direction_num}"
            else:
                options[label] = f"View from direction {direction_num}"
                correct_answer = label  # 不对应的是正确答案
        
        # 构建问题
        question = f"Given the BEV (bird's-eye view), which directional view does NOT correspond to this BEV?"
        
        result = {
            'question': question,
            'options': options,
            'correct_answer': correct_answer,
            'answer_text': options[correct_answer],
            'bev_image': target_data.get('bev', {}).get('image_path', ''),
            'option_images': list(option_images),
            'images': [target_data.get('bev', {}).get('image_path', '')] + list(option_images),
            'target_timestep': target_timestep,
            'distractor_timestep': distractor_timestep,
            'question_type': 'bev_to_view',
            'category': 'Scene Understanding',
            'task': 'Cross-Timestep Multi Image',
            'subtask': 'BEV to View Matching',
            'capabilities': ['Spatial Reasoning', 'Cross-Timestep Analysis', 'BEV Understanding', 'View Matching']
        }
        
        return result
    
    def _view_to_bev_mcq_for_specific_timestep(self, target_timestep: str) -> Dict[str, Any]:
        """为指定的 timestep 生成 View → BEV 选择题
        
        Args:
            target_timestep: 目标 timestep
            
        Returns:
            选择题字典
        """
        if target_timestep not in self.all_timesteps_data:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        if len(self.timestep_keys) < 4:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        target_data = self.all_timesteps_data[target_timestep]
        
        # 获取目标 timestep 的方向
        target_directions = [k for k in target_data.keys() if k.startswith('direction_')]
        if not target_directions:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 随机选择一个方向
        target_direction = random.choice(target_directions)
        direction_num = target_direction.split('_')[1]
        view_path = target_data[target_direction]['image_path']
        
        # 选择 3 个其他 timesteps 作为不对应的选项
        other_timesteps = [t for t in self.timestep_keys if t != target_timestep]
        if len(other_timesteps) < 3:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        distractor_timesteps = random.sample(other_timesteps, 3)
        
        # 构建选项：1 个对应的 BEV（target_timestep），3 个不对应的 BEVs（其他 timesteps）
        option_images = []
        option_sources = []  # 记录每个选项的来源
        
        # 添加对应的 BEV
        target_bev_path = target_data.get('bev', {}).get('image_path', '')
        if not target_bev_path:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        option_images.append(target_bev_path)
        option_sources.append(('target', target_timestep))
        
        # 添加 3 个不对应的 BEVs
        for timestep in distractor_timesteps:
            timestep_data = self.all_timesteps_data[timestep]
            bev_path = timestep_data.get('bev', {}).get('image_path', '')
            if not bev_path:
                return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
            option_images.append(bev_path)
            option_sources.append(('distractor', timestep))
        
        # 打乱选项顺序
        combined = list(zip(option_images, option_sources))
        random.shuffle(combined)
        option_images, option_sources = zip(*combined)
        
        # 构建选项字典
        options = {}
        distractor_answers = []  # 收集所有不对应的选项
        option_labels = ['A', 'B', 'C', 'D']
        
        for i, (img_path, (source_type, timestep)) in enumerate(zip(option_images, option_sources)):
            label = option_labels[i]
            options[label] = f"BEV image {i+1}"
            if source_type == 'distractor':
                distractor_answers.append(label)
        
        # 从 3 个不对应的选项中随机选择一个作为正确答案
        correct_answer = random.choice(distractor_answers)
        
        # 构建问题
        question = f"Given the directional view, which BEV (bird's-eye view) does NOT correspond to this view?"
        
        result = {
            'question': question,
            'options': options,
            'correct_answer': correct_answer,
            'answer_text': options[correct_answer],
            'view_image': view_path,
            'option_images': list(option_images),
            'images': [view_path] + list(option_images),
            'target_timestep': target_timestep,
            'direction': direction_num,
            'question_type': 'view_to_bev',
            'category': 'Scene Understanding',
            'task': 'Cross-Timestep Multi Image',
            'subtask': 'View to BEV Matching',
            'capabilities': ['Spatial Reasoning', 'Cross-Timestep Analysis', 'View Understanding', 'BEV Matching']
        }
        
        return result
    
    def _temporal_order_mcq_for_specific_timestep(self, target_timestep: str) -> Dict[str, Any]:
        """为指定的 timestep 生成时间顺序选择题 - 从该 timestep 开始选择 4 个相邻 timesteps 的相同 view 图片，询问哪个最先发生
        
        Args:
            target_timestep: 目标 timestep（作为4个连续timesteps中的第一个）
            
        Returns:
            选择题字典
        """
        if target_timestep not in self.all_timesteps_data:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        if len(self.timestep_keys) < 4:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 找到 target_timestep 的索引
        try:
            start_idx = self.timestep_keys.index(target_timestep)
        except ValueError:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 检查是否有足够的后续 timesteps
        if start_idx + 4 > len(self.timestep_keys):
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 选择从 target_timestep 开始的 4 个连续 timesteps
        selected_timesteps = self.timestep_keys[start_idx:start_idx + 4]
        
        # 获取第一个 timestep 的可用方向
        first_timestep_data = self.all_timesteps_data[selected_timesteps[0]]
        available_directions = [k for k in first_timestep_data.keys() if k.startswith('direction_')]
        
        if not available_directions:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 随机选择一个方向
        target_direction = random.choice(available_directions)
        direction_num = target_direction.split('_')[1]
        
        # 检查所有选定的 timesteps 是否都有该方向
        for timestep in selected_timesteps:
            if target_direction not in self.all_timesteps_data[timestep]:
                return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 打乱顺序构建选项
        shuffled_timesteps = selected_timesteps.copy()
        random.shuffle(shuffled_timesteps)
        
        options = {}
        option_images = []
        correct_answer = ''
        option_labels = ['A', 'B', 'C', 'D']
        earliest_timestep = selected_timesteps[0]  # 因为已经排序，第一个就是最早的
        
        for i, timestep in enumerate(shuffled_timesteps):
            label = option_labels[i]
            timestep_data = self.all_timesteps_data[timestep]
            view_path = timestep_data[target_direction]['image_path']
            
            options[label] = f"Image from {timestep}"
            option_images.append(view_path)
            
            if timestep == earliest_timestep:
                correct_answer = label
        
        # 构建问题
        question = f"Among these four images from the same viewpoint at different timesteps, which one occurred first?"
        
        result = {
            'question': question,
            'options': options,
            'correct_answer': correct_answer,
            'answer_text': options[correct_answer],
            'images': option_images,
            'target_timestep': target_timestep,
            'earliest_timestep': earliest_timestep,
            'direction': direction_num,
            'timesteps': selected_timesteps,
            'question_type': 'temporal_order',
            'category': 'Temporal Reasoning',
            'task': 'Cross-Timestep Multi Image',
            'subtask': 'Temporal Order',
            'capabilities': ['Temporal Reasoning', 'Cross-Timestep Analysis', 'Sequential Understanding']
        }
        
        return result
    
    def _temporal_between_mcq_for_specific_timesteps(self, ref_timestep_1: str, ref_timestep_2: str) -> Dict[str, Any]:
        """为指定的两个 timesteps 生成时间区间选择题 - 询问哪个时间点在这两者之间发生
        
        Args:
            ref_timestep_1: 第一个参考 timestep（较早的）
            ref_timestep_2: 第二个参考 timestep（较晚的）
            
        Returns:
            选择题字典
        """
        if ref_timestep_1 not in self.all_timesteps_data or ref_timestep_2 not in self.all_timesteps_data:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        if len(self.timestep_keys) < 6:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 获取两个参考 timestep 的索引
        try:
            ref1_idx = self.timestep_keys.index(ref_timestep_1)
            ref2_idx = self.timestep_keys.index(ref_timestep_2)
        except ValueError:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 确保 ref1 在 ref2 之前，如果不是则交换
        if ref1_idx > ref2_idx:
            ref1_idx, ref2_idx = ref2_idx, ref1_idx
            ref_timestep_1, ref_timestep_2 = ref_timestep_2, ref_timestep_1
        
        # 检查两个参考点之间是否有至少一个 timestep
        if ref2_idx - ref1_idx < 2:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 获取可用的方向
        ref1_data = self.all_timesteps_data[ref_timestep_1]
        available_directions = [k for k in ref1_data.keys() if k.startswith('direction_')]
        
        if not available_directions:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        target_direction = random.choice(available_directions)
        direction_num = target_direction.split('_')[1]
        
        # 检查两个参考 timestep 是否都有该方向
        if target_direction not in self.all_timesteps_data[ref_timestep_2]:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 选择正确答案：在两个参考点之间的 timestep
        between_timesteps = self.timestep_keys[ref1_idx + 1:ref2_idx]
        if not between_timesteps:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        correct_timestep = random.choice(between_timesteps)
        
        # 选择干扰项：尽量选择在之前和之后的 timesteps
        before_timesteps = self.timestep_keys[:ref1_idx]
        after_timesteps = self.timestep_keys[ref2_idx + 1:]
        
        distractor_timesteps = []
        
        # 尝试添加一个在之前的
        if before_timesteps:
            distractor_timesteps.append(random.choice(before_timesteps))
        
        # 尝试添加两个在之后的
        if len(after_timesteps) >= 2:
            distractor_timesteps.extend(random.sample(after_timesteps, 2))
        elif len(after_timesteps) == 1:
            distractor_timesteps.append(after_timesteps[0])
        
        # 如果干扰项不够3个，从所有不在区间内且不是参考点的 timesteps 中补充
        if len(distractor_timesteps) < 3:
            available = [t for t in self.timestep_keys 
                        if t not in [correct_timestep, ref_timestep_1, ref_timestep_2] 
                        and t not in distractor_timesteps
                        and t not in between_timesteps]
            if available:
                needed = 3 - len(distractor_timesteps)
                distractor_timesteps.extend(random.sample(available, min(needed, len(available))))
        
        if len(distractor_timesteps) < 3:
            return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 检查所有选项的 timesteps 是否都有该方向
        all_option_timesteps = [correct_timestep] + distractor_timesteps[:3]
        for timestep in all_option_timesteps:
            if target_direction not in self.all_timesteps_data[timestep]:
                return {'question': '', 'options': {}, 'correct_answer': '', 'images': []}
        
        # 构建选项
        option_timesteps = all_option_timesteps.copy()
        random.shuffle(option_timesteps)
        
        options = {}
        option_images = []
        correct_answer = ''
        option_labels = ['A', 'B', 'C', 'D']
        
        for i, timestep in enumerate(option_timesteps):
            label = option_labels[i]
            timestep_data = self.all_timesteps_data[timestep]
            view_path = timestep_data[target_direction]['image_path']
            
            options[label] = f"Image from {timestep}"
            option_images.append(view_path)
            
            if timestep == correct_timestep:
                correct_answer = label
        
        # 获取参考图片
        ref1_path = self.all_timesteps_data[ref_timestep_1][target_direction]['image_path']
        ref2_path = self.all_timesteps_data[ref_timestep_2][target_direction]['image_path']
        
        # 构建问题
        question = f"Given two reference images from {ref_timestep_1} and {ref_timestep_2}, which of the following images occurred between these two timesteps?"
        
        result = {
            'question': question,
            'options': options,
            'correct_answer': correct_answer,
            'answer_text': options[correct_answer],
            'reference_images': [ref1_path, ref2_path],
            'option_images': option_images,
            'images': [ref1_path, ref2_path] + option_images,
            'reference_timesteps': [ref_timestep_1, ref_timestep_2],
            'correct_timestep': correct_timestep,
            'direction': direction_num,
            'question_type': 'temporal_between',
            'category': 'Temporal Reasoning',
            'task': 'Cross-Timestep Multi Image',
            'subtask': 'Temporal Interval',
            'capabilities': ['Temporal Reasoning', 'Cross-Timestep Analysis', 'Interval Understanding']
        }
        
        return result