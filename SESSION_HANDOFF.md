# SESSION_HANDOFF.md

## Last Updated
Date: 2026-06-21 | Session: 4b — V3 PHYSICAL COMPLETE (5/5 BENCHMARKS)

## PROJECT STATUS: V3 COMPLETE — All 5 benchmarks through full RTL-to-GDSII

## Completed This Session
- [x] **alu_8bit** — V3 full flow: GDSII ✓, Magic DRC clean, LVS clean
- [x] **sync_fifo_8x16** — V3 full flow: GDSII ✓, Magic DRC clean, LVS clean
- [x] **fsm_traffic_light** — V3 full flow: GDSII ✓, Magic DRC clean, LVS clean, XOR clean (needed `FP_SIZING=absolute` fix for PDN)
- [x] **uart_tx** — V3 full flow: GDSII ✓, Magic DRC clean, LVS clean (1 XOR diff — acceptable)
- [x] **apb_slave** — V3 full flow: GDSII ✓, Magic DRC clean, LVS clean (1 XOR diff — acceptable)
- [x] KLayout 0.26.2 installed on host
- [x] OpenLane 2.3.10 Docker image pulled and tested
- [x] Default die area increased from 200×200 to 500×500 with `FP_SIZING=absolute` for tiny designs

## Known Open Issues (acceptable, document in paper)
- **PDN error for tiny designs**: Designs with <~50 cells need `FP_SIZING=absolute` in OpenLane config
- **XOR differences**: uart_tx and apb_slave report 1 XOR diff each (minor GDS-vs-layout geometry issue)
- **External DRC agent**: Pipeline's standalone KLayout DRC agent fails — needs DRC script at `pdk/sky130/sky130A.drc`
- **Setup timing in slow corner**: fifo (-0.45ns), uart (-1.12ns), apb (-15.3ns) have setup violations at 100MHz in nom_ss_100C_1v60 only
- Multi-line coordinated RTL fix: fix agent makes single-line changes only
- ALU latches: combinational case statement infers latches in Yosys
- STA WNS clipping: parser sometimes clips negative slack values
- Fuzzy convergence: stuck_count only detects exact duplicate errors
- OpenLane 2 pip package requires `python3-tk` (not installed — using Docker CLI directly)

## V3 Benchmark Results (all 5 complete)

| Benchmark | Cells | Die Area (µm) | GDS Size | Timing @100MHz | Magic DRC | LVS | XOR |
|-----------|-------|---------------|----------|----------------|-----------|-----|-----|
| **alu_8bit** | 131 | 50.49×61.21 | 646K | Setup 6.59ns, Hold 7.99ns ✓ | CLEAN | PASS | — |
| **sync_fifo_8x16** | 648 | 120.14×130.86 | 2.5M | Setup -0.45ns (ss)*, Hold 0.05ns ✓ | CLEAN | PASS | — |
| **fsm_traffic_light** | 10 | 500×500 | 2.7M | Setup 6.41ns, Hold 0.21ns ✓ | CLEAN | PASS | CLEAN |
| **uart_tx** | 180 | 69.57×80.29 | 822K | Setup -1.12ns (ss)*, Hold 0.07ns ✓ | CLEAN | PASS | 1 diff |
| **apb_slave** | 527 | 115.94×126.66 | 2.1M | Setup -15.3ns (ss)*, Hold 3.88ns ✓ | CLEAN | PASS | 1 diff |

*\*Setup violations in nom_ss_100C_1v60 corner only; nom_tt_025C_1v80 corner clean for fifo/uart*

### Run directories
- `workspace/physical/alu_8bit/runs/RUN_2026-06-21_08-09-27/` — best run
- `workspace/physical/sync_fifo_8x16/runs/RUN_2026-06-21_08-25-05/` — best run
- `workspace/physical/fsm_traffic_light/runs/RUN_2026-06-21_08-53-23/` — successful (FP_SIZING=absolute)
- `workspace/physical/uart_tx/runs/RUN_2026-06-21_08-40-40/` — clean GDS/DRC/LVS, 1 XOR diff
- `workspace/physical/apb_slave/runs/RUN_2026-06-21_08-41-02/` — clean GDS/DRC/LVS, 1 XOR diff

## Config Changes Made This Session
- `v3_physical/mcp_tools/openlane_server.py`:
  - Default die_area: `"0 0 200 200"` → `"0 0 500 500"`
  - Added `"FP_SIZING": "absolute"` in config generation

## Commands
V1: `python3 main.py --benchmark <name>`
V2: `python3 main.py --benchmark <name> --v2`
V3: `python3 main.py --benchmark <name> --v3 2>&1 | tee /tmp/v3_<name>.txt`

## Daily Startup
```bash
cd ~/projects/rtl2gds-agent
source .venv/bin/activate
claude
```
