import subprocess
import sys

# Hide console window on Windows
if sys.platform == 'win32':
    STARTUPINFO = subprocess.STARTUPINFO()
    STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    STARTUPINFO.wShowWindow = subprocess.SW_HIDE
    CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    STARTUPINFO = None
    CREATE_NO_WINDOW = 0

class FFmpegWorker:
    @staticmethod
    def get_video_info(path):
        fps = 25.0
        try:
            fps_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                       "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path]
            res = subprocess.run(fps_cmd, capture_output=True, text=True,
                               startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW).stdout.strip()
            if '/' in res:
                num, den = map(int, res.split('/'))
                fps = num / den if den != 0 else 25.0
            else:
                fps = float(res)
        except: pass

        duration = 0.0
        try:
            dur_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                       "-show_entries", "format=duration", "-of", "csv=p=0", path]
            res = subprocess.run(dur_cmd, capture_output=True, text=True,
                               startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW).stdout.strip()
            duration = float(res)
        except: pass

        keyframes = []
        try:
            kf_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                      "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", path]
            res = subprocess.run(kf_cmd, capture_output=True, text=True,
                               startupinfo=STARTUPINFO, creationflags=CREATE_NO_WINDOW)
            keyframes = [float(l.split(',')[0]) for l in res.stdout.splitlines() if 'K' in l]
        except: pass
        
        return fps, duration, keyframes