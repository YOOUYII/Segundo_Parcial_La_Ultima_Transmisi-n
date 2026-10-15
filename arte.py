"""Arte ASCII por historia (nombre del archivo sin extensión) y por ID de escena."""

_CONSOLA = r"""
   .------------------------------.
   |  .--------------------------.|
   |  | ~~~/\/\~~/\~~~/\/\/\~~~  ||
   |  | ~~/    \/  \~~/        \~ ||
   |  | 02:13   SEÑAL ENTRANTE   ||
   |  '--------------------------'|
   |  (o) (o) (o)   [=====]  ::   |
   '------------------------------'
        ((  ayuda...  desde Aurora  ))
"""

_ARCHIVO = r"""
     _______________________
    |  ___________________  |
    | | COD: 7-3-ALFA-9    | |
    | | ORIGEN: ?????????? | |
    | | > buscando...      | |
    | |___________________| |
    |_______________________|
       [ARCHIVO]  ___  ___
         .-----. |___||___|
         | 101 |  fichas
"""

_ANTENA = r"""
            \ | /
          -- (*) --
            / | \
             /|\
            / | \
           /  |  \
          /___|___\
              |
      ________|________
     |   ESTACIÓN       |
     |      AURORA      |
"""

_RESCATE = r"""
              \ | /
            -- (*) --        ~ ~ ~
               /|\          señal OK
              / | \
        *    /__|__\    *
       /|\      |      /|\
       / \   ___|___   / \
     .  .  . EQUIPO  .  .  .
       ~ ~ rescate en camino ~ ~
"""

_ECO = r"""
              \ | /
            -- (*) --
               /|\
              / | \
     "...ayuda..."   "...ayuda..."
        "...ayuda..."   "...ayuda..."
   - - - - - - - - - - - - - - - - -
   . : . amanecer . : . . : . : . :
"""

_CORTE = r"""
        .-------------------.
        |  ___   ___   ___  |
        | | x | | x | | x | |
        | |___| |___| |___| |
        |   SIN SEÑAL  ...   |
        '-------------------'
      ,
     /|   ~~~~ ~~~~ ~~~~
    / |   ~~~~ ~~~~ ~~~~
        > _  <
"""

ARTE = {
    "la_ultima_transmision": {
        "E1": _CONSOLA,
        "E2": _ARCHIVO,
        "E3": _ANTENA,
        "E4": _RESCATE,
        "E5": _ECO,
        "E6": _CORTE,
    },
}


def arte_para(historia: str, escena: str) -> str:
    return ARTE.get(historia, {}).get(escena, "").strip("\n")
