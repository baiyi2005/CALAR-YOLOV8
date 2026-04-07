import numpy as np
from collections import deque

class DistanceTracker:
    def __init__(self, max_history=10):
        self.max_history = max_history
        self.distance_history = {}
        self.last_distances = {}
        self.frame_count = 0
        self.kalman_gain = 0.3
        
        print(f"[Distance] 距离跟踪器初始化完成")
    
    def update_distances(self, detections, controller, current_speed_kmh=0):
        self.frame_count += 1
        updated_distances = []
        
        for det in detections:
            obj_class = det['class']
            obj_id = f"{obj_class}_{det['bbox'][0]}_{det['bbox'][1]}"
            
            # 估计距离
            estimated_distance = controller.estimate_distance(det, current_speed_kmh)
            
            # 平滑
            if obj_id in self.last_distances:
                last_distance = self.last_distances[obj_id]
                smoothed_distance = (1 - self.kalman_gain) * last_distance + self.kalman_gain * estimated_distance
            else:
                smoothed_distance = estimated_distance
            
            # 存储结果
            distance_info = {
                'object_id': obj_id,
                'class': obj_class,
                'distance': smoothed_distance,
                'raw_distance': estimated_distance,
                'frame': self.frame_count,
                'bbox': det['bbox']
            }
            
            updated_distances.append(distance_info)
            
            # 更新历史
            if obj_id not in self.distance_history:
                self.distance_history[obj_id] = deque(maxlen=self.max_history)
            
            self.distance_history[obj_id].append({
                'frame': self.frame_count,
                'distance': smoothed_distance
            })
            
            self.last_distances[obj_id] = smoothed_distance
        
        return updated_distances
    
    def get_closest_object(self, distances):
        if not distances:
            return None
        
        closest = min(distances, key=lambda x: x['distance'])
        return closest
    
    def clear_history(self):
        self.distance_history.clear()
        self.last_distances.clear()
        self.frame_count = 0
        print("[Distance] 距离历史记录已清除")