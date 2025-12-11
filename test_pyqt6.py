"""Test if PyQt6 works"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Test Window")
window.setGeometry(100, 100, 400, 300)

label = QLabel("If you see this, PyQt6 is working!", window)
label.move(50, 50)

window.show()
print("Window should be visible now. Close it to exit.")
sys.exit(app.exec())

