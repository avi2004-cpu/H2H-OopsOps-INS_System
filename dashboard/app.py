import streamlit as st
import pandas as pd
import json, os, sys, time

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH    = os.path.join(ROOT, "network_simulation", "data", "network_data.csv")
TOPO_PATH   = os.path.join(ROOT, "network_simulation", "data", "topology.json")
STATUS_PATH = os.path.join(ROOT, "network_simulation", "data", "sim_status.json")
sys.path.insert(0, ROOT)

from ml_model.model import AnomalyDetector

st.set_page_config(page_title="INS-System", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Rajdhani',sans-serif;background:#030712;color:#e2e8f0;}
.stApp{background:#030712;}
#MainMenu,footer,header{visibility:hidden;}
[data-testid="stToolbar"]{display:none;}
.block-container{padding:1.5rem 2rem;max-width:100%;}
.icard{background:#0d1424;border:1px solid #1e293b;border-radius:8px;padding:.9rem 1.1rem;margin-bottom:6px;}
.icard-t{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#64748b;margin-bottom:3px;}
.icard-v{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:600;}
.stButton>button{font-family:'Rajdhani',sans-serif;font-weight:600;letter-spacing:.06em;border-radius:6px;border:1px solid #334155;background:#0d1424;color:#94a3b8;}
.stButton>button:hover{border-color:#00ff88;color:#00ff88;background:#0a1a0f;}
.stTextInput>div>div>input{background:#0d1424!important;border:1px solid #1e293b!important;color:#e2e8f0!important;font-family:'JetBrains Mono',monospace;border-radius:6px;}
.stTextInput>label,.stSelectbox>label{color:#64748b!important;font-size:12px;}
.ph{display:flex;align-items:center;gap:12px;border-bottom:1px solid #1e293b;padding-bottom:1rem;margin-bottom:1.5rem;}
.ph h1{font-size:21px;font-weight:700;margin:0;color:#f1f5f9;}
.tag{font-family:'JetBrains Mono',monospace;font-size:11px;color:#00ff88;background:#0a1a0f;border:1px solid #00ff88;padding:2px 8px;border-radius:4px;}
.ar{display:flex;align-items:flex-start;gap:9px;padding:7px 11px;margin-bottom:5px;border-radius:6px;font-size:13px;line-height:1.5;}
.ac{background:#1a0505;border-left:3px solid #ef4444;}
.ah{background:#1a0e05;border-left:3px solid #f97316;}
.am{background:#141a05;border-left:3px solid #eab308;}
.al{background:#05141a;border-left:3px solid #06b6d4;}
.dr{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #1e293b;}
.dk{color:#64748b;font-size:12px;} .dv{color:#cbd5e1;font-family:'JetBrains Mono',monospace;font-size:12px;}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in {"logged_in":False,"page":"login","sel_net":None,"sel_dev":None}.items():
    if k not in st.session_state: st.session_state[k]=v

NETWORKS=[
    {"id":"net_a","name":"Campus Network A","location":"Building 1 — Floor 2","aps":3,"switches":2},
    {"id":"net_b","name":"Campus Network B","location":"Building 2","aps":2,"switches":1},
    {"id":"net_lab","name":"IoT Lab","location":"Research Lab","aps":3,"switches":2},
]
SC={"critical":"#ef4444","high":"#f97316","medium":"#eab308","low":"#06b6d4","none":"#00ff88"}
SS={"critical":"ac","high":"ah","medium":"am","low":"al"}

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3)
def load_csv(): return pd.read_csv(CSV_PATH)

@st.cache_resource
def get_detector():
    df=pd.read_csv(CSV_PATH); det=AnomalyDetector(contamination=0.1); det.train(df); return det

@st.cache_data(ttl=60)
def load_topo():
    with open(TOPO_PATH) as f: return json.load(f)

def load_status():
    try:
        with open(STATUS_PATH) as f: return json.load(f)
    except: return {}

def get_results():
    try:
        df=load_csv()
        latest=df.sort_values("timestamp").groupby("device_id").last().reset_index()
        return get_detector().predict(latest), df
    except Exception as e:
        st.error(f"Data error: {e}"); st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown("""<div style="text-align:center;margin:60px 0 2rem;">
          <div style="font-size:48px;">🛡️</div>
          <h1 style="font-size:30px;font-weight:700;letter-spacing:.12em;color:#f1f5f9;">INS System</h1>
          <p style="font-size:11px;color:#475569;letter-spacing:.15em;">INTELLIGENT NETWORK SURVEILLANCE SYSTEM</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("##### Sign in to continue")
        username=st.text_input("USERNAME",placeholder="Username")
        password=st.text_input("PASSWORD",type="password",placeholder="••••••••")
        if st.button("AUTHENTICATE →",use_container_width=True):
            if username=="admin" and password=="admin":
                st.session_state.logged_in=True; st.session_state.page="dashboard"; st.rerun()
            else: st.error("Invalid credentials — use admin / admin")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center;font-size:12px;color:#334155;margin-top:1rem;">Hack2Hire 1.0 · Team OopsOps</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    results,_=get_results(); status=load_status()
    anoms=results[results["is_anomaly"]]; n,na=len(results),len(anoms)
    st.markdown(f"""<div class="ph"><h1>🛡️ INSS Dashboard</h1><span class="tag">LIVE</span>
      <span style="margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:12px;color:#475569;">
        Tick #{status.get('tick','—')} · {time.strftime('%H:%M:%S')}</span></div>""",unsafe_allow_html=True)
    for col,(lb,val,c) in zip(st.columns(5),[
        ("TOTAL DEVICES",str(n),"#94a3b8"),("ANOMALIES",str(na),"#ef4444" if na else "#00ff88"),
        ("NORMAL",str(n-na),"#00ff88"),("SIM TICK",str(status.get("tick","—")),"#00d4ff"),
        ("LAST EVENT",str(status.get("last_anomaly","—"))[:22],"#eab308"),
    ]):
        with col: st.markdown(f'<div class="icard"><div class="icard-t">{lb}</div><div class="icard-v" style="color:{c};">{val}</div></div>',unsafe_allow_html=True)
    st.markdown("<br>**Available Networks**",unsafe_allow_html=True)
    for col,net in zip(st.columns(len(NETWORKS)),NETWORKS):
        with col:
            la=na if net["id"]=="net_a" else 0; ld=n if net["id"]=="net_a" else net["aps"]*4
            st.markdown(f"""<div class="icard" style="border-top:3px solid #00ff88;">
              <div style="font-size:16px;font-weight:700;color:#f1f5f9;margin-bottom:3px;">{net['name']}</div>
              <div style="font-size:12px;color:#64748b;margin-bottom:10px;">{net['location']}</div>
              <span style="font-family:'JetBrains Mono',monospace;font-size:13px;color:{'#ef4444' if la else '#00ff88'};margin-right:14px;">{la} alerts</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:13px;color:#94a3b8;">{ld} devices</span>
            </div>""",unsafe_allow_html=True)
            if st.button("Monitor →",key=f"btn_{net['id']}",use_container_width=True):
                st.session_state.sel_net=net; st.session_state.page="topology"; st.rerun()
    st.markdown("<br>",unsafe_allow_html=True)
    cf,cs=st.columns([2,1])
    with cf:
        st.markdown("#### Recent Alerts")
        if anoms.empty: st.markdown('<div class="icard" style="color:#00ff88;font-size:13px;">✓ All devices normal</div>',unsafe_allow_html=True)
        else:
            for _,row in anoms.head(8).iterrows():
                sv=row.get("severity","low"); c=SC.get(sv,"#06b6d4"); cl=SS.get(sv,"al")
                at=str(row.get("anomaly_type","?")).replace("_"," ").upper()
                st.markdown(f"""<div class="ar {cl}"><div style="width:8px;height:8px;border-radius:50%;background:{c};margin-top:4px;flex-shrink:0;"></div>
                  <div><b style="font-family:'JetBrains Mono',monospace;font-size:11px;">{row['device_id']}</b>
                  <span style="color:{c};font-size:11px;font-weight:600;margin-left:8px;">{at}</span>
                  <div style="color:#94a3b8;font-size:12px;">{str(row.get('explanation',''))[:90]}</div></div></div>""",unsafe_allow_html=True)
    with cs:
        st.markdown("#### Severity")
        if not anoms.empty:
            for sv,cnt in anoms["severity"].value_counts().items():
                c=SC.get(sv,"#64748b"); pct=int(cnt/len(anoms)*100)
                st.markdown(f"""<div style="margin-bottom:8px;">
                  <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
                    <span style="color:{c};font-weight:600;text-transform:uppercase;">{sv}</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#94a3b8;">{cnt}</span></div>
                  <div style="background:#1e293b;border-radius:3px;height:5px;">
                    <div style="width:{pct}%;background:{c};height:100%;border-radius:3px;"></div></div></div>""",unsafe_allow_html=True)
    if st.checkbox("Auto-refresh (3s)",key="dash_auto"): time.sleep(3); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TOPOLOGY  — reads topology.json directly for reliable graph
# ══════════════════════════════════════════════════════════════════════════════
def page_topology():
    results,_=get_results(); topo=load_topo(); status_obj=load_status()
    anoms=results[results["is_anomaly"]]; anom_ids=set(anoms["device_id"].tolist())
    net=st.session_state.sel_net or NETWORKS[0]

    st.markdown(f"""<div class="ph"><h1>📡 {net['name']}</h1>
      <span class="tag">{net['location']}</span></div>""",unsafe_allow_html=True)
    c1,c2,_=st.columns([1,1,4])
    with c1:
        if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    with c2:
        if st.button("Details & Filters"): st.session_state.page="details"; st.rerun()

    # Build enriched node list from topology.json
    res_lkp={r["device_id"]:r for r in results.to_dict("records")}
    lbl_map={"camera":"CAM","thermostat":"THERM","phone":"PHONE","smart_light":"LIGHT",
              "sensor":"SENS","switch":"SW","access_point":"AP","unknown":"UNK"}

    topo_nodes=[]
    for n in topo["nodes"]:
        nid=n["id"]; ntype=n.get("type","device")
        row=res_lkp.get(nid,{})
        faulty=(nid in anom_ids) or int(row.get("mac_changed",0))==1 or str(row.get("status","active"))=="offline"
        is_rogue=str(row.get("mac","")).startswith("RG:")

        if ntype=="switch":         color,border="rgb(100,160,255)","rgb(60,120,220)"
        elif ntype=="access_point": color,border="rgb(255,215,0)",  "rgb(200,160,0)"
        elif faulty:                color,border="rgb(255,30,30)",  "rgb(200,20,20)"
        else:                       color,border="rgb(0,255,80)",   "rgb(0,180,55)"

        topo_nodes.append({
            "id":nid,"type":ntype,"color":color,"border":border,
            "label":lbl_map.get(ntype,ntype[:4].upper()),
            "is_anomaly":faulty,"is_rogue":is_rogue,
            "traffic":int(row.get("traffic",0)),"signal":int(row.get("signal",0)),
            "packet_rate":int(row.get("packet_rate",0)),
            "status":str(row.get("status","—")),"mac":str(row.get("mac","—")),
            "anomaly_type":str(row.get("anomaly_type","normal")),
            "severity":str(row.get("severity","none")),
            "explanation":str(row.get("explanation",""))[:120],
        })

    # Edges use "source"/"target" from NetworkX json_graph export
    topo_edges=[{"from":e["source"],"to":e["target"]} for e in topo["edges"]]

    nodes_json=json.dumps(topo_nodes)
    edges_json=json.dumps(topo_edges)

    col_canvas,col_panel=st.columns([3,1])

    with col_canvas:
        import streamlit.components.v1 as components
        html=f"""<!DOCTYPE html>
<html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#030712;overflow:hidden;}}
#wrap{{width:100%;height:400px;position:relative;}}
canvas{{position:absolute;top:0;left:0;width:100%;height:100%;}}
#tip{{position:absolute;display:none;pointer-events:none;z-index:20;
  background:rgba(10,15,30,0.97);border:1px solid #1e293b;border-radius:8px;
  padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:11px;
  color:#e2e8f0;min-width:190px;line-height:1.9;box-shadow:0 4px 24px rgba(0,0,0,.8);}}
#leg{{position:absolute;bottom:10px;left:12px;display:flex;gap:14px;}}
.lg{{display:flex;align-items:center;gap:5px;font-size:11px;color:#64748b;}}
.ld{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
</style></head>
<body><div id="wrap">
<canvas id="c"></canvas>
<div id="tip"></div>
<div id="leg">
  <div class="lg"><div class="ld" style="background:rgb(0,255,80)"></div>Normal</div>
  <div class="lg"><div class="ld" style="background:rgb(255,30,30)"></div>Anomaly</div>
  <div class="lg"><div class="ld" style="background:rgb(255,215,0)"></div>Access Point</div>
  <div class="lg"><div class="ld" style="background:rgb(100,160,255)"></div>Switch</div>
  <div class="lg"><div class="ld" style="background:white"></div>Packets</div>
</div>
</div>
<script>
const NODES={nodes_json};
const EDGES={edges_json};
const wrap=document.getElementById('wrap');
const cv=document.getElementById('c');
const ctx=cv.getContext('2d');
const tip=document.getElementById('tip');

function resize(){{cv.width=wrap.offsetWidth;cv.height=wrap.offsetHeight;}}
resize();
window.addEventListener('resize',()=>{{resize();layout();}});

/* ── Hierarchical layout ── */
const pos={{}};
function layout(){{
  const W=cv.width,H=cv.height;
  const switches=NODES.filter(n=>n.type==='switch');
  const aps=NODES.filter(n=>n.type==='access_point');
  const devs=NODES.filter(n=>n.type!=='switch'&&n.type!=='access_point');

  /* Row 1: switches */
  switches.forEach((n,i)=>{{
    pos[n.id]={{x:W/2+(i-(switches.length-1)/2)*170,y:H*0.14}};
  }});

  /* Row 2: APs */
  aps.forEach((n,i)=>{{
    pos[n.id]={{x:W*0.12+(W*0.76)*i/Math.max(aps.length-1,1),y:H*0.42}};
  }});

  /* Row 3: devices grouped under their parent AP */
  const apKids={{}};
  aps.forEach(ap=>apKids[ap.id]=[]);
  devs.forEach(d=>{{
    let found=false;
    for(const e of EDGES){{
      if((e.from===d.id&&apKids[e.to]!==undefined)){{apKids[e.to].push(d.id);found=true;break;}}
      if((e.to===d.id&&apKids[e.from]!==undefined)){{apKids[e.from].push(d.id);found=true;break;}}
    }}
    if(!found){{const first=aps[0];if(first)apKids[first.id].push(d.id);}}
  }});

  aps.forEach(ap=>{{
    const kids=apKids[ap.id]||[];
    const apX=pos[ap.id].x;
    const spread=Math.min(kids.length*58,W*0.38);
    kids.forEach((did,i)=>{{
      const xOff=kids.length>1?-spread/2+spread*i/(kids.length-1):0;
      pos[did]={{x:apX+xOff,y:H*0.76+(i%2)*28}};
    }});
  }});
}}
layout();

/* ── Particles ── */
const parts=[];
function spawnParts(){{
  if(Math.random()>0.3)return;
  const e=EDGES[Math.floor(Math.random()*EDGES.length)];
  if(!pos[e.from]||!pos[e.to])return;
  const rev=Math.random()>0.5;
  parts.push({{
    from:rev?e.to:e.from,to:rev?e.from:e.to,
    t:0,speed:0.009+Math.random()*0.011,sz:1.8+Math.random()*2.2
  }});
}}
function tickParts(){{
  for(let i=parts.length-1;i>=0;i--){{
    parts[i].t+=parts[i].speed;
    if(parts[i].t>=1)parts.splice(i,1);
  }}
}}
function drawParts(){{
  parts.forEach(p=>{{
    const a=pos[p.from],b=pos[p.to];
    if(!a||!b)return;
    const x=a.x+(b.x-a.x)*p.t,y=a.y+(b.y-a.y)*p.t;
    const alpha=p.t<0.12?p.t/0.12:p.t>0.85?(1-p.t)/0.15:1;
    ctx.save();
    ctx.globalAlpha=alpha*0.95;
    ctx.shadowBlur=8;ctx.shadowColor='#ffffff';
    ctx.beginPath();ctx.arc(x,y,p.sz,0,2*Math.PI);
    ctx.fillStyle='rgba(255,255,255,0.95)';ctx.fill();
    ctx.restore();
  }});
}}

/* ── Node radius ── */
function nr(n){{
  if(n.type==='switch')return 26;
  if(n.type==='access_point')return 22;
  return 16;
}}

/* ── Draw ── */
function draw(){{
  ctx.clearRect(0,0,cv.width,cv.height);

  /* grid */
  ctx.strokeStyle='rgba(30,41,59,0.3)';ctx.lineWidth=1;
  for(let x=0;x<cv.width;x+=42){{ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,cv.height);ctx.stroke();}}
  for(let y=0;y<cv.height;y+=42){{ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(cv.width,y);ctx.stroke();}}

  /* edges */
  EDGES.forEach(e=>{{
    const a=pos[e.from],b=pos[e.to];
    if(!a||!b)return;
    const fn=NODES.find(n=>n.id===e.from),tn=NODES.find(n=>n.id===e.to);
    const alert=fn?.is_anomaly||tn?.is_anomaly;
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
    ctx.strokeStyle=alert?'rgba(255,40,40,0.45)':'rgba(0,180,60,0.28)';
    ctx.lineWidth=alert?1.5:1;
    if(alert)ctx.setLineDash([5,4]);
    ctx.stroke();ctx.setLineDash([]);
  }});

  /* particles */
  drawParts();

  /* nodes */
  NODES.forEach(n=>{{
    const p=pos[n.id];
    if(!p)return;
    const r=nr(n);

    /* pulse ring for anomalies */
    if(n.is_anomaly){{
      const pulse=(Date.now()%1300)/1300;
      ctx.beginPath();ctx.arc(p.x,p.y,r+5+pulse*16,0,2*Math.PI);
      ctx.strokeStyle=`rgba(255,30,30,${{(0.75*(1-pulse)).toFixed(2)}})`;
      ctx.lineWidth=2;ctx.stroke();
    }}

    /* glow halo */
    const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r+12);
    g.addColorStop(0,n.color.replace('rgb','rgba').replace(')',',0.2)'));
    g.addColorStop(1,'rgba(0,0,0,0)');
    ctx.beginPath();ctx.arc(p.x,p.y,r+12,0,2*Math.PI);
    ctx.fillStyle=g;ctx.fill();

    /* circle body */
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,2*Math.PI);
    ctx.fillStyle=n.color.replace('rgb','rgba').replace(')',',0.16)');
    ctx.strokeStyle=n.border;ctx.lineWidth=2.5;
    ctx.fill();ctx.stroke();

    /* bright centre dot */
    ctx.beginPath();ctx.arc(p.x,p.y,r*0.3,0,2*Math.PI);
    ctx.fillStyle=n.color;ctx.fill();

    /* label text */
    ctx.font=`bold ${{n.type==='switch'?11:10}}px monospace`;
    ctx.fillStyle='#f1f5f9';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(n.label,p.x,p.y);

    /* id below */
    ctx.font='9px monospace';
    ctx.fillStyle=n.is_anomaly?'rgba(255,80,80,0.85)':'#475569';
    ctx.fillText(n.id,p.x,p.y+r+11);
  }});
}}

/* ── Tooltip ── */
let hov=null;
canvas=cv; // alias
cv.addEventListener('mousemove',ev=>{{
  const rc=cv.getBoundingClientRect();
  const mx=(ev.clientX-rc.left)*(cv.width/rc.width);
  const my=(ev.clientY-rc.top)*(cv.height/rc.height);
  hov=null;
  NODES.forEach(n=>{{
    const p=pos[n.id];if(!p)return;
    const dx=p.x-mx,dy=p.y-my;
    if(Math.sqrt(dx*dx+dy*dy)<nr(n)+5)hov=n;
  }});
  if(hov){{
    tip.style.display='block';
    tip.style.left=(ev.clientX+16)+'px';
    tip.style.top=(ev.clientY-10)+'px';
    const c=hov.is_anomaly?'#ef4444':'#00ff88';
    tip.innerHTML=`<b style="color:#f1f5f9;font-size:12px;">${{hov.id}}</b><br>
<span style="color:#64748b">type &nbsp;&nbsp;</span><span style="color:#cbd5e1">${{hov.type}}</span><br>
<span style="color:#64748b">status &nbsp;</span><span style="color:${{c}}">${{hov.status}}</span><br>
<span style="color:#64748b">traffic</span><span style="color:#cbd5e1"> ${{hov.traffic}} pkts/s</span><br>
<span style="color:#64748b">signal &nbsp;</span><span style="color:#cbd5e1"> ${{hov.signal}} dBm</span>
${{hov.is_anomaly?`<br><span style="color:#ef4444;font-weight:600">⚠ ${{hov.anomaly_type.replace(/_/g,' ').toUpperCase()}}</span>`:''}}`;
    cv.style.cursor='pointer';
  }}else{{tip.style.display='none';cv.style.cursor='default';}}
}});
cv.addEventListener('mouseleave',()=>tip.style.display='none');

/* ── Animation loop ── */
(function loop(){{spawnParts();tickParts();draw();requestAnimationFrame(loop);}}());
</script></body></html>"""
        components.html(html, height=600, scrolling=False)

    # ── Side panel ───────────────────────────────────────────────────────────
    with col_panel:
        st.markdown("#### Sim Status")
        st.markdown(f"""<div class="icard">
          <div style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#00ff88;">● LIVE — Tick {status_obj.get('tick','—')}</div>
          <div style="font-size:12px;color:#64748b;margin-top:4px;">Injected: {status_obj.get('anomaly_count','—')} anomalies</div>
          <div style="font-size:11px;color:#475569;word-break:break-all;">Last: {str(status_obj.get('last_anomaly','—'))[:34]}</div>
        </div>""",unsafe_allow_html=True)

        st.markdown("#### Devices")
        for _,row in results.sort_values("is_anomaly",ascending=False).iterrows():
            dev=row["device_id"]; ia=dev in anom_ids
            sev=row.get("severity","none"); c=SC.get(sev,"#00ff88") if ia else "#00ff88"
            icon="⚠" if ia else "✓"
            with st.expander(f"{icon} {dev}",expanded=False):
                at=str(row.get("anomaly_type","normal")).replace("_"," ")
                st.markdown(f"""<div>
                  <div class="dr"><span class="dk">Type</span><span class="dv">{row.get('type','?')}</span></div>
                  <div class="dr"><span class="dk">Traffic</span><span class="dv">{int(row['traffic'])} pkts/s</span></div>
                  <div class="dr"><span class="dk">Signal</span><span class="dv">{int(row['signal'])} dBm</span></div>
                  <div class="dr"><span class="dk">Status</span><span class="dv" style="color:{c}">{row.get('status','?')}</span></div>
                  <div class="dr"><span class="dk">Anomaly</span><span class="dv" style="color:{c}">{at}</span></div>
                  <div class="dr"><span class="dk">Severity</span><span class="dv" style="color:{c}">{sev}</span></div>
                </div>""",unsafe_allow_html=True)
                if st.button("Full Details →",key=f"det_{dev}"):
                    st.session_state.sel_dev=dev; st.session_state.page="details"; st.rerun()

    if st.checkbox("Auto-refresh (3s)",key="topo_auto"): time.sleep(3); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# DETAILS
# ══════════════════════════════════════════════════════════════════════════════
def page_details():
    results,df=get_results()
    st.markdown('<div class="ph"><h1>🔬 Anomaly Analysis</h1><span class="tag">FILTER MODE</span></div>',unsafe_allow_html=True)
    c1,_=st.columns([1,5])
    with c1:
        if st.button("← Topology"): st.session_state.page="topology"; st.rerun()

    st.markdown("#### Filters")
    f1,f2,f3,f4,f5=st.columns(5)
    with f1: ao=st.checkbox("Anomalies only",value=True)
    with f2: at_s=st.selectbox("Anomaly type",["ALL"]+sorted(results["anomaly_type"].dropna().unique().tolist()))
    with f3: sv_s=st.selectbox("Severity",["ALL","critical","high","medium","low","none"])
    with f4: dt_s=st.selectbox("Device type",["ALL"]+sorted(results["type"].dropna().unique().tolist()))
    with f5:
        tmn,tmx=int(results["traffic"].min()),int(results["traffic"].max())
        thr=st.slider("Min traffic",tmn,max(tmx,1),tmn)

    fil=results.copy()
    if ao:         fil=fil[fil["is_anomaly"]]
    if at_s!="ALL":fil=fil[fil["anomaly_type"]==at_s]
    if sv_s!="ALL":fil=fil[fil["severity"]==sv_s]
    if dt_s!="ALL":fil=fil[fil["type"]==dt_s]
    fil=fil[fil["traffic"]>=thr]

    if st.session_state.sel_dev:
        dev=st.session_state.sel_dev; sel=results[results["device_id"]==dev]
        if not sel.empty:
            row=sel.iloc[0]; sv=row.get("severity","none"); c=SC.get(sv,"#00ff88")
            st.markdown(f"#### Focused — `{dev}`")
            for col,(lb,val,cc) in zip(st.columns(4),[
                ("ANOMALY TYPE",str(row.get("anomaly_type","normal")).replace("_"," ").upper(),c),
                ("SEVERITY",sv.upper(),c),
                ("CONFIDENCE",str(row.get("confidence","—")).upper(),"#00d4ff"),
                ("TRAFFIC",f"{int(row['traffic'])} pkts/s","#eab308"),
            ]):
                with col: st.markdown(f'<div class="icard"><div class="icard-t">{lb}</div><div class="icard-v" style="color:{cc};font-size:17px;">{val}</div></div>',unsafe_allow_html=True)
            cls=SS.get(sv,"al")
            st.markdown(f'<div class="ar {cls}" style="margin:10px 0 16px;"><div style="color:{c};font-size:13px;">{row.get("explanation","")}</div></div>',unsafe_allow_html=True)
            hist=df[df["device_id"]==dev].tail(60)
            if not hist.empty:
                h1,h2=st.columns(2)
                with h1: st.markdown("**Traffic**"); st.line_chart(hist.set_index("timestamp")[["traffic"]],height=160,use_container_width=True)
                with h2: st.markdown("**Signal & Packets**"); st.line_chart(hist.set_index("timestamp")[["signal","packet_rate"]],height=160,use_container_width=True)
            if st.button("Clear focus"): st.session_state.sel_dev=None; st.rerun()
            st.markdown("---")

    af=fil[fil["is_anomaly"]]
    st.markdown(f"#### Results — {len(fil)} devices")
    for col,(lb,val,c) in zip(st.columns(4),[
        ("SHOWN",str(len(fil)),"#94a3b8"),
        ("ANOMALIES",str(len(af)),"#ef4444" if len(af) else "#00ff88"),
        ("AVG TRAFFIC",f"{fil['traffic'].mean():.0f}" if not fil.empty else "—","#00d4ff"),
        ("AVG SIGNAL",f"{fil['signal'].mean():.0f}" if not fil.empty else "—","#eab308"),
    ]):
        with col: st.markdown(f'<div class="icard"><div class="icard-t">{lb}</div><div class="icard-v" style="color:{c};">{val}</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    if not af.empty:
        st.markdown("#### Anomaly Events")
        for _,row in af.iterrows():
            sv=row.get("severity","low"); c=SC.get(sv,"#06b6d4"); cl=SS.get(sv,"al")
            at=str(row.get("anomaly_type","?")).replace("_"," ").upper()
            st.markdown(f"""<div class="ar {cl}">
              <div style="width:10px;height:10px;border-radius:50%;background:{c};margin-top:3px;flex-shrink:0;"></div>
              <div style="flex:1;"><b style="font-family:'JetBrains Mono',monospace;font-size:11px;">{row['device_id']}</b>
              <span style="color:{c};font-size:11px;font-weight:600;margin-left:10px;">{at}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#334155;margin-left:6px;">sev:{sv} conf:{row.get('confidence','?')}</span>
              <div style="color:#94a3b8;font-size:12px;">{str(row.get('explanation',''))}</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#334155;margin-top:2px;">
                traffic:{int(row['traffic'])} · signal:{int(row['signal'])} · mac:{str(row.get('mac','?'))[:18]}</div></div>
            </div>""",unsafe_allow_html=True)

    st.markdown("#### Device Table")
    dc=["device_id","type","traffic","packet_rate","signal","status","mac_changed","anomaly_type","severity","confidence","explanation"]
    st.dataframe(fil[[c for c in dc if c in fil.columns]].reset_index(drop=True),use_container_width=True,height=320)

    with st.expander("📁 Historical log (last 200 rows)"):
        hd=st.selectbox("Filter device",["ALL"]+sorted(df["device_id"].unique().tolist()),key="hdev")
        hdf=df if hd=="ALL" else df[df["device_id"]==hd]
        st.dataframe(hdf.tail(200).reset_index(drop=True),use_container_width=True,height=260)

    if st.checkbox("Auto-refresh (3s)",key="det_auto"): time.sleep(3); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:                page_login()
elif st.session_state.page=="dashboard":          page_dashboard()
elif st.session_state.page=="topology":           page_topology()
elif st.session_state.page=="details":            page_details()
else:                                             page_login()