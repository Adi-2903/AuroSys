
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import textwrap

from core import load_asset_as_base64, calculate_oem_strategy
from ui_lib import (
    get_main_styles, get_mobile_theme_styles,
    render_fleet_scatter, render_spectrogram, render_radar_chart, render_load_matrix, render_gauge,
    render_metric_card, render_decision_trace, render_impact_factors, render_strategic_decision_card
)
from agents import MasterAgent
from config import FLEET_SIZE

# --- MOBILE VIEW ---

def render_mobile_html(res, alert, theme, bike_asset_path):
    """
    Constructs the HTML for the phone simulator.
    """
    current_theme = theme
    rpm, temp, batt = 1100, "Normal", "98%"
    rpm_alert, temp_alert = False, False
    bike_msg, bike_color = "OPTIMAL", "#4ade80" # Green

    if res:
        t = res.telemetry
        rpm = t.rpm
        temp = "High" if t.temperature > 105 else "Normal"
        if res.battery_health:
             batt = f"{res.battery_health.get('soh_percentage', 98)}%"

    if alert:
        ft = alert['type']
        if "Knock" in ft: temp_alert = True
        if "Misfire" in ft: rpm_alert = True
        bike_msg, bike_color = "SERVICE DUE", "#ef4444" # Red

    def highlight(is_active):
        return "border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.15); box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);" if is_active else ""

    # Load bike asset
    bike_img_src = "https://freepngimg.com/thumb/motorcycle/1-motorcycle-png-image.png"
    local_img = load_asset_as_base64(bike_asset_path)
    if local_img:
        bike_img_src = f"data:image/png;base64,{local_img}"

    # !!! CRITICAL FIX: Strings are flushed left to prevent Markdown Code Block interpretation !!!
    phone_html = f"""<div class="mobile-frame phone-theme-{current_theme}">
<div class="mobile-content">
<div style="padding:15px 20px; display:flex; justify-content:space-between; font-size:11px; font-weight:600; opacity:0.7;">
<span>{datetime.datetime.now().strftime('%H:%M')}</span>
<span>5G &nbsp; 🔋 {batt}</span>
</div>
<div class="car-hero">
<span style="background:{bike_color}33; color:{bike_color}; border:1px solid {bike_color}; padding:4px 12px; border-radius:20px; font-size:10px; font-weight:bold;">
● {bike_msg}
</span>
<img src="{bike_img_src}" class="car-img">
<div style="font-size:18px; font-weight:800; margin-top:-5px;">Hero <span style="font-weight:300; opacity:0.8">Splendor+</span></div>
<div style="font-size:9px; opacity:0.6; letter-spacing:1px;">XTEC 2.0 CONNECTED</div>
</div>
<div class="glass-grid">
<div class="glass-card" style="{highlight(rpm_alert)}">
<div class="stat-val" style="{'color:#f87171' if rpm_alert else ''}">{rpm}</div>
<div class="stat-label">RPM</div>
</div>
<div class="glass-card" style="{highlight(temp_alert)}">
<div class="stat-val" style="{'color:#f87171' if temp_alert else ''}">{temp}</div>
<div class="stat-label">TEMP</div>
</div>
<div class="glass-card"><div class="stat-val">32 PSI</div><div class="stat-label">TIRES</div></div>
<div class="glass-card"><div class="stat-val">65 km/l</div><div class="stat-label">ECO</div></div>
</div>
<div style="padding:10px 20px; display:flex; gap:8px;">
<div class="sensor-card" style="flex:1; padding:8px; text-align:center; border-radius:8px;">
<div style="font-weight:bold; color:#facc15; font-size:12px;">320°C</div><div style="font-size:7px; opacity:0.7;">EXHAUST</div>
</div>
<div class="sensor-card" style="flex:1; padding:8px; text-align:center; border-radius:8px;">
<div style="font-weight:bold; color:#facc15; font-size:12px;">45°C</div><div style="font-size:7px; opacity:0.7;">INTAKE</div>
</div>
</div>
</div>"""

    # Check Alert State and add Drawer
    if alert:
        a = alert
        sched = a.get('sched') or {}
        center = sched.get('center', 'Hero Hub via GPS')
        slot = sched.get('slot', '2023-01-01 12:00')
        
        # Format Date/Time for UI
        try:
            slot_dt = datetime.datetime.strptime(slot, "%Y-%m-%d %H:%M")
            date_str = slot_dt.strftime("%d %b")
            time_str = slot_dt.strftime("%I:%M %p")
        except:
            date_str = "Today"
            time_str = slot
        
        # Add the slide-up drawer
        phone_html += textwrap.dedent(f"""
            <div class="alert-overlay">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <span class="alert-badge">CRITICAL FAULT</span>
            <span style="font-size:10px; opacity:0.6;">#ERR-{a['type'][:3].upper()}001</span>
            </div>
            <div style="font-size:18px; font-weight:700; leading:1.2; margin-bottom:5px;">{a['type']} Detected</div>
            <div style="font-size:12px; opacity:0.8; line-height:1.4;">{a['msg']}</div>
            <div class="booking-card">
            <div>
            <div style="font-size:10px; opacity:0.6; text-transform:uppercase; letter-spacing:0.5px;">Recommended Service</div>
            <div style="font-weight:700; font-size:13px; color:#38bdf8; margin-top:2px;">{center}</div>
            </div>
            <div style="text-align:right;">
            <div style="font-size:16px; font-weight:700;">{time_str}</div>
            <div style="font-size:10px; opacity:0.7; font-weight:600;">{date_str}</div>
            </div>
            </div>
            
            
            <div style="text-align:center; font-size:10px; opacity:0.5; letter-spacing:1px; margin-top:10px;">
            CONFIRMATION REQUIRED
            </div>
            </div>
        """)

    phone_html += "</div>" # Close Mobile Frame
    return phone_html

# --- DASHBOARD VIEW ---

def render_fleet_overview(fleet_data):
    """Renders the global fleet overview."""
    st.subheader("🌍 Global Fleet Overview")
    df = pd.DataFrame(fleet_data)
    c1, c2 = st.columns([2, 1])
    with c1: st.dataframe(df, use_container_width=True, height=400)
    with c2:
         st.plotly_chart(render_fleet_scatter(df), use_container_width=True)

def render_inspector_view(res):
    """Renders the detailed inspector view for a single vehicle."""
    t = res.telemetry
    st.subheader(f"🔍 Inspector: {res.vehicle_id}")

    # --- ADD THE NEW FUNCTION CALL HERE ---
    ft = res.final_diagnosis.get("fault_type", "Normal")
    conf = res.final_diagnosis.get("confidence", 0.0)
    
    # 1. Get Decision from Core (Logic Engine)
    strat_decision = calculate_oem_strategy(res.vehicle_id, ft)
    
    # 2. Render UI if Core says so (Presentation Layer)
    if strat_decision["show_card"]:
        render_strategic_decision_card(
            vin=res.vehicle_id, 
            batch_id=strat_decision["batch_id"], 
            fault_type=ft, 
            confidence=conf
        )
    # --------------------------------------
    # --------------------------------------

    tab1, tab2, tab3 = st.tabs(["📊 NVH Forensics", "🏎 Vehicle Dynamics", "🧠 Agent Logs"])
    
    with tab1:
        # 1:4 Layout Ratio
        c_sig, c_vis = st.columns([1, 4])
        
        with c_sig:
            st.markdown("##### Signal Core")
            # Calculate Signal Metrics from Telemetry
            sig = np.array(t.raw_waveform)
            dom_freq, crest, kurt = 0, 0, 0
            
            if len(sig) > 0:
                # 1. Dominant Frequency (FFT)
                freqs = np.fft.rfftfreq(len(sig), d=1/2000) # 2000Hz Sample Rate
                amps = np.abs(np.fft.rfft(sig))
                dom_freq = freqs[np.argmax(amps)]
                
                # 2. Crest Factor (Peak / RMS)
                pk = np.max(np.abs(sig))
                rms = np.sqrt(np.mean(sig**2)) + 1e-6
                crest = pk / rms
                
                # 3. Kurtosis (Fourth Moment)
                mean_sig = np.mean(sig)
                std_sig = np.std(sig)
                if std_sig > 0:
                    kurt = np.mean((sig - mean_sig)**4) / (std_sig**4)
                else:
                    kurt = 0
                    
            st.markdown(render_metric_card("Dominant Freq", f"{int(dom_freq)}", "Hz", "#a855f7"), unsafe_allow_html=True)
            st.markdown(render_metric_card("Crest Factor", f"{crest:.2f}", "", "#3b82f6"), unsafe_allow_html=True)
            st.markdown(render_metric_card("Kurtosis", f"{kurt:.2f}", "", "#ef4444" if kurt > 3 else "#22c55e"), unsafe_allow_html=True)

        with c_vis:
            st.markdown("**3D Waterfall Spectrogram (Order Analysis)**")
            st.plotly_chart(render_spectrogram(res.final_diagnosis.get("fault_detected")), use_container_width=True)

    with tab2:
        # --- 1. Top KPI Row ---
        st.markdown("##### 🚀 Live Metrics")
        k1, k2, k3, k4 = st.columns(4)
        cost = res.financial.get('total_estimate_inr', 0) if res.financial else 0
        k1.metric("RPM", t.rpm, delta="-100" if t.rpm < 1000 else "Normal")
        k2.metric("Temp", f"{t.temperature}°C", delta="High" if t.temperature > 100 else "Normal", delta_color="inverse")
        k3.metric("Driver Score", f"{res.driver_behavior['safety_score']}", delta=res.driver_behavior['status'])
        k4.metric("Est. Cost", f"₹{cost:,}", delta="High" if cost > 5000 else "Normal", delta_color="inverse")
        
        st.divider()

        # --- 2. Advanced Visuals ---
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("**🧬 Driver DNA Profile**")
            dna = res.driver_behavior.get('dna', {})
            health_val = res.battery_health.get('soh_percentage', 90)
            st.plotly_chart(render_radar_chart(dna, health_val), use_container_width=True)
            
            # Display Reasoning Tags
            render_impact_factors(res.driver_behavior.get('tags', []))

            st.markdown("**📉 Engine Load Matrix**")
            st.plotly_chart(render_load_matrix(t.speed_kmh, t.throttle_pos), use_container_width=True)
            st.caption("🟢 Green: Efficient Cruising | 🔴 Red: High Load/Struggling")

        with col_right:
            st.markdown("**⚙ Under the Hood Health**")
            
            # Oil Pressure
            st.caption("🛢 Oil Pressure")
            st.plotly_chart(render_gauge("", t.oil_pressure, 80, [20, 50]), use_container_width=True)
            
            # Battery
            st.caption("🔋 Battery Voltage")
            st.plotly_chart(render_gauge("", t.battery_volts, 16, [12.0, 14.8]), use_container_width=True)
            
            # Coolant
            st.caption("🌡 Coolant Temp")
            st.plotly_chart(render_gauge("", t.coolant_temp, 130, [70, 105]), use_container_width=True)
    with tab3:
        render_decision_trace(res.structured_logs)
        with st.expander("📡 Network Packet Sniffer (JSON)"): st.json(res.transmitted_payload)

# --- MAIN LAYOUT ---

def render_app():
    st.set_page_config(page_title="AuroSys Enterprise", layout="wide", page_icon="🛡")
    
    # --- 1. SESSION STATE INIT ---
    if 'sys' not in st.session_state: st.session_state.sys = MasterAgent()
    if 'res' not in st.session_state: st.session_state.res = None
    if 'fleet' not in st.session_state: st.session_state.fleet = st.session_state.sys.get_fleet_data()
    if 'latest_alert' not in st.session_state: st.session_state.latest_alert = None
    if 'selected_vin' not in st.session_state: st.session_state.selected_vin = "VIN-10000"
    if 'mobile_theme' not in st.session_state: st.session_state.mobile_theme = 'dark' 
    if 'booking_success' not in st.session_state: st.session_state.booking_success = False

    # --- 2. CSS STYLING ---
    st.markdown(get_main_styles(), unsafe_allow_html=True)
    st.markdown(get_mobile_theme_styles(), unsafe_allow_html=True)

    # --- 3. HEADER ---
    st.markdown("""
    <div class="navbar">
        <div class="nav-logo">🛡 AuroSys <span style="color:#DC2626">Enterprise v9.5</span></div>
        <div style="font-weight:600; color:#166534;">● Global System Online</div>
    </div>
    """, unsafe_allow_html=True)

    # --- 4. SIDEBAR & CONTROL LOGIC ---
    st.sidebar.header("🎛 Engineering Console")
    view_mode = st.sidebar.radio("View Mode", ["Fleet Overview", "Single Vehicle Inspector"], horizontal=True)
    st.sidebar.divider()

    if view_mode == "Single Vehicle Inspector":
        st.sidebar.subheader("Target Vehicle")
        # NOTE: Using simplified VIN list instead of FLEET_SIZE loop for succinctness if needed
        # But keeping loop if we have the constant.
        selected_vin = st.sidebar.selectbox("VIN", [f"VIN-{10000+i}" for i in range(FLEET_SIZE)])
        st.session_state.selected_vin = selected_vin
        
        st.sidebar.subheader("Fault Injection")
        scen = st.sidebar.radio("Scenario", ["Normal", "Rod Knock"], horizontal=True)
        c1, c2 = st.sidebar.columns(2)
        toggles = {"Misfire": c1.checkbox("Misfire"), "Loose Mount": c2.checkbox("Loose Mount")}
        
        with st.sidebar.expander("🔑 Agent Auth"):
            try:
                default_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else ""
            except Exception:
                default_key = ""
            api_key = st.text_input("Gemini API Key", value=default_key, type="password")
            
        if st.sidebar.button("▶ ACTIVATE MASTER AGENT", type="primary", use_container_width=True):
             with st.spinner("Orchestrating Agents..."):
                res = st.session_state.sys.execute_workflow(selected_vin, scen, toggles, api_key)
                st.session_state.res = res
                if res.final_diagnosis.get("fault_detected"):
                    st.session_state.latest_alert = {
                        "type": res.final_diagnosis.get("fault_type"), 
                        "msg": res.final_diagnosis.get("driver_friendly_message"), 
                        "sched": res.scheduling,
                        "cost": res.financial.get("total_estimate_inr", 0) if res.financial else 0
                    }
                else: st.session_state.latest_alert = None
        st.sidebar.markdown("---")

    # Chatbot
    st.sidebar.subheader("💬 Ask the Car (RAG)")
    chat_prompt = st.sidebar.text_input("Ask about vehicle status...", placeholder="e.g. 'Why is the cost high?'")
    if chat_prompt:
        st.sidebar.chat_message("user").write(chat_prompt)
        response = "I need you to run the diagnosis first (Click ▶ ACTIVATE)."
        if st.session_state.res:
            r = st.session_state.res
            d = r.final_diagnosis
            if "cost" in chat_prompt.lower() and r.financial:
                cost = r.financial.get('total_estimate_inr', 0)
                parts = r.financial.get('parts_cost', 0)
                response = f"The estimate of ₹{cost:,} includes ₹{parts} for parts and the rest for labor."
            elif "fault" in chat_prompt.lower() or "wrong" in chat_prompt.lower():
                ft = d.get('fault_type', 'Unknown')
                conf = d.get('confidence', 0) * 100
                response = f"I detected a **{ft}** with {conf:.0f}% confidence."
            elif "safe" in chat_prompt.lower() or "drive" in chat_prompt.lower():
                response = d.get('driver_friendly_message', "Please drive carefully.")
            else:
                response = f"I am analyzing the {r.vehicle_id}. All vitals are logged in the dashboard."
        st.sidebar.chat_message("assistant").write(response)
    st.sidebar.markdown("---")

    # Visuals - Right Side (Mobile)
    
    # Theme Toggle
    header_col, theme_col = st.sidebar.columns([3, 1.5]) 
    with header_col: st.caption("📱 Driver Companion App")
    with theme_col:
        if st.button("🎨 Theme", key="theme_btn", help="Switch Mobile Theme", use_container_width=True):
            st.session_state.mobile_theme = "light" if st.session_state.mobile_theme == "dark" else "dark"
            st.rerun()

    # Render Mobile Phone
    bike_path = os.path.abspath("bike_asset.png") # Assuming run from root
    
    phone_html = render_mobile_html(
        st.session_state.res, 
        st.session_state.latest_alert, 
        st.session_state.mobile_theme,
        bike_path
    )
    st.sidebar.markdown(phone_html, unsafe_allow_html=True)
    
    # Mobile Interactive Buttons
    if st.session_state.latest_alert:
        if st.sidebar.button("✅ Confirm Appointment", type="primary", use_container_width=True):
            st.toast("Service Appointment Confirmed!")
            st.session_state.latest_alert = None
            st.session_state.booking_success = True
            st.rerun()

    if st.session_state.booking_success:
        st.sidebar.success("🎉 Appointment Booked!")
        if st.sidebar.button("⬅ Back to Dashboard", use_container_width=True):
            st.session_state.booking_success = False
            st.session_state.res = None
            st.rerun()

    if st.sidebar.checkbox("🐞 Debug Mobile UI"):
        st.sidebar.text("Raw HTML Output:")
        st.sidebar.code(phone_html, language="html")

    # --- 5. MAIN CONTENT ---
    if view_mode == "Fleet Overview":
        render_fleet_overview(st.session_state.fleet)
    elif view_mode == "Single Vehicle Inspector":
        if st.session_state.res and st.session_state.res.vehicle_id == st.session_state.selected_vin:
            render_inspector_view(st.session_state.res)
        else:
            st.info("Select a VIN and click ▶ ACTIVATE MASTER AGENT to start diagnosis.")
