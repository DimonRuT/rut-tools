import os
import sys
import platform
import importlib.util
import subprocess
import datetime
import json
import threading
import queue
from typing import Callable, Dict, Optional, List, Tuple, Any
from colorama import Fore, Style, init

init(autoreset=True)

DEFAULT_USERNAME = "user"
DEFAULT_OS_NAME = "UnknownOS"
LIB_DIR = "lib"
SETTINGS_FILE = "settings.json"
LOG_FILE = "rut_dev.log"
COMMAND_PREFIX = "rut."
CURRENT_VERSION = "1.1.0"  # Начальная версия, будет обновлена при check_for_updates
VERSION_URL = "https://raw.githubusercontent.com/DimonRuT/rut-tools/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/DimonRuT/rut-tools/main/rut.py"
MIN_PYTHON_VERSION = (3, 8)

COLOR_THEMES = {
    "lime": {
        "primary": Fore.LIGHTGREEN_EX,
        "secondary": Fore.GREEN,
        "accent": Fore.LIGHTGREEN_EX + Style.BRIGHT,
        "text": Fore.WHITE,
        "error": Fore.RED,
        "warning": Fore.YELLOW,
        "success": Fore.GREEN
    },
    "blue": {
        "primary": Fore.LIGHTBLUE_EX,
        "secondary": Fore.BLUE,
        "accent": Fore.LIGHTBLUE_EX + Style.BRIGHT,
        "text": Fore.WHITE,
        "error": Fore.RED,
        "warning": Fore.YELLOW,
        "success": Fore.GREEN
    }
}

settings: Dict[str, Any] = {}
commands: Dict[str, Dict[str, Callable]] = {}
log_queue = queue.Queue()
log_thread: Optional[threading.Thread] = None
log_thread_stop = threading.Event()
colors = COLOR_THEMES["lime"]

latest_version_available: Optional[str] = None  # Глобальная переменная для статуса обновления


def check_python_version() -> bool:
    return sys.version_info >= MIN_PYTHON_VERSION


def log(message: str, level: str = "info") -> None:
    level_colors = {
        "info": colors["primary"],
        "warning": colors["warning"],
        "error": colors["error"],
        "success": colors["success"]
    }
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    level_color = level_colors.get(level, colors["primary"])
    formatted = f"{colors['primary']}[{level_color}{timestamp}{colors['primary']}] {level_color}{message}{Style.RESET_ALL}"
    print(formatted)
    if settings.get("dev_mode"):
        log_queue.put(f"[{level.upper()}] {message}")


def check_for_updates() -> None:
    """Проверяем версию и обновляем CURRENT_VERSION, сохраняем в latest_version_available."""
    global CURRENT_VERSION, latest_version_available
    import urllib.request
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=5) as resp:
            latest = resp.read().decode("utf-8").strip()
        latest_version_available = latest
        if latest != CURRENT_VERSION:
            log(f"Обнаружена новая версия: {latest} (текущая: {CURRENT_VERSION})", "warning")
            log("Введите rut.core update чтобы обновиться", "info")
        else:
            log(f"Вы используете последнюю версию: {CURRENT_VERSION}", "success")
    except Exception as e:
        log(f"Ошибка проверки обновлений: {e}", "error")
        latest_version_available = None


def get_username() -> str:
    try:
        return os.getlogin()
    except (OSError, AttributeError):
        import getpass
        try:
            return getpass.getuser() or DEFAULT_USERNAME
        except Exception:
            return DEFAULT_USERNAME


def get_os_name() -> str:
    return platform.system() or DEFAULT_OS_NAME


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def load_settings() -> None:
    global settings
    defaults = {
        "color_theme": "lime",
        "dev_mode": False,
        "log_file": LOG_FILE,
        "auto_update": True,
        "verbose": False
    }
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    settings.update(loaded)
        except Exception as e:
            print(f"{colors['error']}Ошибка загрузки настроек: {e}")
    for k, v in defaults.items():
        settings.setdefault(k, v)


def save_settings() -> None:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"{colors['error']}Ошибка сохранения настроек: {e}")


def apply_color_theme() -> None:
    global colors
    theme = settings.get("color_theme", "lime")
    colors = COLOR_THEMES.get(theme, COLOR_THEMES["lime"])


def log_worker() -> None:
    log_file = settings.get("log_file", LOG_FILE)
    with open(log_file, "a", encoding="utf-8") as f:
        while not log_thread_stop.is_set() or not log_queue.empty():
            try:
                msg = log_queue.get(timeout=0.5)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
                f.flush()
            except queue.Empty:
                continue


def start_log_thread() -> None:
    global log_thread
    if log_thread is None or not log_thread.is_alive():
        log_thread_stop.clear()
        log_thread = threading.Thread(target=log_worker, daemon=True)
        log_thread.start()


def stop_log_thread() -> None:
    log_thread_stop.set()
    if log_thread:
        log_thread.join(timeout=1)


ASCII_ART = r"""
██████╗ ██╗   ██╗████████╗    ████████╗ ██████╗  ██████╗ ██╗     ███████╗
██╔══██╗██║   ██║╚══██╔══╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
██████╔╝██║   ██║   ██║          ██║   ██║   ██║██║   ██║██║     ███████╗
██╔══██╗██║   ██║   ██║          ██║   ██║   ██║██║   ██║██║     ╚════██║
██║  ██║╚██████╔╝   ██║          ██║   ╚██████╔╝╚██████╔╝███████╗███████║
╚═╝  ╚═╝ ╚═════╝    ╚═╝          ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
"""


def print_ascii_art() -> None:
    lines = ASCII_ART.strip('\n').split('\n')
    for line in lines:
        print(''.join(colors["accent"] + ch if ch.strip() else ch for ch in line))
    link = "dsc.gg/ruttools"
    width = max(len(line) for line in lines)
    padding = (width - len(link)) // 2
    print(colors["accent"] + ' ' * padding + link)
    # Вывод версии и статуса обновления:
    version_str = f"Версия: {CURRENT_VERSION}"
    if latest_version_available is None:
        status = "Статус обновления неизвестен"
    elif latest_version_available == CURRENT_VERSION:
        status = "Вы используете последнюю версию"
    else:
        status = f"Доступна новая версия {latest_version_available}"
    status_line = f"{version_str} | {status}"
    padding_status = (width - len(status_line)) // 2
    print(colors["accent"] + ' ' * padding_status + status_line + '\n')


def display_prompt(username: str, os_name: str) -> None:
    print(f"{colors['primary']}┌──({colors['text']}{username}@rut_tools{colors['primary']})-[{colors['text']}OS:{os_name}{colors['primary']}]")
    print(f"{colors['primary']}└─$ {colors['text']}", end="", flush=True)


def install_package(package: str) -> bool:
    try:
        log(f"Установка пакета: {package}...", "info")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package],
            stdout=subprocess.DEVNULL if not settings.get("verbose") else None,
            stderr=subprocess.DEVNULL if not settings.get("verbose") else None
        )
        log(f"Пакет {package} успешно установлен", "success")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Ошибка установки пакета {package}: {e}", "error")
        return False


def load_commands() -> Dict[str, Dict[str, Callable]]:
    loaded_commands = {}
    os.makedirs(LIB_DIR, exist_ok=True)
    for filename in os.listdir(LIB_DIR):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        mod_name = filename[:-3]
        mod_path = os.path.join(LIB_DIR, filename)
        try:
            spec = importlib.util.spec_from_file_location(mod_name, mod_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for pkg in getattr(module, "REQUIRED_PACKAGES", []):
                    install_package(pkg)
                mod_cmds = getattr(module, "COMMANDS", {})
                loaded_commands[mod_name] = {k: v for k, v in mod_cmds.items() if callable(v)}
                log(f"Загружен модуль {mod_name} с {len(mod_cmds)} командами", "success")
        except Exception as e:
            log(f"Ошибка загрузки модуля {filename}: {e}", "error")
    return loaded_commands


def parse_user_input(user_input: str) -> Tuple[Optional[str], Optional[str], List[str]]:
    parts = user_input.strip().split()
    if not parts:
        return None, None, []
    if len(parts) == 1 and parts[0].lower() in ("exit", "help"):
        return parts[0].lower(), None, []
    if parts[0].startswith(COMMAND_PREFIX) and len(parts) >= 2:
        namespace = parts[0][len(COMMAND_PREFIX):]
        return namespace, parts[1], parts[2:]
    return None, None, []


def cmd_restart(args: List[str]) -> str:
    log("Перезапуск RuT Tools...", "info")
    os.execv(sys.executable, [sys.executable] + sys.argv)
    return ""


def cmd_update(args: List[str]) -> str:
    import urllib.request
    global CURRENT_VERSION
    try:
        log("Загрузка новой версии...", "info")
        # Скачиваем новую версию скрипта
        with urllib.request.urlopen(UPDATE_URL, timeout=10) as resp:
            new_code = resp.read().decode("utf-8")

        new_code = new_code.replace('\r\n', '\n')  # Убираем лишние переносы строк

        # Записываем новый код
        with open(__file__, "w", encoding="utf-8", newline='\n') as f:
            f.write(new_code)

        # После успешного обновления - обновляем CURRENT_VERSION из version.txt
        with urllib.request.urlopen(VERSION_URL, timeout=5) as resp:
            CURRENT_VERSION = resp.read().decode("utf-8").strip()

        log("Обновление успешно. Перезапуск...", "success")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        log(f"Ошибка обновления: {e}", "error")
        return f"{colors['error']}Ошибка обновления: {e}"


def cmd_settings_show(args: List[str]) -> str:
    return "\n".join(f"{colors['primary']}{k}: {colors['text']}{v}" for k, v in settings.items())


def cmd_settings_set(args: List[str]) -> str:
    if len(args) < 2:
        return f"{colors['error']}Ошибка: укажите настройку и значение"
    key, value = args[0], args[1]
    if key not in settings:
        return f"{colors['error']}Ошибка: неизвестная настройка '{key}'"
    old = settings[key]
    try:
        if isinstance(old, bool):
            settings[key] = value.lower() in ("true", "1", "yes", "on")
        elif isinstance(old, int):
            settings[key] = int(value)
        elif isinstance(old, float):
            settings[key] = float(value)
        else:
            settings[key] = value
        save_settings()
        if key == "color_theme":
            apply_color_theme()
        elif key == "dev_mode":
            if settings[key]:
                start_log_thread()
            else:
                stop_log_thread()
        return f"{colors['success']}Настройка '{key}' изменена: {colors['text']}{old} → {settings[key]}"
    except ValueError as e:
        return f"{colors['error']}Ошибка: неверное значение для настройки '{key}': {e}"


def cmd_help(args: List[str]) -> None:
    print()
    print(f"{colors['accent']}Справка по RuT Tools:")
    print(f"{colors['primary']}  Формат: {colors['text']}rut.<namespace> <команда> [аргументы]")
    print(f"{colors['primary']}  Пример: {colors['text']}rut.math add 2 2")
    print()
    print(f"{colors['accent']}Команды ядра:")

    core_descriptions = {
        "restart": "Перезапустить RuT Tools",
        "help": "Показать это сообщение",
        "show": "Показать текущие настройки",
        "set": "Изменить настройку (пример: set color_theme blue)",
        "update": "Обновить RuT Tools до последней версии"
    }

    for ns in ("core", "settings"):
        for cmd, func in commands.get(ns, {}).items():
            desc = core_descriptions.get(cmd, "Без описания")
            print(f"{colors['primary']}  rut.{ns} {cmd:<10} {colors['text']}{desc}")
    print()

    for ns, cmd_dict in sorted(commands.items()):
        if ns in ("core", "settings"):
            continue
        print(f"{colors['accent']}Модуль {ns}:")
        for cmd in sorted(cmd_dict):
            print(f"{colors['primary']}  rut.{ns} {cmd}")
        print()


def pause_and_refresh() -> None:
    input(f"{colors['text']}Нажмите Enter чтобы продолжить...")
    clear_screen()
    print_ascii_art()


def main() -> None:
    if not check_python_version():
        print(f"{Fore.RED}Ошибка: требуется Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} или выше", file=sys.stderr)
        sys.exit(1)

    load_settings()
    apply_color_theme()
    if settings.get("dev_mode"):
        start_log_thread()

    if settings.get("auto_update"):
        check_for_updates()

    username, os_name = get_username(), get_os_name()

    global commands
    commands = load_commands()
    commands.setdefault("core", {})
    commands["core"]["restart"] = cmd_restart
    commands["core"]["help"] = cmd_help
    commands["core"]["update"] = cmd_update
    commands.setdefault("settings", {})
    commands["settings"]["show"] = cmd_settings_show
    commands["settings"]["set"] = cmd_settings_set

    clear_screen()
    print_ascii_art()

    while True:
        try:
            display_prompt(username, os_name)
            user_input = input()
            if not user_input.strip():
                continue

            cmd_ns, cmd_name, args = parse_user_input(user_input)
            if cmd_ns == "exit":
                log("Выход из RuT Tools...", "info")
                break
            elif cmd_ns == "help":
                cmd_help(args)
                pause_and_refresh()
                continue
            if not cmd_ns or not cmd_name:
                log("Ошибка: неверный формат команды. Введите 'help' для справки", "error")
                pause_and_refresh()
                continue
            if cmd_ns in commands and cmd_name in commands[cmd_ns]:
                try:
                    res = commands[cmd_ns][cmd_name](args)
                    if res:
                        print(res)
                except Exception as e:
                    log(f"Ошибка при выполнении команды: {e}", "error")
                    pause_and_refresh()
            else:
                log(f"Неизвестная команда: {cmd_ns}.{cmd_name}", "error")
                pause_and_refresh()

        except KeyboardInterrupt:
            print()
            log("Для выхода введите 'exit'", "warning")
            pause_and_refresh()
        except Exception as e:
            log(f"Критическая ошибка: {e}", "error")
            pause_and_refresh()

    stop_log_thread()


if __name__ == "__main__":
    main()
