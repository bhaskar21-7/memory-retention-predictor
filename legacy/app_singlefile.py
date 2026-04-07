"""
Memory Retention Predictor — Single File Version
All model code is inlined. No local imports needed.
Just run: streamlit run app_singlefile.py
"""

import streamlit as st
import json
import math
import uuid
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

DATA_PATH = Path(__file__).parent / "user_data.json"

st.set_page_config(page_title="Memory Retention Predictor", page_icon="🧠", layout="wide")

# ── Model functions (all inlined) ─────────────────────────────────────────────

def initial_lambda(score):
    return round(1.0 / max(1, min(5, score)), 4)

def retention(t, lam, stability=1.0):
    return round(math.exp(-lam * t / stability), 4)

def retention_schedule(lam, stability=1.0):
    labels = {(0.8,1.1):"Strong",(0.6,0.8):"Good",(0.4,0.6):"Fading",(0.2,0.4):"Weak",(0,0.2):"Forgotten"}
    def lbl(r):
        for (lo,hi),l in labels.items():
            if lo <= r < hi: return l
        return "Strong" if r >= 0.8 else "Forgotten"
    return {d: {"days":d,"retention_pct":round(retention(d,lam,stability)*100,1),
                "label":lbl(retention(d,lam,stability))} for d in [1,3,7,14,21,30]}

def next_revision_time(lam, stability=1.0, threshold=0.6):
    return round((-math.log(threshold) * stability) / lam, 2) if lam > 0 else 999

def update_lambda(old, pred, actual):
    if actual <= 0: actual = 0.01
    return round(max(0.05, min(2.0, old * (pred / actual))), 4)

def update_stability(stab, actual):
    f = 2.5 if actual>=0.8 else 1.8 if actual>=0.6 else 1.2 if actual>=0.4 else 0.8
    return round(stab * f, 4)

def forgetting_risk(lam, elapsed, stability=1.0):
    r = retention(elapsed, lam, stability)
    if r >= 0.75: return "safe"
    if r >= 0.55: return "review_soon"
    if r >= 0.35: return "urgent"
    return "critical"

def curve_points(lam, stability=1.0, days=30):
    return [{"day":t,"retention":round(retention(t,lam,stability)*100,1)} for t in range(days+1)]

def days_since(date_str):
    return (datetime.now() - datetime.fromisoformat(date_str)).total_seconds() / 86400

def get_current_retention(topic):
    anchor = topic.get("last_revised") or topic.get("study_date")
    if not anchor: return 0.0
    return round(retention(days_since(anchor), topic["lambda"], topic.get("stability",1.0)) * 100, 1)

def get_next_review_date(topic):
    anchor = topic.get("last_revised") or topic.get("study_date")
    if not anchor: return "ASAP"
    elapsed = days_since(anchor)
    days_until = max(0, next_revision_time(topic["lambda"], topic.get("stability",1.0)) - elapsed)
    if days_until < 0.5: return "Today"
    if days_until < 1.5: return "Tomorrow"
    return (datetime.now() + timedelta(days=days_until)).strftime("%b %d")

def get_alerts(topics):
    alerts = []
    for t in topics:
        anchor = t.get("last_revised") or t.get("study_date")
        if not anchor: continue
        r = get_current_retention(t)
        risk = forgetting_risk(t["lambda"], days_since(anchor), t.get("stability",1.0))
        if risk in ("urgent","critical","review_soon"):
            msg = f"⚠️ Revise '{t['name']}' NOW — {r:.0f}%" if risk=="critical" else \
                  f"🔴 '{t['name']}' fading — {r:.0f}%" if risk=="urgent" else \
                  f"🟡 Review '{t['name']}' soon — {r:.0f}%"
            alerts.append({"topic":t["name"],"retention_pct":r,"risk":risk,"message":msg})
    return sorted(alerts, key=lambda x: {"critical":0,"urgent":1,"review_soon":2}[x["risk"]])

def record_revision(topic, actual_pct, elapsed):
    actual = actual_pct / 100.0
    predicted = retention(elapsed, topic["lambda"], topic.get("stability",1.0))
    old_lam = topic["lambda"]
    topic["lambda"] = update_lambda(old_lam, predicted, actual)
    topic["stability"] = update_stability(topic.get("stability",1.0), actual)
    topic["revision_count"] = topic.get("revision_count",0) + 1
    topic["last_revised"] = datetime.now().isoformat()
    if "revision_history" not in topic: topic["revision_history"] = []
    topic["revision_history"].append({
        "date": datetime.now().isoformat()[:10],
        "days_elapsed": round(elapsed,2),
        "predicted_retention": round(predicted*100,1),
        "actual_retention": round(actual*100,1),
        "lambda_before": old_lam,
        "lambda_after": topic["lambda"],
        "accuracy_pct": round((1-abs(predicted-actual))*100,1)
    })
    return topic

def ret_color(pct):
    if pct>=70: return "#22c55e"
    if pct>=50: return "#f59e0b"
    if pct>=30: return "#ef4444"
    return "#7f1d1d"

def risk_icon(risk):
    return {"safe":"🟢","review_soon":"🟡","urgent":"🔴","critical":"⚠️"}.get(risk,"⚪")

# ── Data ──────────────────────────────────────────────────────────────────────

def load_data():
    if not DATA_PATH.exists():
        with open(DATA_PATH,"w") as f: json.dump({"topics":[]},f)
    with open(DATA_PATH) as f: return json.load(f)

def save_data(data):
    with open(DATA_PATH,"w") as f: json.dump(data,f,indent=2)

# ── App ───────────────────────────────────────────────────────────────────────

st.sidebar.title("🧠 Memory Predictor")
st.sidebar.markdown("*Ebbinghaus Curve · Personalized λ*")
st.sidebar.divider()
tab = st.sidebar.radio("", ["📊 Dashboard","➕ Add Topic","📝 Log Revision","📈 Model Accuracy"],
                       label_visibility="collapsed")

data = load_data()
topics = data.get("topics",[])

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if tab == "📊 Dashboard":
    st.title("📊 Memory Dashboard")
    alerts = get_alerts(topics)
    if alerts:
        st.error(f"**{len(alerts)} topic(s) need revision**")
        for a in alerts: st.warning(a["message"])
    else:
        st.success("✅ All topics are in good shape!")
    st.divider()
    if not topics:
        st.info("No topics yet. Add your first topic →")
    else:
        enriched = sorted([{**t, "ret":get_current_retention(t),
                            "elapsed":days_since(t.get("last_revised") or t.get("study_date")),
                            "risk":forgetting_risk(t["lambda"],
                                days_since(t.get("last_revised") or t.get("study_date")),
                                t.get("stability",1.0))} for t in topics],
                          key=lambda x:x["ret"])

        c1,c2,c3,c4 = st.columns(4)
        avg = sum(t["ret"] for t in enriched)/len(enriched)
        c1.metric("Topics", len(enriched))
        c2.metric("Avg Retention", f"{avg:.0f}%")
        c3.metric("Need Review", sum(1 for t in enriched if t["risk"] in ("critical","urgent")))
        c4.metric("Revisions", sum(t.get("revision_count",0) for t in enriched))
        st.divider()

        for t in enriched:
            with st.expander(f"{risk_icon(t['risk'])}  **{t['name']}**  ·  {t['ret']}% retained  ·  Next: {get_next_review_date(t)}"):
                col1, col2 = st.columns([1,2])
                with col1:
                    st.markdown(f"**Score:** {t['understanding_score']}/5  |  **λ:** `{t['lambda']}`  |  **Stability:** `{t['stability']:.2f}x`")
                    st.markdown(f"**Days elapsed:** {t['elapsed']:.1f}  |  **Revisions:** {t.get('revision_count',0)}")
                    sched = retention_schedule(t["lambda"], t.get("stability",1.0))
                    cols = st.columns(6)
                    for i,(k,v) in enumerate(sched.items()):
                        cols[i].metric(f"Day {v['days']}", f"{v['retention_pct']}%")
                with col2:
                    pts = curve_points(t["lambda"], t.get("stability",1.0))
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=[p["day"] for p in pts],y=[p["retention"] for p in pts],
                        mode="lines",line=dict(color="#6366f1",width=2.5),
                        fill="tozeroy",fillcolor="rgba(99,102,241,0.08)"))
                    fig.add_hline(y=60,line_dash="dash",line_color="#f59e0b")
                    fig.add_trace(go.Scatter(x=[t["elapsed"]],y=[t["ret"]],mode="markers",
                        marker=dict(color="#ef4444",size=10)))
                    fig.update_layout(height=240,margin=dict(l=10,r=10,t=10,b=30),
                        xaxis_title="Days",yaxis_title="Retention %",yaxis=dict(range=[0,105]),
                        showlegend=False,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig,use_container_width=True)

# ── ADD TOPIC ─────────────────────────────────────────────────────────────────
elif tab == "➕ Add Topic":
    st.title("➕ Add New Topic")
    with st.form("add"):
        name = st.text_input("Topic Name", placeholder="e.g. Backpropagation")
        score = st.slider("Understanding (1–5)", 1, 5, 3)
        labels = {1:"😰 Barely understood",2:"😕 Shaky",3:"😐 Moderate",4:"😊 Solid",5:"🎯 Mastered"}
        st.caption(labels[score])
        lam = initial_lambda(score)
        st.info(f"λ = {lam} · Day 1 retention: {retention_schedule(lam)[1]['retention_pct']}% · Review in {next_revision_time(lam):.1f} days")
        if st.form_submit_button("Add Topic") and name.strip():
            data["topics"].append({"id":str(uuid.uuid4())[:8],"name":name.strip(),
                "study_date":datetime.now().isoformat(),"last_revised":None,
                "understanding_score":score,"lambda":lam,"stability":1.0,
                "revision_count":0,"revision_history":[]})
            save_data(data)
            st.success(f"✅ '{name}' added!")
            st.rerun()

# ── LOG REVISION ──────────────────────────────────────────────────────────────
elif tab == "📝 Log Revision":
    st.title("📝 Log Revision")
    if not topics:
        st.info("Add topics first.")
    else:
        sel = st.selectbox("Topic", [t["name"] for t in topics])
        t = next(x for x in topics if x["name"]==sel)
        anchor = t.get("last_revised") or t.get("study_date")
        elapsed = days_since(anchor)
        pred = get_current_retention(t)
        c1,c2,c3 = st.columns(3)
        c1.metric("Days elapsed", f"{elapsed:.1f}")
        c2.metric("Predicted retention", f"{pred:.0f}%")
        c3.metric("Current λ", t["lambda"])
        actual = st.slider("Actual recall (%)", 0, 100, int(pred))
        diff = actual - pred
        if diff > 0: st.success(f"Better than predicted by {diff:.0f}% — λ will decrease 📉")
        elif diff < 0: st.error(f"Worse than predicted by {abs(diff):.0f}% — λ will increase 📈")
        else: st.info("Exact match")
        if st.button("Submit Revision", type="primary"):
            idx = next(i for i,x in enumerate(topics) if x["name"]==sel)
            old = t["lambda"]
            updated = record_revision(t, float(actual), elapsed)
            data["topics"][idx] = updated
            save_data(data)
            st.success(f"✅ λ: {old} → {updated['lambda']} · Stability: {updated['stability']:.2f}x")

# ── MODEL ACCURACY ────────────────────────────────────────────────────────────
elif tab == "📈 Model Accuracy":
    st.title("📈 Model Accuracy Over Time")
    if not any(t.get("revision_history") for t in topics):
        st.info("Log some revisions to see accuracy improvement.")
    else:
        for t in topics:
            h = t.get("revision_history",[])
            if not h: continue
            st.subheader(f"📚 {t['name']}")
            if len(h) >= 2:
                c1,c2,c3 = st.columns(3)
                c1.metric("Initial accuracy", f"{h[0]['accuracy_pct']:.0f}%")
                c2.metric("Current accuracy", f"{h[-1]['accuracy_pct']:.0f}%")
                c3.metric("Improvement", f"+{h[-1]['accuracy_pct']-h[0]['accuracy_pct']:.0f}%")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=list(range(1,len(h)+1)),
                y=[r["accuracy_pct"] for r in h],mode="lines+markers",
                line=dict(color="#6366f1",width=2.5),marker=dict(size=8)))
            fig.update_layout(height=200,xaxis_title="Revision #",yaxis_title="Accuracy %",
                yaxis=dict(range=[0,105]),margin=dict(l=10,r=10,t=10,b=30),
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe([{"Date":r["date"],"Predicted":f"{r['predicted_retention']}%",
                "Actual":f"{r['actual_retention']}%","Accuracy":f"{r['accuracy_pct']}%"} for r in h],
                use_container_width=True)
            st.divider()
