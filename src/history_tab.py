from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QRadioButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QPushButton, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from db import insert_history, fetch_all_history

class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = fetch_all_history()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Exercise History")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333;
                padding-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        filter_layout = QHBoxLayout()

        self.mode_group = QGroupBox("Filter by Mode")
        self.mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)
        mode_layout = QHBoxLayout()
        self.all_radio = QRadioButton("All")
        self.squat_radio = QRadioButton("Squat")
        self.plank_radio = QRadioButton("Plank")
        self.all_radio.setChecked(True)
        mode_layout.addWidget(self.all_radio)
        mode_layout.addWidget(self.squat_radio)
        mode_layout.addWidget(self.plank_radio)
        mode_layout.addStretch()
        self.mode_group.setLayout(mode_layout)
        filter_layout.addWidget(self.mode_group)

        self.date_group = QGroupBox("Filter by Date")
        self.date_group.setStyleSheet(self.mode_group.styleSheet())
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.filter_button = QPushButton("Apply Filters")
        self.filter_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(self.to_date)
        date_layout.addWidget(self.filter_button)
        date_layout.addStretch()
        self.date_group.setLayout(date_layout)
        filter_layout.addWidget(self.date_group)

        # Optional: Tambah tombol refresh jika ingin
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #125599;
            }
        """)
        self.refresh_button.clicked.connect(self.reload_history)
        filter_layout.addWidget(self.refresh_button)

        layout.addLayout(filter_layout)

        self.table = self.create_table()
        layout.addWidget(self.table)

        self.empty_label = QLabel("No history records available")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #777;
                padding: 20px;
            }
        """)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.stats_label)

        layout.addStretch()
        self.setLayout(layout)
        self.update_table()

    def create_table(self):
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #e0f7fa;
                gridline-color: #eee;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        return table

    def setup_connections(self):
        self.all_radio.toggled.connect(self.update_table)
        self.squat_radio.toggled.connect(self.update_table)
        self.plank_radio.toggled.connect(self.update_table)
        self.filter_button.clicked.connect(self.update_table)

    def add_record(self, record):
        insert_history(record)
        self.history = fetch_all_history()  # reload dari database setelah insert
        self.update_table()
        self.update_stats()

    def reload_history(self):
        self.history = fetch_all_history()
        self.update_table()
        self.update_stats()

    def update_table(self):
        if self.all_radio.isChecked():
            mode_filter = None
        elif self.squat_radio.isChecked():
            mode_filter = "squat"
        else:
            mode_filter = "plank"

        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().addDays(1).toString("yyyy-MM-dd")

        filtered = []
        for record in self.history:
            record_date = str(record.get("timestamp", "")).split()[0]
            if mode_filter and record.get("mode") != mode_filter:
                continue
            if not (from_date <= record_date < to_date):
                continue
            filtered.append(record)

        if not filtered:
            self.table.hide()
            self.empty_label.show()
            self.update_stats()
            return

        self.empty_label.hide()
        self.table.show()
        headers = ["Name", "Mode", "Count/Time", "Duration", "Date/Time"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(filtered))

        for i, record in enumerate(filtered):
            mode = record.get("mode", "")
            name = record.get("name", "Unknown")
            timestamp = str(record.get("timestamp", ""))
            if mode == "squat":
                count = str(record.get("squat_count", 0))
                duration = f"{record.get('squat_duration', 0)} sec"
                metric = count
            else:
                active_time = str(record.get("plank_active_time", 0))
                total_time = f"{record.get('plank_total_time', 0)} sec"
                metric = f"{active_time} sec"
                duration = total_time

            items = [
                QTableWidgetItem(name),
                QTableWidgetItem(mode.capitalize()),
                QTableWidgetItem(metric),
                QTableWidgetItem(duration),
                QTableWidgetItem(timestamp)
            ]
            for col, item in enumerate(items):
                self.table.setItem(i, col, item)
                if col in [2, 3]:
                    item.setTextAlignment(Qt.AlignCenter)

        self.table.sortByColumn(4, Qt.DescendingOrder)
        self.table.resizeColumnsToContents()
        self.update_stats()

    def update_stats(self):
        if not self.history:
            self.stats_label.setText("No records available")
            return
        total_squats = sum(r.get("squat_count", 0) for r in self.history if r.get("mode") == "squat")
        total_plank_time = sum(r.get("plank_active_time", 0) for r in self.history if r.get("mode") == "plank")
        stats_text = []
        if total_squats > 0:
            stats_text.append(f"Total Squats: {total_squats}")
        if total_plank_time > 0:
            stats_text.append(f"Total Plank Time: {total_plank_time} sec")
        self.stats_label.setText(" | ".join(stats_text) if stats_text else "No exercise data")
