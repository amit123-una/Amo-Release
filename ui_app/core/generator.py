"""
Core generator module that wraps the existing run.py logic without modification.
This module preserves all original functionality while enabling UI integration.
"""
import os
import sys
import traceback
from typing import List, Tuple, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# Import the original run function logic
# We'll import it from the parent directory's run.py
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Lazy imports - only import when actually needed for generation
# This allows the UI to start even if torch/diffusers aren't installed yet


class ImageGenerator(QObject):
    """Wraps the existing image generation logic for use in a threaded environment."""
    
    # Signals for UI updates
    log_message = pyqtSignal(str, str)  # message, level (info, error, warning, step)
    progress_update = pyqtSignal(int, int)  # current, total
    image_generated = pyqtSignal(str, str)  # image_path, prompt
    generation_complete = pyqtSignal(bool, str)  # success, message
    step_update = pyqtSignal(int)  # current step number
    
    def __init__(self):
        super().__init__()
        self.pipe = None
        self._stop_requested = False
        
    def request_stop(self):
        """Request to stop the generation process."""
        self._stop_requested = True
        self.log_message.emit("Stop requested...", "warning")
        
    def generate(self, 
                 model_type: str,
                 scheduler: str,
                 c: float,
                 use_att: bool,
                 prompt_file: str,
                 exp_dir: str,
                 num_inference_steps: int,
                 seed: int,
                 img_size: int,
                 conda_exe: Optional[str] = None):
        """
        Generate images using the exact logic from run.py.
        
        Args match the original argparse arguments exactly.
        conda_exe: Path to conda.exe if conda environment should be used
        """
        self._stop_requested = False
        
        # If conda_exe is provided, use conda run to execute in the amo environment
        if conda_exe and os.path.exists(conda_exe):
            self.log_message.emit("Using conda environment 'amo' for generation", "info")
            return self._generate_with_conda(
                model_type, scheduler, c, use_att, prompt_file, exp_dir,
                num_inference_steps, seed, img_size, conda_exe
            )
        
        # Otherwise, use the existing direct generation method
        try:
            # Import torch and diffusers only when needed (lazy import)
            import torch
            from diffusers import StableDiffusion3Pipeline, FluxPipeline, AuraFlowPipeline
            from diffusers import StochasticRFOvershotDiscreteScheduler
            
            # Step 1: Read prompts
            self.log_message.emit(f"Reading prompts from: {prompt_file}", "info")
            if not os.path.exists(prompt_file):
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_file, 'r') as file:
                prompts = [line.strip() for line in file.readlines() if line.strip()]
            
            if not prompts:
                raise ValueError("No prompts found in the prompt file")
            
            self.log_message.emit(f"Loaded {len(prompts)} prompt(s)", "info")
            
            # Step 2: Load model
            self.log_message.emit(f"Loading model: {model_type}", "step")
            if model_type == "sd3":
                self.pipe = StableDiffusion3Pipeline.from_pretrained(
                    "stabilityai/stable-diffusion-3-medium-diffusers", 
                    torch_dtype=torch.float32
                )
                guidance_scale = 7.0
            elif model_type == "flux":
                self.pipe = FluxPipeline.from_pretrained(
                    "black-forest-labs/FLUX.1-dev", 
                    torch_dtype=torch.bfloat16
                )
                guidance_scale = 3.5
            elif model_type == "auraflow":
                self.pipe = AuraFlowPipeline.from_pretrained(
                    "fal/AuraFlow", 
                    torch_dtype=torch.float16
                )
                guidance_scale = 3.5
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            self.pipe.enable_model_cpu_offload()
            self.log_message.emit(f"Model loaded successfully (guidance_scale={guidance_scale})", "info")
            
            if self._stop_requested:
                self.generation_complete.emit(False, "Generation stopped by user")
                return
            
            # Step 3: Setup scheduler
            self.log_message.emit(f"Setting up scheduler: {scheduler}", "step")
            if scheduler == 'overshoot':
                scheduler_config = self.pipe.scheduler.config
                scheduler_obj = StochasticRFOvershotDiscreteScheduler.from_config(scheduler_config)
                overshot_func = lambda t, dt: t+dt
                exp_prefix = f"{scheduler}_c={str(c).zfill(4)}_use_att={use_att}"
                
                self.pipe.scheduler = scheduler_obj
                self.pipe.scheduler.set_c(c)
                self.pipe.scheduler.set_overshot_func(overshot_func)
                self.log_message.emit(f"Overshoot scheduler configured (c={c}, use_att={use_att})", "info")
            elif scheduler == "euler":
                exp_prefix = f"{scheduler}"
                self.log_message.emit("Euler scheduler configured", "info")
            else:
                raise ValueError(f"Unknown scheduler: {scheduler}")
            
            if self._stop_requested:
                self.generation_complete.emit(False, "Generation stopped by user")
                return
            
            # Step 4: Generate images for each prompt
            total_prompts = len(prompts)
            generated_images = []
            
            for i, prompt in enumerate(prompts):
                if self._stop_requested:
                    self.log_message.emit("Generation stopped by user", "warning")
                    break
                
                self.log_message.emit(f"Processing prompt {i+1}/{total_prompts}", "step")
                self.log_message.emit(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}", "info")
                
                # Create output directory structure (same as original)
                file_save_dir = os.path.join(
                    exp_dir, 
                    "generated_image", 
                    f"num_steps={str(num_inference_steps).zfill(4)}", 
                    exp_prefix
                )
                os.makedirs(file_save_dir, exist_ok=True)
                img_save_path = os.path.join(file_save_dir, f"sample_{str(i).zfill(4)}.png")
                
                # Setup generator with seed
                generator = torch.Generator(device='cuda')
                generator.manual_seed(seed)
                
                # Generate image (original logic)
                self.log_message.emit(f"Starting inference ({num_inference_steps} steps)...", "step")
                try:
                    output = self.pipe(
                        prompt=prompt,
                        num_inference_steps=num_inference_steps,
                        height=img_size,
                        width=img_size,
                        guidance_scale=guidance_scale,
                        generator=generator,
                        use_att=use_att,
                    )
                    
                    image = output.images[0]
                    image.save(img_save_path)
                    
                    self.log_message.emit(f"Image saved: {img_save_path}", "info")
                    self.image_generated.emit(img_save_path, prompt)
                    generated_images.append(img_save_path)
                    
                except Exception as e:
                    error_msg = f"Error generating image {i+1}: {str(e)}"
                    error_trace = traceback.format_exc()
                    self.log_message.emit(error_msg, "error")
                    self.log_message.emit(error_trace, "error")
                    # Continue with next prompt instead of failing completely
                    continue
                
                # Emit progress
                self.progress_update.emit(i + 1, total_prompts)
            
            if self._stop_requested:
                self.generation_complete.emit(False, "Generation stopped by user")
            else:
                success_msg = f"Successfully generated {len(generated_images)} image(s)"
                self.log_message.emit(success_msg, "info")
                self.generation_complete.emit(True, success_msg)
                
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            error_trace = traceback.format_exc()
            
            # Format error with line numbers
            formatted_trace = []
            for line in error_trace.split('\n'):
                if 'File "' in line and ', line' in line:
                    formatted_trace.append(f"  {line}")
                elif line.strip():
                    formatted_trace.append(f"  {line}")
            
            self.log_message.emit(error_msg, "error")
            self.log_message.emit('\n'.join(formatted_trace), "error")
            self.generation_complete.emit(False, error_msg)
    
    def _generate_with_conda(self,
                            model_type: str,
                            scheduler: str,
                            c: float,
                            use_att: bool,
                            prompt_file: str,
                            exp_dir: str,
                            num_inference_steps: int,
                            seed: int,
                            img_size: int,
                            conda_exe: str):
        """Generate images using conda run to ensure correct environment."""
        import subprocess
        import json
        
        self._stop_requested = False
        
        try:
            # Get project directory
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            run_py_path = os.path.join(project_dir, "run.py")
            
            if not os.path.exists(run_py_path):
                raise FileNotFoundError(f"run.py not found at: {run_py_path}")
            
            # Convert relative paths to absolute
            if not os.path.isabs(prompt_file):
                prompt_file = os.path.join(project_dir, prompt_file)
            prompt_file = os.path.normpath(prompt_file)
            
            if not os.path.isabs(exp_dir):
                exp_dir = os.path.join(project_dir, exp_dir)
            exp_dir = os.path.normpath(exp_dir)
            
            # Build command arguments
            cmd_args = [
                conda_exe, "run", "-n", "amo",
                "python", run_py_path,
                "--model_type", model_type,
                "--scheduler", scheduler,
                "--prompt_file", prompt_file,
                "--img_size", str(img_size),
                "--num_inference_steps", str(num_inference_steps),
                "--seed", str(seed),
                "--exp_dir", exp_dir
            ]
            
            # Add overshoot parameters if needed
            if scheduler == "overshoot":
                cmd_args.extend(["--c", str(c)])
                if use_att:
                    cmd_args.append("--use_att")
            
            self.log_message.emit(f"Command: {' '.join(cmd_args)}", "info")
            self.log_message.emit("Executing in conda environment 'amo'...", "step")
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_dir)
            
            try:
                # Run the command and capture output
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Read output line by line and emit as logs
                for line in process.stdout:
                    if self._stop_requested:
                        process.terminate()
                        break
                    line = line.strip()
                    if line:
                        # Determine log level based on content
                        if "ERROR" in line.upper() or "FAILED" in line.upper():
                            level = "error"
                        elif "WARNING" in line.upper():
                            level = "warning"
                        elif "Step" in line or "Loading" in line or "Processing" in line:
                            level = "step"
                        else:
                            level = "info"
                        self.log_message.emit(line, level)
                
                # Wait for process to complete
                return_code = process.wait()
                
                if return_code == 0:
                    self.log_message.emit("Generation completed successfully!", "info")
                    self.generation_complete.emit(True, "Generation completed successfully!")
                else:
                    error_msg = f"Generation failed with return code {return_code}"
                    self.log_message.emit(error_msg, "error")
                    self.generation_complete.emit(False, error_msg)
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            error_trace = traceback.format_exc()
            self.log_message.emit(error_msg, "error")
            self.log_message.emit(error_trace, "error")
            self.generation_complete.emit(False, error_msg)


class GenerationWorker(QThread):
    """Worker thread for running image generation without blocking the UI."""
    
    def __init__(self, generator: ImageGenerator, **kwargs):
        super().__init__()
        self.generator = generator
        self.kwargs = kwargs
        
    def run(self):
        """Run the generation in this thread."""
        self.generator.generate(**self.kwargs)
        
    def stop(self):
        """Request stop and wait for thread to finish."""
        self.generator.request_stop()
        self.wait()

