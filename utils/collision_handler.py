import carla

class CollisionHandler:
    def __init__(self, world, vehicle):
        self.world = world
        self.vehicle = vehicle
        self.collision_sensor = None
        self.collision_events = []
        self.last_collision_time = 0
        
        self._setup_collision_sensor()
        print("[Collision] 碰撞处理器初始化完成")
    
    def _setup_collision_sensor(self):
        try:
            blueprint_lib = self.world.get_blueprint_library()
            collision_bp = blueprint_lib.find('sensor.other.collision')
            
            self.collision_sensor = self.world.spawn_actor(
                collision_bp, 
                carla.Transform(), 
                attach_to=self.vehicle
            )
            
            self.collision_sensor.listen(self._on_collision)
            print("[Collision] 碰撞传感器已安装")
            
        except Exception as e:
            print(f"[Collision] 设置传感器失败: {e}")
    
    def _on_collision(self, collision_event):
        import time
        other_actor = collision_event.other_actor
        impulse = collision_event.normal_impulse
        impulse_magnitude = (impulse.x**2 + impulse.y**2 + impulse.z**2)**0.5
        
        current_time = time.time()
        
        # 避免重复记录
        if current_time - self.last_collision_time < 2.0:
            return
        
        collision_info = {
            'timestamp': current_time,
            'other_actor_type': other_actor.type_id if other_actor else 'unknown',
            'impulse_magnitude': impulse_magnitude
        }
        
        self.collision_events.append(collision_info)
        self.last_collision_time = current_time
        
        print(f"[Collision] 检测到碰撞! 强度: {impulse_magnitude:.2f}")
    
    def has_collision(self):
        if not self.collision_events:
            return False
        
        import time
        current_time = time.time()
        recent = [e for e in self.collision_events if current_time - e['timestamp'] < 2.0]
        
        return len(recent) > 0
    
    def cleanup(self):
        if self.collision_sensor:
            try:
                self.collision_sensor.stop()
                self.collision_sensor.destroy()
                print("[Collision] 碰撞传感器已销毁")
            except Exception as e:
                print(f"[Collision] 清理传感器失败: {e}")