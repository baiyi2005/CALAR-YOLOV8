import carla
import cv2
import numpy as np
from queue import Queue
import threading

class CameraManager:
    def __init__(self, vehicle, world, blueprint_library, display_width=800, display_height=600):
        self.vehicle = vehicle
        self.world = world
        self.image_queue = Queue(maxsize=2)
        self.lock = threading.Lock()
        
        # 创建摄像头
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', str(display_width))
        camera_bp.set_attribute('image_size_y', str(display_height))
        camera_bp.set_attribute('fov', '110')
        
        # 安装位置
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        
        # 生成摄像头
        self.camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        
        # 设置回调
        self.camera.listen(self._process_image)
        
        print(f"[Camera] 摄像头安装完成: {display_width}x{display_height}")
    
    def _process_image(self, carla_image):
        try:
            # 转换图像格式
            array = np.frombuffer(carla_image.raw_data, dtype=np.uint8)
            array = array.reshape((carla_image.height, carla_image.width, 4))
            
            # 转为BGR
            bgr_array = np.zeros((carla_image.height, carla_image.width, 3), dtype=np.uint8)
            bgr_array[:, :, 0] = array[:, :, 2]  # B
            bgr_array[:, :, 1] = array[:, :, 1]  # G
            bgr_array[:, :, 2] = array[:, :, 0]  # R
            
            if not self.image_queue.full():
                self.image_queue.put(bgr_array)
                
        except Exception as e:
            print(f"[Camera] 图像处理错误: {e}")
    
    def get_frame(self, timeout=0.1):
        try:
            if not self.image_queue.empty():
                return self.image_queue.get(timeout=timeout)
        except:
            pass
        return None
    
    def cleanup(self):
        if hasattr(self, 'camera') and self.camera:
            try:
                self.camera.stop()
                self.camera.destroy()
                print("[Camera] 摄像头已销毁")
            except Exception as e:
                print(f"[Camera] 清理错误: {e}")