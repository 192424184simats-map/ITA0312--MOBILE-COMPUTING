"""Security audit model for Assignment 4, Part II Task 4.
STRIDE threat -> mitigation -> residual risk -> release verdict.
Run: python part2_task4_security_audit.py
"""
import json

def audit(app):
    threats = []
    def add(asset, stride, threat, vector, mechanism, status, residual):
        threats.append((asset, stride, threat, vector, mechanism, status, residual))
    dangerous = {"CAMERA", "ACCESS_FINE_LOCATION"}
    for permission in app["permissions"]:
        if permission in dangerous:
            add("Camera/Location", "E", "Over-privileged app abuses " + permission,
                "Malware tricks user / app requests at install",
                "Runtime permission + user consent", "Blocked", "User may still grant; accepted")
    for store in app["stores"]:
        if store == "SharedPreferences:plain_token":
            add("Auth token", "I", "Token theft by rooted/backup reader",
                "adb backup / root read of preferences XML", "App sandbox (UID) only",
                "Exposed", "Plaintext on disk; escalate")
        elif store == "SQLite:encrypted+Keystore":
            add("Appointment DB", "I", "Local data theft", "Rooted device file copy",
                "SQLCipher + hardware-backed Keystore key", "Partially Blocked",
                "Key extraction on compromised OS; accepted")
        elif store == "Keystore":
            add("Session key", "S", "Credential impersonation", "Key export attempt",
                "Keystore/TEE non-exportable key", "Blocked", "TEE vulnerability; accepted")
    for endpoint in app["endpoints"]:
        if endpoint.startswith("http://"):
            add("API traffic", "T/I", "MITM modifies/reads records", "Rogue Wi-Fi proxy",
                "None (cleartext)", "Exposed", "Full read/modify; escalate")
        elif app.get("pinning"):
            add("API traffic", "T/I", "MITM on REST channel", "Rogue Wi-Fi proxy",
                "TLS 1.3 + certificate pinning", "Blocked", "Server key compromise; accepted")
        else:
            add("API traffic", "T/I", "MITM with rogue CA", "User-installed CA",
                "TLS only (no pinning)", "Partially Blocked", "Rogue CA accepted; mitigate with pinning")
    for component in app["components"]:
        if component["exported"] and not component.get("permission"):
            add("Exported " + component["name"], "E/T",
                "Any app launches component with crafted intent", "adb shell am start -n ...",
                "None (exported, no permission)", "Exposed", "Unauthenticated entry point; escalate")
        else:
            label = ("Exported " if component["exported"] else "Internal ") + component["name"]
            add(label, "E/T", "Foreign app invokes component", "Intent from another UID",
                "exported=false / signature permission", "Blocked", "None")
    add("APK integrity", "T", "Tampered update installed", "Sideloaded repackaged APK",
        "APK signature v2/v3 + Play Protect + verified boot", "Blocked", "Developer key theft; accepted")
    add("Audit log", "R", "Repudiation of data access", "No client-side trustworthy record",
        "Server-side signed audit log", "Partially Blocked", "Client log forgeable; accepted")
    add("Service availability", "D", "Battery/CPU exhaustion via intent flood", "Repeated intents",
        "Process limits + rate limiting", "Partially Blocked", "Local DoS possible; accepted")
    return threats

def show(name, app):
    rows = audit(app)
    print("=" * 96)
    print("AUDIT:", name)
    for asset, stride, threat, vector, mechanism, status, residual in rows:
        print(f"Threat[{stride}] {threat}")
        print(f"  Asset: {asset} | Vector: {vector}")
        print(f"  Mitigation: {mechanism}")
        print(f"  Result: {status} | Residual: {residual}")
    exposed = sum(row[5] == "Exposed" for row in rows)
    partial = sum(row[5] == "Partially Blocked" for row in rows)
    blocked = len(rows) - exposed - partial
    verdict = ("FAIL - release blocked" if exposed else
               "CONDITIONAL PASS - residual risks documented" if partial else "PASS")
    print(f"SUMMARY: {len(rows)} threats | Exposed={exposed} | Partial={partial} | Blocked={blocked}")
    print("VERDICT:", verdict)

if __name__ == "__main__":
    baseline = {
        "permissions": ["CAMERA", "ACCESS_FINE_LOCATION", "INTERNET"],
        "stores": ["SQLite:encrypted+Keystore", "Keystore"],
        "endpoints": ["https://api.clinic.example/v1"], "pinning": True,
        "components": [
            {"name": "MainActivity", "exported": True, "permission": "LAUNCHER"},
            {"name": "PatientDetailActivity", "exported": False}
        ]
    }
    show("BASELINE (secure design)", baseline)
    weakened = json.loads(json.dumps(baseline))
    weakened["components"][1]["exported"] = True
    weakened["endpoints"] = ["http://api.clinic.example/v1"]
    weakened["stores"] = ["SharedPreferences:plain_token", "Keystore"]
    show("WEAKENED (exported component + cleartext + plain token)", weakened)
