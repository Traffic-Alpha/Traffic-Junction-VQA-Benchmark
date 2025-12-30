'''
Author: Maonan Wang
Date: 2025-12-30
LastEditTime: 2025-12-30
LastEditors: WANG Maonan
Description: Image Copier
'''

import shutil
from pathlib import Path
from typing import Dict, Any

class ImageCopier:
    """图片复制工具"""
    
    def __init__(self, source_root: Path, target_dir: Path):
        """初始化
        
        Args:
            source_root: 源数据根目录
            target_dir: 目标图片目录
        """
        self.source_root = Path(source_root)
        self.target_dir = Path(target_dir)
        self.copied_images = set()  # 记录已复制的图片，避免重复
    
    def copy_and_update_paths(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """复制图片并更新问题中的路径
        
        Args:
            question: 问题字典
            
        Returns:
            更新后的问题字典
        """
        new_question = question.copy()
        
        # 处理单张图片
        if 'image_path' in question:
            old_path = question['image_path']
            new_path = self._copy_image(old_path)
            new_question['image_path'] = new_path
        
        # 处理多张图片
        if 'images' in question:
            old_paths = question['images']
            new_paths = [self._copy_image(p) for p in old_paths]
            new_question['images'] = new_paths
        
        # 处理其他可能的图片字段
        for key in ['bev_image', 'view_image']:
            if key in question:
                old_path = question[key]
                new_path = self._copy_image(old_path)
                new_question[key] = new_path
        
        if 'option_images' in question:
            old_paths = question['option_images']
            new_paths = [self._copy_image(p) for p in old_paths]
            new_question['option_images'] = new_paths
        
        if 'reference_images' in question:
            old_paths = question['reference_images']
            new_paths = [self._copy_image(p) for p in old_paths]
            new_question['reference_images'] = new_paths
        
        return new_question
    
    def _copy_image(self, relative_path: str) -> str:
        """复制单张图片
        
        Args:
            relative_path: 相对于 source_root 的路径（如 "100/high_quality_rgb/0.png"）
            
        Returns:
            新的相对路径（相对于 images 目录，去掉 high_quality_rgb）
        """
        if not relative_path:
            return relative_path
        
        # 简化路径：去掉 high_quality_rgb
        # "100/high_quality_rgb/0.png" -> "100/0.png"
        simplified_path = relative_path.replace('/high_quality_rgb/', '/')
        
        # 如果已经复制过，直接返回
        if simplified_path in self.copied_images:
            return f"images/{simplified_path}"
        
        # 源文件路径（保持原始路径）
        source_file = self.source_root / relative_path
        
        # 目标文件路径（使用简化路径）
        target_file = self.target_dir / simplified_path
        
        # 创建目标目录
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            self.copied_images.add(simplified_path)
        else:
            print(f"Warning: Image not found: {source_file}")
        
        return f"images/{simplified_path}"