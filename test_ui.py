"""Quick test to verify UI can start"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from ui_app.ui.window import MainWindow
    print("[OK] UI module imports successfully")
    print("[OK] You can now run: python ui_app/main.py")
except Exception as e:
    print(f"[ERROR] Error importing UI: {e}")
    import traceback
    traceback.print_exc()

