---
name: android-reporte-pdf
description: Ejecuta un proyecto de Android Studio en el emulador, toma capturas del código (Kotlin/Java y XML) y de las pruebas de ejecución, y genera el PDF de entrega (p. ej. Valdez_Aldana_Fragments2.pdf). Usar cuando el usuario pida "ejecuta el programa X en el emulador", "toma captura de los códigos y de las pruebas", "genérame el pdf/reporte de la práctica", o un PDF llamado Valdez_Aldana_*.
---

# Reporte PDF de práctica Android

Flujo completo en 4 pasos. Los scripts están en `~/.claude/skills/android-reporte-pdf/scripts/`.
Trabaja las capturas en el scratchpad de la sesión (`$S/shots`), no en el proyecto.

## 1. Compilar, arrancar emulador, instalar y abrir

```bash
~/.claude/skills/android-reporte-pdf/scripts/build_run.sh ~/AndroidStudioProjects/<Proyecto>
```

Los proyectos están en `~/AndroidStudioProjects/`. El script compila, cierra los daemons de Gradle,
arranca el emulador con `-gpu host` si no hay uno, instala el APK y abre la app. Tarda ~3 min en frío
(timeout de Bash ≥ 600000).

## 2. Diseñar y ejecutar las pruebas

Lee el código (`app/src/main/java/**`, `res/layout/*.xml`) para saber qué hace la app y decide los casos:
pantalla inicial, un caso normal por cada función/pantalla, y los casos de validación que el código
maneje (campos vacíos, división entre 0, etc.). Normalmente 5–8 capturas.

Maneja la app por resource-id con `emu.py` (encadena pasos con `+`):

```bash
E=~/.claude/skills/android-reporte-pdf/scripts/emu.py
python3 $E dump                                   # ver ids/textos de la pantalla actual
python3 $E shot $S/shots/00_inicio.png
python3 $E tap btnSuma + type edtNumero1 25 + type edtNumero2 17 + hidekb + tap btnCalcular + shot $S/shots/01_suma.png
```

- Haz `hidekb` antes de tocar botones que el teclado pueda tapar.
- Los Toast duran ~2 s: `shot` justo después del `tap` para que salgan; `wait 2.5` antes del siguiente caso
  para que no se cuele el Toast anterior.
- Escribe `$S/shots/captions.json` (el orden de la lista es el del PDF):

```json
[{"file":"00_inicio.png","caption":"Pantalla inicial","group":"Pruebas de ejecución en el emulador"},
 {"file":"05_error.png","caption":"Campo vacío (mensaje de error)","group":"Pruebas de validación"}]
```

Antes de seguir, mira las capturas (una hoja de contacto con PIL y Read) y confirma que cada resultado es
correcto; si algo falla en la app, repórtalo en vez de ocultarlo.

## 3. Generar el PDF

```bash
python3 ~/.claude/skills/android-reporte-pdf/scripts/make_pdf.py \
  --project ~/AndroidStudioProjects/<Proyecto> --shots $S/shots \
  --out ~/Documentos/Valdez_Aldana_<Tema>.pdf \
  --author "Valdez Aldana" --subtitle "<descripción corta de la app>"
```

- Nombre: el que diga el usuario; si no lo dice, `Valdez_Aldana_<Tema>.pdf`. Destino por defecto `~/Documentos`.
  Si el archivo ya existe, pregunta antes de sobrescribir.
- El script detecta solo los fuentes (.kt/.java), layouts y manifest, y el lenguaje para los títulos.
- Revisa la vista previa que imprime (`$S/shots/_preview.png`) con Read antes de dar por terminado.

## 4. Informar

Respuesta corta: ruta del PDF, tabla de pruebas con resultado, y avisar siempre de:
- si el usuario dijo "Java" pero el proyecto es Kotlin (o al revés);
- que las "capturas" del código son imágenes generadas de los archivos reales, no pantallazos del IDE;
- que la portada solo lleva el nombre (no hay materia/grupo/fecha salvo que los dé).

## Trampas de esta máquina (8 GB RAM, GPU Intel, elementary OS)

- **GPU**: el emulador en modo `auto` cae a render por software (arranque de 6 min). Siempre `-gpu host`
  (el AVD `Medium_Phone` ya tiene `hw.gpu.mode=host`).
- **OOM**: Gradle + Android Studio + emulador no caben; el kernel mata al emulador. Por eso se compila
  primero, se hace `./gradlew --stop`, y luego se instala con `adb install` — nunca `gradlew installDebug`
  con el emulador abierto. Si `adb devices` sale vacío a mitad, fue OOM: volver a correr `build_run.sh`.
- **No usar `pkill -f <patrón>`** dentro de un comando Bash: el patrón coincide con el propio shell y lo mata.
- Java: `JAVA_HOME=~/android-studio/jbr`. adb: `~/Android/Sdk/platform-tools/adb`.
- No hay LibreOffice/Chrome/reportlab: el PDF se hace con Pillow + Pygments (ya instalados).
