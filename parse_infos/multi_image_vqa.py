'''
Author: WANG Maonan
Date: 2025-12-12
LastEditors: WANG Maonan
Description: 多图 VQA 生成器 - 用于生成跨多张图片的 VQA 问题（已包含 MCQ 格式）
LastEditTime: 2025-12-18
'''
import random
from typing import Dict, Any

# Distance thresholds in meters (adjustable)
CLOSE_RANGE = 25  # Clear visibility zone
MID_RANGE = 40 # Partial visibility

class MultiImageVQA:
    def __init__(self, timestep_data: Dict[str, Any], distance_mapping: Dict[int, Dict[str, float]] = None):
        """初始化多图 VQA 生成器
        
        Args:
            timestep_data: 包含一个 timestep 所有方向的数据
                格式: {
                    'direction_0': {'annotation': {...}, 'image_path': '...'},
                    'direction_1': {...},
                    'direction_2': {...},
                    'bev': {'image_path': '...'},
                    'step_info': {...}
                }

            distance_mapping: 不同方向的观测距离映射，需要区分 incoming 和 outgoing
                例如: {
                    0: {'incoming': 90, 'outgoing': 30},
                    1: {'incoming': 90, 'outgoing': 30},
                }
        """
        self.timestep_data = timestep_data
        self.directions = [k for k in timestep_data.keys() if k.startswith('direction_')]
        self.distance_mapping = distance_mapping or {}
        
        # 获取 index2phase 映射关系
        step_info = timestep_data.get('step_info', {})
        self.index2phase = step_info.get('index2phase', {})
        self.phaseInfo = step_info.get('phaseInfo', '')
    
    def _get_distance_threshold(self, direction: str, lane_type: str = 'incoming') -> float:
        """获取指定方向和车道类型的距离阈值
        
        Args:
            direction: 方向名称（如 'direction_0'）
            lane_type: 车道类型，'incoming' 或 'outgoing'
            
        Returns:
            距离阈值（米）
        """
        # 从方向名称中提取数字
        direction_num = int(direction.split('_')[1])
        
        # 获取该方向的距离配置
        direction_distances = self.distance_mapping.get(
            direction_num,
            {'incoming': 60, 'outgoing': 40}  # 默认值
        )
        
        return direction_distances.get(lane_type, 90 if lane_type == 'incoming' else 30)
    
    def generate_all_questions(self):
        """生成所有多图 VQA 问题
        """
        questions = []
        questions.extend(self._generate_comparative_questions())      # 1. 比较类问题
        questions.extend(self._generate_identification_questions())   # 2. 识别与定位类问题
        questions.extend(self._generate_decision_questions())         # 3. 决策类问题
        
        return questions
    
    def _generate_comparative_questions(self):
        """生成比较类问题 - 比较不同方向的某些属性
        """
        return [
            self._which_image_has_most_vehicles(),  # 哪个方向车辆最多
        ]
    
    def _generate_identification_questions(self):
        """生成识别与定位类问题 - 识别特定内容在哪个方向
        """
        return [
            self._which_image_has_special_vehicle(),  # 识别特殊车辆在哪个方向
            self._which_image_has_accident(),         # 识别特殊事件在哪个方向
        ]
    
    def _generate_decision_questions(self):
        """生成决策类问题
        """
        step_info = self.timestep_data.get('step_info', {})
        can_perform_action = step_info.get('can_perform_action', False)
        
        questions = []
        
        # 添加基于 traffic phase 的问题
        questions.extend([
            self._which_phase_has_most_vehicles(),      # 哪一个相位车辆最多
            self._which_phase_has_accident(),           # 事故影响哪一个相位
            self._which_phase_has_special_vehicle(),    # 特殊车辆在哪一个相位
            self._which_phase_is_green(),               # 当前哪一个相位是绿灯
        ])
        
        if can_perform_action:
            questions.append(self._generate_traffic_light_decision())  # 交通信号灯决策
        
        return questions
    
    # ==================
    # 1. 比较类问题
    # ==================
    def _which_image_has_most_vehicles(self):
        """哪张图车辆数最多
        """
        ACCIDENT_TYPES = [
            'barrier_A', 'barrier_B', 'barrier_C', 'barrier_D', 'barrier_E',
            'tree_branch_1lane', 'tree_branch_3lanes',
            'pedestrian', 'crash_vehicle_1lane', 'crash_vehicle_3lanes',
            'other_accidents',
        ]
        
        question = "These images are captured by cameras at an intersection, each showing a different incoming direction. Which direction has the most vehicles, only considering the vehicles in the incoming lanes? Please provide the image index."
        
        # 统计每个方向的车辆数
        direction_counts = {}
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
                
            annotation = self.timestep_data[direction].get('annotation', {})
            vehicles = annotation.get('vehicles', {})
            in_lanes = annotation.get('in_lanes', {})
            in_road = annotation.get('in_road', '')
            
            # 获取该方向的 incoming 可视范围
            max_incoming_distance = self._get_distance_threshold(direction, 'incoming')
            
            # 计算该方向可见的车辆数
            count = 0
            for v in vehicles.values():
                v_type = v.get('vehicle_type', '')
                lane_id = v.get('lane_id', '')
                road_id = v.get('road_id', '')
                
                # 跳过事故类型
                if v_type in ACCIDENT_TYPES:
                    continue
                
                # 只统计进入路口的车辆
                if lane_id in in_lanes and road_id == in_road:
                    # 计算到路口的距离
                    lane_length = in_lanes[lane_id]
                    lane_position = v.get('lane_position', 0)
                    distance = lane_length - lane_position
                    
                    # 只统计可见范围内的车辆
                    if distance <= max_incoming_distance:
                        count += 1
            
            direction_counts[direction] = count
        
        # 找到车辆最多的方向
        if not direction_counts or max(direction_counts.values()) == 0:
            answer = "No vehicles are clearly visible in any direction image."
        else:
            max_count = max(direction_counts.values())
            max_directions = [d for d, c in direction_counts.items() if c == max_count]
            
            if len(max_directions) == 1:
                direction_num = max_directions[0].split('_')[1]
                answer = f"Image index {direction_num} has the most vehicles with {max_count} vehicles visible in the incoming lanes."
            else:
                direction_nums = [d.split('_')[1] for d in max_directions]
                answer = f"Image indices {', '.join(direction_nums)} have the same number of vehicles ({max_count} each) in the incoming lanes."
        
        # 生成 MCQ 选项（方向索引）
        # 找到正确答案的方向索引
        if not direction_counts or max(direction_counts.values()) == 0:
            correct_option_text = "None"
        else:
            max_count = max(direction_counts.values())
            max_directions = [d for d, c in direction_counts.items() if c == max_count]
            
            if len(max_directions) == 1:
                direction_num = max_directions[0].split('_')[1]
                correct_option_text = f"Image Index {direction_num}"
            else:
                # 多个方向车辆数相同，选择第一个
                direction_num = max_directions[0].split('_')[1]
                correct_option_text = f"Image Index {direction_num}"
        
        # 生成所有可能的方向选项
        all_direction_options = [f"Image Index {d.split('_')[1]}" for d in self.directions]
        
        # 生成干扰项
        distractors = [opt for opt in all_direction_options if opt != correct_option_text] # 不包括正确答案
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))] # 最多生成 3 个干扰项
        
        # 生成选项
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Vehicle Analysis',
            'task': 'Multi Image',
            'subtask': 'Counting',
            'capabilities': ['Object Detection', 'Distance Estimation', 'Cross-Image Comparison', 'Quantitative Analysis']
        }
    
    # ========================
    # 2. 识别与定位类问题
    # ========================
    def _which_image_has_special_vehicle(self):
        """识别特殊车辆在哪个方向
        """
        question = "These images are captured by cameras at an intersection, each showing a different incoming direction. In which image(s) are emergency vehicles (police cars, ambulances, or fire trucks) visible? Please provide the image index."
        
        # 查找包含特殊车辆的方向
        special_vehicle_directions = {}
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
                
            annotation = self.timestep_data[direction].get('annotation', {})
            vehicles = annotation.get('vehicles', {})
            in_lanes = annotation.get('in_lanes', {})
            in_road = annotation.get('in_road', '')
            
            # 获取该方向的 incoming 可视范围
            max_incoming_distance = self._get_distance_threshold(direction, 'incoming')
            
            special_vehicles = []
            for v in vehicles.values():
                v_type = v.get('vehicle_type', '').lower()
                lane_id = v.get('lane_id', '')
                road_id = v.get('road_id', '')
                
                if v_type in ['police', 'emergency', 'fire_engine']:
                    # 只统计进入路口的特殊车辆
                    if lane_id in in_lanes and road_id == in_road:
                        # 计算到路口的距离
                        lane_length = in_lanes[lane_id]
                        lane_position = v.get('lane_position', 0)
                        distance = lane_length - lane_position
                        
                        # 只统计可见范围内的车辆
                        if distance <= max_incoming_distance:
                            type_mapping = {
                                'police': 'police car',
                                'emergency': 'ambulance',
                                'fire_engine': 'fire truck',
                            }
                            special_vehicles.append(type_mapping.get(v_type, v_type))
            
            if special_vehicles:
                special_vehicle_directions[direction] = special_vehicles
        
        # 构建答案
        if not special_vehicle_directions:
            answer = "No emergency vehicles are visible in any of the images."
        else:
            descriptions = []
            for direction, vehicles in sorted(special_vehicle_directions.items()):
                direction_num = direction.split('_')[1]
                if len(vehicles) == 1:
                    descriptions.append(f"image index {direction_num} shows a {vehicles[0]}")
                else:
                    vehicle_list = ", ".join(set(vehicles))
                    descriptions.append(f"image index {direction_num} shows {vehicle_list}")
            
            if len(descriptions) == 1:
                answer = f"Emergency vehicles are visible in {descriptions[0]}."
            else:
                answer = f"Emergency vehicles are visible in multiple images: {'; '.join(descriptions)}."
        
        # 生成 MCQ 选项（方向索引）
        # 找到正确答案的方向索引
        if not special_vehicle_directions:
            correct_option_text = "None"
        else:
            # 选择第一个有特殊车辆的方向
            first_direction = sorted(special_vehicle_directions.keys())[0]
            direction_num = first_direction.split('_')[1]
            correct_option_text = f"Image Index {direction_num}"
        
        # 生成所有可能的方向选项
        all_direction_options = [f"Image Index {d.split('_')[1]}" for d in self.directions] + ["None"]
        
        # 生成干扰项
        distractors = [opt for opt in all_direction_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))]
        
        # 生成选项
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Special Vehicles',
            'task': 'Multi Image',
            'subtask': 'Localization',
            'capabilities': ['Object Detection', 'Vehicle Classification', 'Distance Estimation', 'Cross-Image Analysis']
        }
    
    def _which_image_has_accident(self):
        """识别特殊事件在哪个图
        """
        ACCIDENT_TYPES = {
            'barrier_A': 'safety barrier',
            'barrier_B': 'safety barrier',
            'barrier_C': 'safety barrier',
            'barrier_D': 'safety barrier',
            'barrier_E': 'safety barrier',
            'tree_branch_1lane': 'fallen tree branch',
            'tree_branch_3lanes': 'fallen tree branches',
            'pedestrian': 'pedestrian incident',
            'crash_vehicle_1lane': 'vehicle collision',
            'crash_vehicle_3lanes': 'multi-vehicle collision',
        }
        
        question = "These images are captured by cameras at an intersection, each showing a different incoming direction. In which image(s) are traffic accidents or obstructions visible? Please provide the image index."
        
        # 查找包含事故的方向
        accident_directions = {}
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
                
            annotation = self.timestep_data[direction].get('annotation', {})
            vehicles = annotation.get('vehicles', {})
            
            accidents = []
            accidents_type = []
            for v in vehicles.values():
                v_type = v.get('vehicle_type', '')
                if (v_type in ACCIDENT_TYPES) and (v_type not in accidents_type):
                    accident_desc = ACCIDENT_TYPES[v_type]
                    accidents.append(accident_desc)
                    accidents_type.append(v_type)
            
            if accidents:
                accident_directions[direction] = accidents
        
        # 构建答案
        if not accident_directions:
            answer = "No traffic accidents or obstructions are visible in any of the images."
        else:
            descriptions = []
            for direction, accidents in sorted(accident_directions.items()):
                direction_num = direction.split('_')[1]
                if len(accidents) == 1:
                    descriptions.append(f"Image index {direction_num} shows {accidents[0]}")
                else:
                    accident_list = ", ".join(accidents[:-1]) + " and " + accidents[-1]
                    descriptions.append(f"Image index {direction_num} shows {accident_list}")
            
            if len(descriptions) == 1:
                answer = f"Traffic accidents or obstructions are visible in {descriptions[0]}."
            else:
                answer = f"Traffic accidents or obstructions are visible in multiple images: {'; '.join(descriptions)}."
        
        # 生成 MCQ 选项（方向索引）
        # 找到正确答案的方向索引
        if not accident_directions:
            correct_option_text = "None"
        else:
            # 选择第一个有事故的方向
            first_direction = sorted(accident_directions.keys())[0]
            direction_num = first_direction.split('_')[1]
            correct_option_text = f"Image Index {direction_num}"
        
        # 生成所有可能的方向选项
        all_direction_options = [f"Image Index {d.split('_')[1]}" for d in self.directions] + ["None"]
        
        # 生成干扰项
        distractors = [opt for opt in all_direction_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))]
        
        # 生成选项
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Special Events',
            'task': 'Multi Image',
            'subtask': 'Localization',
            'capabilities': ['Object Detection', 'Anomaly Detection', 'Scene Understanding', 'Cross-Image Analysis']
        }
    
    # ================
    # 3. 决策类问题
    # ================
    def _which_phase_has_most_vehicles(self):
        """哪一个相位车辆最多
        """
        ACCIDENT_TYPES = [
            'barrier_A', 'barrier_B', 'barrier_C', 'barrier_D', 'barrier_E',
            'tree_branch_1lane', 'tree_branch_3lanes',
            'pedestrian', 'crash_vehicle_1lane', 'crash_vehicle_3lanes',
            'other_accidents',
        ]
        
        question = f"These images are captured by cameras at an intersection, each showing a different incoming direction. The phase information is as follows:\n{self.phaseInfo}\nWhich traffic phase has the most vehicles waiting? Please provide the phase number."
        
        # 收集所有相位信息
        all_phases = {}
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
            annotation = self.timestep_data[direction].get('annotation', {})
            traffic_phase = annotation.get('traffic_phase', {})
            
            for phase_num, lanes in traffic_phase.items():
                if phase_num not in all_phases:
                    all_phases[phase_num] = set()
                # 提取 road_id（去掉 --l 或 --s 后缀）
                for lane_desc in lanes:
                    road_id = lane_desc.split('--')[0]
                    all_phases[phase_num].add(road_id)
        
        # 统计每个相位的车辆数
        phase_counts = {}
        for phase_num, roads in all_phases.items():
            count = 0
            for direction in self.directions:
                if direction not in self.timestep_data:
                    continue
                    
                annotation = self.timestep_data[direction].get('annotation', {})
                vehicles = annotation.get('vehicles', {})
                in_lanes = annotation.get('in_lanes', {})
                in_road = annotation.get('in_road', '')
                
                # 获取该方向的 incoming 可视范围
                max_incoming_distance = self._get_distance_threshold(direction, 'incoming')
                
                # 只统计属于该相位的道路上的车辆
                if in_road in roads:
                    for v in vehicles.values():
                        v_type = v.get('vehicle_type', '')
                        lane_id = v.get('lane_id', '')
                        road_id = v.get('road_id', '')
                        
                        # 跳过事故类型
                        if v_type in ACCIDENT_TYPES:
                            continue
                        
                        # 只统计进入路口的车辆
                        if lane_id in in_lanes and road_id == in_road:
                            # 计算到路口的距离
                            lane_length = in_lanes[lane_id]
                            lane_position = v.get('lane_position', 0)
                            distance = lane_length - lane_position
                            
                            # 只统计可见范围内的车辆
                            if distance <= max_incoming_distance:
                                count += 1
            
            phase_counts[phase_num] = count
        
        # 找到车辆最多的相位
        if not phase_counts or max(phase_counts.values()) == 0:
            answer = "No vehicles are clearly visible in any traffic phase."
            correct_option_text = "None"
        else:
            max_count = max(phase_counts.values())
            max_phases = [p for p, c in phase_counts.items() if c == max_count]
            
            if len(max_phases) == 1:
                answer = f"Phase {max_phases[0]} has the most vehicles with {max_count} vehicles waiting."
                correct_option_text = f"Phase {max_phases[0]}"
            else:
                answer = f"Phases {', '.join(max_phases)} have the same number of vehicles ({max_count} each) waiting."
                correct_option_text = f"Phase {max_phases[0]}"
        
        # 生成 MCQ 选项
        all_phase_options = [f"Phase {p}" for p in sorted(all_phases.keys())] + ["None"]
        distractors = [opt for opt in all_phase_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))]
        
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Traffic Phase Analysis',
            'task': 'Multi Image',
            'subtask': 'Vehicle Counting',
            'capabilities': ['Object Detection', 'Phase Understanding', 'Cross-Image Comparison', 'Quantitative Analysis']
        }
    
    def _which_phase_has_accident(self):
        """事故影响哪一个相位
        """
        ACCIDENT_TYPES = {
            'barrier_A': 'safety barrier',
            'barrier_B': 'safety barrier',
            'barrier_C': 'safety barrier',
            'barrier_D': 'safety barrier',
            'barrier_E': 'safety barrier',
            'tree_branch_1lane': 'fallen tree branch',
            'tree_branch_3lanes': 'fallen tree branches',
            'pedestrian': 'pedestrian incident',
            'crash_vehicle_1lane': 'vehicle collision',
            'crash_vehicle_3lanes': 'multi-vehicle collision',
        }
        
        question = f"These images are captured by cameras at an intersection, each showing a different incoming direction. The phase information is as follows:\n{self.phaseInfo}\nWhich traffic phase is affected by traffic accidents or obstructions? Please provide the phase number."
        
        # 收集所有相位信息
        all_phases = {}
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
            annotation = self.timestep_data[direction].get('annotation', {})
            traffic_phase = annotation.get('traffic_phase', {})
            
            for phase_num, lanes in traffic_phase.items():
                if phase_num not in all_phases:
                    all_phases[phase_num] = set()
                for lane_desc in lanes:
                    road_id = lane_desc.split('--')[0]
                    all_phases[phase_num].add(road_id)
        
        # 查找包含事故的相位
        phase_accidents = {}
        for phase_num, roads in all_phases.items():
            accidents = []
            accident_types = []
            
            for direction in self.directions:
                if direction not in self.timestep_data:
                    continue
                    
                annotation = self.timestep_data[direction].get('annotation', {})
                vehicles = annotation.get('vehicles', {})
                in_road = annotation.get('in_road', '')
                
                # 只检查属于该相位的道路
                if in_road in roads:
                    for v in vehicles.values():
                        v_type = v.get('vehicle_type', '')
                        road_id = v.get('road_id', '')
                        
                        if (v_type in ACCIDENT_TYPES) and (v_type not in accident_types) and (road_id == in_road):
                            accident_desc = ACCIDENT_TYPES[v_type]
                            accidents.append(accident_desc)
                            accident_types.append(v_type)
            
            if accidents:
                phase_accidents[phase_num] = accidents
        
        # 构建答案
        if not phase_accidents:
            answer = "No traffic accidents or obstructions are affecting any traffic phase."
            correct_option_text = "None"
        else:
            descriptions = []
            for phase_num, accidents in sorted(phase_accidents.items()):
                if len(accidents) == 1:
                    descriptions.append(f"Phase {phase_num} is affected by {accidents[0]}")
                else:
                    accident_list = ", ".join(accidents[:-1]) + " and " + accidents[-1]
                    descriptions.append(f"Phase {phase_num} is affected by {accident_list}")
            
            if len(descriptions) == 1:
                answer = descriptions[0] + "."
            else:
                answer = "Multiple phases are affected: " + "; ".join(descriptions) + "."
            
            first_phase = sorted(phase_accidents.keys())[0]
            correct_option_text = f"Phase {first_phase}"
        
        # 生成 MCQ 选项
        all_phase_options = [f"Phase {p}" for p in sorted(all_phases.keys())] + ["None"]
        distractors = [opt for opt in all_phase_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))]
        
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Traffic Phase Analysis',
            'task': 'Multi Image',
            'subtask': 'Accident Detection',
            'capabilities': ['Object Detection', 'Anomaly Detection', 'Phase Understanding', 'Cross-Image Analysis']
        }
    
    def _which_phase_has_special_vehicle(self):
        """特殊车辆在哪一个相位
        """
        question = f"These images are captured by cameras at an intersection, each showing a different incoming direction. The phase information is as follows:\n{self.phaseInfo}\nWhich traffic phase contains emergency vehicles (police cars, ambulances, or fire trucks)? Please provide the phase number."
        
        # 收集所有相位信息
        all_phases = {}
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
            annotation = self.timestep_data[direction].get('annotation', {})
            traffic_phase = annotation.get('traffic_phase', {})
            
            for phase_num, lanes in traffic_phase.items():
                if phase_num not in all_phases:
                    all_phases[phase_num] = set()
                for lane_desc in lanes:
                    road_id = lane_desc.split('--')[0]
                    all_phases[phase_num].add(road_id)
        
        # 查找包含特殊车辆的相位
        phase_special_vehicles = {}
        for phase_num, roads in all_phases.items():
            special_vehicles = []
            
            for direction in self.directions:
                if direction not in self.timestep_data:
                    continue
                    
                annotation = self.timestep_data[direction].get('annotation', {})
                vehicles = annotation.get('vehicles', {})
                in_lanes = annotation.get('in_lanes', {})
                in_road = annotation.get('in_road', '')
                
                # 获取该方向的 incoming 可视范围
                max_incoming_distance = self._get_distance_threshold(direction, 'incoming')
                
                # 只检查属于该相位的道路
                if in_road in roads:
                    for v in vehicles.values():
                        v_type = v.get('vehicle_type', '').lower()
                        lane_id = v.get('lane_id', '')
                        road_id = v.get('road_id', '')
                        
                        if v_type in ['police', 'emergency', 'fire_engine']:
                            # 只统计进入路口的特殊车辆
                            if lane_id in in_lanes and road_id == in_road:
                                # 计算到路口的距离
                                lane_length = in_lanes[lane_id]
                                lane_position = v.get('lane_position', 0)
                                distance = lane_length - lane_position
                                
                                # 只统计可见范围内的车辆
                                if distance <= max_incoming_distance:
                                    type_mapping = {
                                        'police': 'police car',
                                        'emergency': 'ambulance',
                                        'fire_engine': 'fire truck',
                                    }
                                    special_vehicles.append(type_mapping.get(v_type, v_type))
            
            if special_vehicles:
                phase_special_vehicles[phase_num] = special_vehicles
        
        # 构建答案
        if not phase_special_vehicles:
            answer = "No emergency vehicles are visible in any traffic phase."
            correct_option_text = "None"
        else:
            descriptions = []
            for phase_num, vehicles in sorted(phase_special_vehicles.items()):
                if len(vehicles) == 1:
                    descriptions.append(f"Phase {phase_num} contains a {vehicles[0]}")
                else:
                    vehicle_list = ", ".join(set(vehicles))
                    descriptions.append(f"Phase {phase_num} contains {vehicle_list}")
            
            if len(descriptions) == 1:
                answer = descriptions[0] + "."
            else:
                answer = "Multiple phases contain emergency vehicles: " + "; ".join(descriptions) + "."
            
            first_phase = sorted(phase_special_vehicles.keys())[0]
            correct_option_text = f"Phase {first_phase}"
        
        # 生成 MCQ 选项
        all_phase_options = [f"Phase {p}" for p in sorted(all_phases.keys())] + ["None"]
        distractors = [opt for opt in all_phase_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))]
        
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Traffic Phase Analysis',
            'task': 'Multi Image',
            'subtask': 'Special Vehicle Detection',
            'capabilities': ['Object Detection', 'Vehicle Classification', 'Phase Understanding', 'Cross-Image Analysis']
        }
    
    def _which_phase_is_green(self):
        """当前哪一个相位是绿灯
        """
        question = f"These images are captured by cameras at an intersection, each showing a different incoming direction. The phase information is as follows:\n{self.phaseInfo}\nWhich traffic phase currently has a green light? Please provide the phase number."
        
        # 获取当前相位（从任一 direction 的 annotation 中获取）
        current_phase = None
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
            annotation = self.timestep_data[direction].get('annotation', {})
            current_phase = annotation.get('current_phase')
            if current_phase is not None:
                break
        
        if current_phase is None:
            answer = "Unable to determine the current traffic phase."
            correct_option_text = "Unknown"
        else:
            answer = f"Phase {current_phase} currently has a green light, allowing vehicles in this phase to proceed through the intersection."
            correct_option_text = f"Phase {current_phase}"
        
        # 收集所有可能的相位
        all_phases = set()
        for direction in self.directions:
            if direction not in self.timestep_data:
                continue
            annotation = self.timestep_data[direction].get('annotation', {})
            traffic_phase = annotation.get('traffic_phase', {})
            all_phases.update(traffic_phase.keys())
        
        # 生成 MCQ 选项
        all_phase_options = [f"Phase {p}" for p in sorted(all_phases)]
        distractors = [opt for opt in all_phase_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(3, len(distractors))]
        
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Traffic Phase Analysis',
            'task': 'Multi Image',
            'subtask': 'Signal State Recognition',
            'capabilities': ['Traffic Signal Recognition', 'Phase Understanding', 'Scene Understanding']
        }
    
    def _generate_traffic_light_decision(self):
        """生成交通信号灯决策问题
        """
        step_info = self.timestep_data.get('step_info', {})
        optimal_action = step_info.get('action', 0)
        
        question = f"Based on the current traffic conditions shown in all direction images, what is the optimal traffic signal phase decision? The phase information is as follows:\n{self.phaseInfo}\nPlease provide the phase number."

        # 根据 phase 找到对应的 image index
        image_index = None
        for idx, phase in self.index2phase.items():
            if phase == optimal_action:
                image_index = idx
                break

        # 生成决策答案
        if image_index is not None:
            answer = f"The optimal decision is to switch to Phase {optimal_action}, which corresponds to image index {image_index} (granting green light to this direction). "
        else:
            answer = f"The optimal decision is to switch to Phase {optimal_action}. "
        
        # 生成 MCQ 选项（交通信号相位）
        # 正确答案是 optimal_action
        correct_option_text = f"Phase {optimal_action}"
        
        # 生成可能的相位选项（假设有0-3个相位）
        all_phase_options = [f"Phase {i}" for i in range(3)]
        
        # 生成干扰项
        distractors = [opt for opt in all_phase_options if opt != correct_option_text]
        random.shuffle(distractors)
        selected_distractors = distractors[:3]
        
        # 生成选项
        options_list = [correct_option_text] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Comprehensive Analysis',
            'task': 'Multi Image',
            'subtask': 'Decision Making',
            'capabilities': ['Object Detection', 'Vehicle Classification', 'Traffic Flow Analysis', 'Priority Assessment', 'Multi-Directional Reasoning', 'Traffic Signal Control']
        }