import numpy as np
import random
import datetime
from datetime import timedelta
import json
import logging
from dataclasses import asdict

from config import (
    SAMPLES, WORKSHOPS, FLEET_SIZE, 
    SYSTEM_INSTRUCTION_DIAGNOSIS, SYSTEM_INSTRUCTION_RCA
)
from core import TelemetryFrame, AgentLogStep, PipelineResult, DatabaseManager

# Check for GenAI capability
try:
    import google_genai as genai 
    HAS_GENAI_LIB = True
except ImportError:
    try:
        from google.genai import Client, types
        HAS_GENAI_LIB = True
    except ImportError:
        HAS_GENAI_LIB = False

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class TelematicsAgent:
    """Perception: Simulates high-fidelity sensor streams (EDGE)."""
    def read_sensors(self, vid, scenario, toggles):
        t = np.linspace(0, 0.5, SAMPLES, endpoint=False)
        
        # 1. Vibration Synthesis
        base_freq = 60 # Hz
        signal = 0.3 * np.sin(2 * np.pi * base_freq * t)
        signal += 0.05 * np.random.normal(0, 1, SAMPLES)
        
        # 2. Performance & Vitals Base Values
        rpm = 3200
        speed = 65.0 # km/h
        throttle = 45.0 # %
        temp = 90.0
        coolant = 85.0
        batt = 13.8
        oil = 40.0
        brake = 15.0 # % wear
        
        codes = []
        
        # 3. Batch Logic
        try:
            vid_num = int(vid.replace("VIN-", ""))
        except:
            vid_num = 0
        batch_id = "Batch-2023-A" if vid_num % 2 == 0 else "Batch-2023-B"
        
        # 4. Fault Injection Logic
        if scenario == "Rod Knock":
            for burst_time in np.arange(0.05, 0.5, 0.1):
                mask = np.logical_and(t >= burst_time, t < burst_time + 0.02)
                signal[mask] += 2.5 * np.sin(2 * np.pi * 400 * (t[mask] - burst_time))
            codes.append("P0301")
            temp = 118.0
            coolant = 105.0 # Overheating
            oil = 15.0      # Low oil pressure
            rpm = 3400      # Slight surge
            
        if toggles.get("Misfire"):
            dropout_mask = np.random.choice([True, False], size=SAMPLES, p=[0.1, 0.9])
            signal[dropout_mask] *= 0.1
            codes.append("P0300")
            batt = 12.1     # Alternator struggle
            rpm = 2800      # Power loss
            speed = 58.0    # Speed drop
            
        if toggles.get("Loose Mount"):
            signal += 0.8 * np.sin(2 * np.pi * 5 * t)
            codes.append("C1234")

        # 5. Calculations
        rms = float(np.sqrt(np.mean(signal**2)))
        peak = float(np.max(np.abs(signal)))
        
        secure_lat = 12.9716 + random.uniform(-0.05, 0.05)
        secure_lon = 77.5946 + random.uniform(-0.05, 0.05)

        return TelemetryFrame(
            vehicle_id=vid, timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
            rms=rms, peak=peak, raw_waveform=signal.tolist(),
            rpm=rpm, speed_kmh=speed, throttle_pos=throttle,
            temperature=temp, coolant_temp=coolant, oil_pressure=oil, battery_volts=batt,
            brake_wear_pct=brake, tire_pressure=32.0,
            can_codes=codes, batch_id=batch_id, 
            _secure_lat=secure_lat, _secure_lon=secure_lon
        )

class DriverBehaviorAgent:
    """Analyzes driving patterns for insurance and safety scoring."""
    def analyze(self, telemetry: TelemetryFrame):
        # 1. Base Metrics
        t = telemetry
        
        # 2. Physics Calculations (Multi-Dimensional Analysis)
        # Efficiency: Speed vs Input Effort (High speed with low throttle = Efficient)
        eco_index = min(100, (t.speed_kmh / (t.throttle_pos + 1)) * 50) 
        
        # Aggression: RPM surge vs Thermal State
        agg_raw = (t.rpm / 6000) * 100
        if t.temperature < 70 and t.rpm > 3000: agg_raw += 20 # Penalty for cold revving
        aggression_score = min(100, agg_raw)
        
        # Stability: Vibration analysis (Comfort)
        stability_score = max(0, 100 - (t.rms * 15))
        
        # Braking Health: Inverse of wear
        braking_score = max(0, 100 - (t.brake_wear_pct * 2))

        # 3. Composite Safety Score (Weighted Average)
        # Safety prioritizes Stability (40%) and Low Aggression (30%)
        # Safety = 0.4*Stability + 0.3*(100-Aggression) + 0.2*Braking + 0.1*Eco
        weighted_score = (0.4 * stability_score) + \
                         (0.3 * (100 - aggression_score)) + \
                         (0.2 * braking_score) + \
                         (0.1 * eco_index)
        
        final_score = int(min(100, max(0, weighted_score)))
        
        # 4. Semantic Tagging with Quantification
        tags = []
        if aggression_score > 60: 
            tags.append({"reason": "Aggressive Acceleration", "impact": -15})
        if stability_score < 75: 
            tags.append({"reason": "Rough Terrain/Suspension", "impact": -10})
        if eco_index < 50: 
            tags.append({"reason": "Inefficient Gear Usage", "impact": -5})
        if t.speed_kmh > 100: 
            tags.append({"reason": "High Speed Violation", "impact": -15})
            final_score -= 10 

        # Catch-all
        if final_score < 80 and not tags:
            tags.append({"reason": "General Irregularities", "impact": -5})

        status = "Good Driver"
        if final_score < 75: status = "Moderate"
        if final_score < 50: status = "Risky"
        
        return {
            "safety_score": final_score, 
            "status": status, 
            "tags": tags, # Now a list of dicts
            # Return the DNA for the Radar Chart
            "dna": {
                "efficiency": int(eco_index),
                "aggression": int(aggression_score),
                "stability": int(stability_score),
                "braking": int(braking_score)
            }
        }

class BatteryHealthAgent:
    """Deep analysis of EV/Hybrid battery systems."""
    def check_health(self, telemetry: TelemetryFrame):
        soh = 98.5
        if telemetry.battery_volts < 12.5: soh = 82.0 
        estimated_range = 320 
        if soh < 90: estimated_range = 280
        return {"soh_percentage": soh, "estimated_range_km": estimated_range, "cell_imbalance": "None" if telemetry.battery_volts > 13.0 else "Detected (Cell 4)", "charging_cycles": 142}

class InventoryAgent:
    """Checks supply chain for parts based on diagnosis."""
    def check_stock(self, diagnosis):
        fault = diagnosis.get("fault_type")
        if fault == "Normal": return {"status": "NA", "part": "None", "lead_time_days": 0}
        if fault == "Rod Knock":
            in_stock = random.choice([True, False])
            return {"status": "Available" if in_stock else "Backordered", "part": "Connecting Rod Bearing Kit (Gen3)", "lead_time_days": 1 if in_stock else 14, "warehouse": "Regional Hub - Chennai"}
        elif fault == "Misfire":
            return {"status": "Available", "part": "Ignition Coil Pack", "lead_time_days": 0, "warehouse": "Local Dealer"}
        elif fault == "Mount Failure":
             return {"status": "Low Stock", "part": "Hydraulic Engine Mount", "lead_time_days": 3, "warehouse": "Regional Hub - Chennai"}
        return {"status": "Unknown", "part": "General Diagnostics", "lead_time_days": 0}

class GenAIAgent:
    """Reasoning: Wraps Gemini API."""
    def __init__(self, name, db, instruction):
        self.name = name
        self.db = db
        self.instruction = instruction
    
    def execute(self, inputs, api_key):
        if HAS_GENAI_LIB and api_key:
            try:
                from google.genai import Client
                client = Client(api_key=api_key)
                prompt = f"{self.instruction}\n\nINPUT DATA:\n{json.dumps(inputs)}"
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                self.db.log(self.name, "INFERENCE_SUCCESS", "Gemini 2.0 Flash")
                text = response.text
                if "json" in text: text = text.split("json")[1].split("```")[0]
                return json.loads(text)
            except Exception as e:
                self.db.log(self.name, "API_ERROR", str(e))
                logger.error(f"GenAI Error: {e}")
        
        self.db.log(self.name, "FALLBACK_MODE", "Heuristics Applied")
        return self._heuristic(inputs)

    def _heuristic(self, inputs):
        if self.name == "DiagnosisAgent":
            is_fault = inputs.get("rms") > 1.0 or "P0301" in inputs.get("can_codes") or "P0300" in inputs.get("can_codes")
            f_type = "Normal"
            driver_msg = "Systems nominal."
            safety_tips = ["Maintain regular service intervals.", "Check tire pressure monthly."]
            upload = False
            
            if "P0301" in inputs.get("can_codes"): 
                f_type = "Rod Knock"
                driver_msg = "Critical engine issue detected. Please pull over safely."
                safety_tips = ["Do not exceed 30 km/h.", "Avoid highway driving.", "Watch engine temperature gauge."]
                upload = True
            elif "P0300" in inputs.get("can_codes"): 
                f_type = "Misfire"
                driver_msg = "Engine misfire detected. Service required."
                safety_tips = ["Avoid heavy acceleration.", "Turn off AC to reduce engine load."]
                upload = True
            elif "C1234" in inputs.get("can_codes"): 
                f_type = "Mount Failure"
                driver_msg = "Excessive vibration detected. Drive cautiously."
                safety_tips = ["Avoid rough roads.", "Drive smoothly to minimize vibration."]
                upload = True
            
            return {"fault_detected": is_fault, "fault_type": f_type, "severity": "Critical" if f_type == "Rod Knock" else ("Medium" if f_type != "Normal" else "Low"), "driver_friendly_message": driver_msg, "safety_tips": safety_tips, "upload_required": upload, "confidence": 0.99 if is_fault else 1.0}
        elif self.name == "RCAAgent":
            ft = inputs.get("fault_type")
            if ft == "Rod Knock": return {"is_batch_defect": True, "batch_id": "Batch-2023-A", "manufacturing_action": "Supplier Audit", "estimated_cost_per_unit": 12500, "ota_eligible": False}
            if ft == "Misfire": return {"is_batch_defect": True, "batch_id": "Soft-ECU-v1.2", "manufacturing_action": "OTA Patch", "estimated_cost_per_unit": 0, "ota_eligible": True}
            return {"is_batch_defect": False, "batch_id": None, "manufacturing_action": "None", "estimated_cost_per_unit": 0, "ota_eligible": False}
        return {}

class FinancialAgent:
    def compute(self, diagnosis, rca):
        raw_cost = rca.get("estimated_cost_per_unit", 0)
        labor_cost = 1500 if raw_cost > 0 else 0
        total_estimate = raw_cost + labor_cost
        return {"parts_cost": raw_cost, "labor_cost": labor_cost, "total_estimate_inr": total_estimate, "impact_level": "High" if total_estimate > 5000 else "Low"}

class GPSAgent:
    def find_nearest_workshop(self, lat, lon):
        best = min(WORKSHOPS, key=lambda w: abs(w['lat'] - lat) + abs(w['lon'] - lon))
        dist = round(random.uniform(1.2, 5.5), 1)
        return {"workshop": best["name"], "coordinates": (best["lat"], best["lon"]), "distance_km": dist, "rating": best["rating"], "eta_mins": int(dist * 4)}

class SecureSchedulingAgent:
    def find_slot(self, gps_data):
        return {"center": gps_data["workshop"], "distance": gps_data["distance_km"], "slot": (datetime.datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), "service_id": f"SRV-{random.randint(1000,9999)}"}

class OTAAgent:
    def deploy(self): return "PATCH_V1.3_SUCCESS"

class ComplianceAgent:
    def check(self, diagnosis, financial, scheduling):
        alerts = []
        status = "COMPLIANT"
        
        # 1. Base Compliance Check
        if diagnosis.get("severity") == "Critical":
            status = "VIOLATION"
            alerts.append("Severity Critical Violation")

        # 2. Financial UEBA
        if financial and financial.get("total_estimate_inr", 0) > 20000:
            status = "REVIEW_REQUIRED"
            alerts.append("UEBA: High-Value Transaction Flagged")

        # 3. Scheduling UEBA
        if scheduling and scheduling.get("slot"):
            try:
                # Parse "YYYY-MM-DD HH:MM"
                slot_time = datetime.datetime.strptime(scheduling["slot"], "%Y-%m-%d %H:%M")
                if slot_time.hour < 9 or slot_time.hour >= 19:
                    status = "BLOCKED"
                    alerts.append("UEBA: Suspicious Out-of-Hours Booking")
            except ValueError:
                pass # Ignore parsing errors

        return {
            "status": status,
            "ue_alerts": alerts,
            "checked_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

class CommsModule:
    """Handles logic for packet sizing and data security."""
    def create_payload(self, telemetry, diagnosis):
        upload_required = diagnosis.get('upload_required', False)
        payload = {"v": telemetry.vehicle_id, "ts": telemetry.timestamp, "stat": "OK" if not upload_required else "FAULT", "bat": telemetry.battery_volts, "dtc": []}
        size_kb = 0.5 
        if upload_required:
            payload["gps"] = {"lat": round(telemetry._secure_lat, 4), "lon": round(telemetry._secure_lon, 4)}
            payload["waveform_dump"] = telemetry.raw_waveform 
            payload["dtc"] = telemetry.can_codes
            payload["eng_params"] = {"rpm": telemetry.rpm, "load": telemetry.throttle_pos, "temp": telemetry.temperature}
            size_kb = 1540.2 
        return payload, size_kb

class MasterAgent:
    def __init__(self):
        self.db = DatabaseManager()
        self.telematics = TelematicsAgent()
        
        # New Agents
        self.driver_agent = DriverBehaviorAgent()
        self.battery_agent = BatteryHealthAgent()
        self.inventory_agent = InventoryAgent()
        
        self.diag = GenAIAgent("DiagnosisAgent", self.db, SYSTEM_INSTRUCTION_DIAGNOSIS)
        self.rca = GenAIAgent("RCAAgent", self.db, SYSTEM_INSTRUCTION_RCA)
        self.gps = GPSAgent()
        self.fin = FinancialAgent()
        self.comp = ComplianceAgent()
        self.sched = SecureSchedulingAgent()
        self.ota = OTAAgent()
        self.comms = CommsModule()

    def execute_workflow(self, vid, scenario, toggles, api_key):
        logs = []
        def log_step(agent, location, action, status, details=""):
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            logs.append(AgentLogStep(agent, location, action, status, details, ts))

        # 1. PERCEPTION (EDGE)
        log_step("TelematicsAgent", "🚗 EDGE", "Acquire Sensor Data", "RUNNING", f"Target: {vid}")
        t = self.telematics.read_sensors(vid, scenario, toggles)
        
        # 1.5 DRIVER BEHAVIOR (EDGE) - NEW
        driver_out = self.driver_agent.analyze(t)
        log_step("DriverBehaviorAgent", "🚗 EDGE", "Driving Style Analysis", "OK", f"Score: {driver_out['safety_score']} ({driver_out['status']})")
        
        # 2. DIAGNOSIS (EDGE)
        diag_in = {k:v for k,v in asdict(t).items() if k not in ['raw_waveform', '_secure_lat', '_secure_lon']}
        d_out = self.diag.execute(diag_in, api_key)
        
        fault_found = d_out.get('fault_detected', False)
        
        status = "CRITICAL" if fault_found else "NORMAL"
        log_step("DiagnosisAgent", "🚗 EDGE", "Local Classification", status, f"Type: {d_out.get('fault_type')}")
        
        # 3. COMMS MODULE (Data Minimization Logic)
        payload, data_size = self.comms.create_payload(t, d_out)
        
        r_out, f_out, c_out, s_out, o_out, gps_out, inv_out, bat_out = None, None, None, None, None, None, None, None

        # 4. DATA TRANSMISSION LOGIC
        if fault_found:
            log_step("CommsModule", "📡 UP-LINK", "Blackbox Upload", "TRIGGERED", f"Sending {data_size}KB Full Dump to Cloud...")
            
            # 5. CLOUD PROCESSING (OEM SIDE)
            r_out = self.rca.execute(d_out, api_key)
            log_step("RCAAgent", "☁ CLOUD", "Root Cause Analysis", "DONE", f"Batch: {r_out.get('batch_id')}")
            
            # Inventory Check - NEW
            inv_out = self.inventory_agent.check_stock(d_out)
            log_step("InventoryAgent", "☁ CLOUD", "Supply Chain Check", "DONE", f"Part: {inv_out['part']} ({inv_out['status']})")
            
            # Battery Health Check - NEW
            bat_out = self.battery_agent.check_health(t)
            
            f_out = self.fin.compute(d_out, r_out)
            f_out = self.fin.compute(d_out, r_out)
            
            if r_out.get("ota_eligible"):
                log_step("OTAAgent", "☁ CLOUD", "Software Patch", "DEPLOYING", "Version 1.3")
                o_out = self.ota.deploy()
            else:
                log_step("GPSAgent", "☁ CLOUD", "Geospatial Query", "RUNNING", f"Loc: {t._secure_lat:.4f}, {t._secure_lon:.4f}")
                gps_out = self.gps.find_nearest_workshop(t._secure_lat, t._secure_lon)
                s_out = self.sched.find_slot(gps_out)
                log_step("SecureSchedulingAgent", "☁ CLOUD", "Provisional Booking", "HELD", f"Slot: {s_out['slot']}")
            
            
            # Compliance / Security Check (Late Binding)
            c_out = self.comp.check(d_out, f_out, s_out)
            
            if c_out["status"] == "BLOCKED":
                log_step("ComplianceAgent", "☁ CLOUD", "Security Protocol", "SECURITY", f"Blocked: {c_out.get('ue_alerts')}")
            else:
                log_step("MasterAgent", "☁ CLOUD", "Driver Notification", "SENT", "Action Plan Dispatched to App")
            
        else:
            bat_out = self.battery_agent.check_health(t)
            log_step("CommsModule", "📡 UP-LINK", "Heartbeat Sync", "SENT", f"Routine Packet ({data_size}KB)")
        
        return PipelineResult(vid, t, d_out, r_out, f_out, c_out, gps_out, s_out, o_out, driver_out, bat_out, inv_out, logs, data_size, payload)

    def get_fleet_data(self):
        fleet = []
        for i in range(FLEET_SIZE):
            vid = f"VIN-{10000+i}"
            batch = "Batch-2023-A" if i % 2 == 0 else "Batch-2023-B"
            is_fault = (batch == "Batch-2023-A" and random.random() < 0.3)
            fault_type = "Rod Knock" if is_fault else "Healthy"
            fleet.append({
                "Vehicle ID": vid,
                "Batch ID": batch,
                "Health Status": "Critical" if is_fault else "Healthy",
                "Fault Type": fault_type,
                "RMS": round(random.uniform(1.5, 3.0) if is_fault else random.uniform(0.1, 0.6), 2),
                "Peak": round(random.uniform(3.0, 5.0) if is_fault else random.uniform(0.5, 1.5), 2),
                "Frequency": random.uniform(380, 420) if is_fault else random.uniform(40, 80)
            })
        return fleet
