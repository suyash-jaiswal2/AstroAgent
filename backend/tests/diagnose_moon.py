"""
Diagnostic script: pinpoint the Moon calculation bug.
Run: python tests/diagnose_moon.py  (with venv active, from backend/)
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytz
import swisseph as swe
from datetime import datetime

EPHE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ephemeris_data"))
swe.set_ephe_path(EPHE_PATH)
print(f"Ephemeris path: {EPHE_PATH}")

# --- Step 1: Compute the Julian Day ---
timezone = "Asia/Kolkata"
date = "1990-08-15"
time = "14:30"

tz = pytz.timezone(timezone)
dt_local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
dt_aware = tz.localize(dt_local, is_dst=None)
dt_utc = dt_aware.astimezone(pytz.utc)
print(f"\nLocal : {dt_local}")
print(f"UTC   : {dt_utc}")

jd = swe.julday(
    dt_utc.year, dt_utc.month, dt_utc.day,
    dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
)
print(f"JD    : {jd:.6f}  (expected ≈ 2448117.875)")

# --- Step 2: Raw swe.calc_ut return value ---
print("\n--- Raw swe.calc_ut output ---")
for name, pid in [("Sun", swe.SUN), ("Moon", swe.MOON)]:
    result = swe.calc_ut(jd, pid, 0)
    print(f"  {name}: type={type(result)}, value={result}")

# --- Step 3: Check what version of pyswisseph is installed ---
print(f"\npyswisseph version : {swe.version}")

# --- Step 4: Parse exactly as _calc_planet does ---
print("\n--- Parsed longitudes (as _calc_planet does) ---")
for name, pid in [("Sun", swe.SUN), ("Moon", swe.MOON), ("Rahu", swe.TRUE_NODE)]:
    result = swe.calc_ut(jd, pid, 0)
    xx = result[0] if (isinstance(result, tuple) and isinstance(result[0], (list, tuple))) else result
    lon = float(xx[0]) % 360
    sign_names = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                  "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    sign = sign_names[int(lon / 30)]
    deg = lon % 30
    print(f"  {name}: lon={lon:.4f}°  → {sign} {deg:.2f}°")

# --- Step 5: Check if sidereal mode is already active at import time ---
print("\n--- Sidereal mode check ---")
# If swe.get_ayanamsa_ut returns non-zero with mode active, sidereal is on
ayanamsa = swe.get_ayanamsa_ut(jd)
print(f"  Ayanamsa at start (should be 0 if tropical): {ayanamsa:.4f}°")
