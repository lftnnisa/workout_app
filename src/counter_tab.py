from datetime import datetime
from ultralytics import YOLO
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, 
    QGroupBox, QLineEdit, QMessageBox
)
from voice_thread import VoiceCommandThread
from detection_thread import DetectionThread
from config_manager import get_pc_id

class CounterTab(QWidget):
    sessionFinished = pyqtSignal(dict)
    errorOccurred = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = None
        self.detection_thread = None
        self.voice_thread = None
        self.latest_data = {}
        self.counting_started = False
        self.pc_id = get_pc_id() # Get the PC ID when the tab is initialized
        print(f"CounterTab initialized with PC ID: {self.pc_id}") # DEBUG PRINT
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Name input
        self.name_input = self.create_name_input()
        layout.addLayout(self.name_input)

        # Mode selection (DROPDOWN)
        self.mode_selector = self.create_mode_selector()
        layout.addWidget(self.mode_selector)

        # Camera feed
        self.camera_label = self.create_camera_label()
        layout.addWidget(self.camera_label, 0, Qt.AlignCenter)

        # Countdown label
        self.countdown_label = QLabel("", self)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 24px; color: red;")
        self.countdown_label.hide()  # Hide by default
        layout.addWidget(self.countdown_label)

        # Buttons
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)

        # Info display
        self.info_label = self.create_info_label()
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def create_name_input(self):
        layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold;")
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter your name")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        layout.addStretch()
        return layout

    def create_mode_selector(self):
        group = QGroupBox("Exercise Mode")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Select Mode", "Squat", "Plank"])
        self.mode_combo.setCurrentIndex(0)
        
        # Style for QComboBox
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 120px;
                font-size: 14px;
                color: #000000; /* Added to ensure text color is black */
            }
            QComboBox:hover {
                border: 1px solid #aaa;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ddd;
            }
            QComboBox::down-arrow {
                image: url(icons/down_arrow.svg);  /* Replace with your arrow path */
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ddd;
                background: white;
                selection-background-color: #e0f7fa;
                padding: 4px;
                margin: 0px;
                outline: none;
            }
            QComboBox:disabled {
                background: #f5f5f5;
                color: #999;
            }
        """)
        
        layout = QHBoxLayout()
        layout.addWidget(self.mode_combo)
        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_camera_label(self):
        label = QLabel("Camera Feed")
        label.setFixedSize(640, 480)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                border: 2px solid #aaa;
                border-radius: 5px;
                background-color: #000;
            }
        """)
        return label

    def create_button_layout(self):
        layout = QHBoxLayout()
        
        self.start_button = self.create_button(
            "Start Exercise", "#4CAF50", "#45a049", self.start_tracking
        )
        self.start_button.setEnabled(False)  # Default: disabled

        self.stop_button = self.create_button(
            "Stop Exercise", "#f44336", "#d32f2f", self.stop_tracking
        )
        self.stop_button.setEnabled(False)
        
        layout.addStretch()
        layout.addWidget(self.start_button)
        layout.addSpacing(10)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        return layout

    def create_button(self, text, color, hover_color, callback):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
            }}
        """)
        button.clicked.connect(callback)
        return button

    def create_info_label(self):
        label = QLabel("Please select exercise mode.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        return label

    def setup_connections(self):
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)

    def on_mode_changed(self):
        selected = self.mode_combo.currentText()
        self.stop_camera()
        self.stop_voice_listening()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.counting_started = False

        if selected == "Select Mode":  # Adjust to the new text
            self.info_label.setText("Please select exercise mode.")
            self.mode = None
            return
        else:
            self.mode = selected.lower()
            self.info_label.setText(f"Mode: {selected}\nReady to start. Say 'start' or click Start!")
            self.start_camera_preview()
            self.start_voice_listening()
            self.start_button.setEnabled(True)


    def start_camera_preview(self):
        if self.detection_thread:
            self.detection_thread.stop()
            self.detection_thread = None
        self.detection_thread = DetectionThread(mode=self.mode)
        self.detection_thread.updateFrame.connect(self.update_camera)
        self.detection_thread.start()
        # DO NOT connect updateData here, only for preview (not counting)

    def stop_camera(self):
        if self.detection_thread:
            self.detection_thread.stop()
            self.detection_thread = None
        self.camera_label.clear()

    def start_tracking(self):
        if self.counting_started:
            return  # Already counting, ignore

        name = self.name_edit.text().strip()
        if not name:
            self.show_error("Name cannot be empty!")
            return
        if self.mode is None:
            self.show_error("Please select an exercise mode!")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)  # Disable stop button during countdown

        # Start detection with updateData (activate counting)
        self.detection_thread = DetectionThread(mode=self.mode)
        self.detection_thread.counting_started = False
        self.detection_thread.updateData.connect(self.update_info)
        self.detection_thread.updateFrame.connect(self.update_camera)
        self.detection_thread.errorOccurred.connect(self.handle_detection_error)
        self.detection_thread.start()

        # Initialize countdown variables
        self.countdown_time = 5  # Countdown from 5 seconds
        self.show_countdown_label(self.countdown_time)

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.timeout.connect(self.send_start_to_thread)

        self.countdown_timer.start(1000)  # 1 second intervals

    def send_start_to_thread(self):
        if self.countdown_time == 1 and self.detection_thread:
            self.detection_thread.enable_start()

    def show_countdown_label(self, time_left):
        # You can customize this to show countdown on a QLabel or overlay
        self.countdown_label.setText(f"Starting in {time_left}...")
        self.countdown_label.show()

    def update_countdown(self):
        self.countdown_time -= 1
        if self.countdown_time > 0:
            self.show_countdown_label(self.countdown_time)
        else:
            self.countdown_timer.stop()
            self.countdown_label.hide()
            self.start_counting()

    def start_counting(self):
        self.counting_started = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_tracking(self):
        if not self.counting_started:
            return  # Not currently counting
        self.stop_voice_listening()
        self.stop_camera()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.counting_started = False

        name = self.name_edit.text().strip() or "Unknown"
        session_data = {
            "name": name,
            "mode": self.mode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pc_id": self.pc_id 
        }
        session_data.update(self.latest_data)
        print(f"Emitting session data with PC ID: {session_data.get('pc_id')}") # DEBUG PRINT
        self.sessionFinished.emit(session_data)
        self.info_label.setText("Session finished. Please select mode or start again.")

    def update_info(self, data):
        self.latest_data = data
        if "warning" in data:
            self.show_warning(data["warning"])
            if not self.detection_thread or not self.detection_thread.running:
                self.stop_tracking()
            return
        self.reset_info_style()
        if data["mode"] == "squat":
            text = (f"<b>Mode:</b> Squat<br>"
                   f"<b>Squat Count:</b> {data['squat_count']}<br>"
                   f"<b>Duration:</b> {data['squat_duration']} sec")
        else:
            text = (f"<b>Mode:</b> Plank<br>"
                   f"<b>Plank Active Time:</b> {data['plank_active_time']} sec<br>"
                   f"<b>Total Time:</b> {data['plank_total_time']} sec")
        self.info_label.setText(text)

    def update_camera(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))

    # VOICE LOGIC
    def start_voice_listening(self):
        if self.voice_thread:
            self.stop_voice_listening()
        self.voice_thread = VoiceCommandThread()
        self.voice_thread.commandDetected.connect(self.handle_voice_command)
        self.voice_thread.errorOccurred.connect(self.handle_voice_error)
        self.voice_thread.start()

    def stop_voice_listening(self):
        if self.voice_thread:
            self.voice_thread.stop()
            self.voice_thread = None

    def handle_voice_command(self, command):
        if command == "start" and not self.counting_started:
            self.start_tracking()
        elif command in ["stop", "end"] and self.counting_started:
            self.stop_tracking()

    def handle_voice_error(self, message):
        self.show_error(message)
        self.stop_voice_listening()

    def handle_detection_error(self, message):
        self.show_error(message)
        self.stop_tracking()

    def show_error(self, message):
        self.info_label.setText(f"⚠️ ERROR: {message}")
        self.info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 15px;
                border: 1px solid #ffcccc;
                border-radius: 5px;
                background-color: #ffeeee;
                color: #cc0000;
            }
        """)

    def show_warning(self, message):
        self.info_label.setText(f"⚠️ WARNING: {message}")
        self.info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 15px;
                border: 1px solid #fff3cd;
                border-radius: 5px;
                background-color: #fff3cd;
                color: #856404;
            }
        """)

    def reset_info_style(self):
        self.info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                color: black;
            }
        """)
