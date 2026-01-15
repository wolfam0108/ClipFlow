import os
import subprocess
import sys
import json
import time
from PyQt6.QtCore import QThread, pyqtSignal

# Hide console window on Windows
if sys.platform == 'win32':
    STARTUPINFO = subprocess.STARTUPINFO()
    STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    STARTUPINFO.wShowWindow = subprocess.SW_HIDE
    CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    STARTUPINFO = None
    CREATE_NO_WINDOW = 0

class ExportThread(QThread):
    progress_update = pyqtSignal(int, int, str) # current, total, filename
    finished_all = pyqtSignal()
    log_message = pyqtSignal(str)
    
    def __init__(self, items, output_dir):
        super().__init__()
        self.items = items
        self.output_dir = output_dir
        self.is_running = True

    def run(self):
        total = len(self.items)
        for i, item in enumerate(self.items):
            if not self.is_running:
                break
                
            self.progress_update.emit(i, total, item.filename)
            try:
                self.process_item(item)
            except Exception as e:
                self.log_message.emit(f"Error processing {item.filename}: {str(e)}")
        
        self.finished_all.emit()

    def process_item(self, item):
        source_path = item.path
        filename = item.filename
        
        # Check if output dir is same as source dir to apply _crop suffix
        source_dir = os.path.dirname(source_path)
        name, ext = os.path.splitext(filename)
        
        if os.path.normpath(self.output_dir) == os.path.normpath(source_dir):
            output_filename = f"{name}_crop{ext}"
        else:
            output_filename = filename
            
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 1. Get Info
        duration, keyframes = self.get_video_info_final(source_path)
        if duration is None or not keyframes:
            self.log_message.emit(f"Failed to analyze {filename}")
            return

        # 2. Keyframe snapping
        start_trim = item.start_time
        end_trim = duration - item.end_time # item.end_time is absolute time in current logic? 
        # Wait, in UI item.end_time is the marker position (absolute time from start).
        # In script, args.end was "seconds to cut from END".
        # Let's re-read the script logic vs UI logic.
        # Script: desired_end_time = duration - end_trim
        # UI: item.end_time IS the desired_end_time (absolute timestamp).
        
        # So we need to calculate `end_trim` (amount to cut from end) for metadata ONLY?
        # Or does the script logic rely on calculating from end?
        
        # Script logic:
        # actual_start_time = find_keyframe_before(keyframes, start_trim)
        # desired_end_time = duration - end_trim (where end_trim is user input "cut X sec from end")
        # actual_end_time = find_keyframe_before(keyframes, desired_end_time)
        
        # My UI logic:
        # item.start_time is absolute (e.g. 5.0s)
        # item.end_time is absolute (e.g. duration - 5.0s)
        
        # So:
        desired_start_time = item.start_time
        desired_end_time = item.end_time
        
        # Calculate tolerance (1 frame duration)
        try:
            fps = getattr(item, 'fps', 25.0)
            if not fps or fps <= 0: fps = 25.0
            tolerance = 1.0 / fps
        except:
            tolerance = 0.05

        actual_start_time = self.find_keyframe_before(keyframes, desired_start_time, tolerance)
        actual_end_time = self.find_keyframe_before(keyframes, desired_end_time, tolerance)
        
        if actual_start_time >= actual_end_time:
            self.log_message.emit(f"Video {filename} too short for trimming.")
            return

        new_duration = actual_end_time - actual_start_time
        
        # Calculate legacy "trim" values for metadata to match script style if needed
        # Script stores: start_requested, start_actual, end_requested, end_actual
        # start_requested = item.start_time
        # end_requested (amount from end) = duration - item.end_time
        
        requested_start_trim = item.start_time
        requested_end_trim = max(0, duration - item.end_time)
        
        # 3. Metadata
        existing_meta = self.get_metadata(source_path)
        history_index = 1
        while f"trim_history_{history_index}_source_duration" in existing_meta:
            history_index += 1
            
        metadata_args = [
            "-metadata", f"comment=Trimmed with Pro Video Trimmer 2025",
            "-metadata", f"trim_history_{history_index}_source_duration={duration:.6f}",
            "-metadata", f"trim_history_{history_index}_start_requested={requested_start_trim:.3f}",
            "-metadata", f"trim_history_{history_index}_start_actual={actual_start_time:.6f}",
            "-metadata", f"trim_history_{history_index}_end_requested={requested_end_trim:.3f}",
            "-metadata", f"trim_history_{history_index}_end_actual={(duration - actual_end_time):.6f}",
        ]

        # 4. Command
        command = ["ffmpeg", "-ss", str(actual_start_time), "-i", source_path, "-t", str(new_duration), "-fflags", "+genpts", "-c", "copy"]
        
        if output_path.lower().endswith('.mp4'):
            command.extend(["-movflags", "use_metadata_tags"])
            
        command.extend(metadata_args)
        command.extend(["-y", output_path])
        
        # Execute with hidden console
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW)
        self.log_message.emit(f"Saved: {output_filename}")

    def get_metadata(self, filepath):
        try:
            command = [
                "ffprobe", "-v", "error", "-print_format", "json",
                "-show_format", filepath
            ]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  check=True, text=True, encoding='utf-8',
                                  startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW)
            data = json.loads(result.stdout)
            return data.get('format', {}).get('tags', {})
        except:
            return {}

    def get_video_info_final(self, filepath):
        try:
            probe_command = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", filepath]
            result = subprocess.run(probe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  check=True, text=True, encoding='utf-8',
                                  startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW)
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0.0))
            if duration == 0.0: return None, None
        except:
            return None, None

        try:
            # Note: getting keyframes can be slow for very large files, but it's what the script does.
            keyframes_command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", filepath]
            result = subprocess.run(keyframes_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  check=True, text=True, encoding='utf-8',
                                  startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW)
            keyframes = [float(parts[0]) for line in result.stdout.strip().split('\n') if (parts := line.split(',')) and len(parts) >= 2 and parts[1].strip().startswith('K')]
            return duration, keyframes
        except:
            return None, None

    def find_keyframe_before(self, keyframes, target_time, tolerance=0.0):
        if not keyframes: return 0.0
        best_keyframe = 0.0
        # Use tolerance to snap to keyframe if we are very close (e.g. floating point error)
        # or if user selected a "nearest" point which is technically just before the keyframe.
        limit = target_time + tolerance 
        
        for kf_time in keyframes:
            if kf_time <= limit:
                best_keyframe = kf_time
            else:
                break
        return best_keyframe
