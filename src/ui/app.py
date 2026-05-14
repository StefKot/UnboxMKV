import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import re
from PIL import Image
from core.converter import MKVConverter
from core.thumbnail import extract_thumbnail
from core.audio_analyzer import get_audio_tracks
from tkinterdnd2 import TkinterDnD, DND_FILES

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TkDNDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class UnboxApp(TkDNDApp):
    def __init__(self):
        super().__init__()
        
        self.title("UnboxMKV - Premium Remuxer")
        self.geometry("950x650")
        self.minsize(800, 500)
        
        self.files = []
        self.selected_file = None
        self.file_audio_tracks = {} # Словарь для хранения загруженных списков дорожек: {filepath: [{'index': 0, 'name': '...'}, ...]}
        self.file_selected_audio = {} # Выбранная дорожка для каждого файла: {filepath: 0}
        
        self.output_dir = ""
        self.converter = MKVConverter(
            callback_done=self.on_convert_done,
            callback_error=self.on_convert_error,
            callback_progress=self.on_progress
        )
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_sidebar()
        self._build_main_area()
        self._build_bottom_bar()
        self.update_file_list()
        
        # Регистрация Drag & Drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)
        
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="UNBOX MKV", font=ctk.CTkFont(size=26, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 5))
        
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="PRO VIDEO REMUXER", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00bfff")
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        self.add_btn = ctk.CTkButton(self.sidebar_frame, text="Add MKV Files", command=self.add_files, fg_color="#333", hover_color="#444")
        self.add_btn.grid(row=2, column=0, padx=20, pady=10)
        
        self.clear_btn = ctk.CTkButton(self.sidebar_frame, text="Clear List", command=self.clear_files, fg_color="transparent", border_width=2, text_color="#DCE4EE", hover_color="#333")
        self.clear_btn.grid(row=3, column=0, padx=20, pady=10)

    def on_drop(self, event):
        # TkinterDnD возвращает пути как {C:/path with spaces} C:/path
        raw_files = event.data
        parsed_files = self.parse_dnd_files(raw_files)
        
        added = False
        for f in parsed_files:
            if f.lower().endswith('.mkv') and f not in self.files:
                self.files.append(f)
                added = True
        
        if added:
            self.update_file_list()

    def parse_dnd_files(self, text):
        """Парсинг строки с путями, которые возвращает Drag and Drop"""
        result = []
        if '{' in text:
            # Пути с пробелами обернуты в {}
            parts = re.split(r'\{([^}]+)\}', text)
            for p in parts:
                p = p.strip()
                if p:
                    result.append(p)
        else:
            result = text.split()
        return result

    def _update_preview(self):
        # Если нет выбранного файла, показываем заглушку
        if not self.files or not self.selected_file:
            self._current_preview = None
            empty_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
            self.preview_lbl.configure(text="No Preview\n\nDrag & Drop\nMKV file here", image=empty_img)
            self.audio_combo.configure(values=["No Audio Tracks"], state="disabled")
            self.audio_combo.set("No Audio Tracks")
            return

        target_file = self.selected_file
        
        # Обновляем выпадающий список аудио, если для этого файла уже загружены треки
        self._refresh_audio_dropdown(target_file)

        temp_dir = os.environ.get('TEMP', os.path.dirname(__file__))
        preview_path = os.path.join(temp_dir, "unboxmkv_preview.jpg")
        
        empty_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
        self.preview_lbl.configure(text="Loading preview...", image=empty_img)
        self.update()
        
        import threading
        
        def load_media_info(file_to_load):
            # Дергаем кадр в фоне
            success = extract_thumbnail(file_to_load, preview_path)
            
            # А также сканируем аудиодорожки (если еще не грузили)
            if file_to_load not in self.file_audio_tracks:
                tracks = get_audio_tracks(file_to_load)
                self.file_audio_tracks[file_to_load] = tracks
                # Выбираем первую дорожку по умолчанию (русская или первая попавшаяся)
                if tracks:
                    self.file_selected_audio[file_to_load] = tracks[0]["index"]
            
            # Возвращаемся в UI-поток
            self.after(0, self._apply_preview, success, preview_path, file_to_load)
            
        threading.Thread(target=load_media_info, args=(target_file,), daemon=True).start()

    def _refresh_audio_dropdown(self, target_file):
        """Мгновенно обновляет dropdown сохраненными данными"""
        tracks = self.file_audio_tracks.get(target_file)
        if tracks is None:
            self.audio_combo.configure(state="disabled")
            self.audio_combo.set("Scanning Audio...")
        elif not tracks:
            self.audio_combo.configure(state="disabled", values=["No Audio Found"])
            self.audio_combo.set("No Audio Found")
        else:
            names = [t["name"] for t in tracks]
            self.audio_combo.configure(state="normal", values=names)
            
            # Устанавливаем выбранное значение
            selected_idx = self.file_selected_audio.get(target_file, tracks[0]["index"])
            selected_name = next((t["name"] for t in tracks if t["index"] == selected_idx), names[0])
            self.audio_combo.set(selected_name)

    def on_audio_track_changed(self, choice):
        if not self.selected_file:
            return
        # Находим индекс по имени
        tracks = self.file_audio_tracks.get(self.selected_file, [])
        for t in tracks:
            if t["name"] == choice:
                self.file_selected_audio[self.selected_file] = t["index"]
                break

    def _apply_preview(self, success, preview_path, target_file):
        # Если пользователь уже кликнул на другой файл, отбрасываем старую картинку
        if not self.selected_file or self.selected_file != target_file:
            return
            
        # Обновляем комбобокс со свежими дорожками
        self._refresh_audio_dropdown(target_file)
            
        if success:
            try:
                img = Image.open(preview_path)
                # Подгоняем размер с сохранением пропорций под новое широкое окно (ширина 380-20=360)
                img.thumbnail((360, 400))
                
                # Сохраняем ссылку на изображение
                self._current_preview = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.preview_lbl.configure(text="", image=self._current_preview)
            except Exception as e:
                self.preview_lbl.configure(text="Preview generation\nerror")
        else:
            self.preview_lbl.configure(text="No preview\navailable")

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)
        
        self.list_label = ctk.CTkLabel(self.main_frame, text="Queue & Drag'n'Drop Area:", font=ctk.CTkFont(size=16, weight="bold"))
        self.list_label.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="w")
        
        # Область списка
        self.file_list_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="#1a1a1a", corner_radius=8)
        self.file_list_frame.grid(row=1, column=0, padx=(0, 15), pady=0, sticky="nsew")

        # Картинка превью (Справа) - Теперь шире для вмещения длинных аудиодорожек! (ширина 380)
        self.preview_frame = ctk.CTkFrame(self.main_frame, width=380, corner_radius=10, fg_color="#1a1a1a")
        self.preview_frame.grid(row=0, column=1, rowspan=2, padx=0, pady=0, sticky="nsew")
        self.preview_frame.grid_propagate(False) # чтобы размер держался
        
        self.preview_lbl = ctk.CTkLabel(self.preview_frame, text="No Preview\n\nDrag & Drop\nMKV file here", font=ctk.CTkFont(size=14, weight="bold"), text_color="#444", justify="center")
        self.preview_lbl.place(relx=0.5, rely=0.45, anchor="center")
        
        # Выпадающий список выбора аудиодорожки
        self.audio_combo = ctk.CTkOptionMenu(
            self.preview_frame, 
            values=["Default Audio Track"], 
            state="disabled",
            fg_color="#2b2b2b",
            button_color="#222222",
            button_hover_color="#333333",
            dropdown_fg_color="#222222",
            dropdown_hover_color="#008cba",
            dropdown_text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            dropdown_font=ctk.CTkFont(size=12),
            dynamic_resizing=False,
            command=self.on_audio_track_changed
        )
        self.audio_combo.place(relx=0.5, rely=0.92, anchor="center", relwidth=0.9)

        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0), sticky="ew")
        self.progress_frame.grid_remove() # Скрываем по умолчанию
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=12, progress_color="#00bfff")
        self.progress_bar.pack(fill="x", padx=0, pady=(0, 5))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%", font=ctk.CTkFont(size=12))
        self.progress_label.pack(anchor="e")

    def _build_bottom_bar(self):
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=10)
        self.bottom_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        
        self.out_dir_btn = ctk.CTkButton(self.bottom_frame, text="Choose Output Folder", command=self.choose_output_dir, fg_color="#333", hover_color="#444")
        self.out_dir_btn.grid(row=0, column=0, padx=10, pady=15)
        
        self.out_dir_label = ctk.CTkLabel(self.bottom_frame, text="Same as source...", text_color="gray")
        self.out_dir_label.grid(row=0, column=1, sticky="w", padx=10)
        
        self.convert_btn = ctk.CTkButton(self.bottom_frame, text="UNBOX TO MP4", font=ctk.CTkFont(weight="bold", size=14), fg_color="#00bfff", hover_color="#008cba", text_color="black", text_color_disabled="#111111", command=self.start_conversion, height=45)
        self.convert_btn.grid(row=0, column=2, padx=10, pady=15)

    def add_files(self):
        filetypes = (('MKV files', '*.mkv'), ('All files', '*.*'))
        filenames = filedialog.askopenfilenames(title='Open MKV files', filetypes=filetypes)
        
        for f in filenames:
            if f not in self.files:
                self.files.append(f)
        self.update_file_list()

    def clear_files(self):
        self.files.clear()
        self.selected_file = None
        self.file_audio_tracks.clear()
        self.file_selected_audio.clear()
        self.update_file_list()

    def select_file(self, f):
        self.selected_file = f
        self.update_file_list()

    def remove_file(self, f):
        # Если идет конвертация, не даем удалять файлы из списка
        if self.convert_btn.cget("state") == "disabled":
            return
            
        self.files.remove(f)
        if f in self.file_audio_tracks:
            del self.file_audio_tracks[f]
        if f in self.file_selected_audio:
            del self.file_selected_audio[f]
            
        if self.selected_file == f:
            self.selected_file = None
        self.update_file_list()

    def update_file_list(self):
        # Очищаем фрейм
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        
        if not self.files:
            lbl = ctk.CTkLabel(self.file_list_frame, text="Drag and drop MKV files here...\nOr click 'Add MKV Files' to begin.", text_color="#555")
            lbl.pack(pady=60)
            self.convert_btn.configure(state="disabled", text="UNBOX TO MP4")
            self.selected_file = None
        else:
            if self.selected_file not in self.files:
                self.selected_file = self.files[0]
                
            for i, f in enumerate(self.files):
                filename = os.path.basename(f)
                is_selected = (f == self.selected_file)
                
                row_bg = "#2b2b2b" if is_selected else "transparent"
                row_frame = ctk.CTkFrame(self.file_list_frame, fg_color=row_bg, corner_radius=6)
                row_frame.pack(fill="x", padx=5, pady=2)
                
                name_btn = ctk.CTkButton(row_frame, text=f"{i+1}. {filename}", fg_color="transparent", anchor="w", 
                                         text_color="white" if is_selected else "gray", 
                                         font=ctk.CTkFont(weight="bold" if is_selected else "normal"),
                                         hover_color="#333333", command=lambda file=f: self.select_file(file))
                name_btn.pack(side="left", fill="x", expand=True, padx=5, pady=4)
                
                del_btn = ctk.CTkButton(row_frame, text="✕", width=28, fg_color="transparent", hover_color="#cc0000", text_color="gray", command=lambda file=f: self.remove_file(file))
                del_btn.pack(side="right", padx=5, pady=4)
                
            self.convert_btn.configure(state="normal", text=f"UNBOX {len(self.files)} FILES TO MP4")
            
        self._update_preview()

    def choose_output_dir(self):
        out_dir = filedialog.askdirectory(title="Select Output Directory")
        if out_dir:
            self.output_dir = out_dir
            self.out_dir_label.configure(text=self.output_dir)

    def start_conversion(self):
        if not self.files:
            return
        
        # Блокируем UI
        self.convert_btn.configure(state="disabled", text="CONVERTING...")
        self.add_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.progress_frame.grid()
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        
        # Начинаем с первого файла из очереди
        self._process_queue()

    def _process_queue(self):
        if not self.files:
            self.convert_btn.configure(state="normal", text="UNBOX TO MP4")
            self.add_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
            self.progress_frame.grid_remove()
            
            # Открываем папку с готовыми файлами!
            if self.output_dir:
                os.startfile(self.output_dir)
                
            messagebox.showinfo("Success", "All files have been converted to MP4 successfully!\nNow you can import them to After Effects/Premiere Pro.")
            return
            
        current_file = self.files[0]
        basename = os.path.basename(current_file)
        name_no_ext = os.path.splitext(basename)[0]
        out_name = f"{name_no_ext}.mp4"
        
        if self.output_dir:
            out_path = os.path.join(self.output_dir, out_name)
        else:
            out_folder = os.path.dirname(current_file)
            out_path = os.path.join(out_folder, out_name)
            
        # Обновляем текст кнопки для отображения статуса
        short_name = name_no_ext[:15] + "..." if len(name_no_ext) > 15 else name_no_ext
        self.convert_btn.configure(text=f"CONVERTING: {short_name}")
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        self.update()
        
        # Получаем выбранную аудиодорожку (если есть)
        audio_idx = self.file_selected_audio.get(current_file)
        
        self.converter.convert(current_file, out_path, audio_track_index=audio_idx)

    def on_progress(self, input_file, progress):
        self.after(0, self._handle_progress, progress)
        
    def _handle_progress(self, progress):
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"{int(progress * 100)}%")

    def on_convert_done(self, input_file, output_file):
        # ffmpeg выполняется в другом потоке, поэтому вызываем обновление UI через .after()
        self.after(0, self._handle_done, input_file)

    def _handle_done(self, input_file):
        if input_file in self.files:
            self.files.remove(input_file)
        self.update_file_list()
        self._process_queue()

    def on_convert_error(self, input_file, error_msg):
        self.after(0, self._handle_error, input_file, error_msg)
        
    def _handle_error(self, input_file, error_msg):
        messagebox.showerror("FFmpeg Error", f"Failed to convert {os.path.basename(input_file)}:\n\n{error_msg}")
        if input_file in self.files:
            self.files.remove(input_file)
        self.update_file_list()
        self._process_queue()