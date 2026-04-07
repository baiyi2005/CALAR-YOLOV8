#!/usr/bin/env python3
"""
决策控制器 (暴力刹车版)
唯一目标：检测到障碍物，就强制刹车！
"""
import carla
import numpy as np

class ACPEController:
    def __init__(self, image_width=800, image_height=600):
        self.image_width = image_width
        self.image_height = image_height
        
        # ！！！极端的刹车阈值 ！！！
        # 只要估计距离小于这个值，就全力刹车
        self.EMERGENCY_BRAKE_DISTANCE = 20.0  # 20米内，有障碍物就刹车
        
        # 保守的距离估计系数 (让估计距离比实际更近)
        self.distance_estimate_bias = 0.7
        
        print(f"[控制器] 暴力刹车版初始化！触发距离: {self.EMERGENCY_BRAKE_DISTANCE}米")
    
    def estimate_distance(self, detection, current_speed_kmh=0):
        """
        超级保守的距离估计：永远返回一个偏小的值，促使系统提前刹车。
        """
        x1, y1, x2, y2 = detection['bbox']
        bbox_height = y2 - y1
        
        if bbox_height <= 0:
            return 5.0  # 默认返回很近的距离
        
        # 物体在图像中越高(bbox_height越小)，估计距离越远，但我们把它估计得很近
        estimated_distance = 500.0 / bbox_height  # 简单反比关系
        
        # 应用保守偏置，让估计距离更近
        estimated_distance *= self.distance_estimate_bias
        
        # 进一步考虑车速：车速越快，需要更早刹车
        speed_factor = 1.0 + (current_speed_kmh / 20.0)
        estimated_distance /= speed_factor
        
        return max(1.0, estimated_distance)
    
    def make_decision(self, detections, current_speed_kmh=0, pedal_depth=0, is_mistake_press=False, frame_count=0):
        """
        决策逻辑：有障碍物 -> 刹车
        """
        control = carla.VehicleControl(throttle=0.0, brake=0.0, steer=0.0)
        control_desc = "无目标，正常行驶"
        risk_level = 0
        
        if not detections:
            # 无障碍物，但如果是误踩，也轻轻限制一下
            if is_mistake_press and pedal_depth > 0.7:
                control.brake = 0.3
                control_desc = "误踩，轻度限制"
                risk_level = 1
            else:
                control.throttle = min(pedal_depth, 0.3)  # 限制最高油门
            return control, risk_level, control_desc
        
        # ==== 核心：检测到障碍物 ====
        min_distance = float('inf')
        for det in detections:
            distance = self.estimate_distance(det, current_speed_kmh)
            if distance < min_distance:
                min_distance = distance
                closest_class = det['class']
        
        print(f"[决策] 检测到 {len(detections)} 个障碍物，最近的是 {closest_class}，估计距离 {min_distance:.1f} 米")
        
        # ！！！！！！ 暴力刹车逻辑 ！！！！！！
        if min_distance < self.EMERGENCY_BRAKE_DISTANCE:
            # 只要在触发距离内，无视一切，全力刹车
            control.throttle = 0.0
            control.brake = 1.0  # 全力刹车
            control.hand_brake = False
            control_desc = f"🚨 强制刹车！距离{closest_class}:{min_distance:.1f}m"
            risk_level = 4
            print(f"[决策] {control_desc}")
        else:
            # 距离较远，但检测到了，也限制油门
            control.throttle = 0.1
            control.brake = 0.1
            control_desc = f"检测到目标，谨慎前进。距离{closest_class}:{min_distance:.1f}m"
            risk_level = 2
        
        return control, risk_level, control_desc
    
    def reset(self):
        print("[控制器] 状态重置")