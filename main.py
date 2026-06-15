"""
main.py
Entry point for the RTL-to-GDS V1 agent pipeline.
Usage:
  python main.py --benchmark alu_8bit
  python main.py --spec "8-bit ALU with add sub and or xor" --name alu_test
  python main.py --rtl broken_alu.v --spec "8-bit ALU with bug" --name alu_test
"""

import argparse
from pathlib import Path
from v1_core.pipeline import run_pipeline
from v1_core.utils import logger
from v1_core.utils.trace2skill import get_stats


def main():
    parser = argparse.ArgumentParser(description="RTL-to-GDS V1 Agent Pipeline")
    parser.add_argument("--benchmark", type=str, help="Run a benchmark from benchmarks/ folder")
    parser.add_argument("--spec", type=str, help="Natural language hardware specification")
    parser.add_argument("--name", type=str, help="Design name (required with --spec)")
    parser.add_argument("--rtl", type=str, help="Path to existing RTL file (skips RTL generation)")
    parser.add_argument("--v2", action="store_true", help="Run V2 pipeline with synthesis and STA")
    args = parser.parse_args()

    rtl_code = ""

    # If --rtl is provided, read the file and skip RTL generation
    if args.rtl:
        rtl_path = Path(args.rtl)
        if not rtl_path.exists():
            logger.error(f"RTL file not found: {args.rtl}")
            return
        rtl_code = rtl_path.read_text()
        logger.info(f"Loaded RTL file: {args.rtl} ({len(rtl_code.splitlines())} lines)")

    if args.benchmark:
        spec_path = Path(f"benchmarks/{args.benchmark}/spec.txt")
        if not spec_path.exists():
            logger.error(f"Benchmark not found: {args.benchmark}")
            return
        spec = spec_path.read_text()
        design_name = args.benchmark
        logger.info(f"Loaded benchmark: {design_name}")

    elif args.spec:
        if not args.name:
            logger.error("Please provide --name when using --spec")
            return
        spec = args.spec
        design_name = args.name

    else:
        logger.error("Usage: python main.py --benchmark alu_8bit")
        logger.error("       python main.py --spec 'your spec here' --name design_name")
        logger.error("       python main.py --rtl <file.v> --spec 'spec' --name design_name")
        return

    # Auto-detect reference RTL from benchmarks folder
    if not rtl_code and args.benchmark:
        ref_path = Path(f"benchmarks/{design_name}/reference_rtl.v")
        if ref_path.exists():
            rtl_code = ref_path.read_text()
            logger.info(f"Using reference RTL for {design_name} — skipping LLM generation")

    # Route to V2 or V1 pipeline
    if args.v2:
        try:
            from v2_verification.pipeline import run_v2_pipeline
        except ImportError:
            logger.error("V2 pipeline not available. Install V2 dependencies or check v2_verification/")
            return
        final_state = run_v2_pipeline(spec=spec, design_name=design_name, rtl_code=rtl_code)
    else:
        final_state = run_pipeline(spec=spec, design_name=design_name, rtl_code=rtl_code)

    # Print Trace2Skill stats after run
    logger.divider()
    logger.info("Trace2Skill Memory Stats:")
    stats = get_stats()
    for category, count in stats.items():
        logger.info(f"  {category}: {count} skills stored")
    logger.divider()


if __name__ == "__main__":
    main()
