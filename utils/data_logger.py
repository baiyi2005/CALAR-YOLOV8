import csv
import json
import time
from datetime import datetime
import os

class DataLogger:
    def __init__(self):
        self.data = []
        self.start_time = time.time()
        self.frame_count = 0
        self.collision_count = 0
        self.emergency_brake_count = 0
        
        os.makedirs('output', exist_ok=True)
        print("[Logger] 数据记录器初始化完成")
    
    def log(self, data_dict):
        data_dict['timestamp'] = data_dict.get('timestamp', time.time())
        data_dict['elapsed_time'] = data_dict['timestamp'] - self.start_time
        data_dict['frame'] = self.frame_count
        
        if data_dict.get('risk_level', 0) >= 4:
            self.emergency_brake_count += 1
        
        self.data.append(data_dict)
        self.frame_count += 1
    
    def save_to_csv(self, filename='output/test_data.csv'):
        if not self.data:
            print("[Logger] 没有数据可保存")
            return
        
        try:
            fieldnames = set()
            for entry in self.data:
                fieldnames.update(entry.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in self.data:
                    row = {field: entry.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            print(f"[Logger] 数据已保存: {filename}")
            
        except Exception as e:
            print(f"[Logger] 保存CSV失败: {e}")
    
    def generate_report(self, filename='output/test_report.txt'):
        if not self.data:
            print("[Logger] 没有数据可生成报告")
            return
        
        try:
            total_time = time.time() - self.start_time
            avg_fps = self.frame_count / total_time if total_time > 0 else 0
            
            risk_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
            speed_sum = 0
            
            for entry in self.data:
                risk_level = entry.get('risk_level', 0)
                if risk_level in risk_counts:
                    risk_counts[risk_level] += 1
                speed_sum += entry.get('speed_kmh', 0)
            
            avg_speed = speed_sum / len(self.data) if self.data else 0
            
            report_lines = [
                "=" * 60,
                "低速障碍物检测系统 - 测试报告",
                "=" * 60,
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"总运行时间: {total_time:.2f}秒",
                f"总帧数: {self.frame_count}",
                f"平均帧率: {avg_fps:.2f} FPS",
                f"碰撞次数: {self.collision_count}",
                f"紧急刹车次数: {self.emergency_brake_count}",
                f"平均车速: {avg_speed:.2f} km/h",
                "",
                "风险等级分布:",
                f"  安全(0): {risk_counts[0]}帧 ({risk_counts[0]/self.frame_count*100:.1f}%)",
                f"  低风险(1): {risk_counts[1]}帧 ({risk_counts[1]/self.frame_count*100:.1f}%)",
                f"  中风险(2): {risk_counts[2]}帧 ({risk_counts[2]/self.frame_count*100:.1f}%)",
                f"  高风险(3): {risk_counts[3]}帧 ({risk_counts[3]/self.frame_count*100:.1f}%)",
                f"  紧急(4): {risk_counts[4]}帧 ({risk_counts[4]/self.frame_count*100:.1f}%)",
                "",
                "=" * 60
            ]
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            print(f"[Logger] 报告已生成: {filename}")
            
        except Exception as e:
            print(f"[Logger] 生成报告失败: {e}")
    
    def clear(self):
        self.data.clear()
        self.frame_count = 0
        self.collision_count = 0
        self.emergency_brake_count = 0
        self.start_time = time.time()
        print("[Logger] 数据已清除")