'''
Author: Maonan Wang
Date: 2025-12-30
LastEditTime: 2025-12-30
LastEditors: WANG Maonan
Description: Question Filter
'''

from typing import List, Dict, Any, Optional

class QuestionFilter:
    """问题过滤和分类器"""
    
    def classify_question(self, question: Dict[str, Any]) -> Optional[str]:
        """将问题分类到对应的类型
        
        Args:
            question: 问题字典
            
        Returns:
            问题类型标识符，如果无法分类则返回 None
        """
        category = question.get('category', '')
        task = question.get('task', '')
        subtask = question.get('subtask', '')
        q_text = question.get('question', '').lower()
        q_type = question.get('question_type', '')
        
        # L1.1 Obj - 目标级感知
        if category == 'Vehicle Analysis' and subtask == 'Counting' and task == 'Single Image':
            # Q1: 图片有多少车（总计，包括 incoming and outgoing）
            if 'how many vehicles' in q_text and 'incoming and outgoing' in q_text:
                return 'l1.1_obj_q1_vehicle_count'
        
        if category == 'Special Vehicles':
            if subtask == 'Existence':
                return 'l1.1_obj_q2_special_vehicle_exist'
            elif subtask == 'Recognition' and task == 'Single Image':
                return 'l1.1_obj_q3_special_vehicle_type'
        
        if category == 'Special Events':
            if subtask == 'Existence':
                return 'l1.1_obj_q4_special_event_exist'
            elif subtask == 'Recognition' and task == 'Single Image':
                return 'l1.1_obj_q5_special_event_type'
        
        # L1.2 Topo - 交通结构理解
        if category == 'Road Infrastructure' and subtask == 'Counting':
            if 'incoming lanes' in q_text:
                return 'l1.2_topo_q1_incoming_lanes_count'
            elif 'outgoing lanes' in q_text:
                return 'l1.2_topo_q2_outgoing_lanes_count'
        
        if category == 'Vehicle Analysis' and task == 'Single Image' and subtask == 'Counting':
            # Q7: 特定车道的车辆数量 (incoming lane X 或 outgoing lane X)
            if ('incoming lane' in q_text or 'outgoing lane' in q_text):
                return 'l1.2_topo_q7_lane_vehicles'
            # Q5: 所有 incoming 车道的车辆总数
            elif 'incoming' in q_text:
                return 'l1.2_topo_q5_incoming_vehicles'
            # Q6: 所有 outgoing 车道的车辆总数
            elif 'outgoing' in q_text:
                return 'l1.2_topo_q6_outgoing_vehicles'
        
        if category == 'Special Vehicles' and subtask == 'Localization' and task == 'Single Image':
            return 'l1.2_topo_q8_special_vehicle_lane'
        
        if category == 'Special Events' and subtask == 'Localization' and task == 'Single Image':
            return 'l1.2_topo_q9_special_event_lane'
        
        # L2.1 View - 多视角空间一致性
        if task == 'Multi Image':
            if category == 'Vehicle Analysis' and subtask == 'Counting':
                return 'l2.1_view_q1_most_vehicles'
            elif category == 'Special Vehicles' and subtask == 'Localization':
                return 'l2.1_view_q2_special_vehicle_location'
        
        if task == 'Cross-Timestep Multi Image':
            if q_type == 'bev_to_view':
                return 'l2.1_view_q4_bev_to_view'
            elif q_type == 'view_to_bev':
                return 'l2.1_view_q5_view_to_bev'
        
        # L2.2 Time - 跨时间理解
        if task == 'Cross-Timestep Multi Image':
            if q_type == 'temporal_order':
                return 'l2.2_time_q1_temporal_order'
            elif q_type == 'temporal_between':
                return 'l2.2_time_q3_temporal_between'
        
        # L3 Dec - 决策支持
        if category == 'Traffic Phase Analysis':
            if subtask == 'Vehicle Counting':
                return 'l3_dec_q1_phase_most_vehicles'
            elif subtask == 'Accident Detection':
                return 'l3_dec_q2_phase_accident'
            elif subtask == 'Special Vehicle Detection':
                return 'l3_dec_q3_phase_special_vehicle'
            elif subtask == 'Signal State Recognition':
                return 'l3_dec_q4_phase_green_light'
        
        if category == 'Comprehensive Analysis' and subtask == 'Decision Making':
            return 'l3_dec_q5_phase_decision'
        
        return None
    
    def filter_has_special_vehicle(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出包含特殊车辆的问题
        
        Args:
            questions: 问题列表
            
        Returns:
            过滤后的问题列表
        """
        filtered = []
        for q in questions:
            answer = q.get('answer', '').lower()
            # 检查答案中是否提到了特殊车辆
            if 'yes' in answer or 'police' in answer or 'ambulance' in answer or 'fire truck' in answer:
                if 'no emergency vehicles' not in answer.lower():
                    filtered.append(q)
        return filtered
    
    def filter_no_special_vehicle(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出不包含特殊车辆的问题（常规情况）
        
        Args:
            questions: 问题列表
            
        Returns:
            过滤后的问题列表
        """
        filtered = []
        for q in questions:
            answer = q.get('answer', '').lower()
            # 检查答案中是否明确说明没有特殊车辆
            if 'no emergency vehicles' in answer or ('no' in answer and 'emergency' in q.get('question', '').lower()):
                filtered.append(q)
        return filtered
    
    def filter_has_special_event(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出包含特殊事件的问题
        
        Args:
            questions: 问题列表
            
        Returns:
            过滤后的问题列表
        """
        filtered = []
        for q in questions:
            answer = q.get('answer', '').lower()
            # 检查答案中是否提到了特殊事件
            # 方法1: 明确提到特殊事件类型
            has_event_type = ('barrier' in answer or 'collision' in answer or 
                            'branch' in answer or 'pedestrian' in answer or 
                            'crash' in answer)
            # 方法2: Yes 回答 + 特殊事件问题
            is_yes_answer = 'yes' in answer and 'accident' in q.get('question', '').lower()
            
            if (has_event_type or is_yes_answer) and 'no visible' not in answer and 'no traffic' not in answer:
                filtered.append(q)
        return filtered
    
    def filter_no_special_event(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出不包含特殊事件的问题（常规情况）
        
        Args:
            questions: 问题列表
            
        Returns:
            过滤后的问题列表
        """
        filtered = []
        for q in questions:
            answer = q.get('answer', '').lower()
            # 检查答案中是否明确说明没有特殊事件
            if 'no visible traffic accidents' in answer or 'no traffic accidents' in answer:
                filtered.append(q)
        return filtered