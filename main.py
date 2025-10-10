import os
import re
import shlex

vfs_name = "myvfs"

def parse_command(user_input: str) -> list[str]:
    def expand_env_var(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, f"${{{var_name}}}")

    expanded = re.sub(r'\$(\w+)|\$\{([^}]+)\}', expand_env_var, user_input)
    # \$\w+      → $HOME, $USER и т.д.
    # |\$\{[^}]+\} → ${PATH}, ${SHELL} и т.д.

    try:
        parts = shlex.split(expanded)
        return parts
    except ValueError as e:
        print(f"Ошибка парсинга: {e}")
        return  []

def main():
    while True:
        try:
            # Приглашение к вводу: имя VFS + "$ "
            prompt = f"{vfs_name}$ "
            user_input = input(prompt)

            # Удаляем лишние пробелы
            user_input = user_input.strip()

            # Пропускаем пустой ввод
            if not user_input:
                continue

            #
            parts = parse_command(user_input)
            if not parts:
                print("Ошибка:Пустая команда")
                continue

            command = parts[0]
            args = parts[1:]

            #
            if command == "exit":
                break
            elif command == "ls":
                print('ls', *args)
            elif command == "cd":
                print("cd", *args)
            else:
                print(f"Ошибка: неизвестная команда '{command}'")

        except KeyboardInterrupt:
            print("\nВыход по Ctrl+C")
            break
        except EOFError:
            print()
            break

if __name__ == "__main__":
    main()

