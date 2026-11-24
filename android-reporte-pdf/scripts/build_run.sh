#!/usr/bin/env bash
# Uso: build_run.sh <ruta_proyecto>
# Compila el APK debug, libera la RAM de Gradle, arranca el emulador (GPU host), instala y abre la app.
set -euo pipefail
PROJ="$(realpath "$1")"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
ADB="$SDK/platform-tools/adb"
export JAVA_HOME="${JAVA_HOME:-$HOME/android-studio/jbr}"

"$ADB" start-server >/dev/null 2>&1 </dev/null || true   # que el daemon de adb no herede stdout (colgaría pipes)
cd "$PROJ"
echo ">> Compilando (assembleDebug)..."
./gradlew assembleDebug --console=plain -q
# 8 GB de RAM: los daemons de Gradle/Kotlin + emulador provocan OOM. Cerrarlos ANTES de arrancar el emulador.
./gradlew --stop >/dev/null 2>&1 || true
for p in $(pgrep -u "$USER" java || true); do
  if tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -qE 'KotlinCompileDaemon|GradleDaemon'; then kill "$p" || true; fi
done

META="$PROJ/app/build/outputs/apk/debug/output-metadata.json"
APK="$PROJ/app/build/outputs/apk/debug/app-debug.apk"
PKG=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['applicationId'])" "$META")

if ! "$ADB" devices | grep -q '^emulator-.*device$'; then
  AVD=$("$SDK/emulator/emulator" -list-avds | grep -v '^INFO' | head -1)
  echo ">> Arrancando emulador $AVD (gpu host)..."
  (cd "$HOME" && DISPLAY="${DISPLAY:-:0}" nohup "$SDK/emulator/emulator" -avd "$AVD" -gpu host >/tmp/emulador-$USER.log 2>&1 &)
fi
for i in $(seq 120); do
  [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && break
  sleep 3
done
[ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] || { echo "El emulador no arrancó; ver /tmp/emulador-$USER.log"; exit 1; }
sleep 4
"$ADB" install -r "$APK"
"$ADB" shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 3
echo "OK paquete=$PKG"
