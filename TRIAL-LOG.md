# VASTRENIX — 7-Day Free Trial Implementation Log

## Overview
This document records the implementation, data model, lifecycle transitions, and verification of the **7-Day Free Trial** for new business signups in Vastrenix.

---

### 1. Firestore Schema & Extension
Subscription records are stored at `subscriptions/{businessId}` (as well as mirrored to `meta/subscription` within the store's document namespace for real-time reactivity):

```typescript
interface SubscriptionDocument {
  businessId: string;               // Owner UID / Store ID
  status: "trialing" | "active" | "past_due" | "cancelled";
  trialStartedAt: number;           // Epoch timestamp (ms) when store setup completed
  trialEndsAt: number;              // trialStartedAt + (7 * 24 * 60 * 60 * 1000)
  trialThreeDUsed: number;          // Counter of 3D fabric previews generated during trial
  trialThreeDLimit: number;         // Configurable allowance (default: 3)
  cycleId: "monthly" | "annual" | null; // Set when paid subscription starts
  subscribedAt?: number;            // Timestamp when paid subscription began
  expiresAt?: number;               // Timestamp when current billing cycle ends
  gstin?: string;                   // Store GSTIN tied to trial creation
  createdAt: number;
  updatedAt: number;
}
```

---

### 2. Creation on New Business Signup Only
- **Trigger:** In `A.obNext` (`www/js/shell.js`), when the store owner completes the 5-step onboarding wizard.
- **Single-Trigger Guarantee:**
  - Before writing, `await fresh('meta/subscription')` is checked.
  - If a subscription document already exists for this store/owner, it is preserved and not overwritten.
  - Staff users signing up with a store code join via `gateJoin()` (`A.joinStore`) and never trigger trial creation.
  - **Loophole Protection & Limitation:** The trial is bound to the owner's Firebase Auth account (`request.auth.uid`), the store ID, and the registered GSTIN. If a user registers with a completely fresh throwaway email and a new phone, a new store is created; this is documented as an inherent architectural limitation of client-side auth without third-party PAN/GST verification APIs.

---

### 3. Feature Access During Trial
- **Full Capabilities:** Same as an active paid subscriber:
  - POS checkout & billing in all payment modes (Cash, UPI, Card, Split, Credit).
  - Multi-location stock (Shop Floor + Godown) & stock transfers.
  - Customer Khata (Udhaar) ledger & WhatsApp invoices.
  - Custom Store Logo uploads & 5 invoice visual themes.
  - Purchase Orders, Dealer Orders, Petty Expenses, and Day-Close Shifts.
- **The One Capped Feature:** 3D Fabric Drape Previews are limited to **3 generations** (`trialThreeDLimit: 3`) during the trial period.

---

### 4. Countdown UI
- **Dashboard Countdown Banner:**
  - Rendered at the top of the Home screen if `sub.isTrial && !sub.isExpired`.
  - Copy: `Free trial — {n} days left · Subscribe`
  - Calm visual styling: Light indigo/blue tint (`#EEF2FF`, `#3730A3`), non-alarmist clock icon.
  - Dismissible per session with an `×` close icon (`A.dismissTrialBanner`). Reappears on the next fresh app launch until subscribed or expired.
- **More Section Status Card:**
  - Displays `7-Day Free Trial` badge, remaining days countdown, and `3 free 3D previews included ({used}/3 used)`.
  - Direct "Subscribe" button to open the billing modal.

---

### 5. Day 7 Expiry Behavior (Write-Block)
When `Date.now() > trialEndsAt` without an active subscription:
- **Read Access Preserved:** The owner and team can view all existing bills, products, customers, transactions, reports, and invoices.
- **Write Access Blocked:**
  - **New Bill (`vBill`):** Displays a friendly paywall card explaining the 7-day trial has concluded with a direct "View plans & Subscribe" button.
  - **Checkout (`A.checkout`):** Blocks checkout and prompts the subscription modal.
  - **Add Garment (`A.newProduct`, `A.saveProduct`):** Blocks new garment creation.
  - **Purchase Orders & Dealer Orders:** Write-blocked with a friendly upgrade toast.
  - **Dashboard:** Replaces the countdown banner with an expired notification: *"Your free trial has ended — subscribe to continue."*

---

### 6. Mid-Trial Subscription Transition
- If the owner subscribes on Day 1, 3, or 6 of their trial:
  - `A.doSubscribe` executes immediately.
  - The subscription document updates to:
    - `status: "active"`
    - `cycleId: "monthly" | "annual"`
    - `subscribedAt: now`
    - `expiresAt: now + (cycleId === 'annual' ? 365 days : 30 days)`
  - The trial ends immediately and the paid billing cycle starts from that exact moment without waiting for the remaining trial days.
  - Unlimited 3D fabric drape previews are instantly unlocked.

---

### 7. Security Rules (`firestore.rules`)
Enforced at the database level so direct API tampering cannot bypass the UI:
```javascript
function subDoc() { return /databases/$(database)/documents/stores/$(sid)/meta/subscription; }
function isTrialExpired() {
  return exists(subDoc()) &&
         get(subDoc()).data.status == 'trialing' &&
         request.time.toMillis() > get(subDoc()).data.trialEndsAt;
}
function canWrite() {
  return (isOwner() || (isStaff() && role() != 'auditor')) && !isTrialExpired();
}
```
All read operations remain allowed (`allow read: if isOwner() || isStaff();`), while write operations fail with `permission-denied` once the trial expires.
