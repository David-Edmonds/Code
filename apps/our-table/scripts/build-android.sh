#!/usr/bin/env bash
# Build with an installed Android SDK. No Gradle or external app dependencies.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
if [[ -z "$SDK" ]]; then echo 'Set ANDROID_HOME to an Android SDK directory.' >&2; exit 1; fi
TOOLS="${BUILD_TOOLS:-$SDK/build-tools/35.0.0}"
JAR="$SDK/platforms/android-35/android.jar"
if [[ ! -x "$TOOLS/aapt2" || ! -f "$JAR" ]]; then echo 'Install platforms;android-35 and build-tools;35.0.0 through Android SDK Manager.' >&2; exit 1; fi
BUILD="$ROOT/build"
mkdir -p "$BUILD/compiled" "$BUILD/generated" "$BUILD/classes" "$BUILD/dex" "$BUILD/out"
"$TOOLS/aapt2" compile --dir "$ROOT/android/res" -o "$BUILD/resources.zip"
"$TOOLS/aapt2" link -o "$BUILD/base.apk" -I "$JAR" --manifest "$ROOT/android/AndroidManifest.xml" --java "$BUILD/generated" -A "$ROOT/web" "$BUILD/resources.zip" --min-sdk-version 26 --target-sdk-version 35
find "$ROOT/android/src" "$BUILD/generated" -name '*.java' > "$BUILD/sources.txt"
javac --release 8 -cp "$JAR" -d "$BUILD/classes" @"$BUILD/sources.txt"
jar cf "$BUILD/classes.jar" -C "$BUILD/classes" .
"$TOOLS/d8" --lib "$JAR" --min-api 26 --output "$BUILD/dex" "$BUILD/classes.jar"
cp "$BUILD/base.apk" "$BUILD/unsigned.apk"
(cd "$BUILD/dex" && zip -q -j "$BUILD/unsigned.apk" classes*.dex)
"$TOOLS/zipalign" -f -p 4 "$BUILD/unsigned.apk" "$BUILD/aligned.apk"
# Personal preview signing only. Keep the local key out of source control.
KEYSTORE="${OUR_TABLE_KEYSTORE:-$ROOT/.local-signing/preview.jks}"
mkdir -p "$(dirname "$KEYSTORE")"
if [[ ! -f "$KEYSTORE" ]]; then
  keytool -genkeypair -keystore "$KEYSTORE" -storepass android -keypass android -alias ourtable-preview -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=Our Table Personal Preview' >/dev/null 2>&1
fi
"$TOOLS/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android --key-pass pass:android --ks-key-alias ourtable-preview --out "$BUILD/out/Our-Table-0.1.0.apk" "$BUILD/aligned.apk"
"$TOOLS/apksigner" verify --verbose "$BUILD/out/Our-Table-0.1.0.apk" | tee "$BUILD/out/signature-check.txt"
"$TOOLS/aapt2" dump badging "$BUILD/out/Our-Table-0.1.0.apk" > "$BUILD/out/package-check.txt"
(cd "$BUILD/out" && sha256sum Our-Table-0.1.0.apk > SHA256SUMS.txt)
echo "Built: $BUILD/out/Our-Table-0.1.0.apk"
