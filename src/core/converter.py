import subprocess
import threading
import os
import re

class MKVConverter:
    def __init__(self, callback_done=None, callback_error=None, callback_progress=None):
        self.callback_done = callback_done
        self.callback_error = callback_error
        self.callback_progress = callback_progress
        self.process = None
        self._is_cancelled = False
        self.duration_secs = 0

    def _time_to_secs(self, time_str):
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

    def convert(self, input_file, output_file, audio_track_index=None):
        """Конвертация mkv в mp4 (Remux - без перекодировки)"""
        self._is_cancelled = False
        self.duration_secs = 0
        
        def run_conversion():
            cmd = ['ffmpeg', '-y', '-i', input_file]
            
            # Маппинг потоков
            # По умолчанию ffmpeg берет только первую видео и первую аудио дорожки.
            # Если пользователь выбрал аудиодорожку, мы указываем ее явно.
            if audio_track_index is not None:
                cmd.extend([
                    '-map', '0:v:0', # берем первый видеопоток
                    '-map', f'0:a:{audio_track_index}' # берем выбранную аудиодорожку
                ])
            else:
                # Если дорожка не выбрана, берем первое видео и первое аудио
                cmd.extend([
                    '-map', '0:v:0',
                    '-map', '0:a:0'
                ])
                
            cmd.extend(['-c', 'copy', output_file])
            
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                
                self.process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=creationflags,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                for line in self.process.stderr:
                    if self._is_cancelled:
                        break
                    
                    # Ищем продолжительность видео
                    if "Duration:" in line and self.duration_secs == 0:
                        dur_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                        if dur_match:
                            self.duration_secs = self._time_to_secs(dur_match.group(1))

                    # Ищем текущее время обработки
                    if "time=" in line and self.duration_secs > 0:
                        time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
                        if time_match:
                            curr_secs = self._time_to_secs(time_match.group(1))
                            progress = min(1.0, curr_secs / self.duration_secs)
                            if self.callback_progress:
                                self.callback_progress(input_file, progress)
                
                self.process.wait()
                
                if self._is_cancelled:
                    if os.path.exists(output_file):
                        try:
                            os.remove(output_file)
                        except:
                            pass
                    return
                
                if self.process.returncode == 0:
                    if self.callback_done:
                        self.callback_done(input_file, output_file)
                else:
                    if self.callback_error:
                        self.callback_error(input_file, "Конвертация завершилась с ошибкой.")
            
            except FileNotFoundError:
                if self.callback_error:
                    self.callback_error(input_file, "FFmpeg не найден! Пожалуйста, скачайте FFmpeg и добавьте его в системные переменные PATH (или положите ffmpeg.exe рядом с программой).")
            except Exception as e:
                if self.callback_error:
                    self.callback_error(input_file, str(e))
        
        # Запускаем в отдельном потоке, чтобы не заморозить UI
        threading.Thread(target=run_conversion, daemon=True).start()

    def cancel(self):
        self._is_cancelled = True
        if self.process:
            self.process.kill()