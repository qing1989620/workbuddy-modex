"""Experiment runner (Rule 33-34).

Executes a planned experiment and PERSISTS artifacts to disk
(experiment_lab/<id>/result.json, metrics.csv, predictions.csv). Chat text is
never the source of truth; the Result Ledger reads from these files.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Callable

from .. import atomic
from ..paths import ProjectPaths
from ..schemas.experiment_lab import ExperimentArtifacts, ExperimentPlan, ExperimentStatus


def experiment_dir(pp: ProjectPaths, experiment_id: str) -> Path:
    d = pp.root / "experiment_lab" / experiment_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_result_json(d: Path, result: dict) -> Path:
    p = d / "result.json"
    atomic.write_json(p, result)
    return p


def write_metrics_csv(d: Path, metrics: dict[str, float]) -> Path:
    p = d / "metrics.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in sorted(metrics.items()):
            w.writerow([k, v])
    return p


def write_predictions_csv(d: Path, predictions: list[dict]) -> Path:
    p = d / "predictions.csv"
    if predictions:
        keys = list(predictions[0].keys())
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(predictions)
    else:
        p.write_text("", encoding="utf-8")
    return p


def run_experiment(pp: ProjectPaths, plan: ExperimentPlan,
                   execute: Callable[[ExperimentPlan], dict]) -> ExperimentArtifacts:
    """Run one experiment. `execute` must return a dict with:
    {"metrics": {...}, "predictions": [...], "result": {...}}
    """
    d = experiment_dir(pp, plan.experiment_id)
    started = time.time()
    try:
        out = execute(plan)
    except Exception as e:
        plan.status = ExperimentStatus.failed
        atomic.write_json(d / "failure.json", {"error": str(e), "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        raise
    elapsed = round(time.time() - started, 3)

    rj = write_result_json(d, {**out.get("result", {}), "experiment_id": plan.experiment_id,
                               "elapsed_s": elapsed, "status": "COMPLETED"})
    mc = write_metrics_csv(d, out.get("metrics", {}))
    pc = write_predictions_csv(d, out.get("predictions", []))

    plan.status = ExperimentStatus.completed
    artifacts = ExperimentArtifacts(
        experiment_id=plan.experiment_id,
        result_json=str(rj.relative_to(pp.root)),
        metrics_csv=str(mc.relative_to(pp.root)),
        predictions_csv=str(pc.relative_to(pp.root)),
    )
    return artifacts


def load_result(pp: ProjectPaths, experiment_id: str) -> dict:
    p = experiment_dir(pp, experiment_id) / "result.json"
    return atomic.read_json(p) if p.exists() else {}
