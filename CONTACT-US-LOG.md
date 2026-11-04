# VASTRENIX — Contact Us & Custom Work Inquiries Implementation Log

## Overview
This document records the design, implementation, form handlers, Firestore data contracts, and localization for the **Contact Us** screen in Vastrenix.

---

### 1. Two Visually Distinct Sections
The screen is accessible via **More → Help & Custom Development** (`openSub('contact')`) and is divided into two separate cards:

#### A. "Need help?" (Support & Bug Reports)
- **Target Audience:** Users facing bugs, account issues, billing questions, or general store operational queries.
- **Direct Mailto Option:**
  `mailto:contact@vastrenix.com?subject=Support%20Request%20-%20{StoreName}`
- **In-App Support Form:**
  - `Your name`: Auto-filled with `ME.name`.
  - `Business name`: Auto-filled with `storeV().name`.
  - `Category` dropdown:
    - `bug`: Bug / Something is broken
    - `billing`: Billing / Subscription
    - `account`: Account / Login issue
    - `other`: General inquiry / Other
  - `Message`: Free-text textarea for describing the issue.
  - **Submit Button:** `Send support message` (`A.sendSupportRequest`).

#### B. "Want something built for your business?" (Custom Development & Websites)
- **Target Audience:** Garment merchants wanting dedicated e-commerce web storefronts, B2B wholesale portals, bespoke barcode label templates, or customized reporting pipelines.
- **Styling:** Elevated card with distinct Vastra Violet border (`border: 1.5px solid var(--accent)`) and a `Custom Dev` pill badge.
- **Copy:**
  > *"Want a dedicated website for your store, or a custom feature added just for your business? We can build that — additional charges apply. Reach out and we'll discuss what you need."*
- **Direct Mailto Option:**
  `mailto:contact@vastrenix.com?subject=Custom%20Work%20Inquiry%20-%20{StoreName}`
- **In-App Custom Inquiry Form:**
  - `Your name`: Auto-filled with `ME.name`.
  - `Business name`: Auto-filled with `storeV().name`.
  - `Phone / WhatsApp`: Auto-filled with `storeV().phone`.
  - `What would you like built?`: Focused free-text single-line field (e.g., *"Online storefront for our Surat branch"*).
  - `Details / Specific requirements`: Textarea for timeline, budget expectations, or specific workflows.
  - **Submit Button:** `Submit inquiry` (`A.sendCustomWorkInquiry`).

---

### 2. Firestore Schema & Triage Discriminator
Both forms write to the top-level `supportRequests/{id}` collection in Firestore with explicit `type` tags:

#### Support Ticket Document:
```json
{
  "type": "support",
  "category": "bug" | "billing" | "account" | "other",
  "name": "Rajesh Patel",
  "businessId": "u0v1q4pEF3UdIhC8XL3uLLeic6l1",
  "businessName": "Patel Silks",
  "email": "owner@patelsilks.com",
  "phone": "9898012345",
  "message": "Thermal printer cuts paper before footer finishes",
  "createdAt": 1730190000000,
  "status": "open"
}
```

#### Custom Work Inquiry Document:
```json
{
  "type": "custom_work_inquiry",
  "name": "Rajesh Patel",
  "businessId": "u0v1q4pEF3UdIhC8XL3uLLeic6l1",
  "businessName": "Patel Silks",
  "email": "owner@patelsilks.com",
  "phone": "9898012345",
  "whatToBuild": "Dedicated Shopify-like online catalog for Surat retail customers",
  "message": "We have 800 saree SKUs and want customers to browse online and order for store pickup",
  "createdAt": 1730190000000,
  "status": "open"
}
```

---

### 3. Localization Coverage
Both sections and all form labels, placeholders, buttons, and alert messages are fully localized in:
1. **English (Default)**
2. **हिन्दी (Hindi)**: *"मदद चाहिए?"* / *"अपने व्यापार के लिए कुछ खास बनवाना चाहते हैं?"*
3. **ગુજરાતી (Gujarati)**: *"મદદ જોઈએ છે?"* / *"તમારા વેપાર માટે કંઈક ખાસ બનાવવું છે?"*

---

### 4. Firestore Security Rules
```javascript
match /supportRequests/{id} {
  allow create: if signedIn();
  allow read: if signedIn() && (resource.data.businessId == request.auth.uid || resource.data.email == request.auth.token.email);
  allow update, delete: if false;
}
```
Users can create tickets and read only their own tickets. External update or deletion is disallowed to prevent record tampering.
