'''
Author: Maonan Wang
Date: 2025-12-30
LastEditTime: 2025-12-30
LastEditors: WANG Maonan
Description: Benchmark Sampler
'''

import random
from typing import List, Dict, Any


class BenchmarkSampler:
    """Benchmark 采样器"""
    
    def sample_questions(
        self,
        questions: List[Dict[str, Any]],
        target_count: int,
        question_type: str
    ) -> List[Dict[str, Any]]:
        """采样指定数量的问题
        
        Args:
            questions: 可用问题列表
            target_count: 目标数量
            question_type: 问题类型（用于日志）
            
        Returns:
            采样后的问题列表
        """
        if not questions:
            return []
        
        # 如果可用问题少于目标数量，返回所有问题
        if len(questions) <= target_count:
            return questions
        
        # 随机采样
        return random.sample(questions, target_count)

