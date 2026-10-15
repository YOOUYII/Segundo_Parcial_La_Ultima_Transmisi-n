"""Interfaz de consola para La última transmisión."""
import argparse
import os
import sys
from pathlib import Path

from arte import arte_para
from motor import Session, SessionError, Story, StoryError


def run(story_path: Path) -> int:
    try:
        story = Story.load(story_path)
    except StoryError as exc:
        print(f"No se pudo iniciar la historia: {exc}")
        return 2

    session = Session(story)
    print(f"=== {story.title} ===")
    while True:
        scene = session.scene
        print(f"\n[{scene.id}] {scene.text}")
        undo_command = "u = deshacer, " if session.can_undo else ""
        if scene.final:
            print("FIN DE LA HISTORIA")
            print(f"Comandos: {undo_command}r = reiniciar, q = salir")
        elif session.is_blocked:
            print(f"No hay opciones habilitadas. Comandos: {undo_command}r = reiniciar, q = salir.")
        else:
            print("Opciones disponibles:")
            for number, option in enumerate(session.available_options(), start=1):
                print(f"  {number}. {option.text} [{option.id}]")
            print(f"Escribe el número o ID de una opción; {undo_command}r = reiniciar, q = salir")

        answer = input("> ").strip()
        if answer.lower() == "q" or (
            answer.lower() == "salir"
            and not any(option.id.lower() == "salir" for option in scene.options)
        ):
            return 0
        if answer.lower() in {"r", "reiniciar"}:
            session.reset()
            print("Partida reiniciada.")
            continue
        if answer.lower() in {"u", "deshacer", "undo"}:
            try:
                session.undo()
                print("Última elección deshecha.")
            except SessionError as exc:
                print(exc)
            continue
        if scene.final or session.is_blocked:
            print("Entrada no válida para este estado. La partida no cambió.")
            continue
        choices = session.available_options()
        selected = next((o for o in choices if o.id == answer), None)
        if selected is None and answer.isdigit():
            index = int(answer) - 1
            if 0 <= index < len(choices):
                selected = choices[index]
        if selected is None:
            print(f"La opción {answer!r} no existe aquí o no está habilitada.")
            continue
        try:
            session.choose(selected.id)
        except SessionError as exc:
            print(exc)


def read_key() -> str:
    """Lee una tecla y devuelve 'up', 'down', 'enter', 'ctrl-c' o el carácter en minúscula."""
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
        if ch == "\r":
            return "enter"
        if ch == "\x03":
            return "ctrl-c"
        return ch.lower()
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            return {"[A": "up", "[B": "down"}.get(seq, "")
        if ch in ("\r", "\n"):
            return "enter"
        if ch == "\x03":
            return "ctrl-c"
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run_menu(story_path: Path) -> int:
    try:
        story = Story.load(story_path)
    except StoryError as exc:
        print(f"No se pudo iniciar la historia: {exc}")
        return 2

    os.system("")  # activa secuencias ANSI en la consola de Windows
    session = Session(story)
    selected = 0
    message = ""
    while True:
        scene = session.scene
        entries: list[tuple[str, str, str | None]] = []  # (etiqueta, acción, id de opción)
        if not scene.final and not session.is_blocked:
            for option in session.available_options():
                entries.append((option.text, "choose", option.id))
        if session.can_undo:
            entries.append(("Deshacer última elección", "undo", None))
        entries.append(("Reiniciar partida", "reset", None))
        entries.append(("Salir", "quit", None))
        selected = min(selected, len(entries) - 1)

        print("\x1b[2J\x1b[H", end="")
        print(f"=== {story.title} ===\n")
        art = arte_para(story_path.stem, scene.id)
        if art:
            print(f"\x1b[36m{art}\x1b[0m\n")
        print(f"[{scene.id}] {scene.text}\n")
        if scene.final:
            print("FIN DE LA HISTORIA\n")
        elif session.is_blocked:
            print("No hay opciones habilitadas.\n")
        for i, (label, _, _) in enumerate(entries):
            print(f"  \x1b[7m> {label} \x1b[0m" if i == selected else f"    {label}")
        print("\n↑/↓ moverse · Enter elegir · u deshacer · r reiniciar · q salir")
        if message:
            print(message)
        message = ""

        key = read_key()
        if key in ("q", "ctrl-c"):
            return 0
        if key == "up":
            selected = (selected - 1) % len(entries)
        elif key == "down":
            selected = (selected + 1) % len(entries)
        elif key == "u" and session.can_undo:
            session.undo()
            selected = 0
        elif key == "r":
            session.reset()
            selected = 0
        elif key == "enter":
            _, action, option_id = entries[selected]
            if action == "quit":
                return 0
            if action == "reset":
                session.reset()
                selected = 0
            elif action == "undo":
                session.undo()
                selected = 0
            else:
                try:
                    session.choose(option_id)
                    selected = 0
                except SessionError as exc:
                    message = str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Motor genérico de historias interactivas JSON")
    parser.add_argument("historia", nargs="?", default="historias/la_ultima_transmision.json",
                        help="ruta a un archivo de historia JSON")
    parser.add_argument("--texto", action="store_true",
                        help="usar el modo de texto clásico en lugar del menú con flechas")
    args = parser.parse_args()
    path = Path(args.historia)
    if args.texto or not (sys.stdin.isatty() and sys.stdout.isatty()):
        return run(path)
    return run_menu(path)


if __name__ == "__main__":
    raise SystemExit(main())
