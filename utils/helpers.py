def format_time_hmsf(seconds, fps=25.0):
    """Превращает секунды в формат 00:00:00:00 (HH:MM:SS:FF)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    f = int(round((seconds - int(seconds)) * fps))
    if f >= int(fps): f = 0
    return f"{h:02}:{m:02}:{s:02}:{f:02}"