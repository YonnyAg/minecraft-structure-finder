# Minecraft Structure Finder

Aplicación de escritorio en Python y PySide6 con motor local Cubiomes para Minecraft Java 26.3.

## Descargar el programa

**[Descargar ZIP de Minecraft Structure Finder](https://github.com/YonnyAg/minecraft-structure-finder/archive/refs/heads/main.zip)**

También puedes abrir [el repositorio en GitHub](https://github.com/YonnyAg/minecraft-structure-finder), pulsar el botón verde **Code** y elegir **Download ZIP**. No necesitas instalar Git.

Esta descarga contiene el código del programa y su motor. **Esta versión se ejecuta con Python; todavía no hay un instalador `.exe`.**

## Requisitos

- Windows 10/11 de **64 bits**, arquitectura **x64** (Intel o AMD). El motor incluido no es para Windows ARM64, Linux o macOS.
- **Python 3.11 o superior de 64 bits**, con `pip`. La aplicación se probó con Python 3.11.
- Conexión a internet durante la instalación de dependencias. Después, las búsquedas funcionan sin conexión.
- Una seed de **Minecraft Java 26.3**, con generación estándar. Esta versión del buscador admite cabañas de brujas del Overworld.

Es una aplicación externa: no necesitas instalar mods ni tener Minecraft abierto. No modifica tu mundo.

## Instalar y abrir por primera vez

### 1. Instala Python

Descarga Python desde [la página oficial para Windows](https://www.python.org/downloads/windows/). Elige un **Windows installer (64-bit)**; evita los instaladores de 32 bits, ARM64 y los paquetes *embeddable*.

Si el instalador ofrece la opción **Add python.exe to PATH**, márcala. Mantén habilitado `pip`. Al terminar, cierra y vuelve a abrir la terminal si ya tenías una abierta.

### 2. Extrae el ZIP

Haz clic derecho sobre el ZIP descargado y selecciona **Extraer todo**. Entra en la carpeta extraída `minecraft-structure-finder-main`, donde se encuentran `README.md`, `pyproject.toml` e `iniciar.bat`.

**No ejecutes el programa desde dentro del ZIP.**

### 3. Abre PowerShell en esa carpeta

En el Explorador de archivos, entra en la carpeta del programa, haz clic en la barra de direcciones, escribe `powershell` y pulsa **Enter**.

### 4. Instala las dependencias

Ejecuta estos comandos en orden. Espera a que termine cada uno antes de continuar:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

El punto final de `install -e .` forma parte del comando. Se creará una carpeta `.venv` con el entorno y las dependencias del programa. No necesitas activar el entorno ni cambiar la política de ejecución de PowerShell.

La DLL compilada está incluida en `mc_finder/_native/`; **no necesitas un compilador ni reconstruir el motor** para usar el programa.

### 5. Abre la aplicación

Haz doble clic en **`iniciar.bat`**. También puedes abrirla desde PowerShell:

```powershell
.\.venv\Scripts\python.exe -m mc_finder
```

En los siguientes usos solo necesitas abrir `iniciar.bat`. Mantén la carpeta `.venv` junto al archivo; si mueves el proyecto a otra ruta, vuelve a crear el entorno e instalar las dependencias allí.

## Prueba rápida después de instalar

1. Pulsa **Cargar ejemplo**.
2. Deja seleccionada **Estructura más cercana**.
3. Pulsa **Buscar estructuras**.
4. Con la seed de ejemplo, debe aparecer una cabaña en **X: −2368, Z: 656**.

Para probar los grupos, selecciona **Agrupación de estructuras**, cantidad mínima **2** y radio del grupo **200**. Con el área del ejemplo deben aparecer **3 grupos**.

## Problemas frecuentes

| Problema | Qué revisar |
| --- | --- |
| `python` no se reconoce o abre Microsoft Store | Comprueba la instalación y `PATH`. Si tienes el lanzador `py`, usa `py -3 -m venv .venv` para el primer comando. Los demás comandos no cambian. |
| `iniciar.bat` dice que primero debes instalar | Ejecuta los dos comandos de instalación dentro de la carpeta que contiene `pyproject.toml`. |
| `No module named PySide6` | Repite `.\.venv\Scripts\python.exe -m pip install -e .` dentro de la carpeta del programa. |
| Error al cargar `finder.dll` | Confirma que usas Windows x64 y Python de 64 bits, y que extrajiste el ZIP completo. |
| La instalación de dependencias falla | Revisa la conexión y conserva el mensaje de error para comunicar el problema en [Issues](https://github.com/YonnyAg/minecraft-structure-finder/issues). |
| No aparecen grupos | Reduce la cantidad mínima, amplía el radio del grupo o el área de exploración. Una seed no garantiza agrupaciones para cualquier condición. |

Puedes comprobar tu versión y arquitectura de Python con:

```powershell
python -c "import sys, struct; print(sys.version); print(struct.calcsize('P') * 8, 'bits')"
```

## Enlace para compartir en YouTube

Comparte [la página principal del proyecto](https://github.com/YonnyAg/minecraft-structure-finder): contiene la descarga y estas instrucciones. El botón **Descargar ZIP** de arriba obtiene la versión de la rama `main`.

Si el repositorio es privado, solo pueden acceder las cuentas autorizadas. Para distribuirlo a cualquier espectador debe estar público.

## Qué permite esta etapa

- Introducir una seed numérica de 64 bits, conservando su precisión.
- Buscar cabañas de brujas del Overworld en mundos estándar de Java 26.3.
- Encontrar la más cercana dentro del radio, o listar todas las encontradas.
- Buscar grupos de un mínimo de cabañas dentro de un círculo común configurable.
- Ver centro X/Z, cantidad, radio mínimo y distancia de cada grupo; consultar y copiar sus cabañas.
- Definir origen X/Z y un radio circular de 1 a 50.000 bloques.
- Ver resultados ordenados por distancia horizontal y copiar las coordenadas de una fila.
- Ejecutar en segundo plano con progreso y cancelación, sin mostrar resultados parciales al cancelar.
- Validar y copiar los parámetros como JSON. La seed se exporta como texto para evitar pérdida de precisión en JavaScript.
- Cargar como ejemplo la seed y posición compartidas durante el diseño.

Las otras estructuras y dimensiones están deshabilitadas mientras se implementan.
Los radios son distancias horizontales X/Z; la búsqueda cercana también está limitada por el radio de exploración.
Al cambiar parámetros se borran los resultados anteriores. Los campos numéricos no muestran flechas.

## Prueba con la seed de ejemplo

1. Pulsa **Cargar ejemplo**: seed `5067257298883736067`, origen X `-2599`, Z `1953`, radio `10000`.
2. Selecciona **Estructura más cercana** o **Todas dentro del área**.
3. Pulsa **Buscar estructuras**.
4. Selecciona una fila y pulsa **Copiar X / Z seleccionadas** para contrastarla en Minecraft o Chunkbase.

Con el motor incluido, esta consulta predice 24 cabañas dentro del radio. La más cercana está en X `-2368`, Z `656`, a unos 1.317,4 bloques del origen.
Estos valores son una referencia de regresión del motor, todavía no una verificación dentro del juego.

## Buscar agrupaciones

1. Carga tu seed y elige **Agrupación de estructuras**.
2. Define **Radio de exploración**: cuánto buscar desde el origen (máximo 50.000 bloques).
3. Define **Cantidad mínima** y **Radio del grupo** (máximo 5.000 bloques).
4. Pulsa **Buscar estructuras**. La pestaña **Grupos** muestra cantidad, centro X/Z, radio geométrico mínimo y distancia del centro al origen.
5. Selecciona un grupo y pulsa **Ver cabañas del grupo** o **Copiar centro y cabañas**.

Para una prueba con coincidencias: usa la seed y el origen del ejemplo, exploración de 10.000 bloques, cantidad mínima **2** y radio de grupo **200**. El motor devuelve tres grupos, uno de ellos con tres cabañas. El primero tiene centro X `-2552`, Z `616`, radio aproximado `188,3`, y cabañas en `(-2736, 576)` y `(-2368, 656)`.
Con cantidad mínima **4** y ese mismo radio/área no se encuentran coincidencias. No significa que la seed completa carezca de agrupaciones.

El radio del grupo se mide respecto de un centro común, no entre vecinos. Una cadena de cabañas cercanas no se acepta si no cabe entera en el círculo. Se eliminan duplicados y subconjuntos redundantes: con mínimo 4, un conjunto válido de 5 se muestra como un grupo de 5. Dos grupos distintos pueden compartir cabañas.
Todas las cabañas tienen que estar dentro del círculo de exploración. Un grupo que cruza su límite solo se considera con las estructuras encontradas dentro de ese área.

**El centro geométrico no es un punto AFK validado.** Se calculan referencias de estructuras en X/Z; la altura, los volúmenes donde aparecen mobs, el diseño de las granjas y su activación simultánea requieren una etapa adicional. Este paso permite localizar conjuntos para evaluarlos en el juego.

## Perímetro horizontal por chunks

La pestaña **Perímetro** acepta una referencia X/Z manual. También puedes usar **Ver perímetro** desde una ubicación seleccionada o **Perímetro de este grupo** desde un grupo.

El informe cubre la proyección horizontal completa de un disco de radio 128 bloques con un rectángulo conservador alineado a chunks. Indica:

- Chunks adicionales hacia norte (−Z), sur (+Z), oeste (−X) y este (+X), contados desde el chunk que contiene la referencia, sin volver a contarlo.
- Coordenadas de los últimos bloques del rectángulo y sus chunks límite; todos los límites son inclusivos.
- Tamaño y cantidad total de chunks del rectángulo, y límites del disco antes de alinearlo.
- Un texto copiable con las coordenadas y el origen de la referencia.

Ejemplo, centro X `-2552`, Z `616`: ocho chunks adicionales en cada dirección más el chunk de referencia; rectángulo **17 × 17 = 289 chunks**. Límites X `-2688` a `-2417`, Z `480` a `751`. El total corresponde al rectángulo completo, incluidas esquinas fuera del disco; no es un mínimo de excavación.

No se calcula un punto AFK ni se elige una altura: **el perímetro no garantiza eficiencia ni activación conjunta**. Tampoco indica que haya que vaciar todos sus bloques: faltan la profundidad, el terreno actual y los espacios donde pueden aparecer mobs; deben conservarse las granjas. Si el grupo supera 128 bloques de radio, se avisa que el perímetro no resuelve la separación entre sus estructuras.

Si cambias una referencia manual debes recalcular. Los perímetros importados de resultados se invalidan cuando cambias parámetros de búsqueda, para evitar mezclar grupos o seeds anteriores.

## Alcance

El motor calcula posiciones de generación y comprueba los biomas con la seed completa de 64 bits.
No lee ni modifica mundos, no verifica bloques existentes ni calcula altura Y.
Las coordenadas son referencias de generación, no necesariamente la puerta o el centro exacto del edificio.
No cubre datapacks/mods de generación, biomas grandes ni zonas generadas en versiones anteriores.
Los resultados deben contrastarse en un mundo estándar Java 26.3 antes de considerarlos verificados.

## Organización

- `mc_finder/domain.py`: parámetros, catálogo y contrato inicial de ubicaciones; independiente de Qt.
- `mc_finder/services.py`: validación, errores e interfaz `SearchEngine`.
- `mc_finder/groups.py`: agrupaciones por círculo común, centro y radio mínimo; sin Qt ni dependencias adicionales.
- `mc_finder/perimeter.py`: límites horizontales inclusivos y conteo por dirección con coordenadas negativas.
- `mc_finder/perimeter_panel.py`: informe manual o basado en la selección, y copia de límites.
- `mc_finder/engine.py`: DLL, recorrido por regiones, filtro circular y orden por distancia.
- `mc_finder/worker.py`: ejecución en segundo plano y cancelación cooperativa.
- `mc_finder/window.py`: formulario, resultados y copia de coordenadas.
- `mc_finder/app.py`: arranque de Qt.
- `native/bridge.c`: interfaz C pequeña con contexto independiente por búsqueda.
- `scripts/build_engine.py`: reconstrucción desde una revisión fijada del motor.
- `tests/test_search.py`: integración del motor y de la ventana.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas usan la DLL real. Cubren semillas grandes y negativas, regiones negativas, límite del círculo, búsqueda cercana, cancelación, errores y el ciclo de búsqueda en Qt. La geometría de grupos se contrasta con enumeración exhaustiva de subconjuntos y círculos, incluyendo cadenas, triángulos, grupos solapados y coordenadas cercanas al borde del mundo.

## Reconstruir el motor (solo desarrollo)

```powershell
.\.venv\Scripts\python.exe -m pip install ziglang==0.16.0
.\.venv\Scripts\python.exe scripts/build_engine.py
```

Requiere conexión para descargar el código fuente la primera vez. La búsqueda funciona sin conexión.

Motor: [xpple/cubiomes](https://github.com/xpple/cubiomes), revisión `d3290a8f421863b737ae7c31ad3d800b4fc584c7`, derivado de [Cubitect/cubiomes](https://github.com/Cubitect/cubiomes).
`mc_finder/_native/manifest.json` registra revisión, compilador y hashes de fuente y binario. Los avisos de licencia de Cubiomes, loot y cJSON están junto a la DLL.

## Próxima etapa

Contrastar los grupos en el juego y diseñar la comprobación de un punto AFK común. La carga de mundos y las demás estructuras/dimensiones quedan para etapas posteriores.
