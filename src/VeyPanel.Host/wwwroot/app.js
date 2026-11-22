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
function gpu(data) {
  $('gpu-status').textContent = data?.status || 'N/A';
  $('gpu-total').textContent = pct(data?.busiestEnginePercent);
  $('gpu-encode').textContent = pct(data?.videoEncodePercent);
  $('gpu-decode').textContent = pct(data?.videoDecodePercent);
}
function offline(message) {
  $('status').textContent = message; metric('cpu', null);metric('ram',null);
  resources(null);diskIo(null);gpu(null);
  $('capacity').textContent='N/A';$('timestamp').textContent='No current sample';
  samples.push({});if(samples.length>60)samples.shift();draw();
}
let socket = null, socketFresh = 0, nextConnect = 0, lastTimestamp = 0;
function render(s, transport) {
  const stamp = Date.parse(s.timestampUtc), age = Date.now() - stamp;
  if (!Number.isFinite(age) || age > 5000 || age < -5000) throw Error('Stale sample');
  resources(s.resources);diskIo(s.diskIo);gpu(s.gpu);
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
