"""
Main UI window for the image generation application.
Provides a comprehensive interface for all generation parameters.
"""
import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, List
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QRadioButton, QButtonGroup, QTextEdit, QScrollArea,
    QGroupBox, QFileDialog, QMessageBox, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
import logging

from ui_app.core.generator import ImageGenerator, GenerationWorker


class LogTextEdit(QTextEdit):
    """Custom text edit with color-coded logging."""
    
    LOG_FILE = "ui_app/logs/app.log"
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9) if sys.platform == "win32" else QFont("Monaco", 10))
        
        # Setup file logging
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        self.log_file = open(self.LOG_FILE, 'a', encoding='utf-8')
        
    def append_log(self, message: str, level: str = "info"):
        """Append a log message with appropriate color."""
        color_map = {
            "info": "#000000",
            "error": "#FF0000",
            "warning": "#FF8800",
            "step": "#0066CC"
        }
        color = color_map.get(level, "#000000")
        
        formatted_msg = f'<span style="color: {color};">{self._escape_html(message)}</span>'
        self.append(formatted_msg)
        
        # Write to log file
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
            self.log_file.write(log_entry)
            self.log_file.flush()
        except Exception:
            pass  # Don't fail if logging fails
        
        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def cleanup(self):
        """Close the log file."""
        if hasattr(self, 'log_file'):
            try:
                self.log_file.close()
            except Exception:
                pass
        
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\n", "<br>"))


class ImagePreviewWidget(QWidget):
    """Widget for displaying a single image preview with view button."""
    
    def __init__(self, image_path: str, prompt: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.prompt = prompt
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(250, 250)
        self.image_label.setMaximumSize(350, 350)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0; border-radius: 4px;")
        
        # Load and display image
        self._load_image()
        
        # View button
        view_btn = QPushButton("View Full Image")
        view_btn.setStyleSheet("padding: 5px;")
        view_btn.clicked.connect(self._open_image)
        
        # Prompt label (truncated)
        prompt_label = QLabel(prompt[:80] + "..." if len(prompt) > 80 else prompt)
        prompt_label.setWordWrap(True)
        prompt_label.setStyleSheet("font-size: 9pt; color: #666; padding: 5px;")
        prompt_label.setMaximumWidth(350)
        
        layout.addWidget(self.image_label)
        layout.addWidget(prompt_label)
        layout.addWidget(view_btn)
        
        self.setLayout(layout)
        self.setFixedWidth(360)
        
    def _load_image(self):
        """Load and display the image."""
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # Scale to fit
                scaled = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("Failed to load image")
        else:
            self.image_label.setText("Image not found")
            
    def _open_image(self):
        """Open the image in the system default viewer."""
        if sys.platform == "win32":
            os.startfile(self.image_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", self.image_path])
        else:
            subprocess.run(["xdg-open", self.image_path])


class MainWindow(QMainWindow):
    """Main application window."""
    
    SETTINGS_FILE = "ui_app/settings.json"
    
    def __init__(self):
        super().__init__()
        self.generation_worker: Optional[GenerationWorker] = None
        self.generated_images: List[ImagePreviewWidget] = []
        
        self.setWindowTitle("AMO Image Generator")
        self.setMinimumSize(1200, 800)
        
        # Set window style
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QRadioButton {
                padding: 3px;
            }
            QCheckBox {
                padding: 3px;
            }
            QPushButton {
                border-radius: 4px;
            }
        """)
        
        # Setup UI
        self._setup_ui()
        self._load_settings()
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Cleanup log file
        if hasattr(self, 'log_text'):
            self.log_text.cleanup()
        # Stop generation if running
        if self.generation_worker and self.generation_worker.isRunning():
            self.generation_worker.stop()
        event.accept()
        
    def _setup_ui(self):
        """Setup the UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        central_widget.setLayout(main_layout)
        
        # Left panel: Controls (wrapped in scroll area for responsiveness)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setMinimumWidth(380)
        left_scroll.setMaximumWidth(420)
        left_panel = self._create_controls_panel()
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll)
        
        # Right panel: Logs and Preview
        right_panel = self._create_preview_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
    def _create_controls_panel(self) -> QWidget:
        """Create the left panel with all controls."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignTop)
        panel.setLayout(layout)
        
        # Model Type Group
        model_group = QGroupBox("Model Type")
        model_layout = QVBoxLayout()
        model_layout.setSpacing(8)
        model_layout.setContentsMargins(10, 10, 10, 10)
        self.model_group = QButtonGroup()
        self.model_flux = QRadioButton("Flux")
        self.model_sd3 = QRadioButton("Stable Diffusion 3")
        self.model_auraflow = QRadioButton("AuraFlow")
        self.model_flux.setChecked(True)  # Default
        self.model_group.addButton(self.model_flux, 0)
        self.model_group.addButton(self.model_sd3, 1)
        self.model_group.addButton(self.model_auraflow, 2)
        model_layout.addWidget(self.model_flux)
        model_layout.addWidget(self.model_sd3)
        model_layout.addWidget(self.model_auraflow)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Scheduler Group
        scheduler_group = QGroupBox("Scheduler")
        scheduler_layout = QVBoxLayout()
        scheduler_layout.setSpacing(8)
        scheduler_layout.setContentsMargins(10, 10, 10, 10)
        self.scheduler_group = QButtonGroup()
        self.scheduler_euler = QRadioButton("Euler")
        self.scheduler_overshoot = QRadioButton("Overshoot")
        self.scheduler_euler.setChecked(True)  # Default
        self.scheduler_group.addButton(self.scheduler_euler, 0)
        self.scheduler_group.addButton(self.scheduler_overshoot, 1)
        scheduler_layout.addWidget(self.scheduler_euler)
        scheduler_layout.addWidget(self.scheduler_overshoot)
        scheduler_group.setLayout(scheduler_layout)
        layout.addWidget(scheduler_group)
        
        # Overshoot Parameters (only enabled when overshoot is selected)
        overshoot_group = QGroupBox("Overshoot Parameters")
        overshoot_layout = QGridLayout()
        overshoot_layout.setSpacing(8)
        overshoot_layout.setContentsMargins(10, 10, 10, 10)
        self.c_value = QDoubleSpinBox()
        self.c_value.setRange(0.0, 10.0)
        self.c_value.setSingleStep(0.1)
        self.c_value.setValue(2.0)  # Default
        self.c_value.setDecimals(2)
        self.c_value.setMinimumWidth(100)
        self.use_att = QCheckBox("Use Attention Modulation")
        overshoot_layout.addWidget(QLabel("C Value:"), 0, 0)
        overshoot_layout.addWidget(self.c_value, 0, 1)
        overshoot_layout.addWidget(self.use_att, 1, 0, 1, 2)
        overshoot_group.setLayout(overshoot_layout)
        overshoot_group.setEnabled(False)  # Disabled by default (euler selected)
        self.overshoot_group = overshoot_group
        layout.addWidget(overshoot_group)
        
        # Enable/disable overshoot params based on scheduler selection
        self.scheduler_group.buttonClicked.connect(lambda: self.overshoot_group.setEnabled(
            self.scheduler_overshoot.isChecked()
        ))
        
        # Prompt File
        prompt_group = QGroupBox("Prompt File")
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(8)
        prompt_layout.setContentsMargins(10, 10, 10, 10)
        prompt_file_layout = QHBoxLayout()
        prompt_file_layout.setSpacing(5)
        self.prompt_file_edit = QLineEdit()
        self.prompt_file_edit.setText("prompts.txt")  # Default
        prompt_file_btn = QPushButton("Browse...")
        prompt_file_btn.setMinimumWidth(80)
        prompt_file_btn.clicked.connect(self._browse_prompt_file)
        prompt_file_layout.addWidget(self.prompt_file_edit)
        prompt_file_layout.addWidget(prompt_file_btn)
        prompt_layout.addLayout(prompt_file_layout)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # Output Directory
        output_group = QGroupBox("Output Directory")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(8)
        output_layout.setContentsMargins(10, 10, 10, 10)
        output_file_layout = QHBoxLayout()
        output_file_layout.setSpacing(5)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText("exps/flux")  # Default
        output_dir_btn = QPushButton("Browse...")
        output_dir_btn.setMinimumWidth(80)
        output_dir_btn.clicked.connect(self._browse_output_dir)
        output_file_layout.addWidget(self.output_dir_edit)
        output_file_layout.addWidget(output_dir_btn)
        output_layout.addLayout(output_file_layout)
        open_output_btn = QPushButton("Open Output Folder")
        open_output_btn.clicked.connect(self._open_output_folder)
        output_layout.addWidget(open_output_btn)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Image Settings
        image_group = QGroupBox("Image Settings")
        image_layout = QGridLayout()
        image_layout.setSpacing(8)
        image_layout.setContentsMargins(10, 10, 10, 10)
        self.img_size = QSpinBox()
        self.img_size.setRange(64, 2048)
        self.img_size.setValue(1024)  # Default
        self.img_size.setSingleStep(64)
        self.img_size.setMinimumWidth(100)
        self.num_inference_steps = QSpinBox()
        self.num_inference_steps.setRange(1, 200)
        self.num_inference_steps.setValue(28)  # Default
        self.num_inference_steps.setMinimumWidth(100)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.seed.setValue(10)  # Default
        self.seed.setMinimumWidth(100)
        image_layout.addWidget(QLabel("Image Size:"), 0, 0)
        image_layout.addWidget(self.img_size, 0, 1)
        image_layout.addWidget(QLabel("Inference Steps:"), 1, 0)
        image_layout.addWidget(self.num_inference_steps, 1, 1)
        image_layout.addWidget(QLabel("Seed:"), 2, 0)
        image_layout.addWidget(self.seed, 2, 1)
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.generate_btn = QPushButton("Generate Images")
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; min-height: 35px;")
        self.generate_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.generate_btn.clicked.connect(self._start_generation)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; min-height: 35px;")
        self.stop_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Settings buttons
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(8)
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        save_settings_btn.setMinimumHeight(30)
        save_settings_btn.clicked.connect(self._save_settings)
        load_settings_btn = QPushButton("Load Settings")
        load_settings_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        load_settings_btn.setMinimumHeight(30)
        load_settings_btn.clicked.connect(self._load_settings)
        settings_layout.addWidget(save_settings_btn)
        settings_layout.addWidget(load_settings_btn)
        layout.addLayout(settings_layout)
        
        # Add stretch at bottom to push everything up
        layout.addStretch()
        
        # Set minimum size for panel
        panel.setMinimumWidth(360)
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        return panel
        
    def _create_preview_panel(self) -> QWidget:
        """Create the right panel with logs and preview."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        panel.setLayout(layout)
        
        # Log Panel
        log_group = QGroupBox("Generation Log")
        log_layout = QVBoxLayout()
        self.log_text = LogTextEdit()
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        log_group.setMaximumHeight(250)
        layout.addWidget(log_group)
        
        # Preview Panel
        preview_group = QGroupBox("Generated Images")
        preview_layout = QVBoxLayout()
        
        # Scroll area for image gallery
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.gallery_widget = QWidget()
        self.gallery_layout = QVBoxLayout()
        self.gallery_layout.setAlignment(Qt.AlignTop)
        self.gallery_widget.setLayout(self.gallery_layout)
        
        # Container for image grid (using flow layout approach)
        self.image_container = QWidget()
        self.image_grid = QGridLayout()
        self.image_grid.setSpacing(10)
        self.image_grid.setAlignment(Qt.AlignTop)
        self.image_container.setLayout(self.image_grid)
        
        self.gallery_layout.addWidget(self.image_container)
        self.gallery_layout.addStretch()
        
        scroll_area.setWidget(self.gallery_widget)
        preview_layout.addWidget(scroll_area)
        preview_group.setLayout(preview_layout)
        
        layout.addWidget(preview_group, stretch=1)
        
        return panel
        
    def _browse_prompt_file(self):
        """Browse for prompt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Prompt File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.prompt_file_edit.setText(file_path)
            
    def _browse_output_dir(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            
    def _open_output_folder(self):
        """Open the output folder in system file explorer."""
        output_dir = self.output_dir_edit.text()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(self, "Directory Not Found", 
                              f"Output directory does not exist:\n{output_dir}")
            return
            
        if sys.platform == "win32":
            os.startfile(output_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", output_dir])
        else:
            subprocess.run(["xdg-open", output_dir])
            
    def _get_model_type(self) -> str:
        """Get selected model type."""
        if self.model_flux.isChecked():
            return "flux"
        elif self.model_sd3.isChecked():
            return "sd3"
        elif self.model_auraflow.isChecked():
            return "auraflow"
        return "flux"
        
    def _get_scheduler(self) -> str:
        """Get selected scheduler."""
        return "overshoot" if self.scheduler_overshoot.isChecked() else "euler"
        
    def _validate_inputs(self) -> bool:
        """Validate user inputs."""
        prompt_file = self.prompt_file_edit.text()
        if not prompt_file or not os.path.exists(prompt_file):
            QMessageBox.critical(self, "Validation Error", 
                               f"Prompt file not found:\n{prompt_file}")
            return False
            
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            QMessageBox.critical(self, "Validation Error", 
                               "Output directory cannot be empty")
            return False
            
        return True
        
    def _start_generation(self):
        """Start the image generation process with conda environment activation."""
        if not self._validate_inputs():
            return
            
        if self.generation_worker and self.generation_worker.isRunning():
            QMessageBox.warning(self, "Already Running", 
                              "Generation is already in progress. Please stop it first.")
            return
            
        # Clear previous results
        self._clear_preview()
        self.log_text.clear()
        self.log_text.append_log("Starting image generation...", "step")
        
        # Disable controls
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Find Anaconda installation for conda run
        conda_base = None
        if os.path.exists(os.path.join(os.path.expanduser("~"), "anaconda3", "Scripts", "conda.exe")):
            conda_base = os.path.join(os.path.expanduser("~"), "anaconda3")
        elif os.path.exists(os.path.join(os.getenv("LOCALAPPDATA", ""), "anaconda3", "Scripts", "conda.exe")):
            conda_base = os.path.join(os.getenv("LOCALAPPDATA", ""), "anaconda3")
        elif os.path.exists(os.path.join(os.path.expanduser("~"), "miniconda3", "Scripts", "conda.exe")):
            conda_base = os.path.join(os.path.expanduser("~"), "miniconda3")
        elif os.path.exists(os.path.join(os.getenv("LOCALAPPDATA", ""), "miniconda3", "Scripts", "conda.exe")):
            conda_base = os.path.join(os.getenv("LOCALAPPDATA", ""), "miniconda3")
        
        if not conda_base:
            self.log_text.append_log("WARNING: Conda not found. Running without conda environment.", "warning")
            conda_exe = None
        else:
            conda_exe = os.path.join(conda_base, "Scripts", "conda.exe")
            self.log_text.append_log(f"Found Anaconda at: {conda_base}", "info")
            self.log_text.append_log("Activating conda environment 'amo'...", "step")
        
        # Get parameters
        params = {
            "model_type": self._get_model_type(),
            "scheduler": self._get_scheduler(),
            "c": self.c_value.value(),
            "use_att": self.use_att.isChecked(),
            "prompt_file": self.prompt_file_edit.text(),
            "exp_dir": self.output_dir_edit.text(),
            "num_inference_steps": self.num_inference_steps.value(),
            "seed": self.seed.value(),
            "img_size": self.img_size.value(),
            "conda_exe": conda_exe  # Pass conda executable to generator
        }
        
        # Create generator and worker
        generator = ImageGenerator()
        generator.log_message.connect(self._on_log_message)
        generator.progress_update.connect(self._on_progress_update)
        generator.image_generated.connect(self._on_image_generated)
        generator.generation_complete.connect(self._on_generation_complete)
        
        self.generation_worker = GenerationWorker(generator, **params)
        self.generation_worker.finished.connect(self._on_worker_finished)
        self.generation_worker.start()
        
    def _stop_generation(self):
        """Stop the generation process."""
        if self.generation_worker and self.generation_worker.isRunning():
            self.generation_worker.stop()
            self.log_text.append_log("Stopping generation...", "warning")
            
    @pyqtSlot(str, str)
    def _on_log_message(self, message: str, level: str):
        """Handle log messages from generator."""
        self.log_text.append_log(message, level)
        
    @pyqtSlot(int, int)
    def _on_progress_update(self, current: int, total: int):
        """Handle progress updates."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setFormat(f"Progress: {current}/{total} ({percent}%)")
        
    @pyqtSlot(str, str)
    def _on_image_generated(self, image_path: str, prompt: str):
        """Handle new image generated."""
        preview_widget = ImagePreviewWidget(image_path, prompt, self)
        self.generated_images.append(preview_widget)
        self._update_preview_grid()
        
    @pyqtSlot(bool, str)
    def _on_generation_complete(self, success: bool, message: str):
        """Handle generation completion."""
        if success:
            self.log_text.append_log(message, "info")
        else:
            self.log_text.append_log(message, "error")
            
    def _on_worker_finished(self):
        """Handle worker thread finishing."""
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.log_text.append_log("Generation process finished.", "step")
        
    def _clear_preview(self):
        """Clear the preview gallery."""
        for widget in self.generated_images:
            widget.deleteLater()
        self.generated_images.clear()
        
        # Clear grid
        while self.image_grid.count():
            child = self.image_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def _update_preview_grid(self):
        """Update the preview grid layout."""
        # Clear only the grid, not the widgets list
        while self.image_grid.count():
            child = self.image_grid.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        # Add all images in a grid (2 columns)
        cols = 2
        for i, widget in enumerate(self.generated_images):
            row = i // cols
            col = i % cols
            self.image_grid.addWidget(widget, row, col)
            
    def _save_settings(self):
        """Save current settings to JSON file."""
        settings = {
            "model_type": self._get_model_type(),
            "scheduler": self._get_scheduler(),
            "c": self.c_value.value(),
            "use_att": self.use_att.isChecked(),
            "prompt_file": self.prompt_file_edit.text(),
            "output_dir": self.output_dir_edit.text(),
            "num_inference_steps": self.num_inference_steps.value(),
            "seed": self.seed.value(),
            "img_size": self.img_size.value()
        }
        
        try:
            os.makedirs(os.path.dirname(self.SETTINGS_FILE), exist_ok=True)
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            self.log_text.append_log(f"Settings saved to {self.SETTINGS_FILE}", "info")
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        except Exception as e:
            error_msg = f"Failed to save settings: {str(e)}"
            self.log_text.append_log(error_msg, "error")
            QMessageBox.critical(self, "Save Error", error_msg)
            
    def _load_settings(self):
        """Load settings from JSON file."""
        if not os.path.exists(self.SETTINGS_FILE):
            return
            
        try:
            with open(self.SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                
            # Apply settings
            model_type = settings.get("model_type", "flux")
            if model_type == "flux":
                self.model_flux.setChecked(True)
            elif model_type == "sd3":
                self.model_sd3.setChecked(True)
            elif model_type == "auraflow":
                self.model_auraflow.setChecked(True)
                
            scheduler = settings.get("scheduler", "euler")
            if scheduler == "overshoot":
                self.scheduler_overshoot.setChecked(True)
            else:
                self.scheduler_euler.setChecked(True)
                
            self.c_value.setValue(settings.get("c", 2.0))
            self.use_att.setChecked(settings.get("use_att", False))
            self.prompt_file_edit.setText(settings.get("prompt_file", "prompts.txt"))
            self.output_dir_edit.setText(settings.get("output_dir", "exps/flux"))
            self.num_inference_steps.setValue(settings.get("num_inference_steps", 28))
            self.seed.setValue(settings.get("seed", 10))
            self.img_size.setValue(settings.get("img_size", 1024))
            
            # Update overshoot group enabled state
            self.overshoot_group.setEnabled(self.scheduler_overshoot.isChecked())
            
            self.log_text.append_log(f"Settings loaded from {self.SETTINGS_FILE}", "info")
        except Exception as e:
            error_msg = f"Failed to load settings: {str(e)}"
            self.log_text.append_log(error_msg, "warning")

