
import os
import base64
import sqlite3
import pandas as pd
import datetime
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from config import DB_PATH

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# --- UTILS ---

def load_asset_as_base64(file_path):
    """Loads a file as a base64 encoded string."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None
    return None

# --- MODELS ---

@dataclass
class TelemetryFrame:
    vehicle_id: str
    timestamp: str
    # Vibration
    rms: float
    peak: float
    raw_waveform: List[float]
    # Performance
    rpm: int
    speed_kmh: float
    throttle_pos: float
    # Health/Vitals
    temperature: float
    coolant_temp: float
    oil_pressure: float
    battery_volts: float
    brake_wear_pct: float
    tire_pressure: float
    # Metadata
    can_codes: List[str]
    batch_id: str
    _secure_lat: float
    _secure_lon: float

@dataclass
class AgentLogStep:
    agent: str
    location: str # "EDGE" or "CLOUD"
    action: str
    status: str
    details: str
    timestamp: str

@dataclass
class PipelineResult:
    vehicle_id: str
    telemetry: TelemetryFrame
    final_diagnosis: Dict
    final_rca: Optional[Dict]
    financial: Optional[Dict]
    compliance: Optional[Dict]
    gps_data: Optional[Dict]
    scheduling: Optional[Dict]
    ota_status: Optional[str]
    # New Fields for New Agents
    driver_behavior: Optional[Dict]
    battery_health: Optional[Dict]
    inventory: Optional[Dict]
    
    structured_logs: List[AgentLogStep]
    data_upload_size_kb: float 
    transmitted_payload: Dict # The actual JSON sent over the air

# --- DATABASE ---

class DatabaseManager:
    def __init__(self):
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)

    def _init_db(self):
        conn = self._get_conn()
        try:
            cursor = conn.execute("PRAGMA table_info(audit_log)")
            cols = [row[1] for row in cursor.fetchall()]
            if cols and 'agent' not in cols:
                conn.execute("DROP TABLE audit_log")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    agent TEXT,
                    action TEXT,
                    details TEXT
                )
            """)
            conn.commit()
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
        finally:
            conn.close()

    def log(self, agent, action, details):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO audit_log (timestamp, agent, action, details) VALUES (?, ?, ?, ?)",
                (datetime.datetime.utcnow().isoformat(), agent, action, str(details))
            )
            conn.commit()
        except Exception as e:
             logger.error(f"Logging error for agent {agent}: {e}")
        finally:
            conn.close()

    def get_logs(self, limit=20):
        conn = self._get_conn()
        try:
            return pd.read_sql(f"SELECT * FROM audit_log ORDER BY id DESC LIMIT {limit}", conn)
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
            
    def clear_logs(self):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM audit_log")
            conn.commit()
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
        finally:
            conn.close()

def calculate_oem_strategy(vin: str, fault_type: str) -> dict:
    """
    Logic Engine for Strategic Decisions.
    Determines IF a card should be shown and WHAT the context (batch_id) is.
    Does NOT handle text generation (View concern).
    """
    if not fault_type or "Normal" in fault_type:
        return {"show_card": False, "batch_id": None}

    if "Knock" in fault_type:
        return {"show_card": True, "batch_id": "Batch-2023-A"}
    elif "Misfire" in fault_type:
        return {"show_card": True, "batch_id": "Region-North"}
    else:
        # Fallback for "Mount Failure" or any other anomaly
        return {"show_card": True, "batch_id": "VIN-Specific"}
