import subprocess
import json
import os

def get_audio_tracks(video_path):
    """
    Получает список аудиодорожек из видеофайла с помощью ffprobe.
    Возвращает список словарей: [{'index': 0, 'name': 'Track 1: RUS (ac3) - Dub'}, ...]
    Здесь 'index' - это порядковый номер ИМЕННО аудиопотока (0, 1, 2...), 
    что нужно для флага ffmpeg -map 0:a:X
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-print_format', 'json',
        '-show_entries', 'stream=index,codec_name:stream_tags=language,title',
        '-select_streams', 'a',
        video_path
    ]
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            creationflags=creationflags, 
            text=True, 
            timeout=5
        )
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        
        tracks = []
        for i, stream in enumerate(streams):
            tags = stream.get('tags', {})
            lang = tags.get('language', 'und').upper()
            title = tags.get('title', '')
            codec = stream.get('codec_name', 'unknown')
            
            name = f"[{i+1}] {lang} ({codec})"
            if title:
                name += f" - {title}"
                
            # Вмещаем гораздо больше текста (так как окно теперь шире)
            if len(name) > 55:
                name = name[:52] + "..."
                
            tracks.append({
                "index": i, # Индекс аудиопотока (0 = первая аудиодорожка)
                "name": name
            })
            
        return tracks
    except Exception as e:
        print("Audio analyzer error:", e)
        return []