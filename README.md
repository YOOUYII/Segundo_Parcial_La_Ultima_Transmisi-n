# La última transmisión

## Integrantes

- Integrante 1: [Rodrigo Vazquez Rico]
- Integrante 2: [Angel Fabian Gutierrez Cruz]

## Versiones requeridas

- Python 3.10 o superior.
- No requiere dependencias externas; utiliza la biblioteca estándar de Python.

## Instalación

Instala Python 3.10 o superior y abre PowerShell en la carpeta del proyecto. No es necesario instalar paquetes.

## Ejecución

Historia principal:

    python main.py

Historia secundaria:

    python main.py historias/estacion_de_niebla.json

Ejemplo de validación de destino inexistente:

    python main.py ejemplos/destino_inexistente.json

Durante una partida, escribe `u` para deshacer la última elección válida cuando esté disponible. El comando restaura la escena y las variables anteriores; después se necesita otra elección válida para habilitar un nuevo deshacer. `r` reinicia y elimina esa posibilidad; `q` sale.

## Pruebas

    python -m unittest discover -s tests -v

## Formato de historias

El archivo JSON raíz contiene titulo, inicio, variables y escenas. Cada escena contiene id, texto, final y opciones. Cada opción contiene id, texto, destino, condiciones y efectos. Las variables y los valores de condiciones y efectos son booleanos.

## Rutas de finales

Historia principal:

- E4 Rescate: revisar → investigar → activar_codigo.
- E5 El eco: revisar → continuar → activar_sin_verificar.
- E6 Silencio: revisar → continuar → cortar.

Historia secundaria:

- S4: entrar → examinar → frecuencia_segura.
- S5: entrar → salir → frecuencia_abierta.

## Limitaciones

- La interfaz es de consola.
- El progreso no se guarda entre ejecuciones.
- Solo se permite deshacer una elección válida por vez; no existe rehacer.
