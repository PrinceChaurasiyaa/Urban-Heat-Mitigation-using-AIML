"""
Orchestrates the UHIMP pipeline phase by phase, matching the SRS execution
roadmap (Section 9, Phases 0-7).

Usage:
    python scripts/run_pipeline.py --phase data_acquisition
    python scripts/run_pipeline.py --phase all
"""

import argparse
import sys

PHASES = [
    "data_acquisition",
    "hotspot_mapping",
    "driver_analysis",
    "modeling",
    "scenario_simulation",
    "optimization",
    "reporting",
]


def run_phase(phase, cfg_path):
    print(f"[UHIMP] Running phase: {phase} (config: {cfg_path})")

    if phase == "data_acquisition":
        from src.data_acquisition.landsat8 import load_config, fetch_landsat8_lst
        import ee
        cfg = load_config(cfg_path)
        ee.Initialize(project=cfg["project"]["gee_project_id"])
        coll, aoi = fetch_landsat8_lst(cfg)
        print("Scenes matched:", coll.size().getInfo())

    elif phase == "hotspot_mapping":
        print("TODO: wire up src.hotspot_mapping.classify / hotspot_clustering")

    elif phase == "driver_analysis":
        print("TODO: wire up src.driver_analysis.shap_analysis / gwr_crosscheck")

    elif phase == "modeling":
        print("TODO: wire up src.modeling.baseline_model + physics_informed.pinn_model")

    elif phase == "scenario_simulation":
        print("TODO: wire up src.scenario_simulation.perturbation")

    elif phase == "optimization":
        print("TODO: wire up src.optimization.genetic_algorithm")

    elif phase == "reporting":
        print("TODO: wire up src.visualization.report_builder")

    else:
        print(f"Unknown phase: {phase}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=PHASES + ["all"], required=True)
    parser.add_argument("--config", default="configs/aoi.yaml")
    args = parser.parse_args()

    if args.phase == "all":
        for p in PHASES:
            run_phase(p, args.config)
    else:
        run_phase(args.phase, args.config)
