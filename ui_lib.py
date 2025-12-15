
import streamlit as st
import textwrap
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- STYLES ---

def get_main_styles():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #F8FAFC; color: #0F172A; font-family: 'Inter', sans-serif; }
    
    /* Navbar */
    .navbar { background: white; padding: 15px; border-bottom: 1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center; border-radius:8px; margin-bottom:20px; }
    .nav-logo { font-size: 22px; font-weight:800; color: #1E293B; }
    
    /* PHONE FRAME */
    .mobile-frame {
        border: 14px solid #0f172a; border-radius: 45px; width: 320px; height: 660px;
        margin: 20px auto; position: relative; overflow: hidden; 
        box-shadow: 0 40px 80px -20px rgba(15, 23, 42, 0.5); /* Deep shadow for 3D float */
        font-family: 'Segoe UI', sans-serif; transition: all 0.3s ease;
    }

    /* CONTENT & SCROLL */
    .mobile-content { height: 100%; overflow-y: auto; overflow-x: hidden; padding-bottom: 120px; scrollbar-width: none; -ms-overflow-style: none; }
    .mobile-content::-webkit-scrollbar { display: none; }

    /* 3D CAR DISPLAY */
    .car-hero { 
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 20px 0; perspective: 1000px; z-index: 1;
    }
    .car-img { 
        width: 100%; max-height: 200px; object-fit: contain; 
        filter: drop-shadow(0 20px 20px rgba(0,0,0,0.5)); 
        transform: rotateY(-5deg) scale(1.1); transition: all 0.5s ease; 
    }

    /* METRICS GRID */
    .glass-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 10px 20px; }
    .glass-card { border-radius: 20px; padding: 16px; } /* More rounded for modern feel */
    .stat-val { font-size: 18px; font-weight: 800; letter-spacing: -0.5px; }
    .stat-label { font-size: 10px; letter-spacing: 0.5px; text-transform: uppercase; margin-top: 4px; font-weight: 700; }

    /* === SLIDE-UP ALERT DRAWER === */
    .alert-overlay {
        position: absolute; bottom: 0; left: 0; right: 0;
        background: rgba(15, 23, 42, 0.90); /* Dark mode default */
        backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
        padding: 30px 25px; 
        border-top-left-radius: 35px; border-top-right-radius: 35px;
        animation: slideUp 0.6s cubic-bezier(0.19, 1, 0.22, 1); /* Premium ease-out */
        z-index: 100; color: white;
        box-shadow: 0 -10px 40px rgba(0,0,0,0.4);
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Handlebar */
    .alert-overlay::before {
        content: ''; position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
        width: 50px; height: 5px; background: rgba(255,255,255,0.2); border-radius: 10px;
    }

    @keyframes slideUp { from { transform: translateY(110%); } to { transform: translateY(0); } }
    
    .alert-badge { 
        background: rgba(239, 68, 68, 0.2); color: #ef4444; 
        padding: 4px 12px; border-radius: 12px; 
        font-size: 10px; font-weight: 800; letter-spacing: 0.5px; border: 1px solid rgba(239, 68, 68, 0.5);
    }
    .booking-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; padding: 16px; margin: 15px 0;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    .agent-step { background: white; padding: 10px; margin-bottom: 8px; border-left: 4px solid #3B82F6; border-radius: 6px; }
    div[data-testid="stButton"] button { border-radius: 8px; font-weight: 600; }
    </style>
    """

def get_mobile_theme_styles():
    return """
    <style>
    /* === DARK THEME (Midnight Glass) === */
    .phone-theme-dark { 
        background: radial-gradient(circle at 50% 10%, #334155 0%, #0f172a 40%, #020617 100%);
        color: white; 
    }
    .phone-theme-dark .glass-card { 
        background: rgba(255, 255, 255, 0.03); 
        border-top: 1px solid rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .phone-theme-dark .sensor-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.1); }
    
    /* === LIGHT THEME (Ceramic / Frosted Ice) === */
    .phone-theme-light { 
        /* Premium Platinum Gradient */
        background: linear-gradient(180deg, #FFFFFF 0%, #F1F5F9 100%);
        color: #1e293b; 
    }
    .phone-theme-light .glass-card { 
        /* Milky White Glass */
        background: rgba(255, 255, 255, 0.70); 
        border: 1px solid rgba(255, 255, 255, 1.0); /* Pure white highlight */
        box-shadow: 0 10px 15px -3px rgba(148, 163, 184, 0.1), 0 4px 6px -2px rgba(148, 163, 184, 0.05); /* Soft Blue-Grey Shadow */
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    }
    .phone-theme-light .sensor-card { 
        background: #ffffff; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); 
    }
    .phone-theme-light .stat-label { color: #64748b !important; font-weight: 700; opacity: 1; }
    .phone-theme-light .stat-val { color: #0f172a; }

    /* LIGHT THEME DRAWER OVERRIDE */
    .phone-theme-light .alert-overlay { 
        background: rgba(255, 255, 255, 0.90); /* Milky White */
        color: #0f172a; 
        border-top: 1px solid rgba(0,0,0,0.05); 
        box-shadow: 0 -10px 40px rgba(0,0,0,0.1);
    }
    .phone-theme-light .alert-overlay::before { background: #cbd5e1; } /* Dark handle for light mode */
    </style>
    """

# --- COMPONENTS ---

def render_metric_card(label, value, unit="", color="#38bdf8"):
    """
    Renders a metric card with a given label, value, unit, and color side-strip.
    """
    return f'<div style="background:#1e293b; color:white; padding:15px; border-radius:10px; margin-bottom:15px; border-left: 4px solid {color}; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><div style="font-size:11px; opacity:0.7; text-transform:uppercase; letter-spacing:1px; margin-bottom:5px;">{label}</div><div style="font-size:24px; font-weight:800; font-family:\'Roboto\', sans-serif;">{value} <span style="font-size:14px;opacity:0.5; font-weight:normal;">{unit}</span></div></div>'

def render_decision_trace(structured_logs):
    """
    Renders the decision trace logs from the agent.
    """
    st.markdown("### Decision Trace")
    for step in structured_logs:
        status_color = "green" if step.status in ["OK", "DONE", "SENT"] else "red" if step.status in ["CRITICAL", "TRIGGERED"] else "blue"
        st.markdown(f"""
        <div class="agent-step">
            <div style="display:flex; justify-content:space-between;"><b>{step.agent}</b> <span style="color:{status_color}; font-weight:bold;">{step.status}</span></div>
            <div style="font-size:13px;">{step.action}</div>
            <div style="font-size:11px; color:#64748B;">{step.details}</div>
        </div>
        """, unsafe_allow_html=True)

def render_impact_factors(tags):
    """Renders the impact factors card."""
    if tags:
        items_html = ""
        for tag in tags:
            if isinstance(tag, dict):
                reason = tag['reason']
            else:
                reason = tag
                
            items_html += f'<div style="font-size: 14px; margin-bottom: 5px; color: #334155; padding: 4px 0;">• {reason}</div>'
            items_html += '<div style="border-bottom: 1px dotted #e2e8f0; margin-bottom: 2px;"></div>'

        card_html = f"""
<div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; margin-top: 15px;">
    <div style="color: #0f172a; font-weight: 700; font-size: 16px; margin-bottom: 10px;">
        ⚠️ Impact Factors
    </div>
    {items_html}
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.success("✅ Perfect Driving Record (No negative impact factors)")

# --- CHARTS ---

def render_spectrogram(fault_detected=False):
    """Renders the 3D Waterfall Spectrogram."""
    # Synthetic Data Generation for 3D Spectrogram
    x_freq = np.linspace(0, 1000, 60)
    y_rpm = np.linspace(1000, 6000, 50)
    X, Y = np.meshgrid(x_freq, y_rpm)
    
    # Amplitude Z Calculation
    center_freq_1 = Y / 60.0  # 1st Order
    center_freq_2 = 2 * center_freq_1 # 2nd Harmonic
    
    # Gaussian ridges along the orders
    Z = 12 * np.exp(-((X - center_freq_1)**2) / 150) 
    Z += 6 * np.exp(-((X - center_freq_2)**2) / 150)
    
    # 2. Add Fixed Resonance (Fault Signature) if Fault is detected
    if fault_detected:
        Z += 15 * np.exp(-((X - 400)**2) / 300) 
        
    # 3. Noise Floor
    Z += np.random.normal(0, 0.3, Z.shape)
    Z = np.clip(Z, 0, None)
    
    # ISO 10816 Violation Plane (Red Threshold)
    Z_limit = np.full_like(Z, 2.0)
    
    fig_spec = go.Figure(data=[
        go.Surface(x=X, y=Y, z=Z, colorscale='Viridis', name='Vibration Spec', opacity=0.9),
        go.Surface(x=X, y=Y, z=Z_limit, opacity=0.3, showscale=False, colorscale=[[0, 'red'], [1, 'red']], name='ISO Limit')
    ])
    
    fig_spec.update_layout(
        scene=dict(
            xaxis_title='Frequency (Hz)',
            yaxis_title='Engine RPM',
            zaxis_title='Amplitude (G)',
            xaxis=dict(backgroundcolor="rgb(240, 240, 240)"),
            yaxis=dict(backgroundcolor="rgb(240, 240, 240)"),
            zaxis=dict(backgroundcolor="rgb(240, 240, 240)"),
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=10),
        height=500,
    )
    return fig_spec

def render_radar_chart(dna, health_val):
    """Renders the Driver DNA Radar Chart."""
    categories = ['Efficiency', 'Aggression', 'Stability', 'Braking', 'Health']
    
    eff_val = dna.get('efficiency', 50)
    agg_val = dna.get('aggression', 50)
    stab_val = dna.get('stability', 50)
    brake_val = dna.get('braking', 50)
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[eff_val, agg_val, stab_val, brake_val, health_val],
        theta=categories,
        fill='toself',
        name='Current Profile',
        line_color='#3B82F6'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig_radar

def render_load_matrix(speed, throttle):
    """Renders the Engine Load Scatter Matrix."""
    fig_load = px.scatter(x=[speed], y=[throttle], 
                         labels={'x': 'Speed (km/h)', 'y': 'Throttle (%)'})
    fig_load.update_traces(marker=dict(size=15, color='#F59E0B', line=dict(width=2, color='white')))
    fig_load.update_layout(
        xaxis=dict(range=[0, 140]), 
        yaxis=dict(range=[0, 100]),
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        template="plotly_white"
    )
    # Add background zones
    fig_load.add_shape(type="rect", x0=0, y0=50, x1=60, y1=100, fillcolor="red", opacity=0.1, line_width=0) # High Load
    fig_load.add_shape(type="rect", x0=60, y0=0, x1=140, y1=50, fillcolor="green", opacity=0.1, line_width=0) # Cruising
    return fig_load

def render_gauge(title, val, max_val, thresholds):
    """Renders a gauge chart."""
    fig = go.Figure(go.Indicator(
        mode = "number+gauge+delta", value = val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 14}},
        delta = {'reference': max_val*0.8}, # Dummy reference
        gauge = {
            'axis': {'range': [None, max_val]},
            'bar': {'color': "#3B82F6"},
            'steps': [
                {'range': [0, thresholds[0]], 'color': "#fee2e2"}, 
                {'range': [thresholds[0], thresholds[1]], 'color': "#dcfce7"},
                {'range': [thresholds[1], max_val], 'color': "#fee2e2"}
            ],
        }
    ))
    fig.update_layout(height=140, margin=dict(l=10, r=10, t=30, b=10))
    return fig

def render_fleet_scatter(df):
    """Renders the 3D Fleet Overview Scatter Plot."""
    fig = px.scatter_3d(df, x="RMS", y="Peak", z="Frequency", color="Health Status", color_discrete_map={"Healthy": "green", "Critical": "red"})
    fig.update_layout(height=400, margin=dict(l=0,r=0,b=0,t=0))
    return fig

def render_strategic_decision_card(vin, batch_id="Batch-2023-A", fault_type=None, confidence=0.0):
    """
    Renders the high-level Strategic Decision / Executive Summary card.
    Dynamically updates based on fault_type.
    """
    if not fault_type or "Normal" in fault_type:
        return

    # Dynamic Content Logic
    if "Knock" in fault_type:
        headline = "STRATEGIC RECOMMENDATION: TARGETED BATCH RECALL"
        reasoning = f"The RCA Agent has correlated this Rod Knock pattern across <b>5 distinct vehicles</b> in <code>{batch_id}</code>. This indicates a supplier defect in the connecting rod bearings, not random failure."
        risk_cost = "₹50.0 Cr"
        target_cost = "₹1.2 Cr"
        savings = "₹48.8 Cr"
    elif "Misfire" in fault_type:
        headline = "STRATEGIC RECOMMENDATION: FIRMWARE OTA ROLLOUT"
        reasoning = f"The RCA Agent has detected a timing desync pattern common to <b>1200 units</b> in Region-North. This is a software calibration issue resolvable via OTA update."
        risk_cost = "₹12.0 Cr" # Cost of physical service
        target_cost = "₹0.05 Cr" # cost of OTA
        savings = "₹11.95 Cr"
    else:
        # Fallback/Generic for Mount Failure or any other
        headline = "STRATEGIC RECOMMENDATION: PHYSICAL INSPECTION REQUIRED"
        reasoning = f"High-frequency vibration detected (Order 2.0/4.0) consistent with <b>Engine Mount degradation</b>. Recommend immediate physical inspection of chassis mounting points."
        risk_cost = "N/A" # Minimal risk to fleet
        target_cost = "₹0.02 Cr" # Cost of single replacement
        savings = "N/A"

    conf_pct = f"{confidence*100:.1f}%"

    st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); color: white;">
<div style="font-size: 10px; font-weight: 600; color: #94a3b8; letter-spacing: 1.2px; margin-bottom: 8px; text-transform: uppercase;">OEM ACTION RECOMMENDATION (Auto-Generated)</div>
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
<div style="font-size: 18px; font-weight: 800; color: #ef4444; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px;">
<span>🚨</span> {headline}
</div>
<div style="background: rgba(34, 197, 94, 0.2); color: #22c55e; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid rgba(34, 197, 94, 0.4);">
Confidence: {conf_pct}
</div>
</div>
<div style="font-size: 14px; opacity: 0.9; margin-bottom: 20px; line-height: 1.5; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px;">
<b>Reasoning:</b> {reasoning}
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
<div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; text-align: center;">
<div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">Global Recall Risk</div>
<div style="font-size: 20px; font-weight: 800; color: #f87171; margin-top: 4px;">{risk_cost}</div>
</div>
<div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; text-align: center;">
<div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">Targeted Recall Cost</div>
<div style="font-size: 20px; font-weight: 800; color: #fbbf24; margin-top: 4px;">{target_cost}</div>
</div>
<div style="background: rgba(34, 197, 94, 0.1); padding: 12px; border-radius: 8px; text-align: center; border: 1px solid rgba(34, 197, 94, 0.2);">
<div style="font-size: 11px; text-transform: uppercase; color: #86efac; font-weight: 700;">Net Savings</div>
<div style="font-size: 20px; font-weight: 800; color: #4ade80; margin-top: 4px;">{savings}</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)
