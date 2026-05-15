# UnboxMKV - Premium Video Remuxer

**UnboxMKV** — это стильный, молниеносный и профессиональный инструмент для ремуксинга (remux) MKV-файлов в формат MP4 без потери качества. 
Создан специально для видеомонтажеров (Adobe Premiere Pro, After Effects, DaVinci Resolve), которые часто сталкиваются с тем, что их софт не поддерживает чтение `.mkv` контейнеров.

---

## 📸 Скриншоты интерфейса

| Главный экран (Drag & Drop) | Выбор звуковой дорожки |
|:---:|:---:|
| <img width="1919" height="1040" alt="image" src="https://github.com/user-attachments/assets/4e5db05b-0f12-4334-88fb-00b0e2fd918d" /> | <img width="356" height="157" alt="image" src="https://github.com/user-attachments/assets/4a6e1f50-ed8f-4d58-a411-3020a2b10d72" /> |

| Процесс конвертации | Успешное завершение |
|:---:|:---:|
| <img width="1919" height="1040" alt="image" src="https://github.com/user-attachments/assets/48caee4e-01e8-4173-9779-7c3f560be908" /> | <img width="373" height="151" alt="image" src="https://github.com/user-attachments/assets/eb5612a9-2a7c-4b56-a35d-23dc1808786d" /> |

---

## 🔥 Главные фишки
- **Мгновенная конвертация**: Процесс идет со скоростью копирования файла на вашем накопителе, так как видео не перекодируется (используется Remux `ffmpeg -c copy`).
- **Drag & Drop**: Просто выделите нужные серии или фильмы и бросьте их в окно — полная поддержка перетаскивания файлов.
- **Умные превью (Smart Thumbnails)**: Программа мгновенно вычисляет середину видео и выводит сочный кадр постер прямо в интерфейсе программы.
- **Анализатор аудиодорожек**: В MKV часто вшиты десятки озвучек. Программа сканирует их за миллисекунды и дает выбрать нужную (например, "Русский дубляж") для сохранения в финальный MP4.
- **Асинхронность**: Интерфейс приложения никогда не зависает (даже при работе с огромными файлами) благодаря поточной работе с FFmpeg.
- **Студийный UI**: Строгий, неоново-темный интерфейс на базе *CustomTkinter* без визуального шума.

---

## 🛠 Установка для разработчиков

1. **Скачайте FFmpeg**:
   - Скачайте архив (например с [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)).
   - Добавьте директорию `bin` (там где `ffmpeg.exe` и `ffprobe.exe`) в системную переменную `PATH`, либо просто закиньте эти .exe в папку с проектом.

2. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/your-username/UnboxMKV.git
   cd UnboxMKV
   ```

3. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Запустите программу**:
   ```bash
   python src/main.py
   ```

---

## 📦 Сборка в один файл (.exe)

Чтобы программой было удобно пользоваться как обычным standalone-приложением (без установки Python), соберите её через PyInstaller:

1. Установите упаковщик:
   ```bash
   pip install pyinstaller
   ```
2. Узнайте путь к библиотекам, введя команду `pip show customtkinter`. 
3. Выполните команду сборки (подставьте свой путь к Python `site-packages`):
   ```bash
   pyinstaller --noconfirm --onefile --windowed --add-data "<ВАШ_ПУТЬ>/customtkinter;customtkinter/" --add-data "<ВАШ_ПУТЬ>/tkinterdnd2;tkinterdnd2/" src/main.py
   ```

Готовый независимый файл `main.exe` появится в папке `dist/`. Переименуйте его в `UnboxMKV.exe` и скидывайте коллегам!

---
*Created with ❤️ for Video Editors.*
