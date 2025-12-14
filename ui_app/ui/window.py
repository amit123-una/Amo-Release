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
    QGroupBox, QFileDialog, QMessageBox, QProgressBar, QSizePolicy,
    QDialog, QDialogButtonBox, QPlainTextEdit
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


class MainWindow(QMainWindow):
    """Main application window."""
    
    SETTINGS_FILE = "ui_app/settings.json"
    
    def __init__(self):
        super().__init__()
        self.generation_worker: Optional[GenerationWorker] = None
        self.generated_files: List[str] = []  # Store file paths instead of widgets
        
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
        
        # Prompt Input Options
        prompt_group = QGroupBox("Prompt Input")
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(8)
        prompt_layout.setContentsMargins(10, 10, 10, 10)
        
        # Radio buttons for input method
        self.prompt_input_group = QButtonGroup()
        self.prompt_direct_radio = QRadioButton("Direct Input")
        self.prompt_file_radio = QRadioButton("From File")
        self.prompt_file_radio.setChecked(True)  # Default to file
        self.prompt_input_group.addButton(self.prompt_direct_radio, 0)
        self.prompt_input_group.addButton(self.prompt_file_radio, 1)
        prompt_layout.addWidget(self.prompt_direct_radio)
        prompt_layout.addWidget(self.prompt_file_radio)
        
        # Direct input text area (initially hidden)
        self.prompt_direct_input = QPlainTextEdit()
        self.prompt_direct_input.setPlaceholderText("Enter prompts here, one per line...")
        self.prompt_direct_input.setMaximumHeight(100)
        self.prompt_direct_input.setVisible(False)
        prompt_layout.addWidget(self.prompt_direct_input)
        
        # File input (default visible)
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
        
        # Connect radio buttons to show/hide inputs
        self.prompt_direct_radio.toggled.connect(self._on_prompt_input_changed)
        self.prompt_file_radio.toggled.connect(self._on_prompt_input_changed)
        
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
        
        # Log Panel with controls
        log_group = QGroupBox("Generation Log")
        log_layout = QVBoxLayout()
        
        # Log controls (copy and clear buttons)
        log_controls = QHBoxLayout()
        log_controls.addStretch()
        copy_log_btn = QPushButton("📋 Copy Log")
        copy_log_btn.setMaximumWidth(100)
        copy_log_btn.clicked.connect(self._copy_log)
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.setMaximumWidth(100)
        clear_log_btn.clicked.connect(self._clear_log)
        log_controls.addWidget(copy_log_btn)
        log_controls.addWidget(clear_log_btn)
        log_layout.addLayout(log_controls)
        
        # Log text area (responsive)
        self.log_text = LogTextEdit()
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        log_group.setMinimumHeight(200)
        log_group.setMaximumHeight(400)
        layout.addWidget(log_group, stretch=1)
        
        # Generated Files Panel
        files_group = QGroupBox("Generated Files")
        files_layout = QVBoxLayout()
        
        # Scroll area for file list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.files_widget = QWidget()
        self.files_layout = QVBoxLayout()
        self.files_layout.setAlignment(Qt.AlignTop)
        self.files_widget.setLayout(self.files_layout)
        
        scroll_area.setWidget(self.files_widget)
        files_layout.addWidget(scroll_area)
        files_group.setLayout(files_layout)
        
        layout.addWidget(files_group, stretch=1)
        
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
        current_dir = self.output_dir_edit.text()
        # Convert relative path to absolute if needed
        if current_dir and not os.path.isabs(current_dir):
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            current_dir = os.path.join(project_dir, current_dir)
            if not os.path.exists(current_dir):
                current_dir = project_dir
        
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", current_dir)
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            
    def _open_output_folder(self):
        """Open the output folder in system file explorer."""
        output_dir = self.output_dir_edit.text()
        
        # Convert relative path to absolute
        if output_dir and not os.path.isabs(output_dir):
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(project_dir, output_dir)
        
        # Create directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Directory Error", 
                                  f"Could not create directory:\n{output_dir}\n\nError: {str(e)}")
                return
        
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
    
    def _on_prompt_input_changed(self):
        """Handle prompt input method change."""
        if self.prompt_direct_radio.isChecked():
            self.prompt_direct_input.setVisible(True)
            self.prompt_file_edit.setEnabled(False)
        else:
            self.prompt_direct_input.setVisible(False)
            self.prompt_file_edit.setEnabled(True)
            
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
        # Check prompt input method
        if self.prompt_direct_radio.isChecked():
            prompts_text = self.prompt_direct_input.toPlainText().strip()
            if not prompts_text:
                QMessageBox.critical(self, "Validation Error", 
                                   "Please enter at least one prompt in the direct input field.")
                return False
        else:
            prompt_file = self.prompt_file_edit.text()
            if not prompt_file:
                QMessageBox.critical(self, "Validation Error", 
                                   "Please specify a prompt file.")
                return False
            # Convert to absolute path if relative
            if not os.path.isabs(prompt_file):
                project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                prompt_file = os.path.join(project_dir, prompt_file)
            if not os.path.exists(prompt_file):
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
        self._clear_files_list()
        self.log_text.clear()
        self.log_text.append_log("Starting image generation...", "step")
        
        # Disable generate button and enable stop button
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFormat("Initializing...")
        
        # Handle prompt input based on selected method
        import tempfile
        import datetime
        
        if self.prompt_direct_radio.isChecked():
            # Create temporary file from direct input
            prompts_text = self.prompt_direct_input.toPlainText().strip()
            prompts_list = [line.strip() for line in prompts_text.split('\n') if line.strip()]
            
            if not prompts_list:
                QMessageBox.critical(self, "Validation Error", "No prompts entered.")
                self.generate_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                return
            
            # Create unique temporary file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_prompt_file = os.path.join(tempfile.gettempdir(), f"amo_prompts_{timestamp}_{os.getpid()}.txt")
            with open(temp_prompt_file, 'w', encoding='utf-8') as f:
                for prompt in prompts_list:
                    f.write(prompt + '\n')
            prompt_file = temp_prompt_file
            self.log_text.append_log(f"Created temporary prompt file with {len(prompts_list)} prompt(s)", "info")
        else:
            prompt_file = self.prompt_file_edit.text()
            # Convert to absolute path if relative
            if not os.path.isabs(prompt_file):
                project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                prompt_file = os.path.join(project_dir, prompt_file)
        
        # Get output directory and create datetime-based structure
        exp_dir = self.output_dir_edit.text()
        if not os.path.isabs(exp_dir):
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            exp_dir = os.path.join(project_dir, exp_dir)
        
        # Create module and datetime-based folder structure
        # Structure: base_dir/model_type/YYYYMMDD_HHMMSS/
        model_type = self._get_model_type()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_dir = os.path.join(exp_dir, model_type, timestamp)
        os.makedirs(exp_dir, exist_ok=True)
        self.log_text.append_log(f"Output directory: {exp_dir}", "info")
        self.log_text.append_log(f"Organized by module ({model_type}) and datetime ({timestamp})", "info")
        
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
            "model_type": model_type,
            "scheduler": self._get_scheduler(),
            "c": self.c_value.value(),
            "use_att": self.use_att.isChecked(),
            "prompt_file": prompt_file,
            "exp_dir": exp_dir,
            "num_inference_steps": self.num_inference_steps.value(),
            "seed": self.seed.value(),
            "img_size": self.img_size.value(),
            "conda_exe": conda_exe  # Pass conda executable to generator
        }
        
        # Create generator and worker
        generator = ImageGenerator()
        generator.log_message.connect(self._on_log_message)
        generator.progress_update.connect(self._on_progress_update)
        generator.step_update.connect(self._on_step_update)
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
    
    @pyqtSlot(int)
    def _on_step_update(self, step: int):
        """Handle step updates for progress bar."""
        # Update progress based on steps (0-100)
        self.progress_bar.setValue(step)
        self.progress_bar.setFormat(f"Step: {step}%")
        
    @pyqtSlot(str, str)
    def _on_image_generated(self, image_path: str, prompt: str):
        """Handle new image generated - add to files list."""
        if image_path and os.path.exists(image_path):
            self.generated_files.append(image_path)
            self._add_file_to_list(image_path)
        
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
        
    def _clear_files_list(self):
        """Clear the files list."""
        while self.files_layout.count():
            child = self.files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.generated_files.clear()
    
    def _add_file_to_list(self, file_path: str):
        """Add a generated file to the list with preview button."""
        file_widget = QWidget()
        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(5, 5, 5, 5)
        
        # File path label
        file_label = QLabel(file_path)
        file_label.setWordWrap(True)
        file_label.setStyleSheet("padding: 5px;")
        file_layout.addWidget(file_label, stretch=1)
        
        # Preview button
        preview_btn = QPushButton("Preview")
        preview_btn.setMaximumWidth(80)
        preview_btn.clicked.connect(lambda checked, path=file_path: self._preview_image(path))
        file_layout.addWidget(preview_btn)
        
        file_widget.setLayout(file_layout)
        file_widget.setStyleSheet("border: 1px solid #ccc; border-radius: 3px; margin: 2px;")
        self.files_layout.addWidget(file_widget)
    
    def _preview_image(self, image_path: str):
        """Show image preview in a popup dialog."""
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "File Not Found", f"Image file not found:\n{image_path}")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Image Preview")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Image label
        image_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale to fit dialog while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(780, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("Failed to load image")
        
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        
        # File path label
        path_label = QLabel(f"File: {image_path}")
        path_label.setWordWrap(True)
        path_label.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(path_label)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.close)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _copy_log(self):
        """Copy log content to clipboard."""
        log_content = self.log_text.toPlainText()
        if log_content:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(log_content)
            self.log_text.append_log("Log copied to clipboard!", "info")
        else:
            QMessageBox.information(self, "Empty Log", "No log content to copy.")
    
    def _clear_log(self):
        """Clear the log content."""
        self.log_text.clear()
        self.log_text.append_log("Log cleared.", "info")
            
    def _save_settings(self):
        """Save current settings to JSON file."""
        settings = {
            "model_type": self._get_model_type(),
            "scheduler": self._get_scheduler(),
            "c": self.c_value.value(),
            "use_att": self.use_att.isChecked(),
            "prompt_input_method": "direct" if self.prompt_direct_radio.isChecked() else "file",
            "prompt_direct_input": self.prompt_direct_input.toPlainText(),
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
            # Load prompt settings
            prompt_input_method = settings.get("prompt_input_method", "file")
            if prompt_input_method == "direct":
                self.prompt_direct_radio.setChecked(True)
                self.prompt_direct_input.setPlainText(settings.get("prompt_direct_input", ""))
            else:
                self.prompt_file_radio.setChecked(True)
                self.prompt_file_edit.setText(settings.get("prompt_file", "prompts.txt"))
            self.output_dir_edit.setText(settings.get("output_dir", "exps/flux"))
            self.num_inference_steps.setValue(settings.get("num_inference_steps", 28))
            self.seed.setValue(settings.get("seed", 10))
            self.img_size.setValue(settings.get("img_size", 1024))
            
            # Update overshoot group enabled state
            self.overshoot_group.setEnabled(self.scheduler_overshoot.isChecked())
            
            # Update prompt input visibility based on loaded setting
            self._on_prompt_input_changed()
            
            self.log_text.append_log(f"Settings loaded from {self.SETTINGS_FILE}", "info")
        except Exception as e:
            error_msg = f"Failed to load settings: {str(e)}"
            self.log_text.append_log(error_msg, "warning")

