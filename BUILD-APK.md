# Vastrenix — APK build guide

Ye folder ek complete Android Studio project hai. Web app pehle se `app/src/main/assets/web/` me hai, kuch aur copy nahi karna.

---

## Option A — Android Studio (aapke computer par)

**Chahiye:** Android Studio (Ladybug 2024.2 ya naya) — JDK 17 isi ke saath aata hai.

1. Android Studio → **Open** → ye `Vastrenix-Android` folder select karein.
2. Pehli baar **Gradle sync** 3–10 minute lega (internet chahiye). Agar "SDK 36 missing" bole to **Install** dabayein.
3. **Test APK (debug):** menu → **Build → Build App Bundle(s) / APK(s) → Build APK(s)**
   → file milegi: `app/build/outputs/apk/debug/app-debug.apk`
4. **Release APK (Play Store / customers ke liye):** menu → **Build → Generate Signed App Bundle / APK**
   → **APK** (ya Play Store ke liye **Android App Bundle**) → **Create new…** keystore banayein →
   password yaad rakhein aur `.jks` file ka backup kahin safe (offline) rakhein → **release** → Create.
   → file milegi: `app/release/app-release.apk` (ya `.aab`)

Terminal se bhi chal sakta hai:
```bash
./gradlew assembleDebug                 # test APK
./gradlew assembleRelease bundleRelease # signed (key.properties chahiye — neeche dekhein)
```
Windows par `./gradlew` ki jagah `gradlew.bat`.

### Release signing terminal se
Is folder me `key.properties` banayein (ye file kabhi GitHub par upload na karein — `.gitignore` me already hai):
```
storeFile=C:/keys/vastrenix-upload.jks
storePassword=AAPKA_PASSWORD
keyAlias=upload
keyPassword=AAPKA_PASSWORD
```
Keystore banane ka command (sirf ek baar):
```bash
keytool -genkeypair -v -keystore vastrenix-upload.jks -alias upload -keyalg RSA -keysize 4096 -validity 10000
```
⚠️ Purana `vastrenix-release.keystore` (password `vastrenix123`) leak ho chuka hai — use mat karein.

---

## Option B — GitHub par (Android Studio ke bina)

1. github.com par **naya Private repository** banayein.
2. Is folder ka **sab kuch** upload karein (hidden `.github` folder bhi).
3. **Actions** tab → "Build APK" apne aap chalega (~8 min) → green tick → run kholein → **Artifacts** → `vastrenix-apk` download.
   Secrets ke bina ye **debug APK** banata hai (testing ke liye bilkul theek).
4. **Signed release APK** ke liye repo → Settings → Secrets and variables → Actions me ye 4 secrets daalein:
   - `KEYSTORE_BASE64` — `base64 -w0 vastrenix-upload.jks` ka output (Mac: `base64 -i vastrenix-upload.jks`)
   - `KEYSTORE_PASSWORD`, `KEY_ALIAS` (= `upload`), `KEY_PASSWORD`

---

## Har naye release se pehle
- `app/build.gradle` me `appVersionCode` +1 karein (aur `appVersionName` badlein) — warna phone update nahi lega / Play reject karega.
- Web app badla hai? Naya `www/` content `app/src/main/assets/web/` me replace karein.
- Firebase keys: `app/src/main/assets/web/js/config.js`. UPI ID: usi file me `billing.upiId`.

## Phone par install
APK WhatsApp/Drive se phone par bhejein → kholein → "Install unknown apps" allow → Install.
Debug aur release alag apps ki tarah install hote hain (`com.vastrenix.app.debug` vs `com.vastrenix.app`).

## Project details
| | |
|---|---|
| Package | `com.vastrenix.app` |
| Min Android | 8.0 (API 26) |
| Target | Android 16 (API 36) |
| Build | Gradle 8.11.1 · AGP 8.10.1 · Java 17 |
| Permissions | sirf Internet + network state |
