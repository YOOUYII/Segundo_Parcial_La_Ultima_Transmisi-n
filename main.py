"""Interfaz de consola para La última transmisión."""
import argparse
from pathlib import Path

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
        if scene.final:
            print("FIN DE LA HISTORIA")
            print("Comandos: r = reiniciar, q = salir")
        elif session.is_blocked:
            print("No hay opciones habilitadas. Puedes reiniciar (r) o salir (q).")
        else:
            print("Opciones disponibles:")
            for number, option in enumerate(session.available_options(), start=1):
                print(f"  {number}. {option.text} [{option.id}]")
            print("Escribe el número o ID de una opción; r = reiniciar, q = salir")

        answer = input("> ").strip()
        if answer.lower() in {"q", "salir"}:
            return 0
        if answer.lower() in {"r", "reiniciar"}:
            session.reset()
            print("Partida reiniciada.")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Motor genérico de historias interactivas JSON")
    parser.add_argument("historia", nargs="?", default="historias/la_ultima_transmision.json",
                        help="ruta a un archivo de historia JSON")
    args = parser.parse_args()
    return run(Path(args.historia))


if __name__ == "__main__":
    raise SystemExit(main())