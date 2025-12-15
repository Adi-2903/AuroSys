
# ---- CONFIGURATION ----
DB_PATH = "aurosys_production_v9.db"
SAMPLE_RATE = 2000  # Hz
SAMPLES = 1000      # 0.5s window
FLEET_SIZE = 50

WORKSHOPS = [
    {"name": "Hero Hub - Indiranagar", "lat": 12.9716, "lon": 77.5946, "rating": 4.8},
    {"name": "Hero Hub - Koramangala", "lat": 12.9352, "lon": 77.6245, "rating": 4.5},
    {"name": "Hero Hub - Whitefield", "lat": 12.9698, "lon": 77.7500, "rating": 4.2},
    {"name": "Hero Hub - Central", "lat": 28.6139, "lon": 77.2090, "rating": 4.9},
]

# ---- SYSTEM INSTRUCTIONS (ADK) ----
SYSTEM_INSTRUCTION_DIAGNOSIS = """
ROLE: You are the 'DiagnosisAgent' (Edge Compute Node).
OBJECTIVE: Analyze real-time sensor streams to detect immediate failure modes.
CONTEXT:
- Rod Knock: RMS > 1.2G, Dominant Freq ~400Hz. Code P0301.
- Misfire: RMS < 0.6G, Irregular peaks. Code P0300.
- Mount Failure: Low freq wobble (<20Hz). Code C1234.

OUTPUT: JSON with specific keys:
- fault_detected (bool)
- fault_type (str)
- severity (str): "Critical", "Medium", "Low"
- driver_friendly_message (str): Empathetic message for the driver.
- safety_tips (list[str]): Immediate safety actions.
- upload_required (bool): Set to true if fault is Critical/Medium to trigger cloud upload.
- confidence (float)
"""

SYSTEM_INSTRUCTION_RCA = """
ROLE: You are the 'RCAAgent' (Cloud Compute Node).
OBJECTIVE: Correlate diagnosis to OEM supply chain data.
CONTEXT:
- Batch-2023-A: Known defect in Connecting Rod Bearings.
- Batch-2023-B: Known defect in O2 Sensors.
- Software-ECU-v1.2: Bug causing phantom misfires.
OUTPUT: JSON with keys: is_batch_defect(bool), batch_id(str), manufacturing_action(str), estimated_cost_per_unit(int), ota_eligible(bool).
"""
