// Copies browser builds of third-party libraries into www/vendor so the app works offline (and inside the APK).
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), out = path.join(root, 'www', 'vendor');
fs.mkdirSync(out, { recursive: true });
const files = [
  ['firebase-app-compat.js', ['node_modules/firebase/firebase-app-compat.js', 'node_modules/firebase/compat/dist/firebase-app-compat.js']],
  ['firebase-auth-compat.js', ['node_modules/firebase/firebase-auth-compat.js', 'node_modules/firebase/compat/dist/firebase-auth-compat.js']],
  ['firebase-firestore-compat.js', ['node_modules/firebase/firebase-firestore-compat.js', 'node_modules/firebase/compat/dist/firebase-firestore-compat.js']],
  ['html2canvas.min.js', ['node_modules/html2canvas/dist/html2canvas.min.js']],
  ['jspdf.umd.min.js', ['node_modules/jspdf/dist/jspdf.umd.min.js']],
  ['qrcode.js', ['node_modules/qrcode-generator/qrcode.js', 'node_modules/qrcode-generator/dist/qrcode.js']]
];
let missing = 0;
for (const [name, candidates] of files) {
  const hit = candidates.map(c => path.join(root, c)).find(p => fs.existsSync(p));
  if (!hit) { console.warn('! not found:', name, '(the app will load it from a CDN instead)'); missing++; continue; }
  fs.copyFileSync(hit, path.join(out, name));
  console.log('✓', name);
}
console.log(missing ? `Done with ${missing} missing file(s).` : 'All vendor files copied to www/vendor');
