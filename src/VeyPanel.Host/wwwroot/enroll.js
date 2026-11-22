'use strict';
const $ = id => document.getElementById(id);
const fragment = new URLSearchParams(location.hash.slice(1));
const id = fragment.get('id');
let secret = fragment.get('secret');
history.replaceState(null, '', location.pathname);
let busy = false, expires = 0, claimed = false;
const status = text => { $('enroll-status').textContent = text; };
function clear() {
  secret = null;
  $('enroll-start').hidden = $('enroll-finish').hidden = $('enroll-instructions').hidden = true;
  $('enroll-code').textContent = '';
}
async function request(action) {
  return fetch('/api/v1/enroll/' + action, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id, secret}), cache:'no-store', signal:AbortSignal.timeout(5000)
  });
}
async function run(action) {
  if (busy || !secret) return;
  busy = true;
  $('enroll-start').disabled = $('enroll-finish').disabled = true;
  try { await action(); }
  catch { status('Connection or response failed. Ask the PC owner for a new invitation.'); clear(); }
  finally { busy = false; $('enroll-start').disabled = $('enroll-finish').disabled = false; }
}
if (location.protocol !== 'https:' || !/^[0-9a-f-]{36}$/i.test(id || '') || !/^[0-9A-F]{64}$/.test(secret || '')) {
  clear(); status('Open a valid HTTPS invitation from the PC owner.');
} else {
  status('Invitation ready. Press Accept to begin.');
  $('enroll-start').hidden = false;
}
$('enroll-start').addEventListener('click', () => run(async () => {
  const response = await request('claim');
  if (!response.ok) { clear(); status('Invitation expired, canceled or already used.'); return; }
  const result = await response.json();
  if (result.id !== id || !/^[0-9A-F]{64}$/.test(result.secret) || !/^[0-9]{6}$/.test(result.code))
    throw Error('Invalid claim');
  secret = result.secret; claimed = true; expires = Date.parse(result.expiresUtc);
  $('enroll-code').textContent = result.code;
  $('enroll-start').hidden = true;
  $('enroll-instructions').hidden = $('enroll-finish').hidden = false;
  status('Waiting for owner approval.');
}));
$('enroll-finish').addEventListener('click', () => run(async () => {
  if (!claimed || !Number.isFinite(expires) || Date.now() >= expires) {
    clear(); status('Invitation expired. Ask for a new one.'); return;
  }
  const response = await request('finish');
  if (response.status === 202) { status('Waiting for owner approval.'); return; }
  if (!response.ok) { clear(); status('Enrollment unavailable. Ask the owner for a new invitation.'); return; }
  const result = await response.json();
  if (!/^[0-9A-F]{64}$/.test(result.token)) throw Error('Invalid grant');
  clear();
  location.replace('/#token=' + result.token);
}));
setInterval(() => {
  if (claimed && secret && Date.now() >= expires) { clear(); status('Invitation expired.'); }
}, 1000);
window.addEventListener('pagehide', clear);
