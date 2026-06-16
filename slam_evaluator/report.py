"""
report.py
=========
Assembles the final evaluation report from metrics, log analysis, and config.

Output structure in the report directory:
    report.md          ← main human-readable Markdown report
  results.json       ← machine-readable all metrics
  estimated_traj.txt ← TUM format (symlink or copy)
  gt_traj.txt        ← TUM format (symlink or copy)
  run.log            ← full SLAM output (already written by runner)
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def generate_report(
    report_dir: str,
    dataset_cfg: Dict[str, Any],
    slam_mode: str,
    metrics: Dict[str, Any],
    log_analysis: Dict[str, Any],
    estimated_traj_path: str,
    gt_traj_path: str,
    log_path: str,
    run_start: datetime,
    run_end: datetime,
) -> str:
    """
    Write the full report to report_dir.
    Returns the path to the generated report.md.
    """
    out = Path(report_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Copy trajectory files into the report dir for portability
    _safe_copy(estimated_traj_path, str(out / "estimated_traj.txt"))
    _safe_copy(gt_traj_path,        str(out / "gt_traj.txt"))
    _safe_copy(log_path,            str(out / "run.log"))

    # Generate aligned 2D trajectory plot
    _generate_trajectory_plot(estimated_traj_path, gt_traj_path, str(out / "trajectory.png"))


    # ── results.json ──────────────────────────────────────────────────────────
    results = {
        "dataset":    dataset_cfg.get("name", "unknown"),
        "slam_mode":  slam_mode,
        "timestamp":  run_start.isoformat(),
        "duration_sec": (run_end - run_start).total_seconds(),
        "metrics":    metrics,
        "log_analysis": log_analysis,
    }
    json_path = out / "results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)

    # ── report.md ─────────────────────────────────────────────────────────────
    md = _build_markdown(
        dataset_cfg, slam_mode, metrics, log_analysis,
        run_start, run_end
    )
    md_path = out / "report.md"
    with open(md_path, 'w') as f:
        f.write(md)

    return str(md_path)


# ---------------------------------------------------------------------------
# Markdown builder
# ---------------------------------------------------------------------------

def _build_markdown(
    dataset_cfg, slam_mode, metrics, log_analysis,
    run_start: datetime, run_end: datetime
) -> str:
    dataset_name = dataset_cfg.get("name", "unknown")
    ts = run_start.strftime("%Y-%m-%d %H:%M:%S")
    elapsed = (run_end - run_start).total_seconds()

    md = []
    md.append(f"# SLAM Evaluation Report")
    md.append(f"")
    md.append(f"| Field | Value |")
    md.append(f"|---|---|")
    md.append(f"| Dataset | `{dataset_name}` |")
    md.append(f"| SLAM Mode | `{slam_mode}` |")
    md.append(f"| Run Date | {ts} |")
    md.append(f"| Evaluation Duration | {elapsed:.1f} s |")
    md.append(f"")

    # ── Summary table ─────────────────────────────────────────────────────────
    md.append(f"## Summary")
    md.append(f"")

    if "error" in metrics:
        md.append(f"> **⚠ Metric computation failed:** {metrics['error']}")
        md.append(f"")
    else:
        ape = metrics.get("ape", {})
        rpe1 = metrics.get("rpe_1", {})
        traj_len = metrics.get("traj_length_m", 0.0)
        n_est = metrics.get("n_estimated", 0)
        n_assoc = metrics.get("n_associated", 0)

        md.append(f"| Metric | Value |")
        md.append(f"|---|---|")
        md.append(f"| **APE RMSE** | **{ape.get('rmse', 'N/A')} m** |")
        md.append(f"| APE mean | {ape.get('mean', 'N/A')} m |")
        md.append(f"| APE std | {ape.get('std', 'N/A')} m |")
        md.append(f"| APE max | {ape.get('max', 'N/A')} m |")
        md.append(f"| **RPE RMSE (Δ=1 frame)** | **{rpe1.get('rmse', 'N/A')} m** |")
        md.append(f"| GT trajectory length | {traj_len} m |")
        md.append(f"| Estimated poses | {n_est} |")
        md.append(f"| Associated poses | {n_assoc} |")

        # Derived: drift rate
        if traj_len > 0 and ape.get("rmse"):
            drift_pct = (ape["rmse"] / traj_len) * 100.0
            md.append(f"| **Drift (APE RMSE / traj length)** | **{drift_pct:.2f} %** |")

        md.append(f"")

    # ── APE detail ────────────────────────────────────────────────────────────
    md.append(f"## Absolute Pose Error (APE — translation)")
    md.append(f"")
    if "error" not in metrics:
        ape = metrics.get("ape", {})
        md.append(f"| Stat | Value (m) |")
        md.append(f"|---|---|")
        for stat in ("rmse", "mean", "std", "min", "max", "sse"):
            md.append(f"| {stat} | {ape.get(stat, 'N/A')} |")
        md.append(f"| n_poses | {ape.get('n_poses', 'N/A')} |")
    else:
        md.append(f"*APE computation failed — see summary above.*")
    md.append(f"")

    # ── RPE detail ────────────────────────────────────────────────────────────
    md.append(f"## Relative Pose Error (RPE — translation)")
    md.append(f"")
    for key, label in [("rpe_1", "Δ=1 frame (frame-to-frame drift)"),
                        ("rpe_100", "Δ=100 frames (medium-range drift)")]:
        rpe = metrics.get(key, {})
        md.append(f"### {label}")
        md.append(f"")
        if "error" in rpe:
            md.append(f"*{rpe['error']}*")
        else:
            md.append(f"| Stat | Value (m) |")
            md.append(f"|---|---|")
            for stat in ("rmse", "mean", "std", "max"):
                md.append(f"| {stat} | {rpe.get(stat, 'N/A')} |")
        md.append(f"")

    # ── System behaviour ──────────────────────────────────────────────────────
    md.append(f"## System Behaviour (from logs)")
    md.append(f"")

    if "error" in log_analysis:
        md.append(f"*Log parse error: {log_analysis['error']}*")
    else:
        md.append(f"| Event | Count |")
        md.append(f"|---|---|")
        md.append(f"| Keyframes added | {log_analysis.get('keyframe_count', 'N/A')} |")
        md.append(f"| Graph edges (est.) | {log_analysis.get('edge_count', 'N/A')} |")
        md.append(f"| **Local BA ran** | **{log_analysis.get('ba_runs', 'N/A')}** |")
        md.append(f"| Local BA skipped (immature geometry) | {log_analysis.get('ba_skips', 0)} |")
        md.append(f"| VO rejects (total) | {log_analysis['vo_rejects'].get('total', 0)} |")
        te = log_analysis.get("tracking_events", {})
        md.append(f"| Tracking LOST events | {te.get('lost_count', 0)} |")
        md.append(f"| Tracking WEAK events | {te.get('weak_count', 0)} |")
        md.append(f"| Tracking recoveries | {te.get('recovered_count', 0)} |")
        md.append(f"| Loop closures | {log_analysis.get('loop_closures', 0)} |")
        vf = log_analysis.get('vins_scale_failures', 0)
        if vf > 0:
            md.append(f"| VINS scale failures | {vf} |")
        md.append(f"")

        # VINS init
        vi = log_analysis.get("vins_init")
        md.append(f"### VINS Initialization")
        md.append(f"")
        if vi is None:
            md.append(f"- Status: **Not reached** (insufficient keyframes or no IMU)")
        elif vi.get("disabled"):
            md.append(f"- Status: **Disabled** (pure mono mode)")
        else:
            md.append(f"- Status: **✓ Success**")
            md.append(f"- Scale: `{vi.get('scale', 'N/A')}`")
            md.append(f"- Gravity magnitude: `{vi.get('gravity_norm', 'N/A')} m/s²`")
        md.append(f"")

        # VO reject reasons
        reasons = log_analysis["vo_rejects"].get("reasons", {})
        if reasons:
            md.append(f"### VO Rejection Breakdown")
            md.append(f"")
            md.append(f"| Reason | Count |")
            md.append(f"|---|---|")
            for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
                md.append(f"| {reason} | {count} |")
            md.append(f"")

    # ── Warnings ──────────────────────────────────────────────────────────────
    warnings = log_analysis.get("warnings", [])
    md.append(f"## Warnings ({len(warnings)} unique)")
    md.append(f"")
    if warnings:
        for w in warnings[:30]:  # cap at 30 to keep report readable
            md.append(f"- `{w}`")
        if len(warnings) > 30:
            md.append(f"- *(and {len(warnings) - 30} more — see run.log)*")
    else:
        md.append(f"*No warnings.*")
    md.append(f"")

    # ── Errors ────────────────────────────────────────────────────────────────
    errors = log_analysis.get("errors", [])
    md.append(f"## Errors ({len(errors)} unique)")
    md.append(f"")
    if errors:
        for e in errors[:20]:
            md.append(f"- `{e}`")
        if len(errors) > 20:
            md.append(f"- *(and {len(errors) - 20} more — see run.log)*")
    else:
        md.append(f"*No errors.*")
    md.append(f"")

    # ── Raw JSON embed ────────────────────────────────────────────────────────
    md.append(f"## Raw Results (JSON)")
    md.append(f"")
    md.append(f"```json")
    import json
    summary_json = {
        "dataset": dataset_cfg.get("name"),
        "slam_mode": slam_mode,
        "ape_rmse_m": metrics.get("ape", {}).get("rmse"),
        "rpe1_rmse_m": metrics.get("rpe_1", {}).get("rmse"),
        "traj_length_m": metrics.get("traj_length_m"),
        "keyframes": log_analysis.get("keyframe_count"),
        "vo_rejects_total": log_analysis.get("vo_rejects", {}).get("total"),
        "tracking_lost": log_analysis.get("tracking_events", {}).get("lost_count"),
        "loop_closures": log_analysis.get("loop_closures"),
    }
    md.append(json.dumps(summary_json, indent=2))
    md.append(f"```")
    md.append(f"")

    return "\n".join(md)


def _safe_copy(src: str, dst: str):
    try:
        if Path(src).exists():
            shutil.copy2(src, dst)
    except Exception:
        pass

def _generate_trajectory_plot(est_path: str, gt_path: str, out_path: str):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from evo.tools import file_interface
        from evo.core import sync

        traj_est = file_interface.read_tum_trajectory_file(est_path)
        traj_ref = file_interface.read_tum_trajectory_file(gt_path)

        traj_ref_sync, traj_est_sync = sync.associate_trajectories(traj_ref, traj_est, max_diff=0.5)
        traj_est_sync.align(traj_ref_sync, correct_scale=True)

        gt_xyz = traj_ref_sync.positions_xyz
        est_xyz = traj_est_sync.positions_xyz

        plt.figure(figsize=(10, 8))
        plt.plot(gt_xyz[:, 0], gt_xyz[:, 1], 'k--', label='Ground Truth')
        plt.plot(est_xyz[:, 0], est_xyz[:, 1], 'b-', label='Estimated (Aligned)')
        plt.axis('equal')
        plt.legend()
        plt.title('Trajectory Plot (Sim3 Aligned)')
        plt.xlabel('X (m)')
        plt.ylabel('Y (m)')
        plt.grid(True)
        plt.savefig(out_path)
        plt.close()

        # Generate Error Plot
        from evo.core import metrics as evo_metrics
        ape_metric = evo_metrics.APE(evo_metrics.PoseRelation.translation_part)
        ape_metric.process_data((traj_ref_sync, traj_est_sync))
        
        plt.figure(figsize=(10, 4))
        plt.plot(traj_est_sync.timestamps - traj_est_sync.timestamps[0], ape_metric.error, 'r-')
        plt.title('Absolute Pose Error over Time (Aligned)')
        plt.xlabel('Time (s)')
        plt.ylabel('Translation Error (m)')
        plt.grid(True)
        error_path = out_path.replace('trajectory.png', 'error.png')
        plt.savefig(error_path)
        plt.close()
    except Exception as e:
        print(f"[Warning] Failed to generate plots: {e}")

