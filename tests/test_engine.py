"""Suite automatizada U1-U6 e I1 para la versión posterior al cambio de hora 6."""
import copy
from contextlib import redirect_stdout
from io import StringIO
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import run
from motor import Session, SessionError, Story, StoryError

ROOT = Path(__file__).resolve().parents[1]
STORY_PATH = ROOT / "historias" / "la_ultima_transmision.json"


def raw_story():
    return json.loads(STORY_PATH.read_text(encoding="utf-8"))


class EngineTests(unittest.TestCase):
    def test_u1_only_options_matching_current_state_are_available(self):
        story = Story.load(STORY_PATH)
        session = Session(story)
        session.choose("revisar")
        self.assertEqual([o.id for o in session.available_options()], ["investigar", "continuar"])
        session.choose("investigar")
        self.assertEqual(session.scene_id, "E3")
        self.assertEqual({o.id for o in session.available_options()}, {"activar_codigo", "cortar"})

        session.reset()
        session.choose("revisar")
        session.choose("continuar")
        self.assertEqual({o.id for o in session.available_options()}, {"activar_sin_verificar", "cortar"})

    def test_u2_valid_choice_applies_effect_and_destination(self):
        session = Session(Story.load(STORY_PATH))
        session.choose("revisar")
        session.choose("investigar")
        self.assertEqual(session.scene_id, "E3")
        self.assertIs(session.variables["conoce_origen"], True)

    def test_u3_nonexistent_or_disabled_choice_preserves_state(self):
        session = Session(Story.load(STORY_PATH))
        session.choose("revisar")
        before = (session.scene_id, dict(session.variables))
        for option_id in ("no_existe", "activar_codigo"):
            with self.subTest(option_id=option_id):
                with self.assertRaises(SessionError):
                    session.choose(option_id)
                self.assertEqual((session.scene_id, session.variables), before)

    def test_u4_invalid_content_is_rejected_with_diagnostic(self):
        valid = raw_story()
        cases = []
        cases.append(("estructura de escenas incorrecta", lambda d: d.__setitem__("escenas", {}), "lista"))
        cases.append(("variable inicial no booleana", lambda d: d["variables"].__setitem__("conoce_origen", 1), "booleano"))

        cases.append(("campo ausente", lambda d: d.pop("titulo"), "titulo"))
        cases.append(("inicio inexistente", lambda d: d.__setitem__("inicio", "E99"), "inicial"))
        cases.append(("escena duplicada", lambda d: d["escenas"].append(copy.deepcopy(d["escenas"][0])), "duplicado"))
        cases.append(("opción duplicada", lambda d: d["escenas"][1]["opciones"].append(copy.deepcopy(d["escenas"][1]["opciones"][0])), "duplicado"))
        cases.append(("destino inexistente", lambda d: d["escenas"][0]["opciones"][0].__setitem__("destino", "E99"), "Destino"))
        cases.append(("variable no declarada en efecto", lambda d: d["escenas"][1]["opciones"][0]["efectos"].__setitem__("no_declarada", True), "no declarada"))
        cases.append(("variable no declarada en condición", lambda d: d["escenas"][1]["opciones"][0]["condiciones"].__setitem__("no_declarada", True), "no declarada"))
        cases.append(("valor no booleano en efecto", lambda d: d["escenas"][1]["opciones"][0]["efectos"].__setitem__("conoce_origen", 1), "booleano"))
        cases.append(("valor no booleano en condición", lambda d: d["escenas"][2]["opciones"][0]["condiciones"].__setitem__("conoce_origen", 1), "booleano"))
        cases.append(("final con opciones", lambda d: d["escenas"][3].__setitem__("opciones", [copy.deepcopy(d["escenas"][0]["opciones"][0])]), "final"))
        cases.append(("no final sin opciones", lambda d: d["escenas"][0].__setitem__("opciones", []), "no final"))

        for label, mutate, expected in cases:
            with self.subTest(label=label):
                data = copy.deepcopy(valid)
                mutate(data)
                with self.assertRaisesRegex(StoryError, expected):
                    Story.from_dict(data)

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no-existe.json"
            with self.assertRaisesRegex(StoryError, "No se pudo leer"):
                Story.load(missing)
            malformed = Path(tmp) / "mal.json"
            malformed.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(StoryError, "JSON ilegible"):
                Story.load(malformed)

    def test_u4_blocked_nonfinal_scene_is_reported_by_session_state(self):
        data = {
            "titulo": "Bloqueo", "inicio": "A", "variables": {"abierto": False},
            "escenas": [
                {"id": "A", "texto": "Escena", "final": False, "opciones": [
                    {"id": "pasar", "texto": "Pasar", "destino": "B", "condiciones": {"abierto": True}, "efectos": {}}
                ]},
                {"id": "B", "texto": "Fin", "final": True, "opciones": []}
            ]
        }
        session = Session(Story.from_dict(data))
        self.assertTrue(session.is_blocked)
        self.assertEqual(session.available_options(), [])
        with self.assertRaises(SessionError):
            session.choose("pasar")
        self.assertEqual(session.scene_id, "A")

    def test_u5_reset_restores_scene_and_initial_variables(self):
        session = Session(Story.load(STORY_PATH))
        session.choose("revisar")
        session.choose("investigar")
        self.assertTrue(session.can_undo)
        session.reset()
        self.assertEqual(session.scene_id, "E1")
        self.assertEqual(session.variables, {"conoce_origen": False, "confia_en_la_voz": False})
        self.assertFalse(session.can_undo)
        with self.assertRaises(SessionError):
            session.undo()

    def test_u6_undo_restores_state_once_and_rearms_after_valid_choice(self):
        session = Session(Story.load(STORY_PATH))
        self.assertFalse(session.can_undo)
        with self.assertRaises(SessionError):
            session.undo()

        session.choose("revisar")
        session.choose("investigar")
        self.assertEqual(session.scene_id, "E3")
        self.assertTrue(session.variables["conoce_origen"])
        self.assertTrue(session.can_undo)

        before_invalid = (session.scene_id, dict(session.variables))
        for option_id in ("no_existe", "activar_sin_verificar"):
            with self.subTest(invalid_option=option_id):
                with self.assertRaises(SessionError):
                    session.choose(option_id)
                self.assertEqual((session.scene_id, session.variables), before_invalid)
                self.assertTrue(session.can_undo)

        session.undo()
        self.assertEqual(session.scene_id, "E2")
        self.assertEqual(session.variables, {"conoce_origen": False, "confia_en_la_voz": False})
        self.assertFalse(session.can_undo)
        with self.assertRaises(SessionError):
            session.undo()
        self.assertEqual(session.scene_id, "E2")

        session.choose("continuar")
        self.assertEqual(session.scene_id, "E3")
        self.assertTrue(session.can_undo)
        session.undo()
        self.assertEqual(session.scene_id, "E2")
        self.assertFalse(session.can_undo)

    def test_i1_real_history_reaches_each_final(self):
        routes = {
            "E4": ("revisar", "investigar", "activar_codigo"),
            "E5": ("revisar", "continuar", "activar_sin_verificar"),
            "E6": ("revisar", "continuar", "cortar"),
        }
        for expected_final, route in routes.items():
            with self.subTest(final=expected_final):
                session = Session(Story.load(STORY_PATH))
                for option_id in route:
                    if option_id == route[-1]:
                        state_before_final_choice = (session.scene_id, dict(session.variables))
                    session.choose(option_id)
                self.assertEqual(session.scene_id, expected_final)
                self.assertTrue(session.is_final)
                self.assertTrue(session.can_undo)
                session.undo()
                self.assertEqual((session.scene_id, session.variables), state_before_final_choice)
                self.assertEqual(session.scene_id, "E3")
                self.assertFalse(session.can_undo)

    def test_second_history_works_without_engine_specific_routes(self):
        second = ROOT / "historias" / "estacion_de_niebla.json"
        session = Session(Story.load(second))
        session.choose("entrar")
        session.choose("examinar")
        self.assertTrue(session.variables["codigo_encontrado"])
        session.choose("frecuencia_segura")
        self.assertEqual(session.scene_id, "S4")
        self.assertTrue(session.is_final)

    def test_cli_option_named_salir_is_not_treated_as_exit(self):
        second = ROOT / "historias" / "estacion_de_niebla.json"
        output = StringIO()
        with patch("builtins.input", side_effect=["entrar", "salir", "frecuencia_abierta", "u", "q"]):
            with redirect_stdout(output):
                result = run(second)

        self.assertEqual(result, 0)
        self.assertIn("[S5]", output.getvalue())
        self.assertIn("Última elección deshecha.", output.getvalue())
        self.assertIn("[S3]", output.getvalue())


if __name__ == "__main__":
    unittest.main()
