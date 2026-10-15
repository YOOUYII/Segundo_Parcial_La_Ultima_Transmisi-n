"""Motor genérico para historias interactivas JSON. Versión anterior al cambio de hora 6."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class StoryError(ValueError):
    """El archivo de historia no cumple el contrato de contenido."""


class SessionError(ValueError):
    """La acción solicitada no es válida para el estado actual."""


@dataclass(frozen=True)
class Option:
    id: str
    text: str
    destination: str
    conditions: dict[str, bool]
    effects: dict[str, bool]


@dataclass(frozen=True)
class Scene:
    id: str
    text: str
    final: bool
    options: tuple[Option, ...]


class Story:
    def __init__(self, title: str, start: str, initial_variables: dict[str, bool], scenes: dict[str, Scene]):
        self.title = title
        self.start = start
        self.initial_variables = dict(initial_variables)
        self.scenes = dict(scenes)

    @classmethod
    def load(cls, path: str | Path) -> "Story":
        file_path = Path(path)
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise StoryError(f"No se pudo leer el archivo '{file_path}': {exc}") from exc
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise StoryError(f"JSON ilegible en línea {exc.lineno}, columna {exc.colno}: {exc.msg}") from exc
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Any) -> "Story":
        if not isinstance(data, dict):
            raise StoryError("La raíz de la historia debe ser un objeto JSON.")
        for field in ("titulo", "inicio", "variables", "escenas"):
            if field not in data:
                raise StoryError(f"Falta el campo obligatorio '{field}'.")
        if not isinstance(data["titulo"], str) or not data["titulo"].strip():
            raise StoryError("El campo 'titulo' debe ser texto no vacío.")
        if not isinstance(data["inicio"], str) or not data["inicio"].strip():
            raise StoryError("El campo 'inicio' debe ser un ID de escena no vacío.")
        variables = data["variables"]
        if not isinstance(variables, dict):
            raise StoryError("El campo 'variables' debe ser un objeto de valores booleanos.")
        for name, value in variables.items():
            if not isinstance(name, str) or not name.strip():
                raise StoryError("Cada variable debe tener un nombre de texto no vacío.")
            if type(value) is not bool:
                raise StoryError(f"La variable '{name}' debe tener un valor booleano.")
        raw_scenes = data["escenas"]
        if not isinstance(raw_scenes, list) or not raw_scenes:
            raise StoryError("El campo 'escenas' debe ser una lista no vacía.")

        scene_data: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(raw_scenes):
            where = f"escenas[{index}]"
            if not isinstance(item, dict):
                raise StoryError(f"{where} debe ser un objeto.")
            for field in ("id", "texto", "final", "opciones"):
                if field not in item:
                    raise StoryError(f"Falta el campo obligatorio '{field}' en {where}.")
            scene_id = item["id"]
            if not isinstance(scene_id, str) or not scene_id.strip():
                raise StoryError(f"El ID de {where} debe ser texto no vacío.")
            if scene_id in scene_data:
                raise StoryError(f"ID de escena duplicado: '{scene_id}'.")
            if not isinstance(item["texto"], str) or not item["texto"].strip():
                raise StoryError(f"El texto de la escena '{scene_id}' debe ser texto no vacío.")
            if type(item["final"]) is not bool:
                raise StoryError(f"El campo 'final' de la escena '{scene_id}' debe ser booleano.")
            if not isinstance(item["opciones"], list):
                raise StoryError(f"'opciones' de la escena '{scene_id}' debe ser una lista.")
            scene_data[scene_id] = item

        if data["inicio"] not in scene_data:
            raise StoryError(f"La escena inicial '{data['inicio']}' no existe.")

        scenes: dict[str, Scene] = {}
        for scene_id, item in scene_data.items():
            options_data = item["opciones"]
            if item["final"] and options_data:
                raise StoryError(f"La escena final '{scene_id}' no puede tener opciones.")
            if not item["final"] and not options_data:
                raise StoryError(f"La escena no final '{scene_id}' debe tener al menos una opción.")
            parsed_options: list[Option] = []
            option_ids: set[str] = set()
            for index, option in enumerate(options_data):
                where = f"opciones[{index}] de la escena '{scene_id}'"
                if not isinstance(option, dict):
                    raise StoryError(f"{where} debe ser un objeto.")
                for field in ("id", "texto", "destino", "condiciones", "efectos"):
                    if field not in option:
                        raise StoryError(f"Falta el campo obligatorio '{field}' en {where}.")
                option_id = option["id"]
                if not isinstance(option_id, str) or not option_id.strip():
                    raise StoryError(f"El ID de {where} debe ser texto no vacío.")
                if option_id in option_ids:
                    raise StoryError(f"ID de opción duplicado '{option_id}' en la escena '{scene_id}'.")
                option_ids.add(option_id)
                if not isinstance(option["texto"], str) or not option["texto"].strip():
                    raise StoryError(f"El texto de la opción '{option_id}' debe ser texto no vacío.")
                destination = option["destino"]
                if not isinstance(destination, str) or not destination.strip():
                    raise StoryError(f"El destino de la opción '{option_id}' debe ser un ID de escena.")
                if destination not in scene_data:
                    raise StoryError(f"Destino inexistente '{destination}' en opción '{option_id}' de '{scene_id}'.")
                conditions = cls._read_boolean_map(option["condiciones"], "condiciones", option_id, variables)
                effects = cls._read_boolean_map(option["efectos"], "efectos", option_id, variables)
                parsed_options.append(Option(option_id, option["texto"], destination, conditions, effects))
            scenes[scene_id] = Scene(scene_id, item["texto"], item["final"], tuple(parsed_options))

        return cls(data["titulo"], data["inicio"], variables, scenes)

    @staticmethod
    def _read_boolean_map(value: Any, field: str, option_id: str, declared: dict[str, bool]) -> dict[str, bool]:
        if not isinstance(value, dict):
            raise StoryError(f"'{field}' de la opción '{option_id}' debe ser un objeto.")
        result: dict[str, bool] = {}
        for name, assigned in value.items():
            if name not in declared:
                raise StoryError(f"Variable no declarada '{name}' en {field} de opción '{option_id}'.")
            if type(assigned) is not bool:
                raise StoryError(f"El valor de '{name}' en {field} de opción '{option_id}' debe ser booleano.")
            result[name] = assigned
        return result


class Session:
    """Sesión de juego con deshacer de una sola elección válida."""

    def __init__(self, story: Story):
        self.story = story
        self.reset()

    @property
    def scene(self) -> Scene:
        return self.story.scenes[self.scene_id]

    @property
    def is_final(self) -> bool:
        return self.scene.final

    @property
    def is_blocked(self) -> bool:
        return not self.scene.final and not self.available_options()

    @property
    def can_undo(self) -> bool:
        """Indica si hay una elección válida disponible para deshacer."""
        return self._undo_state is not None

    def available_options(self) -> list[Option]:
        return [
            option for option in self.scene.options
            if all(self.variables[name] is expected for name, expected in option.conditions.items())
        ]

    def choose(self, option_id: str) -> None:
        if self.scene.final:
            raise SessionError("La historia ya llegó a un final. Reinicia para comenzar otra partida.")
        option = next((item for item in self.available_options() if item.id == option_id), None)
        if option is None:
            raise SessionError(f"La opción '{option_id}' no existe aquí o no está habilitada.")
        # Guardar solo después de validar: una entrada inválida conserva el historial.
        self._undo_state = (self.scene_id, dict(self.variables))
        for name, value in option.effects.items():
            self.variables[name] = value
        self.scene_id = option.destination

    def undo(self) -> None:
        """Restaura el estado anterior a la última elección válida, una sola vez."""
        if self._undo_state is None:
            raise SessionError("No hay una elección válida disponible para deshacer.")
        self.scene_id, variables = self._undo_state
        self.variables = dict(variables)
        self._undo_state = None

    def reset(self) -> None:
        self.scene_id = self.story.start
        self.variables = dict(self.story.initial_variables)
        self._undo_state: tuple[str, dict[str, bool]] | None = None
