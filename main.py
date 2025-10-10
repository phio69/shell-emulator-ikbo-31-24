#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shlex
import argparse

# Имя VFS по умолчанию
VFS_NAME = "myvfs"


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


def handle_command(command: str, args: list[str]) -> bool:
    """Обрабатывает команду. Возвращает False, если нужно завершить работу."""
    if command == "exit":
        return False
    elif command == "ls":
        print("ls", *args)
    elif command == "cd":
        print("cd", *args)
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
            continue  # пропускаем ошибки

    print("-" * 40)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Эмулятор shell")
    parser.add_argument("--vfs", type=str, help="Путь к физическому расположению VFS")
    parser.add_argument("--script", type=str, help="Путь к стартовому скрипту")
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Отладочный вывод параметров (требование Этапа 2)
    print("Параметры запуска:")
    print(f"  --vfs    = {args.vfs}")
    print(f"  --script = {args.script}")
    print()

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