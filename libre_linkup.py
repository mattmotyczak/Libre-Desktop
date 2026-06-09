import requests
import hashlib
import time
import random
from datetime import datetime

REGIONS = {
    "us": "https://api.libreview.io",
    "eu": "https://api-eu.libreview.io",
    "eu2": "https://api-eu2.libreview.io",
    "de": "https://api-de.libreview.io",
    "jp": "https://api-jp.libreview.io",
    "ap": "https://api-ap.libreview.io",
    "au": "https://api-au.libreview.io",
    "ae": "https://api-ae.libreview.io"
}

# Trend arrows mapped to symbols and description
TREND_ARROWS = {
    1: ("↓", "Falling quickly"),
    2: ("↘", "Falling"),
    3: ("→", "Stable"),
    4: ("↗", "Rising"),
    5: ("↑", "Rising quickly"),
}

class LibreLinkUpClient:
    def __init__(self, email="", password="", region="us"):
        self.email = email
        self.password = password
        self.region = region
        self.token = None
        self.user_id = None
        self.account_id_hash = None
        
        # Mock mode data state
        self.mock_glucose = 110.0
        self.mock_trend = 3

    def get_base_url(self):
        return REGIONS.get(self.region.lower(), REGIONS["us"])

    def get_headers(self):
        headers = {
            "accept-encoding": "gzip",
            "cache-control": "no-cache",
            "connection": "Keep-Alive",
            "content-type": "application/json",
            "product": "llu.android",
            "version": "4.16.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.user_id:
            if not self.account_id_hash:
                self.account_id_hash = hashlib.sha256(self.user_id.encode('utf-8')).hexdigest()
            headers["Account-Id"] = self.account_id_hash
        return headers

    def login(self):
        # If credentials are not set, run in mock mode
        if not self.email or not self.password:
            print("No credentials provided. Running in OFFLINE MOCK MODE.")
            return True, "Mock Account"

        url = f"{self.get_base_url()}/llu/auth/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        try:
            print(f"Attempting login to base URL: {self.get_base_url()} ...")
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=10)
            print(f"Login Response status code: {response.status_code}")
            if response.status_code == 200:
                res_data = response.json()
                print(f"Login Response JSON keys: {list(res_data.keys())}")
                if "data" in res_data:
                    data_keys = list(res_data["data"].keys())
                    print(f"Login Response data keys: {data_keys}")
                    if "authTicket" in res_data["data"]:
                        ticket_keys = list(res_data["data"]["authTicket"].keys())
                        print(f"Login Response authTicket keys: {ticket_keys}")
                
                if res_data.get("status") == 0:
                    data = res_data.get("data", {})
                    self.token = data.get("authTicket", {}).get("token")
                    self.user_id = data.get("user", {}).get("id")
                    self.account_id_hash = None # Reset to recompute
                    print(f"Token acquired successfully (length={len(self.token) if self.token else 0})")
                    return True, "Login successful"
                else:
                    return False, res_data.get("error", {}).get("message", "Unknown API error")
            else:
                return False, f"Server returned status code {response.status_code}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_connections(self):
        """Returns list of patients (connections). In mock mode, returns a mock connection."""
        if not self.email or not self.password:
            return [{
                "id": "mock-patient-1",
                "firstName": "Demo",
                "lastName": "User",
                "targetLow": 70,
                "targetHigh": 180
            }]

        url = f"{self.get_base_url()}/llu/connections"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("status") == 0:
                    return res_data.get("data", [])
            print(f"Failed to get connections: {response.text}")
            return []
        except Exception as e:
            print(f"Error fetching connections: {e}")
            return []

    def get_glucose_reading(self, patient_id):
        """Gets the latest reading for the specified patient ID."""
        if not self.email or not self.password or patient_id == "mock-patient-1":
            # Generate mock reading
            # Simple random walk to simulate real glucose fluctuation
            change = random.choice([-8, -4, 0, 4, 8])
            self.mock_glucose = max(40.0, min(350.0, self.mock_glucose + change))
            
            # Determine trend arrow based on change
            if change > 4:
                self.mock_trend = 5 # Rising quickly
            elif change > 0:
                self.mock_trend = 4 # Rising
            elif change < -4:
                self.mock_trend = 1 # Falling quickly
            elif change < 0:
                self.mock_trend = 2 # Falling
            else:
                self.mock_trend = 3 # Stable
                
            arrow_sym, arrow_desc = TREND_ARROWS.get(self.mock_trend, ("→", "Stable"))
            
            return {
                "value": self.mock_glucose,
                "trend_arrow": arrow_sym,
                "trend_text": arrow_desc,
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "is_mock": True
            }

        # Otherwise, fetch from live connection list
        connections = self.get_connections()
        for conn in connections:
            if conn.get("id") == patient_id:
                glucose_data = conn.get("glucoseMeasurement")
                if not glucose_data:
                    # Check connection list fallback
                    glucose_data = conn.get("connection", {}).get("glucoseMeasurement")
                
                if glucose_data:
                    val = glucose_data.get("Value")
                    trend = glucose_data.get("TrendArrow")
                    ts_str = glucose_data.get("Timestamp")
                    
                    # Parse timestamp or fallback
                    time_lbl = "Just now"
                    if ts_str:
                        try:
                            # Typically: "MM/DD/YYYY H:MM:SS AM/PM"
                            # Let's return the time part for display
                            parts = ts_str.split(" ")
                            if len(parts) >= 2:
                                time_lbl = f"{parts[1]} {parts[2]}" if len(parts) > 2 else parts[1]
                        except:
                            time_lbl = ts_str
                    
                    arrow_sym, arrow_desc = TREND_ARROWS.get(trend, ("→", "Stable"))
                    return {
                        "value": float(val),
                        "trend_arrow": arrow_sym,
                        "trend_text": arrow_desc,
                        "timestamp": time_lbl,
                        "is_mock": False
                    }
        
        return None
