# Vastrenix

POS billing, garment stock, invoices, dues, dealer orders and staff for Indian clothing stores.
One codebase runs as an **Android app (APK)**, a **website**, or fully **offline on one device**.

---

## Folder guide

| Path | What it is |
|---|---|
| `www/` | The complete app (HTML, CSS, JavaScript). This is what goes inside the APK. |
| `www/js/config.js` | **Your Firebase keys go here.** Empty = offline, device-only mode. |
| `www/js/*.js` | App code: `core` (data layer, rendering), `billing`, `stock`, `money`, `network` (dealers, staff, settings), `i18n` (Hindi/Gujarati), `platform` (Firebase login, Android features). |
| `firestore.rules` | Server-side security: store isolation, staff approval, roles. |
| `capacitor.config.json` | Android app id/name (`com.vastrenix.app`). |
| `.github/workflows/android.yml` | Builds the APK automatically on GitHub. |
| `assets/` | App icon and splash screen source images. |

---

## Step 1 — Firebase setup (10 minutes, one time)

Without this the app still works, but only on one phone with no team sync.

1. Go to <https://console.firebase.google.com> → **Add project** → name it `vastrenix`.
2. **Build → Authentication → Get started → Email/Password → Enable**.
3. **Build → Firestore Database → Create database** → choose region **asia-south1 (Mumbai)** → *Production mode*.
4. Firestore → **Rules** tab → delete everything → paste the full contents of `firestore.rules` → **Publish**.
5. **Project settings (gear icon) → Your apps → Web (`</>`)** → register app → copy the `firebaseConfig` values.
6. Open `www/js/config.js` and fill in `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`.

> Firebase web API keys are safe to ship inside the app — access is controlled by `firestore.rules`, not by hiding the key.

---

## Step 2 — Get the APK

### Option A: GitHub builds it for you (no Android Studio needed)

1. Create a free account at <https://github.com> → **New repository** → name `vastrenix` → *Private* → Create.
2. On the empty repo page click **uploading an existing file** → drag in **everything inside this `vastrenix` folder**
   (including the hidden `.github` folder — on Windows/Mac enable "show hidden files" first) → **Commit changes**.
3. Open the **Actions** tab. The *Build Android APK* run starts by itself (about 6–8 minutes).
4. When it shows a green tick, open the run → **Artifacts** → download **vastrenix-apk** → unzip → `app-debug.apk`.
5. Send the APK to your phone (WhatsApp/Drive) → open it → allow *Install unknown apps* → Install.

Every time you change something and commit, a fresh APK is built.

### Option B: Build on your computer with Android Studio

Needs: Node.js 20+, Android Studio (Hedgehog or newer), JDK 17.

```bash
npm install
npm run vendor            # copies Firebase/QR/PDF libraries into www/vendor
npx cap add android       # first time only
npm run android:icons     # app icon + splash
npx cap sync android
npx cap open android      # opens Android Studio
```

In Android Studio: **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
APK appears at `android/app/build/outputs/apk/debug/app-debug.apk`.

### Signed release APK / Play Store

Android Studio → **Build → Generate Signed Bundle / APK** → create a keystore (keep it safe — you need the same one for every update).
For automatic signed builds on GitHub, add these repository secrets (**Settings → Secrets and variables → Actions**):
`KEYSTORE_BASE64` (output of `base64 -w0 release.jks`), `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD`.
The workflow then also produces a signed release APK. For the Play Store, upload an **AAB** (`./gradlew bundleRelease`).

---

## Step 3 — First run

1. Open the app → **New here? Create account** → enter your name, email, password.
2. Choose **I own a store → Create a new store** → finish the 5-step setup (business, GST, invoice look, payments, team).
   Turn on **Start with demo data** to try every screen; remove it later in **Settings → Data**.
3. Your **store code** (e.g. `VX-ODF-AB12`) is shown in **More → Account** and **Dealers → Network**.

**Adding staff:** they install the same APK → create an account → **I work at a store** → enter your store code →
their request appears in **Staff** → choose a role → **Approve**. Roles: Admin, Branch manager, Cashier, Inventory manager,
Purchase manager, Accountant, Dispatcher, Auditor (read-only, enforced by the server).

---

## Run as a website (optional)

```bash
npm run serve             # http://localhost:8080
```

Or host it free on Firebase: `npm i -g firebase-tools && firebase login && firebase use --add && firebase deploy`
(this also publishes `firestore.rules`).

---

## How the data stays safe

- **Stock-safe billing:** every sale takes a short lock on the store, re-reads the latest stock and only then saves —
  two counters can never sell the same last piece, and invoice numbers never repeat or skip.
- **Posted invoices are locked.** Returns go through credit notes, which restore stock and adjust credit.
- **Offline cache:** Firestore keeps a local copy, so screens open instantly and survive brief network drops.
  Billing itself needs a connection so the stock check is real.
- **Tenant isolation:** each store's data lives under its owner's account; the rules stop anyone else reading it.

## Customising

- Brand colours: top of `www/css/app.css` (`--accent`, `--hero`, …).
- Invoice layouts: `renderInvoiceEn()` in `www/js/money.js` (one renderer for preview, thumbnails and PDF).
- Translations: `www/js/i18n.js` — every English string has a key; add or edit Hindi (`hi`) and Gujarati (`gu`).
- App id / name: `capacitor.config.json` (change **before** the first `npx cap add android`).

## Known limits

- Barcode scanning works with USB/Bluetooth scanners (they type the code). Camera scanning can be added with a Capacitor barcode plugin.
- No direct printing to thermal printers yet — use **PDF → Share → printer app**, or the Compact Thermal theme with a print app.
