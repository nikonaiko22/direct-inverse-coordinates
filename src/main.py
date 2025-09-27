import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geodesic Toolkit (Sodano)")
        self.setMinimumSize(480, 320)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(
            "Welcome to Geodesic Toolkit!\n\n"
            "Direct and Inverse geodetic calculations (Sodano)\n"
            "Ready for expansion (Puissant, etc.)"
        ))
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())