#!/usr/bin/env node
// Usage: node scripts/sign_manifest.js <manifest.json> <private-key.pem>  -> rewrites the file with "signature" (Ed25519 over canonical JSON).
const fs = require('fs'); const crypto = require('crypto'); const { canonical } = require('../app/updater');
const [file, key] = process.argv.slice(2); if (!file || !key) { console.error('usage: sign_manifest.js manifest.json key.pem'); process.exit(2); }
const m = JSON.parse(fs.readFileSync(file, 'utf8')); delete m.signature;
m.signature = crypto.sign(null, Buffer.from(canonical(m)), crypto.createPrivateKey(fs.readFileSync(key))).toString('base64');
fs.writeFileSync(file, JSON.stringify(m, null, 2) + '\n'); console.log('signed', file);
