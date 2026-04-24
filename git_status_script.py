import subprocess


def get_git_status():
    """Ejecuta 'git status' y devuelve su salida."""
    result = subprocess.run(['git', 'status'], capture_output=True, text=True, check=True)
    return result.stdout


def get_git_diff():
    """Ejecuta 'git diff' y devuelve su salida."""
    result = subprocess.run(['git', 'diff'], capture_output=True, text=True, check=True)
    return result.stdout


if __name__ == "__main__":
    print("--- Git Status ---")
    try:
        status = get_git_status()
        print(status)
    except subprocess.CalledProcessError as e:
        print(f"Error al obtener el estado de Git: {e}")
        print(e.stderr)

    print("\n--- Git Diffs ---")
    try:
        diffs = get_git_diff()
        if diffs:
            print(diffs)
        else:
            print("No hay diferencias.")
    except subprocess.CalledProcessError as e:
        print(f"Error al obtener los diffs de Git: {e}")
        print(e.stderr)
