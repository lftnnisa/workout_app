import time
import cv2
import os
import sys
import logging
from datetime import datetime
from ultralytics import YOLO
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DetectionThread(QThread):
    updateData = pyqtSignal(dict)
    updateFrame = pyqtSignal(QImage)
    errorOccurred = pyqtSignal(str)

    def __init__(self, mode="squat", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.running = False
        self.threshold = 0.5
        self.model = self.load_model()
        self.ready_to_start = False
        # Inisialisasi awal untuk memastikan nilai default
        self.squat_start_time = 0.0
        self.plank_start_time = 0.0
        self.last_plank_detection_time = 0.0
        self.squat_count = 0 # Inisialisasi squat_count di sini

    def load_model(self):
        try:
            model_path = resource_path(os.path.join("models", "best_yolov8new.pt"))
            return YOLO(model_path)
        except Exception as e:
            self.errorOccurred.emit(f"Failed to load model: {str(e)}")
            return None
        
    def enable_start(self):
        """Dipanggil setelah hitungan mundur selesai untuk memulai penghitungan."""
        self.ready_to_start = True
        self.squat_start_time = time.time() # Reset waktu mulai squat
        self.plank_start_time = time.time() # Reset waktu mulai plank
        self.last_plank_detection_time = time.time() # Reset waktu deteksi plank terakhir
        self.squat_count = 0 # Reset hitungan squat
        logging.info(f"Exercise started. Squat start time: {self.squat_start_time}, Plank start time: {self.plank_start_time}")

    def run(self):
        if not self.model:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.errorOccurred.emit("Could not open webcam")
            return
            
        self.running = True
        prev_state = "stand"
        state_changed = False
        # squat_count, squat_start_time, plank_start_time, last_plank_detection_time
        # sekarang diambil dari self. variabel
        plank_active_time = 0.0
        plank_detected_in_frame = False
        no_detection_start = None

        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                current_time = time.time()
                results = self.model(frame, imgsz=640, verbose=False)
                
                # Process detections
                annotated_frame, detected_class, detected_conf = self.process_detections(frame, results)

                plank_detected_in_frame = False

                data = {"mode": self.mode}

                if self.mode == "squat":
                    if detected_class == "squat" and prev_state == "stand":
                        state_changed = True
                    elif detected_class == "stand" and prev_state == "squat" and state_changed:
                        if self.ready_to_start: # Hanya hitung jika penghitungan sudah dimulai
                            self.squat_count += 1
                        state_changed = False
                    
                    squat_duration = 0
                    if self.ready_to_start:
                        squat_duration = int(current_time - self.squat_start_time)

                    data.update({
                        "squat_count": self.squat_count,
                        "squat_duration": squat_duration
                    })
                    prev_state, state_changed = self.update_squat_state(detected_class, prev_state, state_changed)
                
                elif self.mode == "plank":
                    if detected_class == "plank" and detected_conf >= 70:
                        plank_detected_in_frame = True
                        
                    if self.ready_to_start:
                        if plank_detected_in_frame:
                            plank_active_time += (current_time - self.last_plank_detection_time)
                        self.last_plank_detection_time = current_time

                        total_time = int(current_time - self.plank_start_time)
                    else:
                        total_time = 0
                        plank_active_time = 0

                    data.update({
                        "plank_total_time": total_time,
                        "plank_active_time": int(plank_active_time),
                        "plank_accuracy": int(detected_conf) if detected_class == "plank" else 0
                    })
                    
                    if detected_class == "plank" and detected_conf < 50:
                        data["warning"] = "Plank accuracy below 50%! Stopping exercise."
                        self.running = False

                no_detection_start = self.update_no_detection(
                    detected_class, current_time, no_detection_start
                )
                
                if detected_class is None and no_detection_start and \
                   (current_time - no_detection_start > 10):
                    data["warning"] = "No pose detected for 10 seconds! Stopping exercise."
                    self.running = False

                if self.ready_to_start:
                    self.updateData.emit(data)
                self.emit_frame(annotated_frame)
                self.msleep(1)

        except Exception as e:
            logging.error(f"Detection error: {e}")
            self.errorOccurred.emit(f"Detection error: {str(e)}")
        finally:
            self.cap.release()

    def process_detections(self, frame, results):
        annotated_frame = frame.copy()
        detected_class = None
        detected_conf = 0.0
        best_box = None
        highest_conf = 0.0

        for result in results:
            if result.keypoints is not None:
                for kp in result.keypoints.xy:
                    keypoints = [(int(x), int(y)) for x, y in kp]

                    for x, y in keypoints:
                        cv2.circle(annotated_frame, (x, y), 4, (0, 0, 255), -1)

                    skeleton = [
                        (0, 1),      # head to neck
                        (1, 2), (2, 3), (3, 4), (4, 5),      # left arm
                        (1, 10), (10, 11), (11, 12), (12, 13),  # right arm
                        (1, 6),       # neck to mid-hip
                        (6, 17), (17, 14), (14, 15), (15, 18),  # left leg
                        (6, 19), (19, 7), (7, 8), (8, 9)        # right leg
                    ]

                    for i, j in skeleton:
                        if i < len(keypoints) and j < len(keypoints):
                            pt1 = keypoints[i]
                            pt2 = keypoints[j]
                            if pt1 != (0, 0) and pt2 != (0, 0):
                                cv2.line(annotated_frame, pt1, pt2, (255, 0, 0), 2)
                            for box in result.boxes:
                                conf = float(box.conf)
                                if conf > highest_conf and conf > self.threshold:
                                    highest_conf = conf
                                    best_box = box
                                    cls_id = int(box.cls)
                                    detected_class = self.model.names[cls_id]
                                    detected_conf = conf * 100

        if best_box:
            xyxy = best_box.xyxy[0].tolist()
            color = (0, 255, 0)
            thickness = 2
            cv2.rectangle(
                annotated_frame,
                (int(xyxy[0]), int(xyxy[1])),
                (int(xyxy[2]), int(xyxy[3])),
                color, thickness
            )
            label = f"{detected_class}: {detected_conf:.1f}%"
            cv2.putText(
                annotated_frame, label,
                (int(xyxy[0]), int(xyxy[1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, thickness
            )

        return annotated_frame, detected_class, detected_conf

    def update_squat_state(self, detected_class, prev_state, state_changed):
        if detected_class == "squat":
            if prev_state == "stand":
                state_changed = True
            return "squat", state_changed
        elif detected_class == "stand":
            return "stand", state_changed
        return prev_state, state_changed

    def update_no_detection(self, detected_class, current_time, no_detection_start):
        if detected_class is None:
            return current_time if no_detection_start is None else no_detection_start
        return None

    def emit_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        q_img = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.updateFrame.emit(q_img)

    def stop(self):
        self.running = False
        self.wait(2000)