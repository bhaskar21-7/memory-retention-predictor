"""
Memory Retention Predictor — Streamlit App
Ebbinghaus Curve with Personalized λ
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import json
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Flat imports — no subfolders needed
from forgetting_curve import (
    initial_lambda, retention_schedule, curve_points,
    next_revision_time, forgetting_risk
)
from update_lambda import record_revision, model_accuracy_over_time
from scheduler import (
    dashboard_topics, get_alerts, get_current_retention,
    get_next_review_date, days_since
)

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH = Path("data/user_data.json")
st.set_page_config(
    page_title="Memory Retention Predictor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def risk_badge(risk):
    colors = {
        "safe": "🟢", "review_soon": "🟡",
        "urgent": "🔴", "critical": "⚠️"
    }
    return colors.get(risk, "⚪")

def retention_color(pct):
    if pct >= 70: return "#22c55e"
    elif pct >= 50: return "#f59e0b"
    elif pct >= 30: return "#ef4444"
    else: return "#7f1d1d"

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🧠 Memory Predictor")
st.sidebar.markdown("*Ebbinghaus Curve · Personalized λ*")
st.sidebar.divider()

tab_choice = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "➕ Add Topic", "📝 Log Revision", "📈 Model Accuracy"],
    label_visibility="collapsed"
)

# ── Load Data ─────────────────────────────────────────────────────────────────
data = load_data()
topics = data.get("topics", [])

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if tab_choice == "📊 Dashboard":
    st.title("📊 Memory Dashboard")

    # Alerts
    alerts = get_alerts(topics)
    if alerts:
        st.error(f"**{len(alerts)} topic(s) need revision**")
        for a in alerts:
            st.warning(a["message"])
    else:
        st.success("✅ All topics are in good shape!")

    st.divider()

    if not topics:
        st.info("No topics yet. Add your first topic →")
    else:
        enriched = dashboard_topics(topics)

        # Summary row
        col1, col2, col3, col4 = st.columns(4)
        avg_ret = sum(t["current_retention_pct"] for t in enriched) / len(enriched)
        critical_count = sum(1 for t in enriched if t["risk"] in ("critical", "urgent"))

        col1.metric("Topics Tracked", len(enriched))
        col2.metric("Avg Retention", f"{avg_ret:.0f}%")
        col3.metric("Need Review", critical_count)
        col4.metric("Total Revisions", sum(t.get("revision_count", 0) for t in enriched))

        st.divider()

        # Topic cards + curves
        for topic in enriched:
            with st.expander(
                f"{risk_badge(topic['risk'])}  **{topic['name']}**  ·  "
                f"{topic['current_retention_pct']}% retained  ·  "
                f"Next review: {topic['next_review']}"
            ):
                c1, c2 = st.columns([1, 2])

                with c1:
                    st.markdown(f"**Understanding Score:** {topic['understanding_score']}/5")
                    st.markdown(f"**Forgetting Rate (λ):** `{topic['lambda']}`")
                    st.markdown(f"**Memory Stability:** `{topic['stability']:.2f}x`")
                    st.markdown(f"**Days Elapsed:** {topic['days_elapsed']:.1f}")
                    st.markdown(f"**Revisions Done:** {topic.get('revision_count', 0)}")

                    # Retention schedule table
                    schedule = retention_schedule(topic["lambda"], topic.get("stability", 1.0))
                    st.markdown("**Prediction Schedule:**")
                    rows = ""
                    for key, val in schedule.items():
                        color = retention_color(val["retention_pct"])
                        rows += f"| Day {val['days']} | " \
                                f"<span style='color:{color}'>{val['retention_pct']}%</span> | " \
                                f"{val['label']} |\n"
                    st.markdown(
                        "| Day | Retention | Status |\n|-----|-----------|--------|\n" + rows,
                        unsafe_allow_html=True
                    )

                with c2:
                    # Plot forgetting curve
                    pts = curve_points(topic["lambda"], topic.get("stability", 1.0), days=30)
                    days_list = [p["day"] for p in pts]
                    ret_list = [p["retention"] for p in pts]

                    current_day = topic["days_elapsed"]
                    current_ret = topic["current_retention_pct"]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=days_list, y=ret_list,
                        mode="lines", name="Predicted Retention",
                        line=dict(color="#6366f1", width=2.5),
                        fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"
                    ))
                    # Threshold line
                    fig.add_hline(
                        y=60, line_dash="dash", line_color="#f59e0b",
                        annotation_text="Revision threshold (60%)",
                        annotation_position="bottom right"
                    )
                    # Current position
                    fig.add_trace(go.Scatter(
                        x=[current_day], y=[current_ret],
                        mode="markers", name="Current",
                        marker=dict(color="#ef4444", size=10, symbol="circle")
                    ))
                    fig.update_layout(
                        height=280, margin=dict(l=20, r=20, t=20, b=20),
                        xaxis_title="Days since study",
                        yaxis_title="Retention (%)",
                        yaxis=dict(range=[0, 105]),
                        legend=dict(orientation="h", y=-0.3),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(size=11)
                    )
                    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ADD TOPIC
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "➕ Add Topic":
    st.title("➕ Add New Topic")
    st.markdown("Log what you studied. The system builds your personalized forgetting curve.")

    with st.form("add_topic"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Topic Name", placeholder="e.g. Backpropagation")
        with col2:
            score = st.slider(
                "How well did you understand it?",
                1, 5, 3,
                help="1 = Barely grasped, 5 = Mastered"
            )

        score_labels = {1: "😰 Barely understood", 2: "😕 Shaky grasp",
                        3: "😐 Moderate", 4: "😊 Solid", 5: "🎯 Mastered"}
        st.caption(score_labels[score])

        lam = initial_lambda(score)
        st.info(f"**Initial λ = {lam}** — "
                f"Predicted retention after 1 day: "
                f"**{round(retention_schedule(lam)['day_1']['retention_pct'], 1)}%**")

        submitted = st.form_submit_button("Add Topic")
        if submitted and name.strip():
            import uuid
            new_topic = {
                "id": str(uuid.uuid4())[:8],
                "name": name.strip(),
                "study_date": datetime.now().isoformat(),
                "last_revised": None,
                "understanding_score": score,
                "lambda": lam,
                "stability": 1.0,
                "revision_count": 0,
                "revision_history": []
            }
            data["topics"].append(new_topic)
            save_data(data)
            st.success(f"✅ '{name}' added! Revision recommended in "
                       f"**{next_revision_time(lam):.1f} days**.")

# ══════════════════════════════════════════════════════════════════════════════
# LOG REVISION
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📝 Log Revision":
    st.title("📝 Log Revision")
    st.markdown("Tell the system how much you actually remembered. It will update your λ.")

    if not topics:
        st.info("Add topics first.")
    else:
        topic_names = [t["name"] for t in topics]
        selected_name = st.selectbox("Select Topic", topic_names)
        topic = next(t for t in topics if t["name"] == selected_name)

        anchor = topic.get("last_revised") or topic.get("study_date")
        elapsed = days_since(anchor)
        predicted = get_current_retention(topic)

        col1, col2, col3 = st.columns(3)
        col1.metric("Days Elapsed", f"{elapsed:.1f}")
        col2.metric("Predicted Retention", f"{predicted:.0f}%")
        col3.metric("Current λ", topic["lambda"])

        actual = st.slider(
            "How much do you actually remember? (0–100%)",
            0, 100, int(predicted),
            help="Be honest — this makes the model smarter!"
        )

        diff = actual - predicted
        if diff > 0:
            st.success(f"Better than predicted by {diff:.0f}% — λ will decrease 📉")
        elif diff < 0:
            st.error(f"Worse than predicted by {abs(diff):.0f}% — λ will increase 📈")
        else:
            st.info("Exact match — λ stays the same")

        if st.button("Submit Revision", type="primary"):
            idx = next(i for i, t in enumerate(topics) if t["name"] == selected_name)
            updated = record_revision(topic, float(actual), elapsed)
            data["topics"][idx] = updated
            save_data(data)
            st.success(f"✅ Updated! New λ = {updated['lambda']} "
                       f"(was {topic['lambda']}). "
                       f"Stability = {updated['stability']:.2f}x")

# ══════════════════════════════════════════════════════════════════════════════
# MODEL ACCURACY
# ══════════════════════════════════════════════════════════════════════════════
elif tab_choice == "📈 Model Accuracy":
    st.title("📈 Model Accuracy Over Time")
    st.markdown(
        "This is the key experiment — how much better does the model get "
        "as it learns YOUR forgetting behavior?"
    )

    has_history = any(t.get("revision_history") for t in topics)

    if not has_history:
        st.info("Log a few revisions to see accuracy improvement here.")
    else:
        for topic in topics:
            history = topic.get("revision_history", [])
            if len(history) < 1:
                continue

            st.subheader(f"📚 {topic['name']}")
            accuracy_data = model_accuracy_over_time(history)

            if len(accuracy_data) >= 2:
                first_acc = accuracy_data[0]["accuracy_pct"]
                last_acc = accuracy_data[-1]["accuracy_pct"]
                improvement = last_acc - first_acc
                col1, col2, col3 = st.columns(3)
                col1.metric("Initial Accuracy", f"{first_acc:.0f}%")
                col2.metric("Current Accuracy", f"{last_acc:.0f}%")
                col3.metric("Improvement", f"+{improvement:.0f}%", delta=f"{improvement:.0f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[d["revision"] for d in accuracy_data],
                y=[d["accuracy_pct"] for d in accuracy_data],
                mode="lines+markers",
                name="Prediction Accuracy",
                line=dict(color="#6366f1", width=2.5),
                marker=dict(size=8)
            ))
            fig.update_layout(
                height=220,
                xaxis_title="Revision #",
                yaxis_title="Accuracy (%)",
                yaxis=dict(range=[0, 105]),
                margin=dict(l=20, r=20, t=10, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Predicted vs actual table
            st.markdown("**Predicted vs Actual Retention:**")
            rows = []
            for r in history:
                rows.append({
                    "Date": r["date"][:10],
                    "Predicted (%)": r["predicted_retention"],
                    "Actual (%)": r["actual_retention"],
                    "Error": f"{abs(r['predicted_retention'] - r['actual_retention']):.1f}%",
                    "Accuracy": f"{r['accuracy_pct']}%"
                })
            st.dataframe(rows, use_container_width=True)
            st.divider()
