#!/usr/bin/env python3
"""
Generate deterministic synthetic datasets for Campus Energy Command Center.

Produces:
1. data/timetable.csv: 24-hour campus occupancy, essential loads, and nominal AC loads
   across Academic, Lab, Hostel, and Library_Admin buildings (BDG2 profile shapes).
2. data/solar_weather_cache.csv: 24-hour ambient temperature, solar irradiance,
   cloud cover, and rooftop solar generation profile (150 kWp array peaking ~128 kW).
"""

import csv
import math
import os
from pathlib import Path


def generate_timetable(data_dir: Path) -> Path:
    """Generate 24-hour timetable with BDG2-inspired building load profiles."""
    filepath = data_dir / "timetable.csv"

    fieldnames = [
        "hour",
        "Academic_occ",
        "Lab_occ",
        "Hostel_occ",
        "Library_Admin_occ",
        "Academic_essential_kw",
        "Lab_essential_kw",
        "Hostel_essential_kw",
        "Library_Admin_essential_kw",
        "Academic_ac_nominal_kw",
        "Lab_ac_nominal_kw",
        "Hostel_ac_nominal_kw",
        "Library_Admin_ac_nominal_kw",
    ]

    # Hourly building profiles (24 hours: 00:00 to 23:00)
    rows = []
    for h in range(24):
        # 1. Academic Building: Class schedule 08:00-18:00, peak 10:00-15:00
        if 8 <= h <= 17:
            academic_occ = int(350 + 130 * math.sin(math.pi * (h - 8) / 9))
            academic_essential = 42.0 + 4.0 * math.sin(math.pi * (h - 8) / 9)
            academic_ac = 45.0 + 35.0 * math.sin(math.pi * (h - 8) / 9)
        elif 18 <= h <= 21:
            academic_occ = 60 - (h - 18) * 15
            academic_essential = 32.0
            academic_ac = 18.0 - (h - 18) * 4.0
        else:
            academic_occ = 10
            academic_essential = 28.0
            academic_ac = 5.0

        # 2. Lab Building: 24/7 mission-critical servers, fume hoods, instrumentation
        # High base essential load (constant ~95-102 kW) + steady chiller cooling
        if 9 <= h <= 18:
            lab_occ = 85 + int(35 * math.sin(math.pi * (h - 9) / 9))
            lab_essential = 102.0
            lab_ac = 58.0 + 8.0 * math.sin(math.pi * (h - 9) / 9)
        else:
            lab_occ = 20
            lab_essential = 96.0  # Server racks & emergency exhaust 24/7
            lab_ac = 46.0

        # 3. Hostel Building: Residential morning (06:00-08:30) & evening/night (18:00-24:00)
        if 0 <= h <= 6:
            hostel_occ = 580 - h * 10
            hostel_essential = 34.0
            hostel_ac = 42.0 - h * 2.0
        elif 7 <= h <= 16:
            hostel_occ = 70 + int(30 * math.cos(math.pi * (h - 7) / 9))
            hostel_essential = 26.0
            hostel_ac = 18.0
        else:  # 17 to 23
            hostel_occ = 250 + (h - 16) * 55
            hostel_essential = 38.0
            hostel_ac = 35.0 + (h - 16) * 4.2

        # 4. Library & Administration: Steady occupancy 08:00-22:00
        if 8 <= h <= 21:
            lib_occ = int(140 + 110 * math.sin(math.pi * (h - 8) / 13))
            lib_essential = 30.0 + 3.0 * math.sin(math.pi * (h - 8) / 13)
            lib_ac = 36.0 + 16.0 * math.sin(math.pi * (h - 8) / 13)
        else:
            lib_occ = 12
            lib_essential = 22.0
            lib_ac = 6.0

        rows.append({
            "hour": h,
            "Academic_occ": int(academic_occ),
            "Lab_occ": int(lab_occ),
            "Hostel_occ": int(hostel_occ),
            "Library_Admin_occ": int(lib_occ),
            "Academic_essential_kw": round(academic_essential, 2),
            "Lab_essential_kw": round(lab_essential, 2),
            "Hostel_essential_kw": round(hostel_essential, 2),
            "Library_Admin_essential_kw": round(lib_essential, 2),
            "Academic_ac_nominal_kw": round(academic_ac, 2),
            "Lab_ac_nominal_kw": round(lab_ac, 2),
            "Hostel_ac_nominal_kw": round(hostel_ac, 2),
            "Library_Admin_ac_nominal_kw": round(lib_ac, 2),
        })

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


def generate_solar_weather_cache(data_dir: Path) -> Path:
    """Generate 24-hour solar radiation, temperature, and 150 kWp solar PV output."""
    filepath = data_dir / "solar_weather_cache.csv"

    fieldnames = [
        "hour",
        "shortwave_radiation_wm2",
        "cloud_cover_pct",
        "ambient_temp_c",
        "solar_kw_available",
    ]

    rows = []
    for h in range(24):
        # Solar radiation model (sunrise ~06:00, sunset ~18:30, peak at 12:30)
        if 6 <= h <= 18:
            # Solar peak ~875 W/m² around 12:00-13:00
            solar_angle = math.sin(math.pi * (h - 6) / 12)
            radiation = max(0.0, 875.0 * (solar_angle ** 1.15))
            # 150 kWp solar array with ~85% performance ratio: 150 * (G / 1000) * 0.98
            # Peaking at 128.0 kW at 12:00-13:00
            solar_kw = round(150.0 * (radiation / 1000.0) * 0.975, 2)
            cloud_cover = round(8.0 + 5.0 * math.sin(h), 1)
        else:
            radiation = 0.0
            solar_kw = 0.0
            cloud_cover = round(6.0 + 3.0 * math.cos(h), 1)

        # Ambient temperature curve: minimum ~22°C at 05:00, maximum ~34.5°C at 14:00
        temp = round(28.0 + 6.5 * math.sin(math.pi * (h - 8) / 12), 2)
        if h < 6:
            temp = round(22.0 + (6 - h) * 0.4, 2)

        rows.append({
            "hour": h,
            "shortwave_radiation_wm2": round(radiation, 2),
            "cloud_cover_pct": cloud_cover,
            "ambient_temp_c": temp,
            "solar_kw_available": max(0.0, solar_kw),
        })

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    timetable_path = generate_timetable(data_dir)
    solar_path = generate_solar_weather_cache(data_dir)

    print(f"Generated: {timetable_path}")
    print(f"Generated: {solar_path}")


if __name__ == "__main__":
    main()

