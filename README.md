# ScreenshotInPDFSkill

Skill para Claude Code que ejecuta un proyecto de Android Studio en el emulador, toma capturas del código (Kotlin/Java y XML) y de las pruebas de ejecución, y genera un PDF de entrega.

## Instalación

```bash
git clone https://github.com/EAldana-Dev/ScreenshotInPDFSkill.git
cp -r ScreenshotInPDFSkill/android-reporte-pdf ~/.claude/skills/
```

## Contenido

- `android-reporte-pdf/SKILL.md` — instrucciones de la skill.
- `android-reporte-pdf/scripts/build_run.sh` — compila, arranca el emulador (GPU host), instala y abre la app.
- `android-reporte-pdf/scripts/emu.py` — controla el emulador por resource-id (tap, type, shot, etc.).
- `android-reporte-pdf/scripts/make_pdf.py` — genera el PDF (portada + código + capturas) con Pillow y Pygments.

## Requisitos

Android SDK (adb, emulator), Python 3 con Pillow y Pygments, fuentes DejaVu.
