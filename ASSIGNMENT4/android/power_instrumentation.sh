#!/usr/bin/env bash
# Assignment 4, Part II Task 5 — run on an Android emulator/device with ADB.
set -e
PKG="${1:-edu.simats.ita03}"
adb shell dumpsys batterystats --reset
adb shell dumpsys batterystats --enable full-wake-history
adb shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
adb shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"
adb shell dumpsys deviceidle force-idle
adb shell dumpsys deviceidle step
adb shell am set-standby-bucket "$PKG" rare
adb shell dumpsys usagestats | grep -i bucket || true
adb shell dumpsys batterystats "$PKG" > "batterystats_${PKG}.txt"
adb bugreport "bugreport_${PKG}.zip"
