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
function offline(message) {
  $('status').textContent = message; metric('cpu', null);metric('ram',null);
  resources(null);
  $('capacity').textContent='N/A';$('timestamp').textContent='No current sample';
  samples.push({});if(samples.length>60)samples.shift();draw();
}
async function update() {
  if (!token) { offline('Open the access link printed by Host'); return; }
  try {
    const response=await fetch('/api/v1/telemetry',{headers:{Authorization:`Bearer ${token}`},cache:'no-store',signal:AbortSignal.timeout(3000)});
    if (!response.ok) throw Error(`HTTP ${response.status}`);
    const s=await response.json(); const age=Date.now()-Date.parse(s.timestampUtc);
    if (!Number.isFinite(age)||age>5000||age< -5000) throw Error('Stale sample / clock mismatch');
    resources(s.resources);
    $('status').textContent=s.status;metric('cpu',s.cpuPercent);metric('ram',s.memoryUsedPercent);
    $('capacity').textContent=Number.isFinite(s.memoryTotalBytes)&&Number.isFinite(s.memoryAvailableBytes)?`${gib(s.memoryTotalBytes-s.memoryAvailableBytes)} / ${gib(s.memoryTotalBytes)} GiB`:'N/A';
    $('timestamp').textContent=`Updated ${new Date(s.timestampUtc).toLocaleTimeString()}`;
    samples.push(s);if(samples.length>60)samples.shift();draw();
  } catch { offline('Disconnected / unauthorized'); }
  setTimeout(update,1000);
}
window.addEventListener('resize',draw);update();
