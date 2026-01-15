import subprocess

class FFmpegWorker:
    @staticmethod
    def get_video_info(path):
        """Возвращает FPS и список ключевых кадров."""
        # Получаем FPS
        fps = 25.0
        try:
            fps_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                       "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path]
            res = subprocess.run(fps_cmd, capture_output=True, text=True).stdout.strip()
            num, den = map(int, res.split('/')) if '/' in res else (float(res), 1)
            fps = num / den
        except: pass

        # Получаем Keyframes
        keyframes = []
        try:
            kf_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                      "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", path]
            res = subprocess.run(kf_cmd, capture_output=True, text=True)
            keyframes = [float(l.split(',')[0]) for l in res.stdout.splitlines() if 'K' in l]
        except: pass
        
        return fps, keyframes