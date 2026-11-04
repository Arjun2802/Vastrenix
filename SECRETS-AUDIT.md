# VASTRENIX — SECRETS & CLIENT BUNDLE SECURITY AUDIT
**Date:** October 31, 2026  
**Auditor:** Senior Android & Security Engineering Pair  
**Target:** Vastrenix Hybrid Android Release APK (`vastrenix-release.apk`, `dist/android/vastrenix-release.apk`) & Web Bundle (`www/`)  
**Audit Verdict:** **PASS (CLEAN)** — Zero private secrets or admin credentials exposed.

---

## 1. Executive Summary

An exhaustive security and credential audit was conducted on the client-bundled web assets (`www/`), the Android application source (`dist/android/`), and the unzipped production release APK (`dist/android/vastrenix-release.apk`).

Because an Android APK is an unencrypted zip archive that any third party can decompile and read, client bundles must never contain administrative credentials, private API keys, payment webhook secrets, or unauthenticated backdoors.

| Audit Category | Scope Checked | Result | Status |
| :--- | :--- | :--- | :--- |
| **Razorpay Private Keys** | `RAZORPAY_KEY_SECRET`, `WEBHOOK_SECRET` | 0 occurrences in client bundle | **PASS** |
| **Firebase Admin Credentials** | `FIREBASE_SERVICE_ACCOUNT_JSON`, Private Keys | 0 occurrences in APK or Git | **PASS** |
| **Firebase Client Config** | `apiKey`, `authDomain`, `projectId`, `appId` | Present in `config.js` (by design) | **PASS (SECURED BY RULES)** |
| **Keystores & Signing Keys** | `*.keystore`, `*.jks`, `key.properties` | Excluded from git & bundle | **PASS** |
| **Debug & Test Credentials** | Passwords, demo auth tokens, internal endpoints | 0 live credentials exposed | **PASS** |
| **Non-Asset Build Artifacts** | `.env`, `.git`, `.DS_Store`, `*.map`, test files | Stripped from packaged APK | **PASS** |

---

## 2. Detailed Findings by Category

### 2.1 Razorpay Payment Credentials
* **Requirement:** Only public client keys (`RAZORPAY_KEY_ID`) may exist client-side for opening the standard Razorpay checkout modal. The secret key (`RAZORPAY_KEY_SECRET`) and webhook signature secret (`RAZORPAY_WEBHOOK_SECRET`) must never touch the client.
* **Findings:**
  - `grep -rEi "rzp_test_secret|rzp_live_secret|KEY_SECRET|WEBHOOK_SECRET" www/` returned zero matches.
  - Inspection of the unzipped APK confirmed no references to payment secrets.
  - Only the public `RAZORPAY_KEY_ID` is used in client scripts to initialize `new Razorpay(options)`. Signature verification and plan webhook processing are handled strictly on the backend.

### 2.2 Firebase Service Account & Admin SDK
* **Requirement:** The Google Cloud / Firebase Admin service account JSON (`firebase-service-account.json`) grants complete administrative bypass over all Firestore and Storage collections. It must strictly reside on trusted backend servers (Render worker, Cloud Functions).
* **Findings:**
  - Automated search across `www/`, `dist/android/assets/`, and the unzipped APK root returned zero matches for private key JSON files.
  - Git commit history was queried across all revisions: `git log --all --full-history -- "*service-account*.json"` returned zero commits.
  - Project `.gitignore` explicitly blocks `*service-account*.json` and `firebase-service-account.json`.

### 2.3 Firebase Client Web Configuration
* **Location:** `www/js/config.js` and `assets/google-services.json`.
* **Nature of Credentials:**
  - `apiKey: "AIzaSy..."`
  - `authDomain: "vastrenix-boutique.firebaseapp.com"`
  - `projectId: "vastrenix-boutique"`
  - `storageBucket: "vastrenix-boutique.appspot.com"`
* **Risk Assessment:** **EXPECTED & SAFE.**
  - Google Firebase architecture is designed such that client SDK configuration keys are public identifiers used by the Firebase Web SDK to locate the cloud project.
  - Client API keys do not grant access to Firestore data. Access control is enforced exclusively by server-side Cloud Firestore Security Rules (`firestore.rules`).
* **Tenant Isolation Verification (`firestore.rules`):**
  - Multi-tenant data partition under `/stores/{sid}` requires `request.auth != null`.
  - Store read access is strictly locked to `isOwner()` (`request.auth.uid == sid`) or active staff members registered under `/stores/{sid}/staff/{uid}`.
  - Store write operations require `canWrite()`, which verifies active staff role (auditors blocked) and validates that the subscription is active or within trial (`!isTrialExpired()`).
  - Cross-tenant data leakage is structurally impossible at the database level even if a malicious actor reads the client Firebase configuration.

### 2.4 Signing Keystore & Environment Files
* **Files:** `dist/android/vastrenix-release.keystore`, `key.properties`, `.env`.
* **Findings:**
  - Both `*.keystore`, `*.jks`, and `key.properties` are explicitly ignored by `.gitignore`.
  - Git status and commit history show no repository tracking for release keystores or password properties files.
  - Keystore is retained strictly on local release build runners.

### 2.5 Build Artifact & Source Map Hygiene
* **APK Asset Directory Inspection:**
  - All source maps (`*.js.map`, `*.css.map`) are automatically pruned during the build packaging stage via `find "$BUILD_DIR/assets" -name "*.map" -delete`.
  - Hidden OS metadata (`.DS_Store`, `Thumbs.db`) and version control files (`.git`, `.gitignore`) are excluded by `aapt2` asset packaging filters.
  - Bundled assets inside `dist/android/vastrenix-release.apk` contain only the production web runtime: HTML, CSS, minified JS, and standard image assets.

---

## 3. Conclusion & Recommendations
The Vastrenix client application and packaged Android release APK adhere to strict secret isolation standards. All sensitive operations (payment verification, queue workers, admin operations) remain decoupled on authenticated cloud services. The APK is safe for public distribution on the Google Play Store.
