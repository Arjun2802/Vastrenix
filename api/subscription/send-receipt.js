/**
 * VASTRENIX SUBSCRIPTION RECEIPT EMAIL API (POST /api/subscription/send-receipt)
 *
 * Dispatches an official confirmation and receipt email to the store owner upon
 * purchasing or submitting a Vastrenix subscription plan.
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
    console.warn('[Vastrenix Receipt API] Firebase Admin init notice:', err.message);
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

function formatInr(val) {
  const n = Math.round(+val || 0);
  return '₹' + n.toLocaleString('en-IN');
}

// Restrict CORS to authorized Vastrenix domains
const ALLOWED_ORIGINS = [
  'https://vastrenix.com',
  'https://www.vastrenix.com',
  'https://vastranix.web.app',
  'https://vastranix.firebaseapp.com',
  'https://appassets.androidplatform.net',
  'http://localhost:8080',
  'http://localhost:3000'
];

function applyCors(req, res) {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  } else if (!origin) {
    res.setHeader('Access-Control-Allow-Origin', 'https://vastrenix.com');
  } else {
    res.setHeader('Access-Control-Allow-Origin', 'https://vastrenix.com');
  }
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Vary', 'Origin');
}

// In-memory rate limiting (max 10 receipt requests per 15 min per IP / UID)
const rateMap = new Map();
const RATE_WINDOW_MS = 15 * 60 * 1000;
const MAX_REQUESTS = 10;

function isRateLimited(key) {
  const now = Date.now();
  const history = rateMap.get(key) || [];
  const valid = history.filter(ts => now - ts < RATE_WINDOW_MS);
  if (valid.length >= MAX_REQUESTS) {
    return true;
  }
  valid.push(now);
  rateMap.set(key, valid);
  if (rateMap.size > 2000) {
    for (const [k, v] of rateMap.entries()) {
      if (!v.some(ts => now - ts < RATE_WINDOW_MS)) rateMap.delete(k);
    }
  }
  return false;
}

function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) {
    return String(forwarded).split(',')[0].trim();
  }
  return (req.socket && req.socket.remoteAddress) || 'unknown';
}

module.exports = async function handler(req, res) {
  applyCors(req, res);

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'method_not_allowed', message: 'POST method required' });
  }

  // Rate limit by IP
  const clientIp = getClientIp(req);
  if (isRateLimited('ip:' + clientIp)) {
    return res.status(429).json({ error: 'too_many_requests', message: 'Rate limit exceeded. Please wait a few minutes before trying again.' });
  }

  // 1. Verify Bearer Token
  const authHeader = req.headers.authorization || req.headers.Authorization || '';
  const match = authHeader.match(/^Bearer\s+(.+)$/i);
  if (!match) {
    return res.status(401).json({ error: 'unauthorized', message: 'Missing Authorization header' });
  }
  const idToken = match[1];

  let tok;
  try {
    tok = await admin.auth().verifyIdToken(idToken);
  } catch (err) {
    return res.status(401).json({ error: 'invalid_token', message: 'Authentication token is invalid or expired' });
  }

  const uid = tok.uid;
  if (isRateLimited('uid:' + uid)) {
    return res.status(429).json({ error: 'too_many_requests', message: 'Too many receipt requests for this account. Please wait a few minutes.' });
  }

  const body = (req.body && typeof req.body === 'object') ? req.body : await parseJsonBody(req);

  // Strictly bind recipient to authenticated user's email to prevent open relay abuse
  const userEmail = tok.email;
  if (!userEmail) {
    return res.status(400).json({ error: 'missing_email', message: 'Authenticated user email not found in token' });
  }

  const storeName = String(body.storeName || 'Your Store').slice(0, 120);
  const storeCode = String(body.storeCode || '').slice(0, 40);
  const planTitle = String(body.plan || 'Standard Plan').slice(0, 80);
  const amount = +body.amount || 0;
  const paymentId = String(body.paymentId || body.utr || '').slice(0, 80);
  const isPending = body.status === 'pending' || body.method === 'upi';
  const expiresAt = body.expiresAt ? new Date(body.expiresAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : null;

  const subject = isPending
    ? `Vastrenix Subscription Request Received — ${planTitle} (Ref: ${paymentId})`
    : `Vastrenix Subscription Confirmed — ${planTitle} Active`;

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0B0B0F; color: #F0EFF6; margin: 0; padding: 24px; }
    .card { max-width: 580px; margin: 0 auto; background: #15151B; border: 1px solid #25252E; border-radius: 16px; padding: 32px 24px; }
    .brand { text-align: center; margin-bottom: 24px; }
    .brand h1 { color: #7A63FF; font-size: 28px; margin: 0; letter-spacing: -0.04em; }
    .brand p { color: #8E8D9A; font-size: 13px; margin: 4px 0 0; }
    .title { font-size: 20px; font-weight: 700; color: ${isPending ? '#F5A623' : '#5BE3A6'}; margin-bottom: 12px; }
    .desc { font-size: 14.5px; line-height: 1.6; color: #F0EFF6; margin-bottom: 20px; }
    .table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }
    .table td { padding: 10px 12px; border-bottom: 1px solid #25252E; }
    .table .label { color: #8E8D9A; width: 40%; }
    .table .val { font-weight: 600; text-align: right; color: #F0EFF6; }
    .pill { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
    .pill-active { background: rgba(91, 227, 166, 0.15); color: #5BE3A6; border: 1px solid rgba(91, 227, 166, 0.3); }
    .pill-pending { background: rgba(245, 166, 35, 0.15); color: #F5A623; border: 1px solid rgba(245, 166, 35, 0.3); }
    .features-box { background: #1D1D25; border: 1px solid #25252E; border-radius: 12px; padding: 16px; margin: 24px 0; }
    .features-box b { color: #7A63FF; font-size: 13px; display: block; margin-bottom: 8px; }
    .features-box ul { margin: 0; padding-left: 20px; font-size: 13px; color: #8E8D9A; line-height: 1.6; }
    .footer { text-align: center; margin-top: 32px; font-size: 12px; color: #8E8D9A; border-top: 1px solid #25252E; padding-top: 20px; }
    .footer a { color: #7A63FF; text-decoration: none; }
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">
      <h1>vastrenix</h1>
      <p>Billing, Stock, and Dealer Orders — One Thread</p>
    </div>

    <div class="title">${isPending ? '⏳ Payment Verification in Progress' : '🎉 Subscription Active & Confirmed!'}</div>
    <div class="desc">
      Hello <b>${storeName}</b>,<br>
      ${isPending
        ? `We have received your payment submission for the <b>${planTitle}</b> plan (${formatInr(amount)}). Our team is verifying the UTR reference with our bank. Your subscription will be active shortly.`
        : `Thank you for choosing Vastrenix! Your payment of <b>${formatInr(amount)}</b> has been processed successfully. Your subscription plan is now active.`}
    </div>

    <table class="table">
      <tr>
        <td class="label">Store Name</td>
        <td class="val">${storeName}</td>
      </tr>
      ${storeCode ? `<tr><td class="label">Store Code</td><td class="val">${storeCode}</td></tr>` : ''}
      <tr>
        <td class="label">Plan Subscribed</td>
        <td class="val">${planTitle}</td>
      </tr>
      <tr>
        <td class="label">Amount Paid</td>
        <td class="val">${formatInr(amount)}</td>
      </tr>
      ${paymentId ? `<tr><td class="label">Payment Reference</td><td class="val"><code style="background:#25252E;padding:2px 6px;border-radius:4px">${paymentId}</code></td></tr>` : ''}
      <tr>
        <td class="label">Status</td>
        <td class="val">
          <span class="pill ${isPending ? 'pill-pending' : 'pill-active'}">
            ${isPending ? 'Pending Verification' : 'Active' + (expiresAt ? ` until ${expiresAt}` : '')}
          </span>
        </td>
      </tr>
    </table>

    <div class="features-box">
      <b>INCLUDED IN YOUR PLAN:</b>
      <ul>
        <li>Unlimited Counter Billing & Fast GST Invoicing</li>
        <li>1-Tap Instant WhatsApp Bill Delivery to Customers</li>
        <li>Multi-Location Stock Tracking (Shop Showroom + Godowns)</li>
        <li>B2B Dealer Orders Network with Real-Time Inventory Sync</li>
        <li>Customer Khata Ledger with Automatic Month-End Dues Reminders</li>
        <li>Automatic Cloud Backup & Multi-Device Counter Sync</li>
      </ul>
    </div>

    <div class="desc" style="font-size:13px;color:#8E8D9A;">
      Need assistance, custom billing formats, or official tax invoices? Reply directly to this email or contact our support team at <a href="mailto:contact@vastrenix.com" style="color:#7A63FF">contact@vastrenix.com</a>.
    </div>

    <div class="footer">
      &copy; 2026 Vastrenix Garment Technologies &middot; <a href="https://vastrenix.com">vastrenix.com</a>
    </div>
  </div>
</body>
</html>
  `.trim();

  const text = `
Vastrenix Subscription ${isPending ? 'Verification' : 'Confirmation'}
------------------------------------------------------------
Store: ${storeName} ${storeCode ? `(${storeCode})` : ''}
Plan: ${planTitle}
Amount: ${formatInr(amount)}
Reference: ${paymentId}
Status: ${isPending ? 'Pending Verification' : 'Active' + (expiresAt ? ` until ${expiresAt}` : '')}

${isPending
  ? 'We have received your payment submission and are verifying it with the bank. Your subscription will be activated shortly.'
  : 'Thank you for your purchase! Your Vastrenix subscription is now active.'}

For support or invoice questions, email contact@vastrenix.com
https://vastrenix.com
  `.trim();

  const db = admin.firestore();

  try {
    // 1. Queue into Firestore /mail collection (Firebase Trigger Email extension compatible)
    await db.collection('mail').add({
      to: userEmail,
      bcc: 'contact@vastrenix.com',
      message: {
        subject: subject,
        html: html,
        text: text
      },
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      uid: uid,
      type: 'subscription_receipt'
    });

    // 2. Also log payment record under /payments
    if (paymentId) {
      await db.collection('payments').add({
        uid: uid,
        email: userEmail,
        storeName: storeName,
        storeCode: storeCode,
        amount: amount,
        plan: planTitle,
        paymentId: paymentId,
        status: isPending ? 'pending' : 'active',
        expiresAt: body.expiresAt || null,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        source: body.method || 'online'
      });
    }

    // 3. If SMTP credentials or Resend API is configured in environment, dispatch immediately
    if (process.env.RESEND_API_KEY) {
      try {
        await fetch('https://api.resend.com/emails', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.RESEND_API_KEY}`
          },
          body: JSON.stringify({
            from: process.env.EMAIL_FROM || 'Vastrenix <billing@vastrenix.com>',
            to: [userEmail],
            bcc: ['contact@vastrenix.com'],
            subject: subject,
            html: html
          })
        });
      } catch (e) {
        console.warn('[Vastrenix] Resend dispatch note:', e.message);
      }
    }

    return res.status(200).json({
      ok: true,
      message: 'Subscription receipt email queued successfully.'
    });

  } catch (err) {
    console.error('[Vastrenix Receipt Error]', err);
    return res.status(500).json({
      error: 'email_failed',
      message: err.message || 'Failed to dispatch subscription receipt email.'
    });
  }
};
