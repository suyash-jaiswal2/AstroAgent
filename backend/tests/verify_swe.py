import swisseph as swe
import os, sys

# Point to ephemeris data (will use Moshier fallback if no .se1 files present)
ephe_path = os.path.join(os.path.dirname(__file__), "..", "ephemeris_data")
swe.set_ephe_path(os.path.abspath(ephe_path))

# Test: 1990-08-15 14:30 UTC → Sun should be ~Leo 22°
# (UTC for 14:30 IST = 14:30 - 5:30 = 09:00 UTC)
jd = swe.julday(1990, 8, 15, 9.0)  # 09:00 UTC
result = swe.calc_ut(jd, swe.SUN)
xx = result[0] if isinstance(result[0], (list, tuple)) else result
sun_lon = xx[0]
sign_idx = int(sun_lon / 30)
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
print(f"Sun longitude: {sun_lon:.4f}°")
print(f"Sun sign: {SIGNS[sign_idx]} {sun_lon % 30:.2f}°")
print("✓ pyswisseph is working" if SIGNS[sign_idx] == "Leo" else "✗ Check ephemeris setup")