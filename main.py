"""
main.py
Entry point for the RTL-to-GDS V1 agent pipeline.
Usage:
  python main.py --benchmark alu_8bit
  python main.py --spec "8-bit ALU with add sub and or xor" --name alu_test
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
    args = parser.parse_args()

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
        return

    # Run the pipeline
    final_state = run_pipeline(spec=spec, design_name=design_name)

    # Print Trace2Skill stats after run
    logger.divider()
    logger.info("Trace2Skill Memory Stats:")
    stats = get_stats()
    for category, count in stats.items():
        logger.info(f"  {category}: {count} skills stored")
    logger.divider()


if __name__ == "__main__":
    main()
