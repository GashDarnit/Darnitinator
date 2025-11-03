from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
import time
import sys

class RenderWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def run(self):
        for i in range(101):
            time.sleep(0.05)  # simulate processing
            self.progress.emit(i)
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Video Editor")

        self.status = QLabel("Idle")
        self.button = QPushButton("Start Render")
        self.button.clicked.connect(self.start_render)

        layout = QVBoxLayout()
        layout.addWidget(self.status)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_render(self):
        self.status.setText("Rendering...")
        self.worker = RenderWorker()
        self.worker.progress.connect(lambda p: self.status.setText(f"Progress: {p}%"))
        self.worker.finished.connect(lambda: self.status.setText("Done!"))
        self.worker.start()


app = QApplication([])
window = MainWindow()
window.show()
sys.exit(app.exec())

   
