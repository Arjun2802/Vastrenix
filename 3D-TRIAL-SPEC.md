# VASTRENIX — 3D Fabric Drape Feature: Parameter & Trial-Limit Specification

## Overview
This specification details the architecture, data contracts, limit enforcement, and scaffolding for the upcoming **3D Fabric Drape Preview** pipeline.

No 3D viewport engine (Three.js) or cloud GPU rendering pipeline is built in this pass; this document establishes the exact data shape and implements the limit-counting scaffolding so future pipeline integration requires zero architectural rework.

---

### 1. Subscription & Policy Confirmation
- **Trial Allowance:** 3 generations (`trialThreeDLimit: 3`), stored as mutable data on the subscription document (`subscriptions/{businessId}.trialThreeDLimit`).
- **Active Paid Subscriber Allowance:** **Unlimited**. Once a merchant subscribes to an active paid plan (Monthly ₹799 or Annual ₹7,999), 3D preview generations are unrestricted.
- **Expired State:** Blocked. Merchants who have exhausted their 7-day trial without subscribing cannot generate new 3D previews until they subscribe.

---

### 2. Future 3D Request Data Contract
When the client initiates a 3D drape generation, the request payload will carry:

```typescript
interface ThreeDGenerationRequest {
  id: string;                       // Unique generation ID (e.g., '3d_abc123')
  businessId: string;               // Store/Business ID (matches request.auth.uid or store ID)
  productId?: string;               // Optional catalog product this preview links to
  variantId?: string;               // Optional variant ID
  garmentTemplateId: GarmentTemplateType; // Base 3D model shape
  fabricPhotoUrl: string;           // URL of source fabric photo uploaded to Firebase Storage
  fabricScale?: number;             // Repeat scale factor for texture mapping (default: 1.0)
  normalMapStrength?: number;       // Bump / weave depth multiplier (0.0 – 2.0)
  requestedAt: number;              // Epoch timestamp (ms)
  completedAt?: number;             // Populated upon completion
  status: "queued" | "processing" | "complete" | "failed";
  errorMessage?: string;            // Populated if processing fails
  resultGlbUrl?: string;            // Cloud Storage URL to the draped .glb 3D mesh
  resultPreviewImageUrls?: {        // Multi-angle rendered 2D previews
    front: string;
    back: string;
    detail: string;
  };
}

type GarmentTemplateType = 
  | "kurta_straight"    // Women's straight-cut kurta
  | "kurta_aline"       // Women's A-line flared kurti
  | "saree_classic"     // 6-yard saree with draped pallu
  | "saree_lehenga"     // Lehenga choli with dupatta
  | "shirt_mens_formal" // Men's full-sleeve collared shirt
  | "shirt_mens_casual" // Men's half-sleeve linen shirt
  | "bottom_palazzo";   // Flared palazzo / salwar
```

---

### 3. Client Scaffolding & Limit-Check Engine
Implemented in `www/js/core.js` as `window.checkAndConsume3DAllowance`:

```javascript
window.checkAndConsume3DAllowance = async function (businessId, reqData) {
  var sid = businessId || (storeV() && storeV().id) || ME.id;
  var sub = subState();

  // 1. Check expired state
  if (sub.isExpired) {
    return {
      allowed: false,
      reason: 'trial_ended',
      message: t('threed_trial_ended', 'Your free trial has ended — subscribe to continue using 3D fabric previews.')
    };
  }

  // 2. Check 7-Day Trial state
  if (sub.isTrial || sub.status === 'trialing') {
    if (sub.trialThreeDUsed >= sub.trialThreeDLimit) {
      return {
        allowed: false,
        reason: 'trial_limit_reached',
        used: sub.trialThreeDUsed,
        limit: sub.trialThreeDLimit,
        message: t('threed_trial_limit', "You've used all {limit} free 3D previews during your trial — subscribe to continue using this feature.", { limit: sub.trialThreeDLimit })
      };
    }

    // Increment trial counter
    var newCount = sub.trialThreeDUsed + 1;
    var now = Date.now();
    var patchObj = { trialThreeDUsed: newCount, updatedAt: now };
    
    await patch('meta/subscription', patchObj);
    if (window.FS && sid) {
      await window.FS.doc('subscriptions/' + sid).set(patchObj, { merge: true });
    }
    if (D.subscription) {
      D.subscription.trialThreeDUsed = newCount;
    }

    return {
      allowed: true,
      unlimited: false,
      used: newCount,
      limit: sub.trialThreeDLimit,
      remaining: Math.max(0, sub.trialThreeDLimit - newCount),
      message: t('threed_success', '3D preview generation initiated. ({rem} free previews left)', { rem: Math.max(0, sub.trialThreeDLimit - newCount) })
    };
  }

  // 3. Active Paid Subscriber State
  if (sub.isActive || sub.status === 'active') {
    return {
      allowed: true,
      unlimited: true,
      message: t('threed_unlimited', '3D preview generation initiated (unlimited plan).')
    };
  }

  return {
    allowed: false,
    reason: 'no_subscription',
    message: t('threed_no_sub', 'Please subscribe to use 3D fabric previews.')
  };
};
```

---

### 4. Verification Test Results
Tested and verified via automated test suite in JavaScriptCore:
1. **Call 1 (Trial, Used = 0):** `allowed: true`, `used: 1`, `remaining: 2`. Counter persisted.
2. **Call 2 (Trial, Used = 1):** `allowed: true`, `used: 2`, `remaining: 1`. Counter persisted.
3. **Call 3 (Trial, Used = 2):** `allowed: true`, `used: 3`, `remaining: 0`. Counter persisted.
4. **Call 4 (Trial, Used = 3):** `allowed: false`, `reason: "trial_limit_reached"`. Message: *"You've used all 3 free 3D previews during your trial — subscribe to continue using this feature."*
5. **Call 5 (Active Paid Subscription):** `allowed: true`, `unlimited: true`. Bypasses counter and runs without restriction.

---

### 5. UI Scaffolding & User Notice
In `www/js/network.js`, a dedicated subscreen `subThreeD` (`openSub('threed')`) and a tile in `vMore()` provide a transparent roadmap notice:
- Displays **"Coming soon — 3D fabric preview"** with a `Coming soon` pill.
- Renders template cards for Kurta, Saree, and Shirt.
- Accurately displays the merchant's current allowance status:
  - Trial: *"Trial Allowance: {used} of 3 used"*
  - Paid: *"Unlimited 3D fabric drape previews active on your subscription"*
  - Expired: *"Your trial has ended. Subscribe to unlock unlimited 3D fabric previews."*
- Explicitly clarifies that the cloud processing pipeline is under development; no dummy file upload buttons are presented that could mislead the user.
