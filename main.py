import sys
import os
import time
import carla
import cv2
import numpy as np
import argparse
from datetime import datetime
import traceback

# 设置CARLA路径
CARLA_INSTALL_PATH = r"D:\calar"  # 修改为您的CARLA路径
sys.path.append(os.path.join(CARLA_INSTALL_PATH, 'PythonAPI', 'carla'))

# 添加项目模块路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(PROJECT_ROOT, 'sensors'))
sys.path.append(os.path.join(PROJECT_ROOT, 'controller'))
sys.path.append(os.path.join(PROJECT_ROOT, 'utils'))

try:
    from camera_manager import CameraManager
    from detector import ACPEDetector
    from decision_maker import ACPEController
    from data_logger import DataLogger
    from collision_handler import CollisionHandler
    from distance_tracker import DistanceTracker
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='低速障碍物检测系统')
    parser.add_argument('--duration', type=int, default=60, help='测试时长(秒)')
    parser.add_argument('--obstacle-type', type=str, default='a2', 
                       choices=['a2', 'person', 'none'], help='障碍物类型')
    parser.add_argument('--obstacle-distance', type=float, default=20.0, 
                       help='障碍物距离(米)')
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs('output', exist_ok=True)
    os.makedirs('output/screenshots', exist_ok=True)
    
    try:
        # 1. 连接CARLA
        print("=" * 60)
        print("低速障碍物检测与加速踏板控制系统")
        print("=" * 60)
        
        print("[1/6] 连接CARLA服务器...")
        client = carla.Client('localhost', 2000)
        client.set_timeout(20.0)
        world = client.get_world()
        blueprint_lib = world.get_blueprint_library()
        
        # 设置天气
        world.set_weather(carla.WeatherParameters.ClearNoon)
        print("✅ CARLA连接成功")
        
        # 2. 生成车辆
        print("[2/6] 生成测试车辆...")
        vehicle_bp = blueprint_lib.filter('model3')[0]
        vehicle_bp.set_attribute('color', '255,0,0')
        
        spawn_points = world.get_map().get_spawn_points()
        vehicle = world.try_spawn_actor(vehicle_bp, spawn_points[0])
        
        if not vehicle:
            print("❌ 车辆生成失败")
            return
        
        print("✅ 车辆生成成功")
        
        # 3. 生成障碍物
        print("[3/6] 生成障碍物...")
        obstacle = None
        if args.obstacle_type != 'none':
            spawn_location = spawn_points[0].location
            obstacle_location = carla.Location(
                x=spawn_location.x + args.obstacle_distance,
                y=spawn_location.y,
                z=spawn_location.z
            )
            
            if args.obstacle_type == 'a2':
                obstacle_bp = blueprint_lib.filter('a2')[0]
                obstacle_bp.set_attribute('color', '0,0,255')
            elif args.obstacle_type == 'person':
                obstacle_bp = blueprint_lib.find('walker.pedestrian.0001')
            
            obstacle = world.try_spawn_actor(
                obstacle_bp, 
                carla.Transform(obstacle_location)
            )
            
            if obstacle:
                print(f"✅ 障碍物生成成功 (距离 {args.obstacle_distance}米)")
        
        # 4. 初始化模块
        print("[4/6] 初始化系统模块...")
        
        # 摄像头
        cam_manager = CameraManager(vehicle, world, blueprint_lib)
        time.sleep(2.0)
        
        # 检测器
        detector = ACPEDetector(confidence_thresh=0.4)
        
        # 控制器
        controller = ACPEController()
        
        # 数据记录器
        data_logger = DataLogger()
        
        # 碰撞处理器
        collision_handler = CollisionHandler(world, vehicle)
        
        # 距离跟踪器
        distance_tracker = DistanceTracker()
        
        print("[5/6] 系统初始化完成")
        
        # 5. 主循环
        print("[6/6] 开始主循环 (按Q退出)...")
        print("=" * 60)
        
        cv2.namedWindow('低速障碍物检测系统', cv2.WINDOW_NORMAL)
        
        start_time = time.time()
        frame_count = 0
        
        # 踏板模拟
        pedal_states = [
            (0.3, False, 5.0),   # 正常5秒
            (0.8, True, 3.0),    # 误踩3秒
            (0.2, False, 20.0)   # 恢复正常
        ]
        state_index = 0
        state_start = time.time()
        
        try:
            while (time.time() - start_time) < args.duration:
                frame_count += 1
                current_time = time.time() - start_time
                
                # 获取图像
                frame = cam_manager.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # 获取速度
                velocity = vehicle.get_velocity()
                speed_kmh = 3.6 * (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
                
                # 踏板状态
                elapsed_state = time.time() - state_start
                if state_index < len(pedal_states):
                    pedal_depth, is_mistake, state_duration = pedal_states[state_index]
                    if elapsed_state > state_duration:
                        state_index += 1
                        state_start = time.time()
                        if state_index < len(pedal_states):
                            pedal_depth, is_mistake, _ = pedal_states[state_index]
                
                # 目标检测
                detections = detector.detect(frame)
                
                # 估计距离
                distances = []
                for det in detections:
                    distance = controller.estimate_distance(det, speed_kmh)
                    distances.append({
                        'detection': det,
                        'distance': distance
                    })
                
                # 决策控制
                control, risk_level, control_desc = controller.make_decision(
                    detections, speed_kmh, pedal_depth, is_mistake, frame_count
                )
                
                # 调试信息
                print(f"[DEBUG] 帧:{frame_count} 速度:{speed_kmh:.1f} 踏板:{pedal_depth:.2f} 误踩:{is_mistake}")
                print(f"[DEBUG] 检测到目标数: 1")
                if detections:
                    for i, det in enumerate(detections):
                        dist = controller.estimate_distance(det, speed_kmh)
                        print(f"[DEBUG]   目标: 1 置信度:{det['confidence']:.2f} 估计距离:{dist:.1f}")
                print(f"[DEBUG] 决策结果: 风险{risk_level} | 描述: {control_desc}")
                print(f"[DEBUG] 控制指令: 油门={control.throttle:.2f}, 刹车={control.brake:.2f}")
                print("-" * 50)
                
                # 应用控制
                vehicle.apply_control(control)
                
                # 碰撞检测
                if collision_handler.has_collision():
                    print("🚨 检测到碰撞！")
                
                # 可视化
                display = frame.copy()
                
                # 绘制检测框
                for i, det in enumerate(detections):
                    x1, y1, x2, y2 = det['bbox']
                    obj_class = det['class']
                    confidence = det['confidence']
                    
                    # 颜色
                    if obj_class == 'person':
                        color = (0, 0, 255)
                    elif obj_class in ['car', 'truck', 'bus']:
                        color = (0, 255, 255)
                    else:
                        color = (0, 255, 0)
                    
                    # 绘制框
                    cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
                    
                    # 标签
                    distance_str = f"{distances[i]['distance']:.1f}m" if i < len(distances) else "N/A"
                    label = f"{obj_class} {confidence:.1f} {distance_str}"
                    
                    cv2.rectangle(display, (x1, y1-20), (x1+200, y1), color, -1)
                    cv2.putText(display, label, (x1, y1-5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # 状态信息
                info = [
                    f"时间: {current_time:.1f}s / {args.duration}s",
                    f"车速: {speed_kmh:.1f} km/h",
                    f"踏板: {pedal_depth:.2f} {'(误踩!)' if is_mistake else ''}",
                    f"检测: {len(detections)} 目标",
                    f"风险: {risk_level}/4",
                    f"控制: {control_desc}",
                    f"油门: {control.throttle:.2f} 刹车: {control.brake:.2f}"
                ]
                
                y0 = 30
                for i, line in enumerate(info):
                    y = y0 + i * 25
                    color = (0, 255, 0)
                    if risk_level >= 4 or "紧急" in line:
                        color = (0, 0, 255)
                    elif risk_level >= 2 or "危险" in line:
                        color = (0, 255, 255)
                    cv2.putText(display, line, (10, y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # 控制条
                bar_y = display.shape[0] - 50
                bar_w = 200
                
                # 油门条
                throttle_w = int(control.throttle * bar_w)
                cv2.rectangle(display, (10, bar_y), (10+throttle_w, bar_y+20), (0, 255, 0), -1)
                cv2.putText(display, f"油门: {control.throttle:.2f}", (10, bar_y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # 刹车条
                brake_w = int(control.brake * bar_w)
                cv2.rectangle(display, (220, bar_y), (220+brake_w, bar_y+20), (0, 0, 255), -1)
                cv2.putText(display, f"刹车: {control.brake:.2f}", (220, bar_y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                cv2.imshow('低速障碍物检测系统', display)
                
                # 按键处理
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"output/screenshots/screenshot_{timestamp}.jpg"
                    cv2.imwrite(filename, display)
                    print(f"截图保存: {filename}")
                
                time.sleep(0.05)
            
        except KeyboardInterrupt:
            print("\n程序中断")
        
        # 6. 清理
        cv2.destroyAllWindows()
        cam_manager.cleanup()
        collision_handler.cleanup()
        if obstacle:
            obstacle.destroy()
        vehicle.destroy()
        
        # 保存数据
        data_logger.save_to_csv('output/test_data.csv')
        data_logger.generate_report('output/test_report.txt')
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()