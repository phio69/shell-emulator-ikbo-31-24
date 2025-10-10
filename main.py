import os
import re
import shlex
import argparse
from pathlib import Path
from datetime import datetime, date

# Имя VFS по умолчанию
VFS_NAME = "myvfs"

# Глобальное состояние VFS
current_vfs = {} #Структура
current_vfs_path = None #Путь к исходной директории
current_dir = [] #Текущая директория


def expand_environment_variables(text: str) -> str:
    """Раскрывает переменные окружения вида $VAR и ${VAR}."""
    def replace_match(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, f"${{{var_name}}}")

    return re.sub(r'\$(\w+)|\$\{([^}]+)\}', replace_match, text)


def parse_user_input(user_input: str) -> list[str]:
    """Парсит строку ввода с поддержкой кавычек и переменных окружения."""
    try:
        expanded = expand_environment_variables(user_input)
        tokens = shlex.split(expanded)
        return tokens
    except ValueError as e:
        print(f"Ошибка парсинга: {e}")
        return []


def load_vfs_from_directory(path: str) -> dict:
    """
    Рекурсивно загружает структуру директории в память в виде вложенного словаря.
    Файлы представлены как строки с содержимым (или пустые строки при ошибке).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"VFS: путь не найден: {path}")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"VFS: путь не является директорией: {path}")

    def _scan(current_path: Path) -> dict:
        result = {}
        for item in current_path.iterdir():
            if item.is_file():
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    content = ""
                result[item.name] = content
            elif item.is_dir():
                result[item.name] = _scan(item)
        return result

    return _scan(Path(path))

def get_current_directory() -> dict:
    """Возвращает словарь, соответствующий текущей директории в VFS."""
    node = current_vfs
    for part in current_dir:
        if part in node and isinstance(node[part], dict):
            node = node[part]
        else:
            raise FileNotFoundError("Текущая директория недоступна (повреждена структура VFS)")
    return node


def handle_command(command: str, args: list[str]) -> bool:
    """Обрабатывает команду. Возвращает False, если нужно завершить работу."""
    global current_vfs, current_vfs_path, current_dir

    if command == "exit":
        return False

    elif command == "vfs-init":
        current_vfs = {}
        current_vfs_path = None
        print("VFS сброшена на значение по умолчанию.")

    elif command == "ls":
        try:
            current = get_current_directory()
            items = list(current.keys())
            if items:
                print(" ".join(sorted(items)))
            # если пусто — просто ничего не выводим
        except Exception as e:
            print(f"ls: ошибка чтения директории: {e}")

    elif command == "cd":
        if not args:
            print("cd: отсутствует аргумент")
            return True

        path = args[0]
        if path == "/":
            current_dir = []
            return True

        # Обработка относительных и абсолютных путей
        if path.startswith("/"):
            # Абсолютный путь: сброс и разбор
            new_dir = [p for p in path.split("/") if p]
            temp_dir = []
        else:
            # Относительный путь: от текущей директории
            new_dir = [p for p in path.split("/") if p]
            temp_dir = current_dir.copy()

        # Обработка ".." и обычных имён
        for part in new_dir:
            if part == "..":
                if temp_dir:
                    temp_dir.pop()
            elif part == "." or not part:
                continue
            else:
                # Проверяем, существует ли папка
                current_node = current_vfs
                for d in temp_dir:
                    current_node = current_node.get(d, {})
                if not isinstance(current_node.get(part), dict):
                    print(f"cd: нет такого каталога: {part}")
                    return True
                temp_dir.append(part)

        current_dir = temp_dir

    elif command == "whoami":
        import getpass
        print(getpass.getuser())

    elif command == "date":
        print(datetime.now().strftime("%a %b %d %H:%M:%S %Y"))

    elif command == "wc":
        if not args:
            print("wc: отсутствует аргумент (имя файла)")
            return True

        path = args[0]
        try:
            # Разбиваем путь на части
            if path.startswith("/"):
                # Абсолютный путь — начинаем с корня VFS
                parts = [p for p in path.split("/") if p]
                current = current_vfs
            else:
                # Относительный путь — начинаем с текущей директории
                parts = [p for p in path.split("/") if p]
                current = get_current_directory()

            # Проходим по всем частям пути, кроме последней
            for part in parts[:-1]:
                if part == "..":
                    # Для простоты — пока не поддерживаем ".." в путях файлов
                    raise NotImplementedError("Поддержка '..' в путях файлов пока не реализована")
                elif part == "." or not part:
                    continue
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    raise FileNotFoundError(f"Папка '{part}' не найдена")

            # Последняя часть — имя файла
            filename = parts[-1]
            if not isinstance(current, dict) or filename not in current:
                raise FileNotFoundError(f"Файл '{filename}' не найден")

            content = current[filename]
            if not isinstance(content, str):
                print(f"wc: {path}: Это каталог")
                return True

            lines = len(content.splitlines())
            words = len(content.split())
            chars = len(content)
            print(f"{lines:4} {words:4} {chars:4} {path}")

        except FileNotFoundError as e:
            print(f"wc: {path}: Нет такого файла или каталога")
        except Exception as e:
            print(f"wc: ошибка чтения файла {path}: {e}")

        filename = args[0]
        try:
            current = get_current_directory()
            if filename not in current:
                print(f"wc: {filename}: Нет такого файла или каталога")
                return True
            content = current[filename]
            if not isinstance(content, str):
                print(f"wc: {filename}: Это каталог")
                return True

            lines = len(content.splitlines())
            words = len(content.split())
            chars = len(content)
            print(f"{lines:4} {words:4} {chars:4} {filename}")
        except Exception as e:
            print(f"wc: ошибка чтения файла {filename}: {e}")

    else:
        print(f"Ошибка: неизвестная команда '{command}'")
    return True


def execute_script(script_path: str, command_handler):
    """
    Выполняет команды из скрипта построчно.
    Имитирует диалог: выводит команду → результат.
    Ошибочные строки пропускаются.
    """
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Ошибка: файл скрипта не найден: {script_path}")
        return
    except Exception as e:
        print(f"Ошибка чтения скрипта: {e}")
        return

    print(f"Выполнение скрипта: {script_path}")
    print("-" * 40)

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        print(f"{VFS_NAME}$ {line}")  # имитация ввода
        try:
            tokens = parse_user_input(line)
            if not tokens:
                continue
            cmd = tokens[0]
            args = tokens[1:]
            should_continue = command_handler(cmd, args)
            if not should_continue:
                break
        except Exception as e:
            print(f"Ошибка при выполнении строки {line_num}: {e}")
            continue

    print("-" * 40)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Эмулятор shell (Вариант 21)")
    parser.add_argument("--vfs", type=str, help="Путь к физическому расположению VFS")
    parser.add_argument("--script", type=str, help="Путь к стартовому скрипту")
    return parser.parse_args()


def main():
    global current_vfs, current_vfs_path
    args = parse_arguments()

    print("Параметры запуска:")
    print(f"  --vfs    = {args.vfs}")
    print(f"  --script = {args.script}")
    print()

    # Загрузка VFS из директории, если указан путь
    if args.vfs:
        try:
            current_vfs = load_vfs_from_directory(args.vfs)
            current_vfs_path = args.vfs
            print(f"VFS успешно загружена из: {args.vfs}")
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"Ошибка загрузки VFS: {e}")
            current_vfs = {}
            current_vfs_path = None
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке VFS: {e}")
            current_vfs = {}
            current_vfs_path = None
    else:
        current_vfs = {}
        current_vfs_path = None
        print("ℹ️  Используется VFS по умолчанию (пустая).")

    # Если указан скрипт — выполняем его и завершаем работу
    if args.script:
        execute_script(args.script, handle_command)
        return

    # Иначе — запускаем интерактивный REPL
    print("Эмулятор shell запущен. Введите 'exit' для выхода.")
    while True:
        try:
            prompt = f"{VFS_NAME}$ "
            user_input = input(prompt).strip()
            if not user_input:
                continue

            tokens = parse_user_input(user_input)
            if not tokens:
                print("Ошибка: пустая команда")
                continue

            command = tokens[0]
            args = tokens[1:]
            should_continue = handle_command(command, args)
            if not should_continue:
                break

        except (KeyboardInterrupt, EOFError):
            print()
            break


if __name__ == "__main__":
    main()