'use strict';
const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.hash.slice(1)).get('token');
if (token) history.replaceState(null, '', location.pathname + location.search);
const samples = [];
const pct = value => Number.isFinite(value) ? `${value.toFixed(1)}%` : 'N/A';
const gib = value => (value / 1073741824).toFixed(1);
function metric(name, value) {
  $(name).textContent = pct(value);
  const bar = $(`${name}-bar`);
  if (Number.isFinite(value)) bar.value = value;
  else bar.removeAttribute('value');
}
function draw() {
  const canvas = $('chart'), ctx = canvas.getContext('2d');
  const ratio = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * ratio; canvas.height = h * ratio;
  ctx.scale(ratio, ratio);
  ctx.strokeStyle = '#354358';
  for (let i=0;i<=4;i++) { ctx.beginPath();ctx.moveTo(0,i*h/4);ctx.lineTo(w,i*h/4);ctx.stroke(); }
  for (const [key,color] of [['cpuPercent','#69baff'],['memoryUsedPercent','#b9a5ff']]) {
    ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=2;let pen=false;
    samples.forEach((sample,i)=>{const v=sample[key];if(!Number.isFinite(v)){pen=false;return;}const x=(60-samples.length+i)*w/59,y=(100-v)*h/100;if(pen)ctx.lineTo(x,y);else ctx.moveTo(x,y);pen=true;});ctx.stroke();
  }
}
function rate(value) {
  if (!Number.isFinite(value)) return 'N/A';
  if (value >= 1048576) return (value / 1048576).toFixed(2) + ' MiB/s';
  return (value / 1024).toFixed(1) + ' KiB/s';
}
function rows(id, records, render, status) {
  const list = $(id);
  list.replaceChildren();
  if (!Array.isArray(records) || records.length === 0) {
    const row = document.createElement('p');
    row.textContent = status || 'N/A';
    list.append(row); return;
  }
  for (const item of records) {
    const row = document.createElement('div');
    row.className = 'resource-row';
    row.textContent = render(item);
    list.append(row);
  }
}
function resources(data) {
  $('network-status').textContent = data?.networkStatus || 'N/A';
  $('storage-status').textContent = data?.storageStatus || 'N/A';
  rows('network-list', data?.network, n => n.name + ' · RX ' + rate(n.receiveBytesPerSecond) + ' · TX ' + rate(n.transmitBytesPerSecond), 'N/A');
  const age = Date.now() - Date.parse(data?.storageTimestampUtc);
  const valid = Number.isFinite(age) && age >= -5000 && age < 12000;
  rows('storage-list', valid ? data?.volumes : null, v => v.name + ' · ' +
    (Number.isFinite(v.freeBytes) && Number.isFinite(v.totalBytes)
      ? gib(v.freeBytes) + ' / ' + gib(v.totalBytes) + ' GiB free' : 'N/A'), 'N/A');
}
function diskIo(data) {
  $('disk-status').textContent = data?.status || 'N/A';
  $('disk-read').textContent = rate(data?.readBytesPerSecond);
  $('disk-write').textContent = rate(data?.writeBytesPerSecond);
  const iops = value => Number.isFinite(value) ? value.toFixed(1) : 'N/A';
  $('disk-iops').textContent = 'Read ' + iops(data?.readsPerSecond) + ' / Write ' + iops(data?.writesPerSecond) + ' IOPS';
}
function physicalDisks(data) {
  $('physical-status').textContent = data?.status || 'N/A';
  const iops = n => Number.isFinite(n) ? n.toFixed(1) : 'N/A';
  rows('physical-list', data?.disks, d => d.instance + ' · Read ' + rate(d.readBytesPerSecond) +
    ' · Write ' + rate(d.writeBytesPerSecond) + ' · R/W IOPS ' +
    iops(d.readsPerSecond) + ' / ' + iops(d.writesPerSecond), 'N/A');
}
function storageHealth(data) {
  const age = Date.now() - Date.parse(data?.timestampUtc);
  const fresh = Number.isFinite(age) && age >= -5000 && age <= 150000;
  $('health-status').textContent = data?.status || 'N/A';
  const number = (v, suffix) => Number.isFinite(v) ? v + suffix : 'N/A';
  rows('health-list', fresh ? data?.disks : null, d =>
    (d.model || d.name || 'Unknown disk') + ' · ' + (d.busType || 'N/A') +
    ' · ' + (d.providerHealth || 'N/A') + ' · ' + number(d.temperatureC, ' °C') +
    ' · Wear ' + number(d.wearPercent, '%') + ' · ' + number(d.powerOnHours, ' h') +
    ' · R/W errors ' + number(d.readErrorsTotal, '') + ' / ' + number(d.writeErrorsTotal, '') +
    ' · ' + d.counterStatus, 'N/A');
}
function thermal(data) {
  const age = Date.now() - Date.parse(data?.receivedUtc);
  const fresh = Number.isFinite(age) && age >= -5000 && age <= 20000;
  $('thermal-status').textContent = data?.status || 'N/A';
  rows('thermal-list', fresh ? data?.sensors : null, t =>
    t.category + ' · ' + t.hardware + ' · ' + t.sensor + ' · ' +
    (Number.isFinite(t.celsius) ? t.celsius.toFixed(1) + ' °C' : 'N/A'), 'N/A');
}
function gpu(data) {
  $('gpu-status').textContent = data?.status || 'N/A';
  $('gpu-total').textContent = pct(data?.busiestEnginePercent);
  $('gpu-encode').textContent = pct(data?.videoEncodePercent);
  $('gpu-decode').textContent = pct(data?.videoDecodePercent);
  $('gpu-inventory').textContent = data?.inventoryStatus || 'N/A';
  rows('gpu-adapters', data?.adapters, a => a.name + (a.software ? ' (software)' : '') + ' · GPU ' + pct(a.busiestEnginePercent) + ' · Encode ' + pct(a.videoEncodePercent) + ' · Decode ' + pct(a.videoDecodePercent) + ' · Dedicated capacity ' + (Number.isFinite(a.dedicatedVideoBytes) ? gib(a.dedicatedVideoBytes) + ' GiB' : 'N/A'), 'N/A');
}
function offline(message) {
  $('status').textContent = message; metric('cpu', null);metric('ram',null);
  resources(null);diskIo(null);physicalDisks(null);storageHealth(null);thermal(null);gpu(null);
  $('capacity').textContent='N/A';$('timestamp').textContent='No current sample';
  samples.push({});if(samples.length>60)samples.shift();draw();
}
let socket = null, socketFresh = 0, nextConnect = 0, lastTimestamp = 0;
function render(s, transport) {
  const stamp = Date.parse(s.timestampUtc), age = Date.now() - stamp;
  if (!Number.isFinite(age) || age > 5000 || age < -5000) throw Error('Stale sample');
  resources(s.resources);diskIo(s.diskIo);physicalDisks(s.physicalDisks);storageHealth(s.storageHealth);thermal(s.thermal);gpu(s.gpu);
  $('status').textContent=s.status + ' · ' + transport;
  metric('cpu',s.cpuPercent);metric('ram',s.memoryUsedPercent);
  $('capacity').textContent=Number.isFinite(s.memoryTotalBytes)&&Number.isFinite(s.memoryAvailableBytes)?`${gib(s.memoryTotalBytes-s.memoryAvailableBytes)} / ${gib(s.memoryTotalBytes)} GiB`:'N/A';
  $('timestamp').textContent=`Updated ${new Date(s.timestampUtc).toLocaleTimeString()}`;
  if (stamp !== lastTimestamp) {
    lastTimestamp=stamp;samples.push(s);if(samples.length>60)samples.shift();draw();
  }
}
function connect() {
  if (!token || socket || Date.now() < nextConnect) return;
  nextConnect = Date.now() + 10000;
  let candidate;
  try {
    const url = new URL('/api/v1/telemetry/ws', location.href);
    url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    candidate = new WebSocket(url);
  } catch { return; }
  socket = candidate;
  let timer = setTimeout(() => candidate.close(), 6000);
  candidate.onopen = () => { if (socket === candidate) candidate.send(token); };
  candidate.onmessage = event => {
    if (socket !== candidate) return;
    try {
      render(JSON.parse(event.data), 'WebSocket');
      socketFresh = Date.now();
      clearTimeout(timer);
      timer = setTimeout(() => candidate.close(), 4500);
    } catch { candidate.close(); }
  };
  candidate.onerror = () => candidate.close();
  candidate.onclose = () => {
    clearTimeout(timer);
    if (socket === candidate) { socket = null; socketFresh = 0; }
  };
}
async function update() {
  if (!token) { offline('Open the access link printed by Host'); return; }
  connect();
  if (!socketFresh || Date.now() - socketFresh > 3500) {
    try {
      const response = await fetch('/api/v1/telemetry', {
        headers: {Authorization:`Bearer ${token}`}, cache:'no-store', signal:AbortSignal.timeout(3000)
      });
      if (!response.ok) throw Error('Unauthorized or unavailable');
      const s=await response.json();
      if (!socketFresh || Date.now()-socketFresh > 3500) render(s,'REST');
    } catch {
      if (!socketFresh || Date.now()-socketFresh > 3500) offline('Disconnected / unauthorized');
    }
  }
  setTimeout(update,1000);
}
window.addEventListener('pagehide',()=>{if(socket)socket.close();});
window.addEventListener('resize',draw);update();

async function ownerRequest(method, path = '', name, body) {
  const headers = {Authorization: 'Bearer ' + token};
  const options = {method, headers, cache: 'no-store', signal: AbortSignal.timeout(5000)};
  if (name !== undefined || body !== undefined) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body ?? {name});
  }
  const response = await fetch('/api/v1/devices' + path, options);
  if (!response.ok) throw Error('HTTP ' + response.status);
  return response.status === 204 ? null : response.json();
}

let ownerBusy = false;
async function ownerAction(action) {
  if (ownerBusy) return;
  ownerBusy = true;
  $('device-create').disabled = $('device-refresh').disabled = true;
  try { await action(); }
  catch { $('device-status').textContent = 'Operation failed. Verify Host access and retry.'; }
  finally {
    ownerBusy = false;
    $('device-create').disabled = $('device-refresh').disabled = false;
  }
}

function renderDevices(devices) {
  const list = $('device-list');
  list.replaceChildren();
  if (!Array.isArray(devices)) throw Error('Invalid device list');
  for (const device of devices) {
    const row = document.createElement('div');
    row.className = 'device-row resource-row';
    const label = document.createElement('span');
    label.textContent = device.name + ' · expires ' + new Date(device.expiresUtc).toLocaleString();
    const revoke = document.createElement('button');
    revoke.type = 'button';
    revoke.textContent = 'Revoke';
    revoke.addEventListener('click', () => ownerAction(async () => {
      if (!window.confirm('Revoke this reader device?')) return;
      await ownerRequest('DELETE', '/' + encodeURIComponent(device.id));
      renderDevices(await ownerRequest('GET'));
      $('device-status').textContent = 'Access revoked';
      clearIssued();
    }));
    row.append(label, revoke);
    list.append(row);
  }
  if (devices.length === 0) list.textContent = 'No active reader devices';
}
function clearIssued() {
  $('issued-link').value = '';
  $('issued-panel').hidden = true;
}
async function initializeOwner() {
  if (!token || location.origin !== 'http://127.0.0.1:47860') return;
  try {
    renderDevices(await ownerRequest('GET'));
    $('device-owner').hidden = false;
    await initializeInvitations();
  } catch { return; }
  $('device-refresh').addEventListener('click', () => ownerAction(async () => {
    clearIssued();
    renderDevices(await ownerRequest('GET'));
    $('device-status').textContent = 'Updated';
  }));
  $('device-clear').addEventListener('click', clearIssued);
  $('device-create').addEventListener('click', () => ownerAction(async () => {
    const name = $('device-name').value.trim();
    if (!name || Array.from(name).some(c => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127)) {
      $('device-status').textContent = 'Enter a device name';
      return;
    }
    clearIssued();
    const issued = await ownerRequest('POST', '', name);
    $('issued-link').value = issued.dashboardUrl || issued.token;
    $('issued-panel').hidden = false;
    $('issued-label').textContent = issued.dashboardUrl
      ? 'Private reader link (24 hours); share only with the intended device.'
      : 'Reader token (24 hours). LAN is disabled; this cannot reach the tablet.';
    $('device-name').value = '';
    $('device-status').textContent = 'Reader access created';
    renderDevices(await ownerRequest('GET'));
  }));
}
window.addEventListener('pagehide', clearIssued);
initializeOwner();

let invitationBusy = false, invitationTimer = null;
function clearInvitation() {
  $('invitation-link').value = '';
  $('invitation-link').hidden = true;
}
async function invitationAction(action) {
  if (invitationBusy) return;
  invitationBusy = true;
  $('invitation-create').disabled = $('invitation-refresh').disabled = true;
  try { await action(); }
  catch { $('invitation-status').textContent = 'Request failed; LAN HTTPS must be enabled.'; }
  finally { invitationBusy = false; $('invitation-create').disabled = $('invitation-refresh').disabled = false; }
}
async function refreshInvitations() {
  const items = await ownerRequest('GET', '/invitations');
  const list = $('invitation-list');
  list.replaceChildren();
  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'device-row resource-row';
    const label = document.createElement('span');
    label.textContent = item.name + ' · ' + item.state + ' · ' + new Date(item.expiresUtc).toLocaleTimeString();
    row.append(label);
    if (item.state === 'pending') {
      const approve = document.createElement('button');
      approve.textContent = 'Compare and approve';
      approve.addEventListener('click', () => invitationAction(async () => {
        const code = prompt('Enter the six-digit code shown on the intended tablet:');
        if (!/^[0-9]{6}$/.test(code || '')) return;
        await ownerRequest('POST', '/invitations/' + item.id + '/approve', undefined, {code});
        clearInvitation();
        await refreshInvitations();
        $('invitation-status').textContent = 'Approved; tablet must finish enrollment.';
      }));
      row.append(approve);
    }
    const cancel = document.createElement('button');
    cancel.textContent = 'Cancel';
    cancel.addEventListener('click', () => invitationAction(async () => {
      await ownerRequest('DELETE', '/invitations/' + item.id);
      clearInvitation(); await refreshInvitations();
    }));
    row.append(cancel);list.append(row);
  }
  if (!items.length) list.textContent = 'No active invitations';
}
async function initializeInvitations() {
  $('invitation-owner').hidden = false;
  $('invitation-create').addEventListener('click', () => invitationAction(async () => {
    clearInvitation();
    const name = $('device-name').value.trim();
    if (!name) { $('invitation-status').textContent = 'Enter the intended device name above.'; return; }
    const issued = await ownerRequest('POST', '/invitations', name);
    $('invitation-link').value = issued.url;
    $('invitation-link').hidden = false;
    $('invitation-status').textContent = 'Private invitation; expires in two minutes.';
    clearTimeout(invitationTimer);
    invitationTimer = setTimeout(clearInvitation, 120000);
    await refreshInvitations();
  }));
  $('invitation-refresh').addEventListener('click', () => invitationAction(refreshInvitations));
  $('invitation-clear').addEventListener('click', clearInvitation);
  await invitationAction(refreshInvitations);
}
window.addEventListener('pagehide', clearInvitation);
