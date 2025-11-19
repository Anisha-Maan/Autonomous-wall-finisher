const BASE_URL = "http://localhost:8000";

// DOM
const planBtn = document.getElementById("planBtn");
const loadLast = document.getElementById("loadLast");
const playBtn = document.getElementById("play");
const pauseBtn = document.getElementById("pause");
const speedEl = document.getElementById("speed");
const info = document.getElementById("info");
const canvas = document.getElementById("cv");
const ctx = canvas.getContext("2d");

// Obstacle inputs
const obsXInput = document.getElementById("obsX");
const obsYInput = document.getElementById("obsY");
const obsWInput = document.getElementById("obsW");
const obsHInput = document.getElementById("obsH");
const addObsBtn = document.getElementById("addObstacleBtn");
const obsListDiv = document.getElementById("obstacle-list");

// State
let traj = { waypoints: [], obstacles: [] };
let obstacles = [];
let playing = false;
let tIndex = 0; // continuous index (can be fractional for interpolation)
let speed = 1;
let SCALE = 100; // pixels per meter (updated per-plan)
const MAX_CANVAS_PIXELS = 800; // maximum width/height in pixels when auto-scaling
let currentWallHeight = parseFloat(document.getElementById("h").value) || 5;

// scrubber & step controls
const scrub = document.getElementById("scrub");
const scrubInfo = document.getElementById("scrubInfo");
const stepBack = document.getElementById("stepBack");
const stepForward = document.getElementById("stepForward");

// --- Drawing ---
function drawGrid(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  // grid spacing in meters (approx) then convert to pixels
  const approxMeterStep = 0.25; // 25cm grid
  const step = Math.max(6, Math.round(approxMeterStep * SCALE));
  ctx.strokeStyle = "#f1f1f1";
  ctx.lineWidth = 1;
  for(let x=0;x<canvas.width;x+=step){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke();}
  for(let y=0;y<canvas.height;y+=step){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke();}
}
function drawObstacles(obsArray){
  ctx.save();
  ctx.fillStyle = "rgba(255,0,0,0.35)";
  obsArray.forEach(obs=>{
    const ow = (obs.w !== undefined) ? obs.w : obs.width;
    const oh = (obs.h !== undefined) ? obs.h : obs.height;
    // obstacles are provided in bottom-left coordinates; convert to canvas (top-left origin)
    const xpx = (obs.x||0) * SCALE;
    const ypx = canvas.height - ((obs.y||0) + (oh||0)) * SCALE;
    ctx.fillRect(xpx, ypx, (ow||0) * SCALE, (oh||0) * SCALE);
    // outline
    ctx.strokeStyle = "rgba(200,0,0,0.7)";
    ctx.strokeRect(xpx, ypx, (ow||0) * SCALE, (oh||0) * SCALE);
  });
  ctx.restore();
}
function drawTrajectory(points){
  if(!points||!points.length) return;
  ctx.save(); ctx.lineWidth=2; ctx.beginPath();
  // draw segments with color based on tool_on (paint) flag
  for(let i=0;i<points.length-1;i++){
    const a = points[i], b = points[i+1];
    const ax = a.x * SCALE, ay = canvas.height - a.y * SCALE;
    const bx = b.x * SCALE, by = canvas.height - b.y * SCALE;
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by);
    ctx.strokeStyle = (b.tool_on===false) ? "#888888" : "#0b5fff";
    ctx.lineWidth = 2;
    ctx.stroke();
  }
  // marker interpolated
  const pos = getPositionAt(tIndex, points);
  if(pos){ const px = pos.x * SCALE; const py = canvas.height - pos.y * SCALE; ctx.beginPath(); ctx.arc(px, py, Math.max(4,6*(SCALE/100)),0,Math.PI*2); ctx.fillStyle="red"; ctx.fill(); }
  ctx.restore();
}

function getPositionAt(t, points){
  if(!points || points.length===0) return null;
  if(t <= 0) return points[0];
  const i = Math.floor(t);
  if(i >= points.length-1) return points[points.length-1];
  const a = points[i];
  const b = points[i+1];
  const frac = t - i;
  return { x: a.x + (b.x - a.x) * frac, y: a.y + (b.y - a.y) * frac };
}
function render(){
  drawGrid();
  drawObstacles(obstacles);
  drawTrajectory(traj.waypoints);
  renderObstacleList();
  updateScrubUI();
}
function renderObstacleList(){
  obsListDiv.innerHTML = obstacles.length===0?"No obstacles yet":"";
  obstacles.forEach((obs,i)=>{
    const ow = (obs.w !== undefined) ? obs.w : obs.width;
    const oh = (obs.h !== undefined) ? obs.h : obs.height;
    const div=document.createElement("div");
    div.innerText=`Obstacle ${i+1}: x=${obs.x} y=${obs.y} w=${ow} h=${oh}`;
    obsListDiv.appendChild(div);
  });
}

// --- Obstacle management ---
addObsBtn.onclick = () => {
  const x_top = parseFloat(obsXInput.value), y_top=parseFloat(obsYInput.value), w=parseFloat(obsWInput.value), h=parseFloat(obsHInput.value);
  if([x_top,y_top,w,h].some(isNaN)) return alert("Fill all obstacle fields!");
  // convert top-left input to bottom-left coordinates for storage and backend
  const y_bottom = currentWallHeight - y_top - h;
  obstacles.push({x: x_top, y: y_bottom, w: w, h: h});
  render();
};

// --- Plan & Save ---
planBtn.onclick = async ()=>{
  const w=parseFloat(document.getElementById("w").value);
  const h=parseFloat(document.getElementById("h").value);
  const brush=parseFloat(document.getElementById("brush").value);
  // Auto-scale canvas: choose pixels-per-meter such that the canvas fits within MAX_CANVAS_PIXELS
  const ppm = Math.max(10, Math.min(MAX_CANVAS_PIXELS / Math.max(w,h), 300)) ; // pixels per meter
  SCALE = ppm;
  canvas.width = Math.max(200, Math.round(w * SCALE));
  canvas.height = Math.max(200, Math.round(h * SCALE));
  currentWallHeight = h;

  const payload={wall:{width:w,height:h,brush_width:brush,resolution:0.02,obstacles},name:"demo_with_obstacles"};

  try{
    const res=await fetch(`${BASE_URL}/api/plan`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const j=await res.json();
    if(!j.id){info.innerText="Plan failed"; return;}
    const t=await fetch(`${BASE_URL}/api/trajectory/${j.id}`);
    const tj=await t.json();
    traj.waypoints=tj.waypoints;
    traj.obstacles=obstacles;
    info.innerText=`Points: ${traj.waypoints.length}  Length: ${tj.length_m.toFixed(3)} m`;
    tIndex=0; playing=false; setPlaybackRange(); render();
  }catch(err){console.error(err); info.innerText="Plan failed (check console)";}
};

// --- Load last trajectory ---
loadLast.onclick = async ()=>{
  try{
    const resp=await fetch(`${BASE_URL}/api/trajectories?limit=1`);
    const j=await resp.json();
    if(j.count===0){info.innerText="No saved trajectories"; return;}
    const id=j.results[0].id;
    const t=await fetch(`${BASE_URL}/api/trajectory/${id}`);
    const tj=await t.json();
    traj.waypoints=tj.waypoints; obstacles=tj.obstacles||[];
    info.innerText=`Loaded: ${tj.name} Points: ${traj.waypoints.length} Length: ${tj.length_m.toFixed(3)} m`;
    tIndex=0; setPlaybackRange(); render();
  }catch(err){console.error(err); info.innerText="Failed to load trajectory";}
};

// --- Play / Pause ---
playBtn.onclick=()=>{playing=true; loop();};
pauseBtn.onclick=()=>{playing=false;};
speedEl.oninput=(e)=>{speed=parseFloat(e.target.value);};

// scrubber and step control handlers
scrub.oninput = (e)=>{
  const val = parseFloat(e.target.value);
  if(!traj.waypoints || traj.waypoints.length===0) return;
  tIndex = (val/100) * (traj.waypoints.length-1);
  render();
};
stepBack.onclick = ()=>{
  if(!traj.waypoints || traj.waypoints.length===0) return;
  tIndex = Math.max(0, tIndex - 1);
  render();
};
stepForward.onclick = ()=>{
  if(!traj.waypoints || traj.waypoints.length===0) return;
  tIndex = Math.min(traj.waypoints.length-1, tIndex + 1);
  render();
};

function setPlaybackRange(){
  if(!traj.waypoints || traj.waypoints.length===0){ scrub.disabled = true; scrub.value = 0; scrubInfo.innerText = '' ; return; }
  scrub.disabled = false;
  scrub.value = 0;
  updateScrubUI();
}

function updateScrubUI(){
  if(!traj.waypoints || traj.waypoints.length===0){ scrubInfo.innerText = '' ; return; }
  const idx = Math.min(traj.waypoints.length-1, Math.floor(tIndex));
  const pct = Math.round((tIndex/(traj.waypoints.length-1))*100)||0;
  scrub.value = pct;
  scrubInfo.innerText = ` ${idx+1}/${traj.waypoints.length} (${pct}%)`;
}

function loop(){
  if(!playing) return;
  // advance by speed scaled to points count for consistent behaviour
  const step = 0.5 * speed;
  tIndex += step;
  if(tIndex >= (traj.waypoints.length-1)) { playing = false; tIndex = traj.waypoints.length-1; }
  render();
  if(playing) requestAnimationFrame(loop);
}

render();


