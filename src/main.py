import sys
import os

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ui.app import UnboxApp

def main():
    app = UnboxApp()
    app.mainloop()

if __name__ == "__main__":
    main()