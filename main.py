import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import urllib.request
import os
import certifi

#Фикс бага с сертификатом
if getattr(sys, 'frozen', False):
    # Если мы внутри .exe, ищем сертификат во временной папке распаковки
    base_path = sys._MEIPASS
    cacert_path = os.path.join(base_path, 'certifi', 'cacert.pem')

    # Если файл там есть, используем его
    if os.path.exists(cacert_path):
        os.environ['SSL_CERT_FILE'] = cacert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cacert_path
else:
    # Если запускаем просто .py файл, используем стандартный путь certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Настройки установщика
APP_NAME = "ZOMBIE IS-25-05 Launcher"
APP_VERSION = "1.1"
INSTALL_DIR = os.path.join(os.getenv('LOCALAPPDATA'), "ZombieLauncher")

LAUNCHER_URL = "https://github.com/Vladik1092/ServerLauncher/releases/download/v1.2/launcher.exe"

# Цвета
COLOR_BG = "#1e1e1e"
COLOR_PANEL = "#3c3c3c"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_DIM = "#a0a0a0"
COLOR_ACCENT = "#4caf50"
COLOR_ACCENT_H = "#66bb6a"

LICENSE_TEXT = """
ZOMBIE IS-25-05 Launcher
Версия 1.2

Добро пожаловать! Этот установщик создан для удобной установки лаунчера сервера ZOMBIE IS-25-05.

БЕЗОПАСНОСТЬ:
Лаунчер не содержит вирусов, майнеров или шпионского ПО. Он использует официальные библиотеки для запуска игры и скачивания модов.
Весь исходный код открыт и доступен на GitHub:
https://github.com/Vladik1092/ServerLauncher

Нажимая "Установить", вы соглашаетесь с тем, что установщик скачает файлы лаунчера из интернета.

Приятной игры на сервере ZOMBIE IS-25-05!
"""


def create_shortcut(target_path, shortcut_path, icon_path):
    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{target_path}"
    $Shortcut.IconLocation = "{icon_path}"
    $Shortcut.Save()
    """
    try:
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, check=True)
        return True
    except Exception:
        return False



class InstallProgressWindow:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback

        self.win = tk.Toplevel(root)
        self.win.title("Установка...")
        self.win.geometry("800x600")
        self.win.resizable(False, False)
        self.win.configure(bg=COLOR_BG)

        main_frame = tk.Frame(self.win, bg=COLOR_PANEL, bd=0)
        main_frame.place(relx=0.5, rely=0.5, anchor="center", width=600, height=300)

        tk.Frame(main_frame, bg="#6a6a6a", height=2).pack(fill="x", side="top")
        tk.Frame(main_frame, bg="#6a6a6a", width=2).pack(fill="y", side="left")

        inner = tk.Frame(main_frame, bg=COLOR_PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(inner, text="Установка ZOMBIE Launcher", font=("Arial", 18, "bold"), fg=COLOR_TEXT,
                 bg=COLOR_PANEL).pack(pady=(20, 10))

        self.status_label = tk.Label(inner, text="Подготовка...", font=("Arial", 11), fg=COLOR_TEXT_DIM, bg=COLOR_PANEL)
        self.status_label.pack(pady=10)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=25, troughcolor="#1e1e1e", background=COLOR_ACCENT)

        self.progress = ttk.Progressbar(inner, orient="horizontal", length=500, mode="determinate",
                                        style="TProgressbar")
        self.progress.pack(pady=20)

        threading.Thread(target=self.do_install, daemon=True).start()

    def update_progress(self, value, text):
        self.progress['value'] = value
        self.status_label.config(text=text)
        self.win.update_idletasks()

    def download_file(self, url, dest_path):
        def report(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, int(downloaded * 100 / total_size))
                self.update_progress(percent, f"Скачивание лаунчера... {percent}%")

        urllib.request.urlretrieve(url, dest_path, reporthook=report)

    def do_install(self):
        try:
            if not os.path.exists(INSTALL_DIR):
                os.makedirs(INSTALL_DIR)

            launcher_dst = os.path.join(INSTALL_DIR, "launcher.exe")
            if os.path.exists(launcher_dst):
                try:
                    os.remove(launcher_dst)
                except PermissionError:
                    raise PermissionError("Закройте запущенный лаунчер перед установкой!")

            self.update_progress(0, "Подключение к серверу GitHub...")
            self.download_file(LAUNCHER_URL, launcher_dst)

            # Копируем иконку из установщика
            self.update_progress(90, "Создание ярлыка...")
            if getattr(sys, 'frozen', False):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            src_icon = os.path.join(base_dir, "icon.ico")
            icon_dst = os.path.join(INSTALL_DIR, "icon.ico")
            if os.path.exists(src_icon):
                shutil.copy2(src_icon, icon_dst)

            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            shortcut_path = os.path.join(desktop, f"{APP_NAME}.lnk")
            create_shortcut(launcher_dst, shortcut_path, icon_dst if os.path.exists(icon_dst) else "")

            self.update_progress(100, "Установка завершена!")
            time.sleep(1)

            self.win.destroy()
            self.callback(True, launcher_dst)

        except Exception as e:
            self.win.destroy()
            self.callback(False, str(e))


# Главное окно
def start_installation(root, btn_install, agree_check):
    def on_finish(success, message):
        if success:
            messagebox.showinfo("Установка завершена", f"{APP_NAME} успешно установлен!\nЗапускаем лаунчер...")
            os.startfile(message)
            root.destroy()
        else:
            messagebox.showerror("Ошибка установки", f"Произошла ошибка:\n{message}")
            btn_install.config(state=tk.NORMAL, bg=COLOR_ACCENT)
            agree_check.config(state=tk.NORMAL)

    InstallProgressWindow(root, on_finish)


def main():
    root = tk.Tk()
    root.title(f"Установка {APP_NAME}")
    root.geometry("800x600")
    root.resizable(False, False)
    root.configure(bg=COLOR_BG)

    # Главная панель
    main_frame = tk.Frame(root, bg=COLOR_PANEL, bd=0)
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=680, height=520)

    tk.Frame(main_frame, bg="#6a6a6a", height=2).pack(fill="x", side="top")
    tk.Frame(main_frame, bg="#6a6a6a", width=2).pack(fill="y", side="left")

    inner = tk.Frame(main_frame, bg=COLOR_PANEL)
    inner.pack(fill="both", expand=True, padx=30, pady=30)

    # Заголовок
    tk.Label(inner, text=f"Установка {APP_NAME}", font=("Arial", 20, "bold"), fg=COLOR_TEXT, bg=COLOR_PANEL).pack(
        pady=(0, 15))

    # Текст лицензии
    license_frame = tk.Frame(inner, bg="#1a1a1a", bd=0, height=250)
    license_frame.pack(fill="x", pady=(0, 15))
    license_frame.pack_propagate(False)

    text_area = tk.Text(license_frame, wrap="word", font=("Consolas", 10), bg="#1a1a1a", fg=COLOR_TEXT_DIM, bd=0,
                        padx=10, pady=10)
    text_area.insert("1.0", LICENSE_TEXT)
    text_area.config(state="disabled")
    text_area.pack(fill="both", expand=True)

    # Чекбокс
    agree_var = tk.BooleanVar()

    def toggle_button():
        if agree_var.get():
            btn_install.config(state=tk.NORMAL, bg=COLOR_ACCENT, cursor="hand2")
        else:
            btn_install.config(state=tk.DISABLED, bg="#4a4a4a")

    agree_check = tk.Checkbutton(
        inner, text="Я принимаю условия соглашения", variable=agree_var, command=toggle_button,
        font=("Arial", 11), fg=COLOR_TEXT, bg=COLOR_PANEL, activebackground=COLOR_PANEL, activeforeground=COLOR_TEXT,
        selectcolor="#1a1a1a", bd=0, cursor="hand2"
    )
    agree_check.pack(pady=10)

    # Кнопка установки
    btn_install = tk.Button(
        inner, text="УСТАНОВИТЬ", state=tk.DISABLED, command=lambda: start_installation(root, btn_install, agree_check),
        font=("Arial", 14, "bold"), bg="#4a4a4a", fg=COLOR_TEXT, relief="flat", width=25, height=2,
        activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT
    )
    btn_install.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()