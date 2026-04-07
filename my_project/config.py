#!/usr/bin/env python3
"""
配置文件
系统参数和配置
"""

import os

class Config:
    """系统配置类"""
    
    # 项目路径
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # CARLA配置
    CARLA_HOST = 'localhost'
    CARLA_PORT = 2000
    CARLA_TIMEOUT = 20.0
    
    # 摄像头配置
    CAMERA_WIDTH = 800
    CAMERA_HEIGHT = 600
    CAMERA_FOV = 110
    CAMERA_POSITION = {'x': 1.5, 'y': 0.0, 'z': 2.4}  # 相对于车辆的位置
    
    # 检测器配置
    DETECTOR_MODEL = 'yolov8n.pt'  # 自动下载
    DETECTOR_CONFIDENCE_THRESH = 0.5
    TARGET_CLASSES = {
        0: 'person',
        1: 'bicycle',
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck'
    }
    
    # 控制器配置
    CONTROL_PARAMS = {
        'max_speed_kmh': 30.0,
        'person_risk_zone_height': 150,
        'vehicle_risk_zone_height': 100,
        'max_throttle': 0.3,
        'creep_throttle': 0.05,
        'brake_pedal': 1.0,
        'steer_angle': 0.0,
        'emergency_brake_speed': 5.0
    }
    
    # 测试场景配置
    TEST_SCENARIOS = [
        {
            'name': '无障碍物',
            'description': '车辆在空旷道路前进',
            'obstacle_type': 'none',
            'obstacle_distance': 0,
            'duration': 30
        },
        {
            'name': '前方静止车辆',
            'description': '测试对静止障碍物的反应',
            'obstacle_type': 'a2',
            'obstacle_distance': 20.0,
            'duration': 60
        },
        {
            'name': '前方行人',
            'description': '测试对行人的反应',
            'obstacle_type': 'person',
            'obstacle_distance': 15.0,
            'duration': 60
        }
    ]
    
    # 车辆配置
    VEHICLE_TYPE = 'model3'
    VEHICLE_COLOR = '255,0,0'  # 红色
    OBSTACLE_COLOR = '0,0,255'  # 蓝色
    
    # 输出配置
    OUTPUT_DIR = 'output'
    DATA_FILE = 'test_data.csv'
    REPORT_FILE = 'test_report.txt'
    LOG_FILE = 'system_log.txt'
    
    @classmethod
    def setup_directories(cls):
        """创建必要的目录"""
        directories = [
            cls.OUTPUT_DIR,
            os.path.join(cls.OUTPUT_DIR, 'screenshots'),
            os.path.join(cls.OUTPUT_DIR, 'videos'),
            os.path.join(cls.OUTPUT_DIR, 'logs')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"[Config] 创建目录: {directory}")
    
    @classmethod
    def get_camera_transform(cls):
        """获取摄像头位置变换"""
        from carla import Transform, Location
        return Transform(
            Location(
                x=cls.CAMERA_POSITION['x'],
                y=cls.CAMERA_POSITION['y'],
                z=cls.CAMERA_POSITION['z']
            )
        )
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("=" * 60)
        print("系统配置")
        print("=" * 60)
        
        print(f"项目根目录: {cls.PROJECT_ROOT}")
        print(f"CARLA服务器: {cls.CARLA_HOST}:{cls.CARLA_PORT}")
        print(f"摄像头分辨率: {cls.CAMERA_WIDTH}x{cls.CAMERA_HEIGHT}")
        print(f"检测模型: {cls.DETECTOR_MODEL}")
        print(f"检测置信度阈值: {cls.DETECTOR_CONFIDENCE_THRESH}")
        print(f"目标类别: {list(cls.TARGET_CLASSES.values())}")
        print(f"最大速度限制: {cls.CONTROL_PARAMS['max_speed_kmh']} km/h")
        print(f"输出目录: {cls.OUTPUT_DIR}")
        
        print("\n测试场景:")
        for i, scenario in enumerate(cls.TEST_SCENARIOS, 1):
            print(f"  {i}. {scenario['name']}: {scenario['description']}")
        
        print("=" * 60)
