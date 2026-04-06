import cv2
import numpy as np

class ACPEDetector:
    def __init__(self, model_path='yolov8n.pt', confidence_thresh=0.5):
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
        except ImportError:
            print("请安装: pip install ultralytics")
            raise
        
        self.conf_thresh = confidence_thresh
        self.target_classes = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle',
            5: 'bus', 7: 'truck'
        }
        
        print(f"[Detector] 模型加载: {model_path}")
    
    def detect(self, image_bgr):
        if image_bgr is None:
            return []
        
        try:
            # 转为RGB
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            
            # 检测
            results = self.model(image_rgb, conf=self.conf_thresh, verbose=False)[0]
            
            detections = []
            if hasattr(results, 'boxes') and results.boxes is not None:
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    if cls_id in self.target_classes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        
                        detections.append({
                            'class': self.target_classes[cls_id],
                            'confidence': conf,
                            'bbox': (int(x1), int(y1), int(x2), int(y2))
                        })
            
            return detections
            
        except Exception as e:
            print(f"[Detector] 检测错误: {e}")
            return []