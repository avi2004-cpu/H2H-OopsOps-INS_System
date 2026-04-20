import streamlit as st
import pandas as pd
import json, os, sys, time

ROOT = r"C:\Users\chhet\OneDrive\Desktop\H2H-OopsOps-INS_System"
sys.path.insert(0, ROOT)

CSV_PATH  = os.path.join(ROOT, 'network_simulation', 'data', 'network_data.csv')
TOPO_PATH = os.path.join(ROOT, 'network_simulation', 'data', 'topology.json')

from ml_model.model import AnomalyDetector

st.set_page_config(page_title="INSS — IoT Network Monitor", page_icon="🛡️", layout="wide")
st.title("🛡️ Intelligent Network Surveillance System")
st.caption("Real-time IoT Anomaly Detection | Hack2Hire 1.0 — Team OopsOps")

# ── Load data first ──
@st.cache_data(ttl=2)
def load_data():
    return pd.read_csv(CSV_PATH)

@st.cache_resource
def get_detector():
    df = pd.read_csv(CSV_PATH)
    det = AnomalyDetector(contamination=0.1)
    det.train(df)
    return det

try:
    df = load_data()
except Exception as e:
    st.error(f"Cannot load CSV: {e}")
    st.stop()

latest   = df.sort_values('timestamp').groupby('device_id').last().reset_index()
detector = get_detector()
results  = detector.predict(latest)
anomalies = results[results['is_anomaly']]

# ── Sidebar (uses results which is now defined) ──
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    auto = st.checkbox("Auto Refresh (3s)", value=False)
    st.divider()
    st.markdown("### 📊 Stats")
    st.markdown(f"**Devices:** {len(results)}")
    st.markdown(f"**Anomalies:** {len(anomalies)}")
    st.markdown(f"**Avg Traffic:** {results['traffic'].mean():.1f} pkts/s")
    st.markdown(f"**Avg Signal:** {results['signal'].mean():.1f} dBm")
    st.divider()
    st.markdown("### 🎨 Legend")
    st.markdown("🟢 Normal device")
    st.markdown("🔴 Anomaly detected")
    st.markdown("🟡 Access point")

# ── Metrics ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Devices", len(results))
c2.metric("🔴 Anomalies", len(anomalies))
c3.metric("🟢 Normal", len(results) - len(anomalies))
c4.metric("Avg Traffic", f"{results['traffic'].mean():.1f} pkts/s")

st.divider()

# ── Main layout ──
col_graph, col_alerts = st.columns([3, 1])

with col_graph:
    st.subheader("Network Topology")
    import streamlit.components.v1 as components

    anomaly_ids = set(anomalies['device_id'].tolist())
    nodes_data  = []
    edges_data  = []

    for _, row in results.iterrows():
        dev    = row['device_id']
        is_anom = dev in anomaly_ids
        conn   = row.get('connected_to', '')
        dtype  = str(row.get('type', 'device'))

        if 'camera'     in dtype: icon = '📷'
        elif 'thermostat' in dtype: icon = '🌡️'
        elif 'phone'    in dtype: icon = '📱'
        elif 'light'    in dtype: icon = '💡'
        elif 'sensor'   in dtype: icon = '📟'
        elif 'rogue'    in dev:   icon = '☠️'
        else:                      icon = '📡'

        nodes_data.append({
            'id': dev, 'icon': icon,
            'color':  '#ef4444' if is_anom else '#22c55e',
            'border': '#ff0000' if is_anom else '#16a34a',
            'conn': conn,
            'traffic':     int(row['traffic']),
            'signal':      int(row['signal']),
            'packet_rate': int(row['packet_rate']),
            'status':      row['status'],
            'type':        dtype,
            'anomaly_type': row['anomaly_type'],
            'explanation':  row['explanation'],
            'is_anomaly':   bool(is_anom)
        })

        if pd.notna(conn) and conn:
            if not any(n['id'] == conn for n in nodes_data):
                nodes_data.append({
                    'id': conn, 'icon': '🔀',
                    'color': '#f59e0b', 'border': '#d97706',
                    'conn': 'switch_1', 'traffic': 0, 'signal': 100,
                    'packet_rate': 0, 'status': 'active',
                    'type': 'access_point', 'anomaly_type': 'normal',
                    'explanation': 'Access Point', 'is_anomaly': False
                })
            edges_data.append({
                'from': dev, 'to': conn,
                'color': '#ef4444' if is_anom else '#334155'
            })

    nodes_json = json.dumps(nodes_data)
    edges_json = json.dumps(edges_data)

    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0f172a; font-family:'Segoe UI',sans-serif; overflow:hidden; }}
canvas {{ display:block; }}
#fs-btn {{
    position:absolute; top:10px; right:10px;
    background:#1e293b; border:1px solid #334155;
    color:#94a3b8; padding:6px 10px;
    border-radius:6px; cursor:pointer; font-size:12px; z-index:100;
}}
#fs-btn:hover {{ background:#334155; color:#f1f5f9; }}
#tooltip {{
    position:absolute; display:none;
    background:#1e293b; border:1px solid #334155;
    border-radius:8px; padding:8px 12px;
    color:#e2e8f0; font-size:12px; pointer-events:none;
    box-shadow:0 4px 20px rgba(0,0,0,0.5);
}}
#panel {{
    position:absolute; right:0; top:0; width:220px; height:100%;
    background:#0f172a; border-left:1px solid #1e293b;
    color:#e2e8f0; padding:16px; display:none; overflow-y:auto;
}}
#panel h3 {{ font-size:14px; margin-bottom:12px; color:#f8fafc; }}
.stat-row {{ display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #1e293b; font-size:12px; }}
.stat-label {{ color:#94a3b8; }}
.stat-val {{ color:#f1f5f9; font-weight:600; }}
.badge {{ display:inline-block; padding:3px 8px; border-radius:12px; font-size:11px; font-weight:600; margin-top:8px; }}
.badge-red {{ background:#450a0a; color:#ef4444; }}
.badge-green {{ background:#052e16; color:#22c55e; }}
.gauge-wrap {{ margin:12px 0; }}
.gauge-label {{ font-size:11px; color:#94a3b8; margin-bottom:4px; }}
.gauge-bar {{ height:6px; background:#1e293b; border-radius:3px; overflow:hidden; }}
.gauge-fill {{ height:100%; border-radius:3px; transition:width 0.3s; }}
#close-btn {{ position:absolute; top:8px; right:8px; background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px; }}
#close-btn:hover {{ color:#f1f5f9; }}
#legend {{ position:absolute; bottom:10px; left:10px; display:flex; gap:12px; }}
.leg {{ display:flex; align-items:center; gap:5px; font-size:11px; color:#94a3b8; }}
.leg-dot {{ width:10px; height:10px; border-radius:50%; }}
</style>
</head>
<body>
<button id="fs-btn" onclick="toggleFS()">⛶ Fullscreen</button>
<canvas id="c"></canvas>
<div id="tooltip"></div>
<div id="panel">
  <button id="close-btn" onclick="closePanel()">✕</button>
  <div id="panel-content"></div>
</div>
<div id="legend">
  <div class="leg"><div class="leg-dot" style="background:#22c55e"></div>Normal</div>
  <div class="leg"><div class="leg-dot" style="background:#ef4444"></div>Anomaly</div>
  <div class="leg"><div class="leg-dot" style="background:#f59e0b"></div>Access Point</div>
</div>
<script>
const NODES = {nodes_json};
const EDGES = {edges_json};
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
const panel = document.getElementById('panel');

function resize() {{ canvas.width = window.innerWidth; canvas.height = window.innerHeight; }}
resize();
window.addEventListener('resize', () => {{ resize(); layout(); draw(); }});

const pos = {{}};
const vel = {{}};
const ids = [...new Set(NODES.map(n => n.id))];

function layout() {{
  const W = canvas.width, H = canvas.height, cx = W/2, cy = H/2;
  const aps = NODES.filter(n => n.type === 'access_point').map(n => n.id);
  const devs = NODES.filter(n => n.type !== 'access_point').map(n => n.id);
  aps.forEach((id, i) => {{
    const a = (2*Math.PI*i/Math.max(aps.length,1)) - Math.PI/2;
    pos[id] = {{ x: cx + 130*Math.cos(a), y: cy + 100*Math.sin(a) }};
    vel[id] = {{ x:0, y:0 }};
  }});
  devs.forEach((id, i) => {{
    const a = (2*Math.PI*i/Math.max(devs.length,1)) - Math.PI/2;
    pos[id] = {{ x: cx + 240*Math.cos(a), y: cy + 200*Math.sin(a) }};
    vel[id] = {{ x:0, y:0 }};
  }});
}}
layout();

function simulate() {{
  const k = 80, rep = 6000, damp = 0.85;
  ids.forEach(a => {{
    let fx=0, fy=0;
    ids.forEach(b => {{
      if(a===b) return;
      const dx=pos[a].x-pos[b].x, dy=pos[a].y-pos[b].y;
      const d=Math.max(Math.sqrt(dx*dx+dy*dy),1);
      fx+=rep*dx/(d*d*d); fy+=rep*dy/(d*d*d);
    }});
    EDGES.forEach(e => {{
      let other = e.from===a ? e.to : e.to===a ? e.from : null;
      if(!other||!pos[other]) return;
      const dx=pos[other].x-pos[a].x, dy=pos[other].y-pos[a].y;
      const d=Math.max(Math.sqrt(dx*dx+dy*dy),1);
      fx+=k*(d-120)*dx/d; fy+=k*(d-120)*dy/d;
    }});
    fx+=(canvas.width/2-pos[a].x)*0.02;
    fy+=(canvas.height/2-pos[a].y)*0.02;
    vel[a].x=(vel[a].x+fx*0.016)*damp;
    vel[a].y=(vel[a].y+fy*0.016)*damp;
    pos[a].x+=vel[a].x; pos[a].y+=vel[a].y;
  }});
}}

let simSteps=120;
function tick() {{
  if(simSteps>0){{ simulate(); simSteps--; }}
  draw();
  requestAnimationFrame(tick);
}}

function draw() {{
  ctx.clearRect(0,0,canvas.width,canvas.height);
  EDGES.forEach(e => {{
    if(!pos[e.from]||!pos[e.to]) return;
    ctx.beginPath();
    ctx.moveTo(pos[e.from].x,pos[e.from].y);
    ctx.lineTo(pos[e.to].x,pos[e.to].y);
    ctx.strokeStyle=e.color; ctx.lineWidth=1.5; ctx.globalAlpha=0.6;
    ctx.stroke(); ctx.globalAlpha=1;
  }});
  NODES.forEach(n => {{
    if(!pos[n.id]) return;
    const {{x,y}}=pos[n.id];
    const r=n.type==='access_point'?22:18;
    if(n.is_anomaly) {{
      ctx.beginPath(); ctx.arc(x,y,r+8,0,2*Math.PI);
      const grd=ctx.createRadialGradient(x,y,r,x,y,r+8);
      grd.addColorStop(0,'rgba(239,68,68,0.4)');
      grd.addColorStop(1,'rgba(239,68,68,0)');
      ctx.fillStyle=grd; ctx.fill();
    }}
    ctx.beginPath(); ctx.arc(x,y,r,0,2*Math.PI);
    ctx.fillStyle=n.color+'33'; ctx.fill();
    ctx.strokeStyle=n.border; ctx.lineWidth=2; ctx.stroke();
    ctx.font=n.type==='access_point'?'18px serif':'14px serif';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(n.icon,x,y);
    ctx.font='10px Segoe UI'; ctx.fillStyle='#94a3b8';
    ctx.fillText(n.id,x,y+r+10);
    if(n.is_anomaly) {{
      const pulse=(Date.now()%1500)/1500;
      ctx.beginPath(); ctx.arc(x,y,r+pulse*15,0,2*Math.PI);
      ctx.strokeStyle=`rgba(239,68,68,${{(0.6*(1-pulse)).toFixed(2)}})`;
      ctx.lineWidth=2; ctx.stroke();
    }}
  }});
}}

let hovered=null;
canvas.addEventListener('mousemove', e => {{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  hovered=null;
  NODES.forEach(n => {{
    if(!pos[n.id]) return;
    const dx=pos[n.id].x-mx, dy=pos[n.id].y-my;
    if(Math.sqrt(dx*dx+dy*dy)<22) hovered=n;
  }});
  if(hovered) {{
    tooltip.style.display='block';
    tooltip.style.left=(e.clientX+12)+'px';
    tooltip.style.top=(e.clientY-10)+'px';
    tooltip.innerHTML=`<b>${{hovered.id}}</b><br>Traffic: ${{hovered.traffic}} pkts/s<br>Signal: ${{hovered.signal}} dBm<br>Status: ${{hovered.status}}<br>${{hovered.is_anomaly?'⚠️ '+hovered.anomaly_type:'✅ Normal'}}`;
    canvas.style.cursor='pointer';
  }} else {{
    tooltip.style.display='none';
    canvas.style.cursor='default';
  }}
}});

canvas.addEventListener('click', e => {{
  if(!hovered) return;
  const n=hovered;
  const tp=Math.min(n.traffic/200*100,100).toFixed(0);
  const sp=n.signal;
  const pp=Math.min(n.packet_rate/150*100,100).toFixed(0);
  const bc=n.is_anomaly?'badge-red':'badge-green';
  const bt=n.is_anomaly?'⚠️ '+n.anomaly_type.replace(/_/g,' ').toUpperCase():'✅ NORMAL';
  document.getElementById('panel-content').innerHTML=`
    <h3>${{n.icon}} ${{n.id}}</h3>
    <span class="badge ${{bc}}">${{bt}}</span>
    <div style="margin-top:12px">
      <div class="stat-row"><span class="stat-label">Type</span><span class="stat-val">${{n.type}}</span></div>
      <div class="stat-row"><span class="stat-label">Status</span><span class="stat-val">${{n.status}}</span></div>
      <div class="stat-row"><span class="stat-label">Connected to</span><span class="stat-val">${{n.conn||'—'}}</span></div>
    </div>
    <div class="gauge-wrap">
      <div class="gauge-label">Traffic — ${{n.traffic}} pkts/s</div>
      <div class="gauge-bar"><div class="gauge-fill" style="width:${{tp}}%;background:${{n.traffic>50?'#ef4444':'#22c55e'}}"></div></div>
    </div>
    <div class="gauge-wrap">
      <div class="gauge-label">Signal — ${{n.signal}} dBm</div>
      <div class="gauge-bar"><div class="gauge-fill" style="width:${{sp}}%;background:${{n.signal<40?'#ef4444':'#3b82f6'}}"></div></div>
    </div>
    <div class="gauge-wrap">
      <div class="gauge-label">Packet Rate — ${{n.packet_rate}}</div>
      <div class="gauge-bar"><div class="gauge-fill" style="width:${{pp}}%;background:#a855f7"></div></div>
    </div>
    <div style="margin-top:12px;padding:8px;background:#1e293b;border-radius:6px;font-size:11px;color:#94a3b8;line-height:1.6">
      ${{n.explanation}}
    </div>`;
  panel.style.display='block';
}});

function closePanel() {{ panel.style.display='none'; }}
function toggleFS() {{
  if(!document.fullscreenElement) {{
    document.documentElement.requestFullscreen();
    document.getElementById('fs-btn').textContent='✕ Exit';
  }} else {{
    document.exitFullscreen();
    document.getElementById('fs-btn').textContent='⛶ Fullscreen';
  }}
}}
tick();
</script>
</body>
</html>"""
    components.html(html, height=620, scrolling=False)

with col_alerts:
    st.subheader("🚨 Live Alerts")
    if len(anomalies) == 0:
        st.success("All devices normal")
    else:
        for _, row in anomalies.iterrows():
            atype = row['anomaly_type'].replace('_', ' ').upper()
            st.error(f"**{row['device_id']}** — `{atype}`\n\n{row['explanation']}")

st.divider()
st.subheader("📡 All Devices")
st.dataframe(
    results[['device_id','traffic','packet_rate','signal',
             'status','anomaly_type','explanation']],
    use_container_width=True
)

if auto:
    time.sleep(3)
    st.rerun()