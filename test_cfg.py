import os

# Директорії, які треба ігнорувати
EXCLUDE_DIRS = {'.venv', 'venv', '.idea', '.git', '__pycache__'}

def print_structure(root_path, prefix=""):
    try:
        entries = sorted(os.listdir(root_path))
    except PermissionError:
        return

    entries = [e for e in entries if e not in EXCLUDE_DIRS]

    for index, entry in enumerate(entries):
        path = os.path.join(root_path, entry)
        connector = "└── " if index == len(entries) - 1 else "├── "
        print(prefix + connector + entry)

        if os.path.isdir(path):
            extension = "    " if index == len(entries) - 1 else "│   "
            print_structure(path, prefix + extension)

if __name__ == "__main__":
    project_root = "."  # або шлях до каталогу проєкту
    print_structure(project_root)
