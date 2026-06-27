#!/usr/bin/env python3
"""
capture_demo_data.py — Run V3 pipeline in real mode, capture all SSE events
and artifacts, save to demo_data/alu_8bit_demo.json.

Usage:
    ./capture_demo_data.py

Requires:
    - Backend running on localhost:8000 with PIPELINE_MODE=real
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
OUTPUT_DIR = Path(__file__).resolve().parent / "demo_data"
OUTPUT_FILE = OUTPUT_DIR / "alu_8bit_demo.json"

# Mapping of stage names to display names and icons
STAGE_INFO = {
    "spec_parser": {"label": "Spec Parser", "icon": "📋"},
    "verification_planner": {"label": "Verification Planner", "icon": "📐"},
    "rtl_gen": {"label": "RTL Generator", "icon": "🔧"},
    "testbench": {"label": "Testbench Generator", "icon": "🧪"},
    "simulation": {"label": "Simulation", "icon": "⚡"},
    "simulation_re": {"label": "Simulation (re-run)", "icon": "⚡"},
    "synthesis": {"label": "Synthesis", "icon": "🔬"},
    "sta": {"label": "Static Timing Analysis", "icon": "⏱️"},
    "openlane": {"label": "Physical Design", "icon": "🏭"},
    "drc": {"label": "Design Rule Check", "icon": "✅"},
    "log_analysis": {"label": "Log Analysis", "icon": "🔍"},
    "fix": {"label": "Fix Agent", "icon": "🛠️"},
}


def api_get(path):
    """GET request to the backend API."""
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"  [ERROR] HTTP {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def api_post(path, data):
    """POST JSON to the backend API."""
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"  [ERROR] HTTP {e.code}: {e.read().decode()[:300]}")
        return None


def stream_sse(job_id, timeout=600):
    """Stream SSE events for a job, yielding parsed events."""
    url = f"{API_BASE}/api/run/stream?job_id={job_id}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        buffer = b""
        start = time.time()
        while time.time() - start < timeout:
            chunk = resp.read(1)
            if not chunk:
                break
            buffer += chunk
            if b"\n\n" in buffer:
                raw, buffer = buffer.split(b"\n\n", 1)
                text = raw.decode(errors="replace")
                for line in text.split("\n"):
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            event = json.loads(data_str)
                            elapsed = time.time() - start
                            event["_captured_at"] = round(elapsed, 3)
                            yield event
                        except json.JSONDecodeError:
                            pass
                    elif line.startswith("event:"):
                        event_type = line[6:].strip()
                        if event_type in ("done", "stream_end"):
                            return


def collect_artifacts(job_id, benchmark):
    """Collect all artifacts from a completed job."""
    artifacts = {}

    # Get job status to check results
    job_data_raw = api_get(f"/api/run/{job_id}")
    if not job_data_raw:
        return artifacts
    job_data = json.loads(job_data_raw).get("data", {})

    artifacts["sim_passed"] = job_data.get("sim_passed")
    artifacts["timing_met"] = job_data.get("timing_met")
    artifacts["drc_passed"] = job_data.get("drc_passed")
    artifacts["progress_pct"] = job_data.get("progress_pct")
    artifacts["event_count"] = job_data.get("event_count")
    artifacts["elapsed_seconds"] = job_data.get("elapsed_seconds")
    artifacts["stages"] = job_data.get("stages", [])

    # Get artifacts list
    artifacts_raw = api_get(f"/api/run/{job_id}/artifacts")
    if artifacts_raw:
        artifacts["artifact_list"] = json.loads(artifacts_raw).get("data", {}).get("artifacts", [])

    # Check for VCD file
    vcd_path = Path("workspace") / benchmark / f"{benchmark}.vcd"
    if vcd_path.exists():
        artifacts["vcd_path"] = str(vcd_path)
        artifacts["vcd_size_bytes"] = vcd_path.stat().st_size

    # Check for netlist
    netlist_path = Path("workspace/synthesis") / f"{benchmark}_netlist.v"
    if netlist_path.exists():
        artifacts["netlist_path"] = str(netlist_path)
        artifacts["netlist_size_bytes"] = netlist_path.stat().st_size

    # Check for GDS files
    gds_files = list(Path("workspace/physical").rglob("*.gds"))
    if gds_files:
        # Pick the most recent final/gds
        final_gds = sorted(gds_files, key=lambda p: p.stat().st_mtime, reverse=True)
        latest = final_gds[0]
        artifacts["gds_path"] = str(latest)
        artifacts["gds_size_bytes"] = latest.stat().st_size

    # Extract synthesis report from backend logs
    log_path = Path("/tmp/backend_v3c.log")
    if log_path.exists():
        content = log_path.read_text()
        syn_match = re.search(r"Synthesis complete.*?cells:\s*(\d+).*?area:\s*([\d.]+)", content)
        if syn_match:
            artifacts["synthesis_cell_count"] = int(syn_match.group(1))
            artifacts["synthesis_area"] = float(syn_match.group(2))
        sta_match = re.search(r"Timing met.*?WNS=([-\d.]+)", content)
        if sta_match:
            artifacts["sta_wns"] = float(sta_match.group(1))

    return artifacts


def run():
    print("=" * 60)
    print("  V3 PIPELINE DATA CAPTURE")
    print("=" * 60)
    print()

    # Health check
    print("[1/4] Checking backend...")
    health = api_get("/health")
    if not health:
        print("  [FAIL] Backend not reachable at", API_BASE)
        sys.exit(1)
    print(f"  [OK] Backend healthy")

    # Submit V3 job
    print()
    print("[2/4] Submitting V3 pipeline job (alu_8bit, reference RTL+TB)...")
    resp = api_post("/api/run", {
        "benchmark": "alu_8bit",
        "pipeline_version": "v3",
        "use_reference_rtl": True,
        "use_reference_tb": True,
    })
    if not resp:
        print("  [FAIL] Could not submit job")
        sys.exit(1)

    job_data = json.loads(resp).get("data", {})
    job_id = job_data.get("job_id")
    print(f"  Job ID: {job_id}")
    print(f"  Status: {job_data.get('status')}")

    # Stream SSE events
    print()
    print("[3/4] Streaming SSE events (waiting for pipeline to complete)...")
    events = []
    last_stage = ""
    for event in stream_sse(job_id):
        events.append(event)
        ev_type = event.get("event_type", "")
        stage = event.get("stage", "")
        if ev_type == "stage_started" and stage != last_stage:
            last_stage = stage
            print(f"    stage={stage}  seq={event.get('sequence_num')}  elapsed={event.get('_captured_at')}s")
        elif ev_type in ("simulation_result", "synthesis_result", "sta_result", "drc_result"):
            payload = event.get("payload", {})
            passed = payload.get("passed")
            cells = payload.get("cell_count")
            timing = payload.get("timing_met")
            drc = payload.get("drc_passed")
            print(f"    result: {ev_type}  seq={event.get('sequence_num')}  passed={passed} cells={cells} timing={timing} drc={drc}")
        elif ev_type == "job_completed":
            print(f"    JOB COMPLETED — total elapsed: {event.get('elapsed_time'):.1f}s")

    print(f"  Captured {len(events)} events")

    if not events:
        print("  [FAIL] No events captured")
        sys.exit(1)

    # Collect artifacts
    print()
    print("[4/4] Collecting artifacts...")
    artifacts = collect_artifacts(job_id, "alu_8bit")
    print(f"  sim_passed: {artifacts.get('sim_passed')}")
    print(f"  timing_met: {artifacts.get('timing_met')}")
    print(f"  drc_passed: {artifacts.get('drc_passed')}")
    print(f"  synthesis: {artifacts.get('synthesis_cell_count')} cells, {artifacts.get('synthesis_area')} µm²")
    print(f"  STA WNS: {artifacts.get('sta_wns')}")
    print(f"  VCD: {artifacts.get('vcd_path', 'N/A')} ({artifacts.get('vcd_size_bytes', 0)} bytes)")
    print(f"  GDS: {artifacts.get('gds_path', 'N/A')} ({artifacts.get('gds_size_bytes', 0)} bytes)")
    print(f"  Netlist: {artifacts.get('netlist_path', 'N/A')} ({artifacts.get('netlist_size_bytes', 0)} bytes)")
    print(f"  Total stages: {len(artifacts.get('stages', []))}")

    # Build the demo payload
    demo = {
        "meta": {
            "version": "1.0",
            "description": "RTL-to-GDS demo data — alu_8bit benchmark",
            "benchmark": "alu_8bit",
            "pipeline_version": "v3",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": "PIPELINE_MODE=real",
            "total_events": len(events),
            "total_elapsed_seconds": artifacts.get("elapsed_seconds", 0),
        },
        "events": events,
        "artifacts": artifacts,
    }

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(demo, indent=2, default=str))
    file_size = OUTPUT_FILE.stat().st_size
    print(f"\n  Saved: {OUTPUT_FILE} ({file_size / 1024:.1f} KB)")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
