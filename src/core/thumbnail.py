import subprocess
import os

def get_video_duration(video_path):
    """Получает длительность видео в секундах с помощью ffprobe."""
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        video_path
    ]
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags, text=True, timeout=5)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def extract_thumbnail(video_path, output_path):
    """
    Извлекает кадр из середины фильма.
    """
    duration = get_video_duration(video_path)
    # Если узнали длину, берем середину (или хотя бы 1 секунду)
    target_time = str(max(1, int(duration / 2)))

    cmd = [
        'ffmpeg', 
        '-y',
        '-ss', target_time,    # Быстрая перемотка на середину (в секундах)
        '-i', video_path,
        '-vframes', '1',    # Берем ровно 1 кадр
        '-q:v', '2',        # Сжимаем в хороший JPEG
        output_path
    ]
    
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
            timeout=10 # Перемотка быстрая, но перестрахуемся
        )
        return os.path.exists(output_path)
    except Exception:
        return False