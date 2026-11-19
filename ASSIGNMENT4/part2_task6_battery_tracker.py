"""Battery-aware secure field-tracking simulation (Assignment 4, Part II Task 6).
Run: python part2_task6_battery_tracker.py
Uses only the Python standard library.
"""
from dataclasses import dataclass
import csv
from pathlib import Path

GPS_MA, GPS_SECONDS = 30.0, 2.0
CPU_WAKE_MAH = 0.002
ENCRYPT_MAH = 0.0001
RADIO_FIXED_MAH = {"WIFI": 0.05, "LTE": 0.50, "NONE": None}
RADIO_PER_KB_MAH = {"WIFI": 0.0001, "LTE": 0.0005}
RECORD_KB = 0.2

@dataclass
class Condition:
    name: str
    battery: int
    charging: bool
    network: str
    moving: bool
    saver: bool = False
    temperature_c: int = 30

def policy(c):
    if c.temperature_c >= 42:
        return 300, "defer"
    if c.charging and c.network == "WIFI":
        return 10, "batch_now"
    if c.saver or c.battery <= 15:
        return 300, "defer"
    if c.network == "NONE":
        return (30 if c.moving else 120), "defer"
    if c.battery <= 30:
        return (60 if c.moving else 120), "defer"
    return (15 if c.moving else 60), ("batch_now" if c.network == "WIFI" else "batch_lte")

def sample_energy_mah():
    gps = GPS_MA * GPS_SECONDS / 3600
    return gps + CPU_WAKE_MAH + ENCRYPT_MAH

def simulate(c, hours=1.0, batch_size=60, baseline=False):
    if baseline:
        interval, upload_mode = 10, "immediate"
    else:
        interval, upload_mode = policy(c)
    samples = int(hours * 3600 / interval)
    energy = samples * sample_energy_mah()
    uploads = 0
    if c.network != "NONE" and upload_mode != "defer":
        uploads = samples if upload_mode == "immediate" else (samples + batch_size - 1) // batch_size
        energy += uploads * RADIO_FIXED_MAH[c.network]
        energy += samples * RECORD_KB * RADIO_PER_KB_MAH[c.network]
    wakeups = samples + uploads
    return interval, upload_mode, samples, uploads, wakeups, energy

CONDITIONS = [
    Condition("1 Charging, Wi-Fi", 70, True, "WIFI", False),
    Condition("2 Battery 80%, LTE, moving", 80, False, "LTE", True),
    Condition("3 Battery 20%, stationary, LTE", 20, False, "LTE", False),
    Condition("4 Battery saver ON, 50%, LTE", 50, False, "LTE", True, True),
    Condition("5 No connectivity, 60%, moving", 60, False, "NONE", True),
    Condition("6 Device hot (45C), 70%, Wi-Fi", 70, False, "WIFI", True, False, 45),
    Condition("7 Battery 10%, moving, LTE", 10, False, "LTE", True),
]

def main():
    output = Path(__file__).parent / "data"
    output.mkdir(exist_ok=True)
    csv_path = output / "battery_results.csv"
    headers = ["condition", "interval_seconds", "upload_mode", "samples",
               "uploads", "wakeups", "policy_mAh_per_hour", "baseline_mAh_per_hour"]
    rows = []
    print(f"{'Condition':37} {'Interval':>8} {'Upload':>11} {'Samples':>8} "
          f"{'Uploads':>8} {'Policy mAh':>11} {'Baseline mAh':>13}")
    for condition in CONDITIONS:
        interval, mode, samples, uploads, wakeups, energy = simulate(condition)
        baseline_energy = simulate(condition, baseline=True)[5]
        rows.append([condition.name, interval, mode, samples, uploads, wakeups,
                     f"{energy:.3f}", f"{baseline_energy:.3f}"])
        print(f"{condition.name:37} {interval:>6}s {mode:>11} {samples:>8} "
              f"{uploads:>8} {energy:>11.3f} {baseline_energy:>13.3f}")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"\nResults saved to: {csv_path}")
    print("Energy per sample:", f"{sample_energy_mah():.6f}", "mAh")

if __name__ == "__main__":
    main()
