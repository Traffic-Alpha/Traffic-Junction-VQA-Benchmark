'''
Author: WANG Maonan
Date: 2025-08-14 15:38:00
LastEditors: WANG Maonan
Description: 将 JSON 转换为 QA 和 MCQ
LastEditTime: 2025-12-18
'''
import random

# Distance thresholds in meters (adjustable)
CLOSE_RANGE = 25  # Clear visibility zone
MID_RANGE = 40 # Partial visibility

class SingleImageVQA:
    def __init__(self, data, max_incoming_distance:float=90, max_outgoing_distance:float=30):
        """将 JSON 数据转换为基于模板的 QA 问题对
        
        Args:
            data: annotation 数据
            max_incoming_distance: incoming 车道的可视范围（米）
            max_outgoing_distance: outgoing 车道的可视范围（米）
        """
        self.max_incoming_distance = max_incoming_distance # incoming 车道的可视范围
        self.max_outgoing_distance = max_outgoing_distance # outgoing 车道的可视范围
        self.data = data
        self.in_road = data['in_road']
        self.out_road = data['out_road']
        self.in_lanes = data['in_lanes'] # 获得 in lanes 的 (id, 车道长度)
        self.out_lanes = data['out_lanes'] # out lanes 的 (id, 车道长度)
        self.vehicles = data['vehicles']
    
    # -----
    # Update Vehicle Information (将 lane position 转换为距离路口的距离)
    # -----
    def calculate_distance_to_intersection(self):
        """计算每个车辆到十字路口的距离，并将结果添加到车辆信息中。

        :param in_lanes: 包含 in lanes 的 lane id 和长度
        :param out_lanes: 包含 out lanes 的 lane id 和长度
        :param vehicles: 包含车辆的详细信息
        :return: 直接对 self.vehicles 进行更新
        """
        self.closest_vehicle_distance = 1e4 # 记录距离路口最近的车辆位置, 用于判断当前路口是否有车进入
        for vehicle_id, vehicle_info in self.vehicles.items():
            lane_id = vehicle_info['lane_id']
            lane_position = vehicle_info['lane_position']

            # 根据车道 ID 判断当前车辆是在 in lane 还是 out lane
            if lane_id in self.in_lanes:
                # 在 in lane 上，距离路口的距离 = 车道长度 - 当前车辆的位置
                distance_to_intersection = self.in_lanes[lane_id] - lane_position
                if distance_to_intersection < self.closest_vehicle_distance:
                    self.closest_vehicle_distance = distance_to_intersection

            elif lane_id in self.out_lanes:
                # 在 out lane 上，距离路口的距离 = 当前车辆的位置
                distance_to_intersection = lane_position
            else:
                # 如果车道 ID 不在 in lanes 和 out lanes 中，距离设为 None
                distance_to_intersection = None

            # 将计算结果添加到车辆信息中
            vehicle_info['distance_to_intersection'] = distance_to_intersection
    
    # ------------
    # Generate VQA
    # ------------
    def generate_all_questions(self):
        self.calculate_distance_to_intersection() # 首先更新车辆到路口的距离
        questions = list()
        questions.extend(self._generate_counting_questions()) # 1. 数量问题
        questions.extend(self._generate_existence_questions()) # 2. 存在问题
        questions.extend(self._generate_identification_questions()) # 3. 识别问题
        questions.extend(self._generate_localization_questions()) # 4. 定位问题
        
        return questions
    
    # #############
    # 1. 数量问题（6个）
    # #############
    def _generate_counting_questions(self):
        """生成数量问题"""
        return [
            self._generate_total_incoming_lanes(), # 进口车道总数
            self._generate_total_outgoing_lanes(), # 出口车道总数
            self._generate_total_vehicles_by_distance(), # 图片中的车辆总数
            self._generate_lane_vehicle_distribution(lane_type='Incoming'), # 每条进口车道的车辆数
            self._generate_lane_vehicle_distribution(lane_type='Outgoing'), # 每条出口车道的车辆数
            self._generate_specific_lane_vehicle_count(), # 特定进口车道的车辆数
        ]
    
    # #############
    # 2. 存在问题（2个）
    # #############
    def _generate_existence_questions(self):
        """生成存在问题"""
        return [
            self._generate_existing_special_vehicles(), # 是否包含特殊车辆
            self._generate_existing_accident(), # 是否包含特殊事件
        ]
    
    # #############
    # 3. 识别问题（2个）
    # #############
    def _generate_identification_questions(self):
        """生成识别问题"""
        return [
            self._generate_special_vehicle_type(), # 特殊车辆类型识别
            self._generate_detailed_existing_accident(), # 特殊事件类型识别
        ]
    
    # #############
    # 4. 定位问题（2个）
    # #############
    def _generate_localization_questions(self):
        """生成定位问题"""
        return [
            self._generate_special_vehicle_lane_location(), # 特殊车辆所在车道
            self._generate_accident_affected_lanes(), # 特殊事件影响的车道
        ]

    # ==================
    # 问题生成器实现
    # ==================
    
    # ----------
    # 数量问题
    # ----------
    def _generate_total_incoming_lanes(self):
        """数量问题：进口车道总数
        """
        question = "How many incoming lanes are there in total?"
        correct_answer = len(self.in_lanes)
        answer = f"There are a total of {correct_answer} incoming lanes."
        
        # 生成干扰项：±1, ±2, ±3
        distractors = []
        for offset in [-3, -2, -1, 1, 2, 3]:
            if correct_answer + offset > 0: # 干扰项 >0
                distractors.append(str(correct_answer + offset))
        
        # 随机选择3个干扰项
        random.shuffle(distractors)
        selected_distractors = distractors[:3]
        
        # 生成选项
        options_list = [str(correct_answer)] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(str(correct_answer)))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Road Infrastructure',
            'task': 'Single Image',
            'subtask': 'Counting',
            'capabilities': ['Lane Detection', 'Spatial Understanding']
        }

    def _generate_total_outgoing_lanes(self):
        """数量问题：出口车道总数
        """
        question = "How many outgoing lanes are there in total?"
        correct_answer = len(self.out_lanes)
        answer = f"There are a total of {correct_answer} outgoing lanes."
        
        # 生成干扰项：±1, ±2, ±3
        distractors = []
        for offset in [-3, -2, -1, 1, 2, 3]:
            if correct_answer + offset > 0:
                distractors.append(str(correct_answer + offset))
        
        # 随机选择3个干扰项
        random.shuffle(distractors)
        selected_distractors = distractors[:3]
        
        # 生成选项
        options_list = [str(correct_answer)] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(str(correct_answer)))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Road Infrastructure',
            'task': 'Single Image',
            'subtask': 'Counting',
            'capabilities': ['Lane Detection', 'Spatial Understanding']
        }

    def _generate_total_vehicles_by_distance(self):
        """数量问题：图片中的车辆总数
        
        统计可见范围内的车辆总数
        
        Returns:
            dict: Contains question and detailed answer about vehicle distribution
        """
        ACCIDENT_TYPES = [
            'barrier_A', 'barrier_B', 'barrier_C', 'barrier_D', 'barrier_E',
            'tree_branch_1lane', 'tree_branch_3lanes',
            'pedestrian', 'crash_vehicle_1lane', 'crash_vehicle_3lanes',
        ]
        
        # Check if incoming lane has green light
        traffic_phase = self.data.get('traffic_phase', {})
        current_phase = str(self.data.get('current_phase', ''))
        has_green = False
        try:
            current_directions = traffic_phase.get(current_phase, [])
            controlled_lanes = {
                direction.split('--')[0] 
                for direction in current_directions if '--' in direction
            } # 获得控制的 edge (包含多个 lanes)
            has_green = self.in_road in controlled_lanes
        except Exception:
            pass
        
        # Initialize counters for each distance range
        incoming_counts = {'close': 0, 'mid': 0, 'far': 0}
        outgoing_counts = {'close': 0, 'mid': 0, 'far': 0}

        # 统计可见范围内的车辆总数 (incoming 和 outgoing 分开统计)
        for v in self.vehicles.values():
            v_type = v['vehicle_type']
            dist = v['distance_to_intersection']
            
            # Skip accident types
            if v_type in ACCIDENT_TYPES:
                continue
                
            if v['road_id'] == self.in_road: # 进口车道
                # Skip if distance exceeds incoming max range
                if dist > self.max_incoming_distance:
                    continue
                if dist <= CLOSE_RANGE:
                    incoming_counts['close'] += 1
                elif dist <= MID_RANGE:
                    incoming_counts['mid'] += 1
                else:
                    incoming_counts['far'] += 1
            elif v['road_id'] == self.out_road: # 出口车道
                # Skip if distance exceeds outgoing max range
                if dist > self.max_outgoing_distance:
                    continue
                if dist <= CLOSE_RANGE:
                    outgoing_counts['close'] += 1
                elif dist <= MID_RANGE:
                    outgoing_counts['mid'] += 1
                else:
                    outgoing_counts['far'] += 1

        # Generate natural language description
        question = "How many vehicles are there in total on the incoming and outgoing lanes, considering visibility?"
        
        answer_parts = []
        for direction, counts in [('incoming', incoming_counts), ('outgoing', outgoing_counts)]:
            if sum(counts.values()) > 0:
                dir_text = (
                    f"{direction} road: {counts['close']} clear vehicles nearby, "
                    f"{counts['mid']} somewhat visible vehicles further out"
                )
                if counts['far'] > 0:
                    dir_text += f", and approximately {counts['far']} faint vehicles in the distance"
                
                if direction == 'incoming':
                    if has_green:
                        dir_text += '. Note: The vehicles are leaving the incoming lanes due to green light. Vehicles that have left the lane markings are not counted'
                    else:
                        dir_text += '. Vehicles exiting the intersection are not counted'
                answer_parts.append(dir_text)
        
        if not answer_parts:
            answer = "No vehicles are clearly visible in the image."
        else:
            total = sum(incoming_counts.values()) + sum(outgoing_counts.values())
            answer = (
                f"Camera detects {total} vehicles total. "
                f"{' '.join(answer_parts)}. "
                "Note: Distant vehicles may be less accurate due to limited visibility."
            )

        # 生成 MCQ 选项（基于车辆分布的无重叠区间）
        total = sum(incoming_counts.values()) + sum(outgoing_counts.values())
        close_count = incoming_counts['close'] + outgoing_counts['close'] # 近距离车辆
        mid_count = incoming_counts['mid'] + outgoing_counts['mid']
        far_count = incoming_counts['far'] + outgoing_counts['far']
        num_lanes = len(self.in_lanes)  # 车道数
        
        # 根据是否是绿灯和车辆分布确定范围
        if has_green:
            # 最少：只有 close + mid (最前方车辆离开)
            # 最多：所有车辆 + 可能新进入的车辆
            range_start = max(0, close_count - num_lanes) + mid_count
            range_end = total + min(num_lanes, 2)  # 最多新进入车道数或2辆
        else:
            # 红灯：车辆相对稳定，范围较小
            range_start = max(0, total - far_count)
            range_end = total + 1
        
        correct_range = f"{range_start}-{range_end}"
        
        # 生成连续的不重叠区间（不需要从5的倍数开始）
        interval_size = 5  # 每个区间包含5个数字
        
        # 生成候选区间（围绕正确答案）
        distractors = []
        
        # 左侧相邻区间（如果正确答案起点>0）
        if range_start >= interval_size:
            left_end = range_start - 1
            left_start = max(0, left_end - interval_size + 1)
            distractors.append(f"{left_start}-{left_end}")
        
        # 右侧连续区间（最多生成3个，限制最大值≤30）
        current_start = range_end + 1
        for i in range(3):
            if current_start <= 30:  # 限制最大值
                current_end = min(current_start + interval_size - 1, 30)
                distractors.append(f"{current_start}-{current_end}")
                current_start = current_end + 1
            else:
                break
        
        # 如果右侧区间不够3个，补充更多左侧区间
        if len(distractors) < 3 and range_start > 0:
            # 在第一个左侧区间之前再添加一个
            if distractors and distractors[0].split('-')[0] != '0':
                first_left_start = int(distractors[0].split('-')[0])
                if first_left_start >= interval_size:
                    new_left_end = first_left_start - 1
                    new_left_start = max(0, new_left_end - interval_size + 1)
                    distractors.insert(0, f"{new_left_start}-{new_left_end}")
        
        # 确保有3个干扰项
        if len(distractors) < 3:
            # 补充基础区间
            if "0-4" not in distractors and correct_range != "0-4":
                distractors.insert(0, "0-4")
        
        selected_distractors = distractors[:3]
        
        # 生成选项
        options_list = [correct_range] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_range))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Vehicle Analysis',
            'task': 'Single Image',
            'subtask': 'Counting',
            'capabilities': ['Object Detection', 'Distance Estimation', 'Visibility Assessment']
        }

    def _generate_specific_lane_vehicle_count(self):
        """数量问题：特定进口车道的车辆数
        
        随机选择一个 incoming lane，询问该车道上的车辆数量
        
        Returns:
            dict: Contains question and detailed answer about specific lane vehicle count
        """
        ACCIDENT_TYPES = [
            'barrier_A', 'barrier_B', 'barrier_C', 'barrier_D', 'barrier_E',
            'tree_branch_1lane', 'tree_branch_3lanes',
            'pedestrian', 'crash_vehicle_1lane', 'crash_vehicle_3lanes',
        ]
        
        # Check if incoming lane has green light
        traffic_phase = self.data.get('traffic_phase', {})
        current_phase = str(self.data.get('current_phase', ''))
        has_green = False
        try:
            current_directions = traffic_phase.get(current_phase, [])
            controlled_lanes = {
                direction.split('--')[0] 
                for direction in current_directions if '--' in direction
            }
            has_green = self.in_road in controlled_lanes
        except Exception:
            pass
        
        # Randomly select one incoming lane
        lane_ids = list(self.in_lanes.keys())
        if not lane_ids:
            # No incoming lanes, return empty result
            return {
                'question': "How many vehicles are in the specified incoming lane?",
                'answer': "There are no incoming lanes available.",
                'options': {'A': '0', 'B': '1-2', 'C': '3-4', 'D': '5-6'},
                'correct_answer': 'A',
                'category': 'Vehicle Analysis',
                'task': 'Single Image',
                'subtask': 'Counting',
                'capabilities': ['Object Detection', 'Lane Detection', 'Spatial Understanding', 'Distance Estimation']
            }
        
        selected_lane_id = random.choice(lane_ids)
        
        # Extract lane number from lane_id (format: "road_laneNum")
        _, lane_num_str = selected_lane_id.rsplit('_', 1)
        lane_num = int(lane_num_str)
        display_lane_num = lane_num + 1  # 车道编号从1开始显示（从左往右）
        
        # Count vehicles in this lane by distance tier
        lane_counts = {'close': 0, 'mid': 0, 'far': 0}
        
        for v in self.vehicles.values():
            v_type = v['vehicle_type']
            dist = v['distance_to_intersection']
            lane_id = v['lane_id']
            
            # 只统计选定车道、可视范围内、非事故类型的车辆
            if lane_id != selected_lane_id \
                or dist > self.max_incoming_distance \
                    or v_type in ACCIDENT_TYPES:
                continue
            
            if dist <= CLOSE_RANGE:
                lane_counts['close'] += 1
            elif dist <= MID_RANGE:
                lane_counts['mid'] += 1
            else:
                lane_counts['far'] += 1
        
        total_count = sum(lane_counts.values())
        
        # Generate natural language description
        question = f"How many vehicles are there in incoming lane {display_lane_num} (from left to right, starting from 1), considering visibility?"
        
        if total_count == 0:
            answer = f"Incoming lane {display_lane_num} (from left to right, starting from 1) is empty with no vehicles detected."
        else:
            parts = []
            if lane_counts['close'] > 0:
                parts.append(f"{lane_counts['close']} clear vehicles nearby")
            if lane_counts['mid'] > 0:
                parts.append(f"{lane_counts['mid']} somewhat visible vehicles further out")
            if lane_counts['far'] > 0:
                parts.append(f"approximately {lane_counts['far']} faint vehicles in the distance")
            
            answer = f"Incoming lane {display_lane_num} (from left to right) has {total_count} vehicles total: {', '.join(parts)}."
            
            if has_green:
                answer += " Note: The vehicles are leaving the lane due to green light. Vehicles that have left the lane markings are not counted."
            else:
                answer += " Note: Vehicles exiting the intersection are not counted."
        
        # 生成 MCQ 选项（基于车辆数量的范围）
        close_count = lane_counts['close']
        mid_count = lane_counts['mid']
        far_count = lane_counts['far']
        
        # 根据是否是绿灯确定范围
        if has_green:
            # 绿灯：最前方的车辆可能离开
            range_start = max(0, close_count - 1) + mid_count
            range_end = total_count + 1  # 可能有新车进入
        else:
            # 红灯：车辆相对稳定
            range_start = max(0, total_count - far_count)
            range_end = total_count + 1
        
        correct_range = f"{range_start}-{range_end}"
        
        # 生成不重叠区间作为干扰项
        interval_size = 3  # 每个区间包含3个数字（比总体统计的区间小）
        
        distractors = []
        
        # 左侧相邻区间
        if range_start >= interval_size:
            left_end = range_start - 1
            left_start = max(0, left_end - interval_size + 1)
            distractors.append(f"{left_start}-{left_end}")
        
        # 右侧连续区间（最多生成3个，限制最大值≤20）
        current_start = range_end + 1
        for i in range(3):
            if current_start <= 20:
                current_end = min(current_start + interval_size - 1, 20)
                distractors.append(f"{current_start}-{current_end}")
                current_start = current_end + 1
            else:
                break
        
        # 如果干扰项不够，补充更多左侧区间
        if len(distractors) < 3 and range_start > 0:
            if distractors and distractors[0].split('-')[0] != '0':
                first_left_start = int(distractors[0].split('-')[0])
                if first_left_start >= interval_size:
                    new_left_end = first_left_start - 1
                    new_left_start = max(0, new_left_end - interval_size + 1)
                    distractors.insert(0, f"{new_left_start}-{new_left_end}")
        
        # 确保有3个干扰项
        if len(distractors) < 3:
            if "0-2" not in distractors and correct_range != "0-2":
                distractors.insert(0, "0-2")
        
        selected_distractors = distractors[:3]
        
        # 生成选项
        options_list = [correct_range] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_range))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Vehicle Analysis',
            'task': 'Single Image',
            'subtask': 'Counting',
            'capabilities': ['Object Detection', 'Lane Detection', 'Spatial Understanding', 'Distance Estimation']
        }

    def _generate_lane_vehicle_distribution(self, lane_type='Incoming'):
        """数量问题：每条车道的车辆数
        
        统计每条进口/出口车道的车辆数量分布
        
        Args:
            lane_type: 'Incoming' or 'Outgoing'
        
        Returns:
            dict: Contains question and detailed answer about lane distribution
        """
        ACCIDENT_TYPES = [
            'barrier_A', 'barrier_B', 'barrier_C', 'barrier_D', 'barrier_E',
            'tree_branch_1lane', 'tree_branch_3lanes',
            'pedestrian', 'crash_vehicle_1lane', 'crash_vehicle_3lanes',
        ]
        
        # Check if incoming lane has green light
        traffic_phase = self.data.get('traffic_phase', {})
        current_phase = str(self.data.get('current_phase', ''))
        has_green = False
        if lane_type == 'Incoming':
            try:
                current_directions = traffic_phase.get(current_phase, [])
                controlled_lanes = {
                    direction.split('--')[0] 
                    for direction in current_directions if '--' in direction
                }
                has_green = self.in_road in controlled_lanes
            except Exception:
                pass
        
        # Select target lanes and max distance
        lanes = self.in_lanes if lane_type == 'Incoming' else self.out_lanes
        max_distance = self.max_incoming_distance if lane_type == 'Incoming' else self.max_outgoing_distance

        # Initialize lane statistics
        lane_stats = {
            lane_num: {
                'close': 0,
                'mid': 0,
                'far': 0,
                'total': 0
            }
            for lane_num in range(len(lanes))
        }

        # Count vehicles per distance tier
        for v in self.vehicles.values():
            v_type = v['vehicle_type']
            dist = v['distance_to_intersection'] # 车辆的距离
            lane_id = v['lane_id']

            # 排除不在对应车道、观测不到的车辆、以及事故类型
            if dist > max_distance \
                or lane_id not in lanes \
                    or v_type in ACCIDENT_TYPES:
                continue
            
            # Extract lane number from lane_id (format: "road_laneNum")
            _, lane_num_str = v['lane_id'].rsplit('_', 1)
            lane_num = int(lane_num_str) # 获得车道数
                
            if lane_num in lane_stats:
                if dist <= CLOSE_RANGE:
                    lane_stats[lane_num]['close'] += 1
                elif dist <= MID_RANGE:
                    lane_stats[lane_num]['mid'] += 1
                else:
                    lane_stats[lane_num]['far'] += 1
                # 更新车道对应的车辆总数
                lane_stats[lane_num]['total'] += 1

        # Generate natural language description
        question = f"How many vehicles are there in the {lane_type.lower()} direction, considering visibility?"
        
        # Build lane-by-lane descriptions
        lane_descriptions = []
        for lane_num, counts in sorted(lane_stats.items()):
            # 车道编号从1开始显示，并说明方向
            display_lane_num = lane_num + 1
            if lane_type == 'Incoming':
                # Incoming: index 0 是从左往右第一个
                position_desc = f"Lane {display_lane_num} (from left to right)"
            else:
                # Outgoing: index 0 是从右往左第一个
                position_desc = f"Lane {display_lane_num} (from right to left)"
            
            if counts['total'] == 0:
                lane_desc = f"{position_desc}: empty"
            else:
                parts = []
                if counts['close'] > 0:
                    parts.append(f"{counts['close']} clear")
                if counts['mid'] > 0:
                    parts.append(f"{counts['mid']} faint")
                if counts['far'] > 0:
                    parts.append(f"~{counts['far']} very faint")
                lane_desc = f"{position_desc}: {'+'.join(parts)} vehicles"
            lane_descriptions.append(lane_desc)
        
        # Compose final answer
        total_vehicles = sum(v['total'] for v in lane_stats.values())
        
        if total_vehicles == 0:
            answer = f"No vehicles detected on {lane_type.lower()} lanes."
        else:
            if lane_type == 'Incoming':
                if has_green:
                    visibility_note = "Note: (1) The vehicles are leaving the incoming lanes due to green light. Vehicles that have left the lane markings are not counted; (2) Distant vehicles may be less accurate."
                else:
                    visibility_note = "Note: (1) Vehicles exiting the intersection are not counted; (2) Distant vehicles may be less accurate."
            else:
                visibility_note = "Note: Distant vehicles may be less accurate."
            answer = (
                f"Total {total_vehicles} vehicles across {len(lanes)} {lane_type.lower()} lanes. "
                f"{'; '.join(lane_descriptions)}. {visibility_note}"
            )

        # 生成 MCQ 选项（基于车辆分布的无重叠区间）
        num_lanes_count = len(lanes)  # 该方向的车道数
        
        close_total = sum(1 for counts in lane_stats.values() if counts['close'] > 0)
        mid_total = sum(1 for counts in lane_stats.values() if counts['mid'] > 0)
        far_total = sum(1 for counts in lane_stats.values() if counts['far'] > 0)

        # 根据是否是绿灯（仅对 Incoming 有效）和车道类型确定范围
        if lane_type == 'Incoming' and has_green:
            # 绿灯：需要减去车道数
            range_start = max(0, close_total - num_lanes_count) + mid_total
            range_end = total_vehicles + min(num_lanes_count, 2)
        else:
            # 红灯或出口车道：车辆相对稳定，范围较小
            range_start = max(0, total_vehicles - far_total)
            range_end = total_vehicles + 1
        
        correct_range = f"{range_start}-{range_end}"
        correct_span = range_end - range_start  # 正确答案的跨度
        
        # 生成连续的不重叠区间（不需要从5的倍数开始）
        interval_size = 5  # 每个区间包含5个数字
        
        # 生成候选区间（围绕正确答案）
        distractors = []
        
        # 左侧相邻区间（如果正确答案起点>0）
        if range_start >= interval_size:
            left_end = range_start - 1
            left_start = max(0, left_end - interval_size + 1)
            distractors.append(f"{left_start}-{left_end}")
        
        # 右侧连续区间（最多生成3个，限制最大值≤30）
        current_start = range_end + 1
        for i in range(3):
            if current_start <= 30:  # 限制最大值
                current_end = min(current_start + interval_size - 1, 30)
                distractors.append(f"{current_start}-{current_end}")
                current_start = current_end + 1
            else:
                break
        
        # 如果右侧区间不够3个，补充更多左侧区间
        if len(distractors) < 3 and range_start > 0:
            # 在第一个左侧区间之前再添加一个
            if distractors and distractors[0].split('-')[0] != '0':
                first_left_start = int(distractors[0].split('-')[0])
                if first_left_start >= interval_size:
                    new_left_end = first_left_start - 1
                    new_left_start = max(0, new_left_end - interval_size + 1)
                    distractors.insert(0, f"{new_left_start}-{new_left_end}")
        
        # 确保有3个干扰项
        if len(distractors) < 3:
            # 补充基础区间
            if "0-4" not in distractors and correct_range != "0-4":
                distractors.insert(0, "0-4")
        
        selected_distractors = distractors[:3]
        
        # 生成选项
        options_list = [correct_range] + selected_distractors
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_range))
        
        return {
            'question': question,
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Vehicle Analysis',
            'task': 'Single Image',
            'subtask': 'Counting',
            'capabilities': ['Object Detection', 'Lane Detection', 'Spatial Understanding', 'Distance Estimation']
        }

    # ----------
    # 存在问题
    # ----------
    def _generate_existing_special_vehicles(self):
        """存在问题：是否包含特殊车辆
        
        简单回答是否存在特殊车辆（警车、消防车、救护车等）
        
        Returns:
            dict: 包含生成的问题和答案的字典
        """
        question = "Does the image contain any emergency vehicles such as police cars, ambulances, or fire trucks?"
        
        # 查找特殊车辆
        has_special_vehicle = False
        for v in self.vehicles.values():
            if v['vehicle_type'].lower() in ['police', 'emergency', 'fire_engine'] and v['lane_id'] in self.in_lanes:
                dist = v.get('distance_to_intersection', float('inf'))
                if dist < self.max_incoming_distance:
                    has_special_vehicle = True
                    break
        
        # 生成答案
        if has_special_vehicle:
            answer = "Yes, there are emergency vehicles in the image."
            correct_option_text = "Yes"
        else:
            answer = "No, there are no emergency vehicles in the image."
            correct_option_text = "No"
        
        # 生成 MCQ 选项（是/否 + 模糊选项）
        options_list = [
            "Yes",
            "No",
        ]
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_option_text))

        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Special Vehicles',
            'task': 'Single Image',
            'subtask': 'Existence',
            'capabilities': ['Object Detection', 'Vehicle Classification', 'Distance Estimation']
        }

    def _generate_existing_accident(self):
        """存在问题：是否包含特殊事件（事故/障碍物）
        
        简单回答是否存在交通事故或障碍物
        """
        ACCIDENT_TYPES = [
            'barrier_A', 'barrier_B', 'barrier_C', 'barrier_D', 'barrier_E',
            'tree_branch_1lane', 'tree_branch_3lanes',
            'pedestrian', 'crash_vehicle_1lane', 'crash_vehicle_3lanes',
        ]
        
        question = "Is there any traffic accident or obstruction visible in the image?"
        
        # 查找是否有事故/障碍物
        has_accident = False
        for v in self.vehicles.values():
            if v['vehicle_type'] in ACCIDENT_TYPES:
                has_accident = True
                break

        # 生成答案
        if has_accident:
            answer = "Yes, there are traffic accidents or obstructions visible in the image."
            correct_option_text = "Yes"
        else:
            answer = "No, there are no visible traffic accidents or obstructions."
            correct_option_text = "No"
        
        # 生成 MCQ 选项（是/否 + 模糊选项）
        options_list = [
            "Yes",
            "No",
        ]
        random.shuffle(options_list)
        
        correct_option = chr(65 + options_list.index(correct_option_text))
        
        return {
            'question': question, 
            'answer': answer,
            'options': {chr(65 + i): opt for i, opt in enumerate(options_list)},
            'correct_answer': correct_option,
            'category': 'Special Events',
            'task': 'Single Image',
            'subtask': 'Existence',
            'capabilities': ['Object Detection', 'Anomaly Detection', 'Scene Understanding']
        }

    # ----------
    # 识别问题
    # ----------
    def _generate_special_vehicle_type(self):
        """识别问题：特殊车辆类型识别
        
        识别图像中特殊车辆的具体类型并提供详细信息
        
        Returns:
            dict: 包含生成的问题和答案的字典
        """
        question = "What type of emergency vehicle is shown in the image, and where is it located?"
        
        # 查找所有特殊车辆
        special_vehicles = []
        for v in self.vehicles.values():
            if v['vehicle_type'].lower() in ['police', 'emergency', 'fire_engine'] and v['lane_id'] in self.in_lanes:
                dist = v.get('distance_to_intersection', float('inf'))
                if dist < self.max_incoming_distance:
                    type_mapping = {
                        'police': 'police car',
                        'emergency': 'ambulance',
                        'fire_engine': 'fire truck',
                    }
                    friendly_type = type_mapping.get(v['vehicle_type'].lower(), v['vehicle_type'])
                    special_vehicles.append({
                        'type': friendly_type,
                        'distance': dist
                    })
        
        # 生成答案
        if not special_vehicles:
            answer = "There are no emergency vehicles visible in the image."
        elif len(special_vehicles) == 1:
            veh = special_vehicles[0]
            if veh['distance'] < 25:
                position = f"clearly visible near the intersection ({veh['distance']:.1f}m away)"
            elif veh['distance'] < 50:
                position = f"approaching the intersection ({veh['distance']:.1f}m away)"
            else:
                position = f"in the distance ({veh['distance']:.1f}m from the intersection)"
            answer = f"The image shows a {veh['type']} {position}."
        else:
            # 多个特殊车辆
            types_count = {}
            for veh in special_vehicles:
                types_count[veh['type']] = types_count.get(veh['type'], 0) + 1
            
            types_desc = []
            for veh_type, count in types_count.items():
                if count == 1:
                    types_desc.append(f"a {veh_type}")
                else:
                    types_desc.append(f"{count} {veh_type}s")
            
            answer = f"The image shows multiple emergency vehicles: {', '.join(types_desc)}."
        
        # 生成 MCQ 选项（特殊车辆类型）
        all_vehicle_types = ["Police car", "Ambulance", "Fire truck", "None"]
        
        if not special_vehicles:
            correct_option_text = "None"
        elif len(special_vehicles) == 1:
            # 首字母大写
            correct_option_text = special_vehicles[0]['type'].capitalize()
            if correct_option_text == "Police car":
                correct_option_text = "Police car"
            elif correct_option_text == "Fire truck":
                correct_option_text = "Fire truck"
        else:
            # 多个特殊车辆，选择最常见的类型
            types_count = {}
            for veh in special_vehicles:
                veh_type = veh['type'].capitalize()
                if veh_type == "Police car":
                    veh_type = "Police car"
                elif veh_type == "Fire truck":
                    veh_type = "Fire truck"
                types_count[veh_type] = types_count.get(veh_type, 0) + 1
            correct_option_text = max(types_count, key=types_count.get)
        
        # 生成干扰项
        distractors = [vt for vt in all_vehicle_types if vt != correct_option_text]
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
            'category': 'Special Vehicles',
            'task': 'Single Image',
            'subtask': 'Recognition',
            'capabilities': ['Object Detection', 'Vehicle Classification', 'Distance Estimation', 'Spatial Understanding']
        }

    def _generate_detailed_existing_accident(self):
        """识别问题：特殊事件类型识别
        
        识别图像中特殊事件的具体类型并解释原因
        """
        ACCIDENT_TYPES = {
            'barrier_A': {
                'type': 'safety barrier',
                'reason': 'temporary road closure for maintenance or event',
                'explanation': 'the area is blocked off for safety reasons'
            },
            'barrier_B': {
                'type': 'safety barrier', 
                'reason': 'construction work or road repair',
                'explanation': 'construction zone requires complete closure'
            },
            'barrier_C': {
                'type': 'safety barrier',
                'reason': 'police checkpoint or security operation',
                'explanation': 'authorities have restricted access to the area'
            },
            'barrier_D': {
                'type': 'safety barrier',
                'reason': 'special event or parade route',
                'explanation': 'road is temporarily closed for public event'
            },
            'barrier_E': {
                'type': 'safety barrier',
                'reason': 'emergency response operation',
                'explanation': 'emergency services have sealed off the area'
            },
            'tree_branch_1lane': {
                'type': 'fallen tree branch',
                'reason': 'severe weather conditions like strong winds or storm',
                'explanation': 'debris makes the lane unsafe for vehicle passage'
            },
            'tree_branch_3lanes': {
                'type': 'multiple fallen tree branches',
                'reason': 'extreme weather event causing widespread damage',
                'explanation': 'extensive debris blocks multiple lanes completely'
            },
            'pedestrian': {
                'type': 'pedestrian incident',
                'reason': 'pedestrian injury or medical emergency on roadway',
                'explanation': 'emergency personnel are assisting and the area is unsafe'
            },
            'crash_vehicle_1lane': {
                'type': 'vehicle collision',
                'reason': 'traffic accident involving one or more vehicles',
                'explanation': 'damaged vehicles and emergency response block the lane'
            },
            'crash_vehicle_3lanes': {
                'type': 'multi-vehicle collision',
                'reason': 'major traffic accident involving multiple cars',
                'explanation': 'wreckage and emergency operations block all affected lanes'
            }
        }
        
        question = "What types of traffic accidents or obstructions are visible in the image?"
        
        # 查找所有事故/障碍物，合并相同类型
        accidents = []
        accidents_type = []
        has_barrier = False  # 标记是否已经有 barrier, barrier 类型合并为一个
        
        for v in self.vehicles.values():
            v_type = v['vehicle_type']
            if v_type in ACCIDENT_TYPES:
                # 检查是否是 barrier 类型
                if v_type.startswith('barrier_'):
                    # 如果还没有添加 barrier，添加一个通用的 barrier 说明
                    if not has_barrier:
                        # 使用 barrier_A 的描述作为代表（可以是任意一个）
                        accident_desc = ACCIDENT_TYPES['barrier_A']
                        accidents.append(accident_desc)
                        accidents_type.append('barrier')  # 使用通用标记
                        has_barrier = True
                # 其他类型的事故正常处理
                elif v_type not in accidents_type:
                    accident_desc = ACCIDENT_TYPES[v_type]
                    accidents.append(accident_desc)
                    accidents_type.append(v_type)
        
        # 构建详细回答
        if accidents:
            if len(accidents) == 1:
                acc = accidents[0]
                answer = f"There is a {acc['type']} due to {acc['reason']}. " \
                        f"The road cannot be passed because {acc['explanation']}."
            else:
                answer = "There are multiple types of obstructions preventing passage: "
                details = []
                for i, acc in enumerate(accidents, 1):
                    details.append(f"({i}) {acc['type']} caused by {acc['reason']} - {acc['explanation']}")
                answer += "; ".join(details) + "."
        else:
            answer = "There are no visible traffic accidents or obstructions blocking the road."
        
        # 生成 MCQ 选项（特殊事件类型）
        all_accident_types = ["Safety barrier", "Fallen tree", "Vehicle collision", "None"]
        
        if not accidents:
            correct_option_text = "None"
        else:
            # 确定正确答案类型, 每张图片只有一种类型的障碍
            accident_type = accidents[0]['type']
            if 'barrier' in accident_type.lower():
                correct_option_text = "Safety barrier"
            elif 'tree' in accident_type.lower():
                correct_option_text = "Fallen tree"
            elif 'collision' in accident_type.lower() or 'crash' in accident_type.lower():
                correct_option_text = "Vehicle collision"
            else:
                correct_option_text = "Safety barrier"  # 默认
        
        # 生成干扰项
        distractors = [at for at in all_accident_types if at != correct_option_text]
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
            'category': 'Special Events',
            'task': 'Single Image',
            'subtask': 'Recognition',
            'capabilities': ['Object Detection', 'Anomaly Detection', 'Scene Understanding', 'Event Classification']
        }    

    # ----------
    # 定位问题
    # ----------    
    def _generate_special_vehicle_lane_location(self):
        """定位问题：特殊车辆所在车道
        
        定位特殊车辆在哪个车道
        
        Returns:
            dict: 包含生成的问题和答案的字典
        """
        question = "Which lane are the emergency vehicles located in (from left to right, lane index starts from 1)?"
        
        # 查找特殊车辆及其车道
        special_vehicles_lanes = []
        for v in self.vehicles.values():
            if v['vehicle_type'].lower() in ['police', 'emergency', 'fire_engine'] and v['lane_id'] in self.in_lanes:
                dist = v['distance_to_intersection']
                if dist < self.max_incoming_distance:
                    # 从 lane_id 中提取车道编号 (格式: "road_laneNum")
                    _, lane_num_str = v['lane_id'].rsplit('_', 1)
                    lane_num = int(lane_num_str)
                    
                    type_mapping = {
                        'police': 'police car',
                        'emergency': 'ambulance',
                        'fire_engine': 'fire truck',
                    }
                    friendly_type = type_mapping.get(v['vehicle_type'], v['vehicle_type'])
                    
                    special_vehicles_lanes.append({
                        'type': friendly_type,
                        'lane': lane_num,
                        'distance': dist
                    })
        
        # 构建答案
        if not special_vehicles_lanes:
            answer = "There are no emergency vehicles visible in the incoming lanes."
        elif len(special_vehicles_lanes) == 1:
            veh = special_vehicles_lanes[0]
            # 车道编号+1，从1开始，说明是从左往右
            display_lane = veh['lane'] + 1
            answer = f"The {veh['type']} is located in incoming lane {display_lane} (from left to right), approximately {veh['distance']:.1f}m from the intersection."
        else: # 存在多个特殊车辆
            # 按车道分组
            lane_groups = {}
            for veh in special_vehicles_lanes:
                lane = veh['lane']
                if lane not in lane_groups:
                    lane_groups[lane] = []
                lane_groups[lane].append(veh)
            
            # 构建描述
            descriptions = []
            for lane, vehs in sorted(lane_groups.items()):
                # 车道编号+1，从1开始
                display_lane = lane + 1
                if len(vehs) == 1:
                    descriptions.append(f"lane {display_lane} (from left to right) has a {vehs[0]['type']}")
                else:
                    types = [v['type'] for v in vehs]
                    descriptions.append(f"lane {display_lane} (from left to right) has {', '.join(types)}")
            
            answer = f"Emergency vehicles are located in incoming {', '.join(descriptions)}."
        
        # 生成 MCQ 选项（车道编号）
        total_lanes = len(self.in_lanes)
        
        if not special_vehicles_lanes:
            correct_option_text = "None"
        else:
            # 选择第一个特殊车辆的车道作为正确答案
            primary_lane = special_vehicles_lanes[0]['lane'] + 1  # 从1开始
            correct_option_text = f"Lane {primary_lane}"
        
        # 生成所有可能的车道选项
        all_lane_options = [f"Lane {i+1}" for i in range(total_lanes)] + ["None"]
        
        # 生成干扰项
        distractors = [opt for opt in all_lane_options if opt != correct_option_text]
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
            'category': 'Special Vehicles',
            'task': 'Single Image',
            'subtask': 'Localization',
            'capabilities': ['Object Detection', 'Vehicle Classification', 'Lane Detection', 'Spatial Understanding', 'Distance Estimation']
        }
    
    def _generate_accident_affected_lanes(self):
        """定位问题：特殊事件影响的车道
        
        识别特殊事件影响哪些车道
        
        Returns:
            dict: 包含生成的问题和答案的字典
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
        
        question = "Which lanes are affected by the traffic accident or obstruction (from left to right, lane index starts from 1)?"

        # 获取incoming车道编号范围
        in_lane_nums = set()
        for lane_id in self.in_lanes.keys():
            _, lane_num_str = lane_id.rsplit('_', 1)
            in_lane_nums.add(int(lane_num_str))
        
        # 查找所有incoming车道的事故及其影响的车道
        accidents_by_lane = {}
        for v in self.vehicles.values():
            v_type = v['vehicle_type']
            if v_type in ACCIDENT_TYPES:
                lane_id = v['lane_id'] # 事故发生的 lane id
                
                # 只考虑incoming车道
                if lane_id in self.in_lanes:
                    _, lane_num_str = lane_id.rsplit('_', 1)
                    lane_num = int(lane_num_str)
                    available_lanes = in_lane_nums
                else:
                    # 跳过非incoming车道的事故
                    continue
                
                # 合并所有 barrier 类型为一个
                if v_type.startswith('barrier_'):
                    accident_type = 'safety barrier'
                else:
                    accident_type = ACCIDENT_TYPES[v_type]
                
                # 确定影响的车道列表
                # tree_branch_3lanes 和 crash_vehicle_3lanes 影响 3 个车道
                if v_type in ['tree_branch_3lanes', 'crash_vehicle_3lanes']:
                    affected_lanes = [lane_num - 1, lane_num, lane_num + 1]
                    # 过滤出有效的车道编号
                    affected_lanes = [ln for ln in affected_lanes if ln in available_lanes]
                else:
                    # 其他类型只影响当前车道
                    affected_lanes = [lane_num]
                
                # 为所有受影响的车道添加事故信息
                for affected_lane in affected_lanes:
                    if affected_lane not in accidents_by_lane:
                        accidents_by_lane[affected_lane] = []
                    
                    if accident_type not in accidents_by_lane[affected_lane]:
                        accidents_by_lane[affected_lane].append(accident_type)
        
        # 构建答案
        if not accidents_by_lane:
            answer = "There are no visible traffic accidents or obstructions affecting any incoming lanes."
        else:
            # 构建受影响车道的描述
            affected_lane_descs = []
            
            for lane_num, accidents in sorted(accidents_by_lane.items()):
                # 车道编号从1开始（+1）
                display_lane_num = lane_num + 1
                
                if len(accidents) == 1:
                    lane_desc = f"lane {display_lane_num} (blocked by {accidents[0]})"
                else:
                    accidents_list = ", ".join(accidents[:-1]) + " and " + accidents[-1]
                    lane_desc = f"lane {display_lane_num} (blocked by {accidents_list})"
                
                affected_lane_descs.append(lane_desc)
            
            # 构建详细答案
            total_incoming = len(in_lane_nums)
            answer = (
                f"Incoming direction has {total_incoming} lanes in total. "
                f"From left to right, {', '.join(affected_lane_descs)} "
                f"{'is' if len(affected_lane_descs) == 1 else 'are'} affected."
            )
        
        # 生成 MCQ 选项（车道组合）
        if not accidents_by_lane:
            correct_option_text = "None"
        else:
            # 生成车道组合字符串，例如 "Lane 1, 2"
            affected_lane_nums = sorted([lane_num + 1 for lane_num in accidents_by_lane.keys()])
            if len(affected_lane_nums) == 1:
                correct_option_text = f"Lane {affected_lane_nums[0]}"
            else:
                correct_option_text = f"Lane {', '.join(map(str, affected_lane_nums))}"
        
        # 生成干扰项（其他车道组合）
        total_incoming = len(in_lane_nums)
        all_possible_options = set()
        
        # 单个车道选项
        for i in range(total_incoming):
            all_possible_options.add(f"Lane {i+1}")
        
        # 两个车道组合（如果车道数>=2）
        if total_incoming >= 2:
            for i in range(total_incoming - 1):
                all_possible_options.add(f"Lane {i+1}, {i+2}")
        
        # 三个车道组合（如果车道数>=3）
        if total_incoming >= 3:
            for i in range(total_incoming - 2):
                all_possible_options.add(f"Lane {i+1}, {i+2}, {i+3}")
        
        all_possible_options.add("None")
        
        # 移除正确答案
        distractors = [opt for opt in all_possible_options if opt != correct_option_text]
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
            'category': 'Special Events',
            'task': 'Single Image',
            'subtask': 'Localization',
            'capabilities': ['Object Detection', 'Anomaly Detection', 'Lane Detection', 'Spatial Understanding', 'Impact Assessment']
        }

    # ----------
    # 其他问题
    # ----------  
    def _describe_vehicle_behavior_by_traffic_light(self):
        """Describe vehicle behavior based on known traffic light status.
        Note: Traffic light status is obtained from JSON data (not visible in image).
        
        Returns:
            dict: Contains the generated question and answer describing the scene
        """
        APPROACHING_THRESHOLD = 30
        question = "What are the vehicles in this lane doing? Are they moving or stopped?"
        
        # Get data with safety checks
        in_road = self.data.get('in_road', '')
        traffic_phase = self.data.get('traffic_phase', {})
        current_phase = str(self.data.get('current_phase', ''))
        
        # Determine if current road has green light
        has_green = False
        try:
            current_directions = traffic_phase.get(current_phase, [])
            controlled_lanes = {
                direction.split('--')[0] 
                for direction in current_directions if '--' in direction
            }
            has_green = in_road in controlled_lanes
        except Exception:
            pass
        
        # Generate description
        if self.closest_vehicle_distance >= self.max_incoming_distance:
            answer = "The lane is currently clear with no close vehicles near the intersection."
        elif self.closest_vehicle_distance <= APPROACHING_THRESHOLD:
            if has_green:
                answer = "Vehicles are flowing through the intersection with green light."
            else:
                answer = "Vehicles are fully stopped at the red light."
        else:
            if has_green:
                answer = f"Approaching vehicles are maintaining speed toward the green light."
            else:
                answer = f"Distant vehicles ({self.closest_vehicle_distance:.0f}m away) are beginning to slow for the red light."
        
        return {
            'question': question,
            'answer': answer,
            'category': 'Comprehensive Analysis',
            'task': 'Single Image',
            'subtask': 'Reasoning',
            'capabilities': ['Object Detection', 'Traffic Light Recognition', 'Distance Estimation', 'Behavior Analysis', 'Traffic Rule Understanding']
        }
