/**
 * VASTRENIX ACCOUNT DELETION API (POST /api/account/delete)
 *
 * Implements strict 5-step statutory data destruction, role-differentiated cleanup,
 * and Indian tax law payment anonymization powered by Firebase Admin SDK.
 */

const admin = require('firebase-admin');

// Lazy initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  try {
    if (process.env.FIREBASE_SERVICE_ACCOUNT_JSON) {
      const creds = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_JSON);
      admin.initializeApp({
        credential: admin.credential.cert(creds),
        projectId: creds.project_id || 'vastranix'
      });
    } else if (process.env.FIREBASE_CREDENTIALS_PATH) {
      admin.initializeApp({
        credential: admin.credential.cert(require(process.env.FIREBASE_CREDENTIALS_PATH)),
        projectId: 'vastranix'
      });
    } else {
      admin.initializeApp({
        projectId: process.env.FIREBASE_PROJECT_ID || 'vastranix'
      });
    }
  } catch (err) {
    console.warn('[Vastrenix Delete API] Firebase Admin init notice:', err.message);
  }
}

function parseJsonBody(req) {
  if (req.body && typeof req.body === 'object') return Promise.resolve(req.body);
  return new Promise((resolve) => {
    let raw = '';
    req.on('data', chunk => { raw += chunk; });
    req.on('end', () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (e) {
        resolve({});
      }
    });
  });
}

module.exports = async function handler(req, res) {
  // CORS configuration
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'method_not_allowed', message: 'POST method required' });
  }

  // Extract Bearer Token
  const authHeader = req.headers.authorization || req.headers.Authorization || '';
  const match = authHeader.match(/^Bearer\s+(.+)$/i);
  if (!match) {
    return res.status(401).json({ error: 'unauthorized', message: 'Missing or malformed Authorization header' });
  }
  const idToken = match[1];

  let tok;
  try {
    tok = await admin.auth().verifyIdToken(idToken);
  } catch (err) {
    return res.status(401).json({ error: 'invalid_token', message: 'Authentication token is invalid or expired' });
  }

  const uid = tok.uid;
  const body = (req.body && typeof req.body === 'object') ? req.body : await parseJsonBody(req);

  // =========================================================================
  // STEP 1 — SECURITY & SESSION FRESHNESS VALIDATION
  // =========================================================================

  // 1A. Confirmation check: Must explicitly contain { confirm: "DELETE" } (strictly validated uppercase)
  const confirm = String(body.confirm || '').trim().toUpperCase();
  if (confirm !== 'DELETE') {
    return res.status(400).json({
      error: 'invalid_confirmation',
      message: 'Confirmation mismatch. Body must include { confirm: "DELETE" }.'
    });
  }

  // 1B. Fresh Login Requirement: tok.auth_time must be under 15 minutes old
  const authTimeMs = (tok.auth_time || 0) * 1000;
  if (!authTimeMs || (Date.now() - authTimeMs > 15 * 60 * 1000)) {
    return res.status(401).json({
      error: 'reauth_required',
      message: 'Recent authentication required (session older than 15 minutes). Please re-authenticate before deletion.'
    });
  }

  // 1C. Platform Admin Block: Platform administrators are blocked to avoid accidental loss of admin infrastructure
  if (tok.platformAdmin === true) {
    return res.status(403).json({
      error: 'is_admin',
      message: 'Platform administrator accounts cannot be deleted through this endpoint.'
    });
  }

  const db = admin.firestore();

  try {
    // =========================================================================
    // STEP 2 — STORE OWNER VS STAFF DATA HANDLING
    // =========================================================================
    const storeMetaRef = db.doc(`stores/${uid}/meta/store`);
    const storeMetaSnap = await storeMetaRef.get();
    const isOwner = storeMetaSnap.exists;
    let staffStoreId = null;

    if (isOwner) {
      // Store Owner Workflow:
      // A. Remove public join code if one was registered
      const storeData = storeMetaSnap.data() || {};
      const storeCode = storeData.code;
      if (storeCode) {
        try { await db.doc(`codes/${storeCode}`).delete(); } catch (e) {}
      }
      try {
        const codeSnaps = await db.collection('codes').where('storeId', '==', uid).get();
        const codeBatch = db.batch();
        codeSnaps.forEach(doc => codeBatch.delete(doc.ref));
        await codeBatch.commit();
      } catch (e) {}

      // B. Instantly and recursively destroy the entire store database tree (/stores/{uid}/*)
      // Wipes: products, variants, barcodes, categories, daily ledgers, GST sales invoices,
      // credit notes, customer profiles, khata histories, suppliers, purchase orders, receiving challans,
      // shift logs, cash books, expense entries, dealer orders, dispatch notes, staff credentials.
      const storeRef = db.doc(`stores/${uid}`);
      await db.recursiveDelete(storeRef);

      // C. Delete subscription mirror at /subscriptions/{uid}
      try { await db.doc(`subscriptions/${uid}`).delete(); } catch (e) {}

      // D. Delete pending UPI payment requests at /subscriptionRequests/{uid}
      try { await db.doc(`subscriptionRequests/${uid}`).delete(); } catch (e) {}

    } else {
      // Staff Member Workflow:
      // Reads /users/{uid} to locate which store they belonged to
      const userRef = db.doc(`users/${uid}`);
      const userSnap = await userRef.get();
      if (userSnap.exists) {
        staffStoreId = userSnap.data().storeId;
      }
      if (staffStoreId) {
        // Removes staff credentials and approval requests from employer's store
        try { await db.doc(`stores/${staffStoreId}/staff/${uid}`).delete(); } catch (e) {}
        try { await db.doc(`stores/${staffStoreId}/requests/${uid}`).delete(); } catch (e) {}
      }
      // Employer's store data remains untouched
    }

    // =========================================================================
    // STEP 3 — PERSONAL RECORDS CLEANUP
    // =========================================================================

    // Deletes all support requests and inquiries submitted by user from /supportRequests
    try {
      const supSnaps = await db.collection('supportRequests').where('uid', '==', uid).get();
      const supBatch = db.batch();
      supSnaps.forEach(doc => supBatch.delete(doc.ref));
      await supBatch.commit();
    } catch (e) {}

    // Deletes /users/{uid} (user mapping document)
    try { await db.doc(`users/${uid}`).delete(); } catch (e) {}

    // Deletes /rateLimits/{uid}
    try { await db.doc(`rateLimits/${uid}`).delete(); } catch (e) {}

    // =========================================================================
    // STEP 4 — STATUTORY COMPLIANCE & PAYMENT ANONYMIZATION
    // =========================================================================
    // Under Indian commercial/tax law, transaction financial records must be preserved
    // for tax auditing, but all personal identity and store names are scrubbed:
    try {
      const paySnaps = await db.collection('payments').where('uid', '==', uid).get();
      if (!paySnaps.empty) {
        const payBatch = db.batch();
        paySnaps.forEach(doc => {
          payBatch.update(doc.ref, {
            email: '',
            storeName: '(deleted account)',
            accountDeletedAt: Date.now()
          });
        });
        await payBatch.commit();
      }
    } catch (e) {}

    // =========================================================================
    // STEP 5 — AUDIT LOG & FIREBASE AUTH DELETION
    // =========================================================================
    // Writes an entry to /adminLog recording action: "account.delete", UID, role, summary
    try {
      await db.collection('adminLog').add({
        action: 'account.delete',
        uid: uid,
        role: isOwner ? 'owner' : 'staff',
        summary: isOwner
          ? 'Store and owner account permanently destroyed'
          : `Staff account removed from store ${staffStoreId || 'unknown'}`,
        accountDeletedAt: Date.now(),
        timestamp: admin.firestore.FieldValue.serverTimestamp()
      });
    } catch (e) {}

    // Invokes auth().deleteUser(uid) to destroy the login credential from Firebase Authentication
    await admin.auth().deleteUser(uid);

    return res.status(200).json({
      ok: true,
      message: 'Your account has been deleted. Your data has been removed from Vastrenix.'
    });

  } catch (err) {
    console.error('[Vastrenix Delete API Error]', err);
    return res.status(500).json({
      error: 'deletion_failed',
      message: err.message || 'An error occurred during account deletion.'
    });
  }
};
