import streamlit as st
import pandas as pd
import json, os, sys, time
import altair as alt

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH    = os.path.join(ROOT, "network_simulation", "data", "network_data.csv")
TOPO_PATH   = os.path.join(ROOT, "network_simulation", "data", "topology.json")
STATUS_PATH = os.path.join(ROOT, "network_simulation", "data", "sim_status.json")
sys.path.insert(0, ROOT)

from ml_model.model import AnomalyDetector

st.set_page_config(page_title="INS-System", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")

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

for k,v in {"logged_in":False,"page":"login","sel_net":None,"sel_dev":None}.items():
    if k not in st.session_state: st.session_state[k]=v

NETWORKS=[
    {"id":"net_a","name":"Campus Network A","location":"Building 1 — Floor 2","aps":3,"switches":2},
    {"id":"net_b","name":"Campus Network B","location":"Building 2","aps":2,"switches":1},
    {"id":"net_lab","name":"IoT Lab","location":"Research Lab","aps":3,"switches":2},
]
SC={"critical":"#ef4444","high":"#f97316","medium":"#eab308","low":"#06b6d4","none":"#00ff88"}
SS={"critical":"ac","high":"ah","medium":"am","low":"al"}

@st.cache_data(ttl=3)
def load_csv():
    df = pd.read_csv(CSV_PATH)

    # ✅ Fix data types
    df["traffic"] = pd.to_numeric(df["traffic"], errors="coerce")
    df["signal"] = pd.to_numeric(df["signal"], errors="coerce")
    df["packet_rate"] = pd.to_numeric(df["packet_rate"], errors="coerce")
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")

    # remove bad rows (optional but safe)
    df = df.dropna()

    return df

@st.cache_resource
def get_detector():
    df= load_csv(); det=AnomalyDetector(contamination=0.1); det.train(df); return det

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
        st.markdown('<p style="text-align:center;font-size:12px;color:#334155;margin-top:1rem;">Hack2Hire 1.0 · Team OopsOps</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    results,df=get_results(); status=load_status()
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
# TOPOLOGY — circular layout, 3 view modes, coloured animated wires
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
        if st.button("Analytics →"): st.session_state.page="details"; st.rerun()

    res_lkp={r["device_id"]:r for r in results.to_dict("records")}
    lbl_map={"camera":"CAM","thermostat":"THERM","phone":"PHONE","smart_light":"LIGHT",
              "sensor":"SENS","switch":"SW","access_point":"AP","unknown":"UNK"}
    topo_nodes=[]
    for n in topo["nodes"]:
        nid=n["id"]; ntype=n.get("type","device")
        row=res_lkp.get(nid,{})
        faulty=(nid in anom_ids) or int(row.get("mac_changed",0))==1 or str(row.get("status","active"))=="offline"
        if ntype=="switch":         color,border="rgb(100,160,255)","rgb(60,120,220)"
        elif ntype=="access_point": color,border="rgb(255,200,0)",  "rgb(200,150,0)"
        elif faulty:                color,border="rgb(255,40,40)",  "rgb(200,20,20)"
        else:                       color,border="rgb(0,255,120)",  "rgb(0,180,80)"
        topo_nodes.append({
            "id":nid,"type":ntype,"color":color,"border":border,
            "label":lbl_map.get(ntype,ntype[:4].upper()),
            "is_anomaly":faulty,
            "traffic":int(row.get("traffic",0)),"signal":int(row.get("signal",0)),
            "packet_rate":int(row.get("packet_rate",0)),
            "status":str(row.get("status","—")),"mac":str(row.get("mac","—")),
            "anomaly_type":str(row.get("anomaly_type","normal")),
            "severity":str(row.get("severity","none")),
            "explanation":str(row.get("explanation",""))[:130],
        })
    topo_edges=[{"from":e["source"],"to":e["target"]} for e in topo["edges"]]
    net_id = (st.session_state.sel_net or NETWORKS[0])['id']
    if net_id == 'net_b':
      allowed = set([n['id'] for n in topo['nodes'] 
                   if 'ap_2' in n['id'] or 'switch_2' in n['id'] 
                   or n.get('connected_to') == 'ap_2'])
      topo_nodes = [n for n in topo_nodes if n['id'] in allowed or n['type'] in ('switch','access_point')]
      topo_edges = [e for e in topo_edges if e['from'] in allowed or e['to'] in allowed]
    elif net_id == 'net_lab':
      allowed = set([n['id'] for n in topo['nodes'] 
                   if 'ap_3' in n['id'] or 'switch_1' in n['id']
                   or n.get('connected_to') == 'ap_3'])
      topo_nodes = [n for n in topo_nodes if n['id'] in allowed or n['type'] in ('switch','access_point')]
      topo_edges = [e for e in topo_edges if e['from'] in allowed or e['to'] in allowed]
    # 🔥 ADD INTERNET + ROUTER (DO NOT REMOVE EXISTING CODE)

    topo_nodes.insert(0, {
        "id": "internet",
        "type": "internet",
        "color": "rgb(0,200,255)",
        "border": "rgb(0,150,200)",
        "label": "NET",
        "is_anomaly": False
    })

    topo_nodes.insert(1, {
        "id": "router_main",
        "type": "router",
        "color": "rgb(0,255,200)",
        "border": "rgb(0,200,150)",
        "label": "RTR",
        "is_anomaly": False
    })

    topo_edges.insert(0, {"from": "internet", "to": "router_main"})

    for n in topo_nodes:
        if n["type"] == "switch":
            topo_edges.append({"from": "router_main", "to": n["id"]})  
    nodes_json=json.dumps(topo_nodes)
    edges_json=json.dumps(topo_edges)

    col_canvas,col_panel=st.columns([3,1])
    with col_canvas:
        import streamlit.components.v1 as components
        html=f"""<!DOCTYPE html><html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#030712;overflow:hidden;font-family:'JetBrains Mono',monospace;}}
#wrap{{width:100%;height:560px;position:relative;}}
canvas{{position:absolute;top:0;left:0;width:100%;height:100%;}}
#tip{{position:absolute;display:none;pointer-events:none;z-index:20;
  background:rgba(8,12,24,0.97);border:1px solid #1e3a5f;border-radius:10px;
  padding:12px 16px;font-size:11px;color:#e2e8f0;min-width:210px;
  line-height:2;box-shadow:0 4px 32px rgba(0,150,255,.15);}}
#leg{{position:absolute;bottom:12px;left:14px;display:flex;gap:16px;flex-wrap:wrap;}}
.lg{{display:flex;align-items:center;gap:6px;font-size:10px;color:#475569;}}
.ld{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
#mode{{position:absolute;top:10px;right:12px;display:flex;gap:6px;}}
.mb{{background:#0d1424;border:1px solid #1e293b;color:#64748b;padding:4px 10px;
  border-radius:5px;font-size:10px;cursor:pointer;font-family:monospace;}}
.mb.active,.mb:hover{{border-color:#00ff88;color:#00ff88;}}
</style></head>
<body><div id="wrap">
<canvas id="c"></canvas>
<div id="tip"></div>
<div id="mode">
  <button class="mb active" id="mb-circular" onclick="setMode('circular',this)">CIRCULAR</button>
  <button class="mb" id="mb-hierarchy" onclick="setMode('hierarchy',this)">HIERARCHY</button>
  <button class="mb" onclick="toggleFullscreen()">⛶</button>
</div>
<div id="leg">
  <div class="lg"><div class="ld" style="background:rgb(0,255,120)"></div>Normal</div>
  <div class="lg"><div class="ld" style="background:rgb(255,40,40)"></div>Anomaly</div>
  <div class="lg"><div class="ld" style="background:rgb(255,200,0)"></div>Access Point</div>
  <div class="lg"><div class="ld" style="background:rgb(100,160,255)"></div>Switch</div>
  <div class="lg"><div class="ld" style="background:rgba(255,255,255,0.8)"></div>Packets</div>
</div>
</div>
<script>
const NODES={nodes_json};
const EDGES={edges_json};
const wrap=document.getElementById('wrap');
const cv=document.getElementById('c');
const ctx=cv.getContext('2d');
const tip=document.getElementById('tip');
let layoutMode='circular';

function resize(){{
  cv.width = wrap.clientWidth;
  cv.height = wrap.clientHeight;}}
resize();
window.addEventListener('resize',()=>{{resize();applyLayout();}});
document.addEventListener('fullscreenchange', resize);

const pos={{}};
const vel={{}};

function circularLayout(){{
  const W=cv.width,H=cv.height,cx=W/2,cy=H/2;
  const internet=NODES.filter(n=>n.type==='internet');
  const router=NODES.filter(n=>n.type==='router');
  const switches=NODES.filter(n=>n.type==='switch');
  const aps=NODES.filter(n=>n.type==='access_point');
  const devs=NODES.filter(n=>!['internet','router','switch','access_point'].includes(n.type));

  internet.forEach(n=>{{pos[n.id]={{x:cx,y:cy-180}};vel[n.id]={{x:0,y:0}};}});
  router.forEach(n=>{{pos[n.id]={{x:cx,y:cy-120}};vel[n.id]={{x:0,y:0}};}});

  switches.forEach((n,i)=>{{
    const a=(2*Math.PI*i/Math.max(switches.length,1))-Math.PI/2;
    pos[n.id]={{x:cx+120*Math.cos(a),y:cy+20*Math.sin(a)}};vel[n.id]={{x:0,y:0}};
  }});

  aps.forEach((n,i)=>{{
    const a=(2*Math.PI*i/Math.max(aps.length,1))-Math.PI/2;
    pos[n.id]={{x:cx+210*Math.cos(a),y:cy+120*Math.sin(a)}};vel[n.id]={{x:0,y:0}};
  }});

  const apKids={{}};
  aps.forEach(ap=>{{apKids[ap.id]=[];}});
  devs.forEach(d=>{{
    let found=false;
    for(const e of EDGES){{
      if(e.from===d.id && apKids[e.to]!==undefined){{apKids[e.to].push(d.id);found=true;break;}}
      if(e.to===d.id && apKids[e.from]!==undefined){{apKids[e.from].push(d.id);found=true;break;}}
    }}
    if(!found && aps.length>0){{apKids[aps[0].id].push(d.id);}}
  }});

  aps.forEach(ap=>{{
    const kids=apKids[ap.id]||[];
    const baseAngle=Math.atan2(pos[ap.id].y-cy,pos[ap.id].x-cx);
    const spread=kids.length>1?0.55:0;
    kids.forEach((did,i)=>{{
      const t=kids.length>1?i/(kids.length-1):0.5;
      const a=baseAngle-spread/2+spread*t;
      pos[did]={{x:cx+315*Math.cos(a),y:cy+240*Math.sin(a)}};vel[did]={{x:0,y:0}};
    }});
  }});
}}

function hierarchyLayout(){{
  const W = cv.width;
  const H = cv.height;
  const internet = NODES.filter(n=>n.type==='internet');
  const router   = NODES.filter(n=>n.type==='router');
  const switches = NODES.filter(n=>n.type==='switch');
  const aps      = NODES.filter(n=>n.type==='access_point');
  const devs     = NODES.filter(n=>!['internet','router','switch','access_point'].includes(n.type));

  internet.forEach(n=>{{pos[n.id]={{x:W/2,y:H*0.08}};vel[n.id]={{x:0,y:0}};}});
  router.forEach(n=>{{pos[n.id]={{x:W/2,y:H*0.18}};vel[n.id]={{x:0,y:0}};}});

  switches.forEach((n,i)=>{{
    const x = W*0.16 + (i/(Math.max(switches.length-1,1)))*W*0.68;
    pos[n.id]={{x:x,y:H*0.32}};vel[n.id]={{x:0,y:0}};
  }});

  aps.forEach((n,i)=>{{
    const x = W*0.15 + (i/(Math.max(aps.length-1,1)))*W*0.7;
    pos[n.id]={{x:x,y:H*0.52}};vel[n.id]={{x:0,y:0}};
  }});

  const apKids={{}};
  aps.forEach(ap=>{{apKids[ap.id]=[];}});
  devs.forEach(d=>{{
    let found=false;
    for(const e of EDGES){{
      if(e.from===d.id && apKids[e.to]!==undefined){{apKids[e.to].push(d.id);found=true;break;}}
      if(e.to===d.id && apKids[e.from]!==undefined){{apKids[e.from].push(d.id);found=true;break;}}
    }}
    if(!found && aps.length>0){{apKids[aps[0].id].push(d.id);}}
  }});

  aps.forEach(ap=>{{
    const kids = apKids[ap.id]||[];
    const spread = Math.min(140, W*0.18);
    kids.forEach((child,i)=>{{
      const xOffset = kids.length > 1
        ? -spread/2 + (spread * i)/(kids.length - 1)
        : 0;
      pos[child] = {{x: pos[ap.id].x + xOffset, y: pos[ap.id].y + 120}};
      vel[child] = {{x:0,y:0}};
    }});
  }});

  const placed = new Set(Object.values(apKids).flat());
  const leftovers = devs.filter(d=>!placed.has(d.id));
  leftovers.forEach((d,i)=>{{
    const x = W*0.15 + (i/(Math.max(leftovers.length-1,1)))*W*0.7;
    pos[d.id] = {{x:x,y:H*0.78}};
    vel[d.id] = {{x:0,y:0}};
  }});
}}

function forceInit(){{
  const W = cv.width;
  const H = cv.height;
  const radius = Math.min(W, H) * 0.34;
  NODES.forEach((n,i)=>{{
    const angle = 2*Math.PI*i/Math.max(NODES.length,1);
    pos[n.id] = {{
      x: W/2 + Math.cos(angle) * radius + (Math.random()-0.5) * 80,
      y: H/2 + Math.sin(angle) * radius + (Math.random()-0.5) * 80
    }};
    vel[n.id] = {{x:0, y:0}};
  }});
}}

function applyLayout(){{
  if(layoutMode==='circular')circularLayout();
  else if(layoutMode==='hierarchy')hierarchyLayout();
  else forceInit();
}}
applyLayout();

function setMode(m,btn){{
  layoutMode=m;
  document.querySelectorAll('.mb').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  applyLayout();
}}

let simSteps=0;
function simulate(){{
  if(layoutMode!=='force')return;
  const k=60,rep=5000,damp=0.82;
  NODES.forEach(a=>{{
    let fx=0,fy=0;
    NODES.forEach(b=>{{
      if(a.id===b.id)return;
      const dx=pos[a.id].x-pos[b.id].x,dy=pos[a.id].y-pos[b.id].y;
      const d=Math.max(Math.sqrt(dx*dx+dy*dy),1);
      fx+=rep*dx/(d*d*d);fy+=rep*dy/(d*d*d);
    }});
    EDGES.forEach(e=>{{
      let oid=e.from===a.id?e.to:e.to===a.id?e.from:null;
      if(!oid||!pos[oid])return;
      const dx=pos[oid].x-pos[a.id].x,dy=pos[oid].y-pos[a.id].y;
      const d=Math.max(Math.sqrt(dx*dx+dy*dy),1);
      fx+=k*(d-130)*dx/d;fy+=k*(d-130)*dy/d;
    }});
    fx+=(cv.width/2-pos[a.id].x)*0.015;fy+=(cv.height/2-pos[a.id].y)*0.015;
    vel[a.id].x=(vel[a.id].x+fx*0.016)*damp;
    vel[a.id].y=(vel[a.id].y+fy*0.016)*damp;
    pos[a.id].x+=vel[a.id].x;pos[a.id].y+=vel[a.id].y;
  }});
}}

const parts=[];
function spawnParts(){{
  if(Math.random()>0.35||!EDGES.length)return;
  const e=EDGES[Math.floor(Math.random()*EDGES.length)];
  if(!pos[e.from]||!pos[e.to])return;
  const fn=NODES.find(n=>n.id===e.from);
  const tn=NODES.find(n=>n.id===e.to);
  const alert=fn?.is_anomaly||tn?.is_anomaly;
  const count=alert?3:1;
  for(let i=0;i<count;i++){{
    const rev=Math.random()>0.5;
    parts.push({{
      from:rev?e.to:e.from,to:rev?e.from:e.to,
      t:Math.random()*0.2,speed:0.008+Math.random()*0.013,
      sz:alert?2.8+Math.random()*1.5:1.5+Math.random()*2,
      color:alert?'rgba(255,80,80,0.95)':'rgba(255,255,255,0.9)',
      glow:alert?'#ff4040':'#ffffff'
    }});
  }}
}}
function tickParts(){{for(let i=parts.length-1;i>=0;i--){{parts[i].t+=parts[i].speed;if(parts[i].t>=1)parts.splice(i,1);}}}}
function drawParts(){{
  parts.forEach(p=>{{
    const a=pos[p.from],b=pos[p.to];if(!a||!b)return;
    const x=a.x+(b.x-a.x)*p.t,y=a.y+(b.y-a.y)*p.t;
    const alpha=p.t<0.1?p.t/0.1:p.t>0.88?(1-p.t)/0.12:1;
    ctx.save();ctx.globalAlpha=alpha;
    ctx.shadowBlur=p.sz*4;ctx.shadowColor=p.glow;
    ctx.beginPath();ctx.arc(x,y,p.sz,0,2*Math.PI);
    ctx.fillStyle=p.color;ctx.fill();ctx.restore();
  }});
}}

function nr(n){{
  if(n.type==='internet') return 30;
  if(n.type==='router') return 28;
  if(n.type==='switch') return 26;
  if(n.type==='access_point') return 24;
  return 20;
  }}

function drawIcon(n, x, y) {{
  ctx.font = "18px Segoe UI Emoji";

  const icons = {{
    phone: "📱",
    camera: "📷",
    smart_light: "💡",
    thermostat: "🌡️",
    sensor: "📡",
    switch: "🔀",
    router: "📶",
    access_point: "📡",
    internet: "🌐",
    device: "🖥️",
    unknown: "❓"
  }};

  const icon = icons[n.type] || "🖥️";

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(icon, x, y);
}}

function draw(){{
  ctx.clearRect(0,0,cv.width,cv.height);
  ctx.strokeStyle='rgba(30,41,59,0.22)';ctx.lineWidth=1;
  for(let x=0;x<cv.width;x+=44){{ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,cv.height);ctx.stroke();}}
  for(let y=0;y<cv.height;y+=44){{ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(cv.width,y);ctx.stroke();}}

  EDGES.forEach(e=>{{
    const a=pos[e.from],b=pos[e.to];if(!a||!b)return;
    const fn=NODES.find(n=>n.id===e.from),tn=NODES.find(n=>n.id===e.to);
    const alert=fn?.is_anomaly||tn?.is_anomaly;
    const isAPSW=(fn?.type==='access_point'&&tn?.type==='switch')||(tn?.type==='access_point'&&fn?.type==='switch');
    // Glow
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
    ctx.strokeStyle=alert?'rgba(255,40,40,0.12)':isAPSW?'rgba(100,160,255,0.10)':'rgba(0,255,100,0.07)';
    ctx.lineWidth=8;ctx.shadowBlur=alert?14:0;ctx.shadowColor='rgba(255,40,40,0.35)';
    ctx.stroke();ctx.shadowBlur=0;
    // Core wire
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
    ctx.strokeStyle=alert?'rgba(255,60,60,0.65)':isAPSW?'rgba(100,160,255,0.45)':'rgba(0,220,80,0.28)';
    ctx.lineWidth=alert?2:1.5;
    if(alert)ctx.setLineDash([6,4]);else ctx.setLineDash([]);
    ctx.stroke();ctx.setLineDash([]);
  }});

  drawParts();

  NODES.forEach(n=>{{
    const p=pos[n.id];if(!p)return;
    const r=nr(n);
    if(n.is_anomaly){{
      const pulse=(Date.now()%1400)/1400;
      ctx.beginPath();ctx.arc(p.x,p.y,r+6+pulse*18,0,2*Math.PI);
      ctx.strokeStyle=`rgba(255,40,40,${{(0.8*(1-pulse)).toFixed(2)}})`;
      ctx.lineWidth=2.5;ctx.stroke();
    }}
    const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r+14);
    g.addColorStop(0,n.color.replace('rgb','rgba').replace(')',',0.18)'));
    g.addColorStop(1,'rgba(0,0,0,0)');
    ctx.beginPath();ctx.arc(p.x,p.y,r+14,0,2*Math.PI);ctx.fillStyle=g;ctx.fill();
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,2*Math.PI);
    ctx.fillStyle=n.color.replace('rgb','rgba').replace(')',',0.14)');
    ctx.strokeStyle=n.border;ctx.lineWidth=2.5;ctx.fill();ctx.stroke();
    ctx.beginPath();ctx.arc(p.x,p.y,r*0.32,0,2*Math.PI);ctx.fillStyle=n.color;ctx.fill();
    ctx.fillStyle='#f1f5f9';ctx.textAlign='center';ctx.textBaseline='middle';
    drawIcon(n, p.x, p.y);
    ctx.font='9px monospace';
    ctx.fillStyle=n.is_anomaly?'rgba(255,90,90,0.9)':'#334155';
    ctx.fillText(n.id,p.x,p.y+r+12);
  }});
}}

let hov=null;
cv.addEventListener('mousemove',ev=>{{
  const rc=cv.getBoundingClientRect();
  const mx=(ev.clientX-rc.left)*(cv.width/rc.width);
  const my=(ev.clientY-rc.top)*(cv.height/rc.height);
  hov=null;
  NODES.forEach(n=>{{const p=pos[n.id];if(!p)return;const dx=p.x-mx,dy=p.y-my;if(Math.sqrt(dx*dx+dy*dy)<nr(n)+6)hov=n;}});
  if(hov){{
    tip.style.display='block';
    tip.style.left=Math.min(ev.clientX+18,window.innerWidth-230)+'px';
    tip.style.top=(ev.clientY-14)+'px';
    const c=hov.is_anomaly?'#ef4444':'#00ff88';
    const sc2={{critical:'#ef4444',high:'#f97316',medium:'#eab308',low:'#06b6d4',none:'#00ff88'}};
    tip.innerHTML=`<b style="color:#f1f5f9;font-size:13px">${{hov.id}}</b><br>
<span style="color:#475569">type &nbsp;&nbsp;&nbsp;</span><span style="color:#cbd5e1">${{hov.type}}</span><br>
<span style="color:#475569">status &nbsp;</span><span style="color:${{c}}">${{hov.status}}</span><br>
<span style="color:#475569">traffic </span><span style="color:#94a3b8">${{hov.traffic}} pkts/s</span><br>
<span style="color:#475569">signal &nbsp;</span><span style="color:#94a3b8">${{hov.signal}} dBm</span><br>
<span style="color:#475569">pkt rate</span><span style="color:#94a3b8"> ${{hov.packet_rate}}</span>
${{hov.is_anomaly?`<br><hr style="border-color:#1e293b;margin:5px 0">
<span style="color:${{sc2[hov.severity]||'#94a3b8'}};font-weight:700">⚠ ${{hov.anomaly_type.replace(/_/g,' ').toUpperCase()}}</span><br>
<span style="color:${{sc2[hov.severity]||'#94a3b8'}};font-size:10px">severity: ${{hov.severity}}</span><br>
<span style="color:#64748b;font-size:10px">${{hov.explanation.substring(0,110)}}</span>`:''}}`;
    cv.style.cursor='pointer';
  }}else{{tip.style.display='none';cv.style.cursor='default';}}
}});
cv.addEventListener('mouseleave',()=>tip.style.display='none');
(function loop(){{simulate();spawnParts();tickParts();draw();requestAnimationFrame(loop);}}());
</script></body></html>"""
        components.html(html, height=580, scrolling=False)

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
# ANALYTICS — time-series, anomaly distribution, device drilldown
# ══════════════════════════════════════════════════════════════════════════════
def page_details():
    results,df=get_results()
    st.markdown('<div class="ph"><h1>📊 Analytics & Anomaly Analysis</h1><span class="tag">FILTER MODE</span></div>',unsafe_allow_html=True)
    c1,c2,_=st.columns([1,1,5])
    with c1:
        if st.button("← Topology"): st.session_state.page="topology"; st.rerun()
    with c2:
        if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()

    tab1,tab2,tab3=st.tabs(["📈 Time Series","🥧 Anomaly Distribution","🔬 Device Drilldown"])

    with tab1:
        st.markdown("#### Traffic & Signal Over Time")
        sel_dev_ts=st.selectbox("Filter by device",["ALL"]+sorted(df["device_id"].unique().tolist()),key="ts_dev")
        plot_df=(df if sel_dev_ts=="ALL" else df[df["device_id"]==sel_dev_ts]).copy()
        plot_df["time"]=pd.to_datetime(plot_df["timestamp"],unit="s")
        if not plot_df.empty:
            st.markdown("**Traffic (pkts/s)**")
            tc=alt.Chart(plot_df).mark_line(color="#00ff88",strokeWidth=1.5,opacity=0.85).encode(
                x=alt.X("time:T",title="Time",axis=alt.Axis(labelColor="#475569",titleColor="#475569")),
                y=alt.Y("traffic:Q",title="pkts/s",axis=alt.Axis(labelColor="#475569",titleColor="#475569")),
                tooltip=["device_id","traffic","time:T"]
            ).properties(height=180).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
            st.altair_chart(tc,use_container_width=True)

            st.markdown("**Signal Strength (dBm)**")
            sc3=alt.Chart(plot_df).mark_line(color="#00d4ff",strokeWidth=1.5,opacity=0.85).encode(
                x=alt.X("time:T",title="Time"),y=alt.Y("signal:Q",title="dBm"),
                tooltip=["device_id","signal","time:T"]
            ).properties(height=180).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
            st.altair_chart(sc3,use_container_width=True)

            st.markdown("**Anomaly Count Over Time (30s buckets)**")
            anom_ts=df.copy()
            anom_ts["time"]=pd.to_datetime(anom_ts["timestamp"],unit="s").dt.floor("30s")
            mean_t=anom_ts["traffic"].mean()
            anom_ts["flagged"]=(anom_ts["traffic"]>mean_t*2).astype(int)
            anom_agg=anom_ts.groupby("time")["flagged"].sum().reset_index()
            anom_agg.columns=["time","anomaly_count"]
            ac=alt.Chart(anom_agg).mark_area(color="#ef4444",opacity=0.4,line={"color":"#ef4444","strokeWidth":1.5}).encode(
                x=alt.X("time:T",title="Time"),y=alt.Y("anomaly_count:Q",title="Count"),
                tooltip=["time:T","anomaly_count"]
            ).properties(height=160).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
            st.altair_chart(ac,use_container_width=True)

    with tab2:
        st.markdown("#### Anomaly Distribution")
        anoms=results[results["is_anomaly"]]
        if anoms.empty:
            st.success("No anomalies detected — all devices normal")
        else:
            ch1,ch2=st.columns(2)
            with ch1:
                st.markdown("**By Anomaly Type**")
                tc2=anoms["anomaly_type"].value_counts().reset_index()
                tc2.columns=["type","count"]
                bar=alt.Chart(tc2).mark_bar(cornerRadiusTopLeft=4,cornerRadiusTopRight=4).encode(
                    x=alt.X("type:N",sort="-y",axis=alt.Axis(labelAngle=-30,labelColor="#64748b")),
                    y=alt.Y("count:Q",axis=alt.Axis(labelColor="#64748b")),
                    color=alt.Color("type:N",scale=alt.Scale(
                        domain=["traffic_flood","device_offline","rogue_device","mac_spoof","signal_drop","packet_flood","suspicious_behavior"],
                        range=["#ef4444","#f97316","#a855f7","#ec4899","#eab308","#06b6d4","#64748b"]
                    ),legend=None),tooltip=["type","count"]
                ).properties(height=220).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
                st.altair_chart(bar,use_container_width=True)
            with ch2:
                st.markdown("**By Severity**")
                sc4=anoms["severity"].value_counts().reset_index()
                sc4.columns=["severity","count"]
                sb=alt.Chart(sc4).mark_bar(cornerRadiusTopLeft=4,cornerRadiusTopRight=4).encode(
                    x=alt.X("severity:N",sort=["critical","high","medium","low"],axis=alt.Axis(labelColor="#64748b")),
                    y=alt.Y("count:Q",axis=alt.Axis(labelColor="#64748b")),
                    color=alt.Color("severity:N",scale=alt.Scale(
                        domain=["critical","high","medium","low"],
                        range=["#ef4444","#f97316","#eab308","#06b6d4"]
                    ),legend=None),tooltip=["severity","count"]
                ).properties(height=220).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
                st.altair_chart(sb,use_container_width=True)

            st.markdown("#### All Anomalous Devices")
            for _,row in anoms.iterrows():
                sv=row.get("severity","low"); c=SC.get(sv,"#06b6d4"); cl=SS.get(sv,"al")
                at=str(row.get("anomaly_type","?")).replace("_"," ").upper()
                st.markdown(f"""<div class="ar {cl}">
                  <div style="width:10px;height:10px;border-radius:50%;background:{c};margin-top:3px;flex-shrink:0;"></div>
                  <div style="flex:1;">
                    <b style="font-family:'JetBrains Mono',monospace;font-size:11px;">{row['device_id']}</b>
                    <span style="color:{c};font-size:11px;font-weight:600;margin-left:10px;">{at}</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#334155;margin-left:6px;">sev:{sv} · conf:{row.get('confidence','?')}</span>
                    <div style="color:#94a3b8;font-size:12px;margin-top:2px;">{str(row.get('explanation',''))}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#334155;margin-top:2px;">
                      traffic:{int(row['traffic'])} · signal:{int(row['signal'])} · mac:{str(row.get('mac','?'))[:18]}</div>
                  </div>
                </div>""",unsafe_allow_html=True)

    with tab3:
        st.markdown("#### Device Drilldown")
        dev_list=sorted(df["device_id"].unique().tolist())
        default=dev_list.index(st.session_state.sel_dev) if st.session_state.sel_dev in dev_list else 0
        sel=st.selectbox("Select device",dev_list,index=default,key="drill_dev")
        st.session_state.sel_dev=sel
        row_sel=results[results["device_id"]==sel]
        hist=df[df["device_id"]==sel].tail(80).copy()
        hist["time"]=pd.to_datetime(hist["timestamp"],unit="s")
        if not row_sel.empty:
            row=row_sel.iloc[0]; sv=row.get("severity","none"); c=SC.get(sv,"#00ff88")
            for col,(lb,val,cc) in zip(st.columns(4),[
                ("ANOMALY TYPE",str(row.get("anomaly_type","normal")).replace("_"," ").upper(),c),
                ("SEVERITY",sv.upper(),c),
                ("CONFIDENCE",str(row.get("confidence","—")).upper(),"#00d4ff"),
                ("TRAFFIC",f"{int(row['traffic'])} pkts/s","#eab308"),
            ]):
                with col: st.markdown(f'<div class="icard"><div class="icard-t">{lb}</div><div class="icard-v" style="color:{cc};font-size:17px;">{val}</div></div>',unsafe_allow_html=True)
            cl=SS.get(sv,"al")
            st.markdown(f'<div class="ar {cl}" style="margin:10px 0 16px;"><div style="color:{c};font-size:13px;">{row.get("explanation","")}</div></div>',unsafe_allow_html=True)
        if not hist.empty:
            d1,d2=st.columns(2)
            with d1:
                st.markdown("**Traffic history**")
                tch=alt.Chart(hist).mark_area(color="#00ff88",opacity=0.3,line={"color":"#00ff88","strokeWidth":1.5}).encode(
                    x=alt.X("time:T",title=""),y=alt.Y("traffic:Q",title="pkts/s"),tooltip=["time:T","traffic"]
                ).properties(height=180).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
                st.altair_chart(tch,use_container_width=True)
            with d2:
                st.markdown("**Signal & Packet Rate**")
                base=alt.Chart(hist)
                s2=base.mark_line(color="#00d4ff",strokeWidth=1.5).encode(x="time:T",y=alt.Y("signal:Q"),tooltip=["time:T","signal"])
                p2=base.mark_line(color="#a855f7",strokeWidth=1.5,strokeDash=[4,2]).encode(x="time:T",y="packet_rate:Q",tooltip=["time:T","packet_rate"])
                combo=(s2+p2).properties(height=180).configure_view(strokeOpacity=0).configure_axis(gridColor="#1e293b",domainColor="#1e293b")
                st.altair_chart(combo,use_container_width=True)
            st.markdown("**Raw history (last 80 readings)**")

# Get per-column thresholds for this device
            b = get_detector().device_baselines.get(sel, {})
            t_thresh = b.get('traffic_flood_thresh', 500)
            s_thresh = b.get('signal_drop_thresh', 20)
            p_thresh = b.get('packet_flood_thresh', 250)

            def colour_row(row):
                styles = [''] * len(row)
                cols = list(row.index)

                # Traffic
                if 'traffic' in cols:
                    v = row['traffic']
                    if v > t_thresh:
                        styles[cols.index('traffic')] = 'background-color:#450a0a;color:#ef4444;font-weight:600'
                    elif v > t_thresh * 0.6:
                        styles[cols.index('traffic')] = 'background-color:#1a0e05;color:#f97316'

                # Signal
                if 'signal' in cols:
                    v = row['signal']
                    if v < s_thresh:
                        styles[cols.index('signal')] = 'background-color:#450a0a;color:#ef4444;font-weight:600'
                    elif v < s_thresh * 2:
                        styles[cols.index('signal')] = 'background-color:#141a05;color:#eab308'

                # Packet rate
                if 'packet_rate' in cols:
                    v = row['packet_rate']
                    if v > p_thresh:
                        styles[cols.index('packet_rate')] = 'background-color:#450a0a;color:#ef4444;font-weight:600'
                    elif v > p_thresh * 0.6:
                        styles[cols.index('packet_rate')] = 'background-color:#1a0e05;color:#f97316'

                # Status
                if 'status' in cols:
                    if row['status'] == 'offline':
                        styles[cols.index('status')] = 'background-color:#450a0a;color:#ef4444;font-weight:600'

                return styles

            display_hist = hist[['time','traffic','packet_rate','signal','status']].reset_index(drop=True)
            st.dataframe(
                display_hist.style.apply(colour_row, axis=1),
                use_container_width=True,
                height=280
            )

            # Summary stats below table
            s1,s2,s3,s4 = st.columns(4)
            s1.markdown(f"""<div class="icard">
              <div class="icard-t">Peak Traffic</div>
              <div class="icard-v" style="color:{'#ef4444' if hist['traffic'].max()>t_thresh else '#00ff88'};font-size:16px;">
                {hist['traffic'].max():,.0f} pkts/s</div>
            </div>""", unsafe_allow_html=True)
            s2.markdown(f"""<div class="icard">
              <div class="icard-t">Avg Traffic</div>
              <div class="icard-v" style="color:#94a3b8;font-size:16px;">
                {hist['traffic'].mean():,.0f} pkts/s</div>
            </div>""", unsafe_allow_html=True)
            s3.markdown(f"""<div class="icard">
              <div class="icard-t">Min Signal</div>
              <div class="icard-v" style="color:{'#ef4444' if hist['signal'].min()<s_thresh else '#00ff88'};font-size:16px;">
                {hist['signal'].min()} dBm</div>
            </div>""", unsafe_allow_html=True)
            s4.markdown(f"""<div class="icard">
              <div class="icard-t">Offline Events</div>
              <div class="icard-v" style="color:{'#ef4444' if (hist['status']=='offline').sum()>0 else '#00ff88'};font-size:16px;">
                {(hist['status']=='offline').sum()}</div>
            </div>""", unsafe_allow_html=True)

    if st.checkbox("Auto-refresh (3s)",key="det_auto"): time.sleep(3); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:               page_login()
elif st.session_state.page=="dashboard":         page_dashboard()
elif st.session_state.page=="topology":          page_topology()
elif st.session_state.page=="details":           page_details()
else:                                            page_login()