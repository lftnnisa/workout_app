import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QStatusBar
from counter_tab import CounterTab
from history_tab import HistoryTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Exercise Tracker with History")
        self.resize(1200, 800)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.tab_widget = QTabWidget()
        self.counter_tab = CounterTab()
        self.history_tab = HistoryTab()
        self.tab_widget.addTab(self.counter_tab, "Exercise Counter")
        self.tab_widget.addTab(self.history_tab, "History Records")
        self.setCentralWidget(self.tab_widget)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #d3d3d3;
                border-radius: 5px;
                padding: 5px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 20px;
                background: #e0e0e0;
                border: 1px solid #d3d3d3;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            QTabBar::tab:hover {
                background: #f0f0f0;
            }
        """)

    def setup_connections(self):
        self.counter_tab.sessionFinished.connect(self.history_tab.add_record)
        self.counter_tab.errorOccurred.connect(self.show_status_message)

    def show_status_message(self, message):
        self.status_bar.showMessage(message, 5000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application error: {e}")
