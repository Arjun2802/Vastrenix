#!/bin/bash
set -e

BUILD_TOOLS="./android-sdk/build-tools/34.0.0"
PLATFORM="./android-sdk/platforms/android-34/android.jar"
RES_DIR="dist/android/res"
MANIFEST="dist/android/AndroidManifest.xml"
BUILD_DIR="build/android_single"
DIST_DIR="dist/android"
OUTPUT_APK="$DIST_DIR/vastrenix-release.apk"
ROOT_OUTPUT_APK="vastrenix-release.apk"

echo "=========================================================="
echo " VASTRENIX Single Universal Release APK Build Engine      "
echo "=========================================================="

# 1. Resolve Keystore and Passwords
KEYSTORE_PATH="${VASTRENIX_KEYSTORE_PATH:-}"
KEYSTORE_PASS="${VASTRENIX_KEYSTORE_PASS:-}"
KEY_ALIAS="${VASTRENIX_KEY_ALIAS:-}"
KEY_PASS="${VASTRENIX_KEY_PASS:-}"

if [ -f "key.properties" ]; then
    echo "Loading signing credentials from key.properties..."
    source <(grep = key.properties | sed 's/ *= */=/g')
    KEYSTORE_PATH="${storeFile:-$KEYSTORE_PATH}"
    KEYSTORE_PASS="${storePassword:-$KEYSTORE_PASS}"
    KEY_ALIAS="${keyAlias:-$KEY_ALIAS}"
    KEY_PASS="${keyPassword:-$KEY_PASS}"
fi

if [ -z "$KEYSTORE_PATH" ]; then
    KEYSTORE_PATH="$DIST_DIR/vastrenix-release.keystore"
fi
if [ -z "$KEYSTORE_PASS" ]; then
    KEYSTORE_PASS="vastrenix123"
fi
if [ -z "$KEY_ALIAS" ]; then
    KEY_ALIAS="vastrenix"
fi
if [ -z "$KEY_PASS" ]; then
    KEY_PASS="vastrenix123"
fi

if [ ! -f "$KEYSTORE_PATH" ]; then
    echo "Generating release signing keystore at: $KEYSTORE_PATH"
    mkdir -p "$(dirname "$KEYSTORE_PATH")"
    keytool -genkeypair -v -keystore "$KEYSTORE_PATH" -alias "$KEY_ALIAS" \
        -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass "$KEYSTORE_PASS" -keypass "$KEY_PASS" \
        -dname "CN=VASTRENIX Release, OU=Mobile, O=Vastrenix Garments, L=Surat, S=Gujarat, C=IN"
fi

echo "=== 1. Preparing clean build directory ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/compiled_res" "$BUILD_DIR/classes" "$BUILD_DIR/dex" "$BUILD_DIR/unaligned" "$BUILD_DIR/assets" "$DIST_DIR"

echo "=== 2. Compiling resources with aapt2 (adaptive icon, file_paths, network security) ==="
$BUILD_TOOLS/aapt2 compile --dir "$RES_DIR" -o "$BUILD_DIR/compiled_res.zip"

echo "=== 3. Packaging updated web client assets (Vastrenix www) ==="
mkdir -p "$BUILD_DIR/assets/web"
cp -r www/* "$BUILD_DIR/assets/web/"
cp -r www/* "$BUILD_DIR/assets/"
if [ -d "assets" ]; then
    cp -r assets/* "$BUILD_DIR/assets/"
fi
if [ -f "google-services.json" ]; then
    cp google-services.json "$BUILD_DIR/assets/"
fi

echo "=== 3b. Minifying client JS assets (Production Build Hygiene) ==="
python3 -c "
import os

def strip_js_comments(code):
    out = []
    i, n = 0, len(code)
    IN_SINGLE, IN_DOUBLE, IN_TEMPLATE, IN_REGEX, IN_LINE_COMMENT, IN_BLOCK_COMMENT, NORMAL = 1, 2, 3, 4, 5, 6, 0
    state = NORMAL
    last_sig = ''
    while i < n:
        c = code[i]
        c2 = code[i:i+2]
        if state == NORMAL:
            if c == '\"':
                state, last_sig = IN_DOUBLE, '\"'
                out.append(c)
                i += 1
            elif c == '\'':
                state, last_sig = IN_SINGLE, '\''
                out.append(c)
                i += 1
            elif c == '\`':
                state, last_sig = IN_TEMPLATE, '\`'
                out.append(c)
                i += 1
            elif c2 == '//':
                state = IN_LINE_COMMENT
                i += 2
            elif c2 == '/*':
                state = IN_BLOCK_COMMENT
                i += 2
            elif c == '/':
                if last_sig in '(=[!&|?:,;{}' or last_sig == '':
                    state = IN_REGEX
                out.append(c)
                i += 1
            else:
                out.append(c)
                if not c.isspace():
                    last_sig = c
                i += 1
        elif state == IN_DOUBLE:
            out.append(c)
            if c == '\\\\':
                if i + 1 < n:
                    out.append(code[i+1])
                    i += 2
                    continue
            elif c == '\"':
                state, last_sig = NORMAL, '\"'
            i += 1
        elif state == IN_SINGLE:
            out.append(c)
            if c == '\\\\':
                if i + 1 < n:
                    out.append(code[i+1])
                    i += 2
                    continue
            elif c == '\'':
                state, last_sig = NORMAL, '\''
            i += 1
        elif state == IN_TEMPLATE:
            out.append(c)
            if c == '\\\\':
                if i + 1 < n:
                    out.append(code[i+1])
                    i += 2
                    continue
            elif c == '\`':
                state, last_sig = NORMAL, '\`'
            i += 1
        elif state == IN_REGEX:
            out.append(c)
            if c == '\\\\':
                if i + 1 < n:
                    out.append(code[i+1])
                    i += 2
                    continue
            elif c == '/':
                state, last_sig = NORMAL, '/'
            i += 1
        elif state == IN_LINE_COMMENT:
            if c == '\n' or c == '\r':
                out.append(c)
                state = NORMAL
            i += 1
        elif state == IN_BLOCK_COMMENT:
            if c2 == '*/':
                state = NORMAL
                i += 2
            else:
                i += 1
    res = ''.join(out)
    clean_lines = [line for line in res.splitlines() if line.strip()]
    return '\n'.join(clean_lines)

dirs = ['$BUILD_DIR/assets', '$BUILD_DIR/assets/web']
count = 0
for d in dirs:
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith('.js') and not f.endswith('.min.js'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as fh:
                    code = fh.read()
                minified = strip_js_comments(code)
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(minified)
                count += 1
print(f'Successfully minified {count} packaged JavaScript asset files.')
"
find "$BUILD_DIR/assets" -name "*.map" -delete 2>/dev/null || true

echo "=== 4. Linking resources with Android 14 SDK (minSdk=26, targetSdk=34) ==="
$BUILD_TOOLS/aapt2 link -o "$BUILD_DIR/unaligned/app-res.apk" \
    -I "$PLATFORM" \
    --min-sdk-version 26 \
    --target-sdk-version 34 \
    --version-code 7 \
    --version-name "1.0.6" \
    --manifest "$MANIFEST" \
    -A "$BUILD_DIR/assets" \
    "$BUILD_DIR/compiled_res.zip" \
    --auto-add-overlay

echo "=== 5. Compiling native Java sources (MainActivity + FileProvider) ==="
/opt/homebrew/opt/openjdk@17/bin/javac -cp "$PLATFORM" -d "$BUILD_DIR/classes" \
    dist/android/src/main/java/com/vastrenix/app/MainActivity.java \
    dist/android/src/main/java/com/vastrenix/app/VastrenixFileProvider.java

echo "=== 6. Converting bytecode to classes.dex with d8 (min-api 26) ==="
$BUILD_TOOLS/d8 --output "$BUILD_DIR/dex/" --lib "$PLATFORM" --min-api 26 $BUILD_DIR/classes/com/vastrenix/app/*.class

echo "=== 7. Assembling Universal Single APK ==="
cp "$BUILD_DIR/unaligned/app-res.apk" "$BUILD_DIR/unaligned/app-universal.apk"
cd "$BUILD_DIR/dex" && zip -u "../unaligned/app-universal.apk" classes.dex && cd ../../..

echo "=== 8. 4-Byte ZipAligning ==="
$BUILD_TOOLS/zipalign -v -p 4 "$BUILD_DIR/unaligned/app-universal.apk" "$BUILD_DIR/app-aligned.apk"

echo "=== 9. Signing with apksigner (v2 & v3 schemes) ==="
$BUILD_TOOLS/apksigner sign --ks "$KEYSTORE_PATH" \
    --ks-pass pass:"$KEYSTORE_PASS" \
    --ks-key-alias "$KEY_ALIAS" \
    --key-pass pass:"$KEY_PASS" \
    --min-sdk-version 26 \
    --out "$OUTPUT_APK" \
    "$BUILD_DIR/app-aligned.apk"

# Copy also to root directory and universal name for easy access
cp "$OUTPUT_APK" "$ROOT_OUTPUT_APK"
cp "$OUTPUT_APK" "$DIST_DIR/vastrenix-universal.apk"

echo "=== 10. Cryptographic Signature Verification ==="
$BUILD_TOOLS/apksigner verify --verbose "$OUTPUT_APK"

echo "=== 11. Inspecting Package Manifest & Badging ==="
$BUILD_TOOLS/aapt2 dump badging "$OUTPUT_APK" | grep -E "package:|sdkVersion:|targetSdkVersion:|application-label:"

echo "=========================================================="
echo " BUILD SUCCESSFUL — Universal Release APK Ready:"
echo "=========================================================="
ls -lh "$OUTPUT_APK" "$ROOT_OUTPUT_APK"
