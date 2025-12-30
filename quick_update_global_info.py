#!/usr/bin/env python3
"""
JSON True Values Shifter
将 JSON 文件中指定字段的所有 true 值往后移动指定步长

使用方法:
    python shift_json_true_values.py <json_file_path> [options]

示例:
    # 基本使用（往后移动1步）
    python shift_json_true_values.py global.json
    
    # 指定字段路径和移动步长
    python shift_json_true_values.py global.json --field can_perform_action --shift 2
    
    # 往前移动（使用负数）
    python shift_json_true_values.py global.json --shift -1
    
    # 创建备份
    python shift_json_true_values.py global.json --backup
"""

import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime


def shift_true_values(data_dict, shift_amount=1):
    """
    将字典中所有 true 值往后（或往前）移动指定步长
    
    Args:
        data_dict: 要处理的字典
        shift_amount: 移动步长，正数往后，负数往前
    
    Returns:
        处理后的字典和统计信息
    """
    # 找到所有值为 true 的键
    true_keys = [int(key) for key, value in data_dict.items() if value is True]
    
    if not true_keys:
        print("警告: 未找到任何 true 值")
        return data_dict, {"count": 0, "original": [], "new": []}
    
    # 排序（如果往后移动就从大到小处理，避免覆盖；往前移动就从小到大）
    true_keys.sort(reverse=(shift_amount > 0))
    
    # 创建新字典
    new_dict = data_dict.copy()
    
    # 先将所有原来为 true 的键设置为 false
    for key in true_keys:
        new_dict[str(key)] = False
    
    # 然后将 key+shift_amount 的位置设置为 true
    for key in true_keys:
        new_key = key + shift_amount
        if new_key < 0:
            print(f"警告: 键 {key} 移动后变成负数 {new_key}，已跳过")
            continue
        new_dict[str(new_key)] = True
    
    # 统计信息
    stats = {
        "count": len(true_keys),
        "original": sorted(true_keys),
        "new": sorted([k + shift_amount for k in true_keys if k + shift_amount >= 0])
    }
    
    return new_dict, stats


def get_nested_value(data, field_path):
    """
    根据字段路径获取嵌套字典的值
    
    Args:
        data: JSON 数据
        field_path: 字段路径，用点分隔，如 "can_perform_action" 或 "a.b.c"
    
    Returns:
        字段对应的值，如果路径不存在则返回 None
    """
    keys = field_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    
    return current


def set_nested_value(data, field_path, value):
    """
    根据字段路径设置嵌套字典的值
    
    Args:
        data: JSON 数据
        field_path: 字段路径，用点分隔
        value: 要设置的值
    """
    keys = field_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def main():
    parser = argparse.ArgumentParser(
        description='将 JSON 文件中指定字段的所有 true 值往后移动指定步长',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'json_file',
        type=str,
        help='要处理的 JSON 文件路径'
    )
    
    parser.add_argument(
        '-f', '--field',
        type=str,
        default='can_perform_action',
        help='要处理的字段路径（支持嵌套，用点分隔）默认: can_perform_action'
    )
    
    parser.add_argument(
        '-s', '--shift',
        type=int,
        default=1,
        help='移动步长（正数往后，负数往前）默认: 1'
    )
    
    parser.add_argument(
        '-b', '--backup',
        action='store_true',
        help='是否备份原文件'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出文件路径（不指定则覆盖原文件）'
    )
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"错误: 文件不存在: {args.json_file}")
        return 1
    
    # 备份原文件
    if args.backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = json_path.with_suffix(f'.backup_global_{timestamp}.json')
        shutil.copy2(json_path, backup_path)
        print(f"✓ 已创建备份: {backup_path}")
    
    # 读取 JSON 文件
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败: {e}")
        return 1
    except Exception as e:
        print(f"错误: 读取文件失败: {e}")
        return 1
    
    # 获取要处理的字段
    target_field = get_nested_value(data, args.field)
    if target_field is None:
        print(f"错误: 字段 '{args.field}' 不存在")
        return 1
    
    if not isinstance(target_field, dict):
        print(f"错误: 字段 '{args.field}' 不是字典类型")
        return 1
    
    # 处理数据
    print(f"\n{'='*60}")
    print(f"处理文件: {json_path}")
    print(f"处理字段: {args.field}")
    print(f"移动步长: {args.shift} ({'往后' if args.shift > 0 else '往前'})")
    print(f"{'='*60}\n")
    
    new_field, stats = shift_true_values(target_field, args.shift)
    
    # 更新数据
    set_nested_value(data, args.field, new_field)
    
    # 保存文件
    output_path = Path(args.output) if args.output else json_path
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✓ 文件已保存: {output_path}")
    except Exception as e:
        print(f"错误: 保存文件失败: {e}")
        return 1
    
    # 显示统计信息
    print(f"\n{'='*60}")
    print(f"处理完成！")
    print(f"{'='*60}")
    print(f"处理的 true 值数量: {stats['count']}")
    
    if stats['count'] > 0:
        print(f"\n原始 true 的键:")
        print(f"  范围: {stats['original'][0]} ~ {stats['original'][-1]}")
        print(f"  前5个: {stats['original'][:5]}")
        print(f"  后5个: {stats['original'][-5:]}")
        
        print(f"\n新的 true 的键:")
        print(f"  范围: {stats['new'][0]} ~ {stats['new'][-1]}")
        print(f"  前5个: {stats['new'][:5]}")
        print(f"  后5个: {stats['new'][-5:]}")
    
    print(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    exit(main())

