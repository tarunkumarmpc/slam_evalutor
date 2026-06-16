import os
import sys
import yaml
import time
import json
import rclpy
import argparse
import subprocess
import logging
from datetime import datetime
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

from evaluator_core.log_parser import LogParser
from evaluator_core.plot_traj import plot_trajectory

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('slam_evaluator')

class TrajectoryCapturer(Node):
    """
    Subscribes to SLAM estimated path and Ground Truth path, accumulating 
    poses to be written to TUM format.
    """
    def __init__(self, slam_topic: str, gt_topic: str):
        super().__init__('trajectory_capturer')
        self.est_poses = []
        self.gt_poses = []
        
        self.sub_slam = self.create_subscription(Path, slam_topic, self.slam_cb, 10)
        self.sub_gt = self.create_subscription(Path, gt_topic, self.gt_cb, 10)
        
    def slam_cb(self, msg: Path):
        self.est_poses = msg.poses

    def gt_cb(self, msg: Path):
        self.gt_poses = msg.poses

    def write_tum(self, poses, filepath: str):
        """Writes accumulated nav_msgs/Path to a TUM format text file."""
        try:
            with open(filepath, 'w') as f:
                for pose in poses:
                    t = pose.header.stamp.sec + pose.header.stamp.nanosec * 1e-9
                    p = pose.pose.position
                    q = pose.pose.orientation
                    f.write(f"{t:.6f} {p.x:.6f} {p.y:.6f} {p.z:.6f} {q.x:.6f} {q.y:.6f} {q.z:.6f} {q.w:.6f}\n")
            logger.info(f"Wrote {len(poses)} poses to {filepath}")
        except Exception as e:
            logger.error(f"Failed to write TUM file {filepath}: {e}")


def main():
    parser = argparse.ArgumentParser(description="SLAM Evaluation Orchestrator")
    parser.add_argument('--dataset', type=str, required=True, help="Path to dataset YAML")
    parser.add_argument('--report-dir', type=str, default="reports", help="Output directory")
    parser.add_argument('--mode', type=str, default="", help="Override SLAM mode")
    parser.add_argument('--dry-run', action='store_true', help="Skip execution, just print plan")
    args = parser.parse_args()

    # 1. Load config
    dataset_path = os.path.abspath(args.dataset)
    try:
        with open(dataset_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load dataset config: {e}")
        sys.exit(1)

    dataset_name = config.get('name', 'unknown_dataset')
    
    # Resolve bag_path relative to the yaml file location if it's not absolute
    bag_path = config.get('bag_path')
    if bag_path and not os.path.isabs(bag_path):
        bag_path = os.path.join(os.path.dirname(dataset_path), bag_path)

    slam_mode = args.mode if args.mode else config.get('slam_mode', 'mono')
    topics = config.get('topics', {})
    slam_topic = topics.get('slam_path', '/slam/path')
    gt_topic = topics.get('gt_path', '/slam/gt_path')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(args.report_dir, f"{dataset_name}_{slam_mode}_{timestamp}")
    
    logger.info(f"Initializing evaluation for dataset: {dataset_name} (Mode: {slam_mode})")
    logger.info(f"Report directory: {out_dir}")

    if args.dry_run:
        logger.info("DRY RUN: Configuration looks good. Exiting.")
        sys.exit(0)

    os.makedirs(out_dir, exist_ok=True)
    run_log_path = os.path.join(out_dir, 'run.log')
    est_traj_path = os.path.join(out_dir, 'estimated_traj.txt')
    gt_traj_path = os.path.join(out_dir, 'gt_traj.txt')

    # 2. Start Trajectory Capturer
    rclpy.init()
    capturer = TrajectoryCapturer(slam_topic, gt_topic)
    
    import threading
    spin_thread = threading.Thread(target=rclpy.spin, args=(capturer,), daemon=True)
    spin_thread.start()

    # 3. Launch SLAM Node & Bag Playback
    logger.info("Starting SLAM system and Bag playback...")
    
    # NOTE: Since no specific launch file was provided by the user, we assume a standard
    # visual_graph_slam pipeline for now. This can be parameterized via the YAML.
    launch_cmd = [
        "ros2", "launch", "visual_graph_slam", "graph_slam.launch.py",
        f"mode:={slam_mode}",
        f"bag_path:={bag_path}"
    ]

    process = None
    bag_process = None
    try:
        with open(run_log_path, 'w') as log_file:
            process = subprocess.Popen(launch_cmd, stdout=log_file, stderr=subprocess.STDOUT)
            
            # In a real scenario, we wait for the bag to finish.
            bag_cmd = ["ros2", "bag", "play", bag_path]
            # Use Popen to allow better handling of KeyboardInterrupt
            bag_process = subprocess.Popen(bag_cmd)
            bag_process.wait()
            
            # Allow some time for final graph optimization / publishing
            logger.info("Bag playback completed. Waiting 5s for final optimization...")
            time.sleep(5.0)
            
    except KeyboardInterrupt:
        logger.warning("Evaluation manually interrupted by user! Terminating background processes...")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
    finally:
        if bag_process and bag_process.poll() is None:
            bag_process.terminate()
            try:
                bag_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bag_process.kill()
                
        if process and process.poll() is None:
            import signal
            # Use SIGINT (Ctrl+C) instead of SIGTERM because ros2 launch 
            # handles SIGINT much better and propagates it to its child nodes.
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        # 4. Save paths and shutdown ROS
        capturer.write_tum(capturer.est_poses, est_traj_path)
        capturer.write_tum(capturer.gt_poses, gt_traj_path)
        rclpy.shutdown()
        spin_thread.join()

    # 5. Parse Logs
    logger.info("Parsing runtime logs...")
    parser = LogParser()
    metrics = parser.parse_log(run_log_path)
    
    # 6. Generate Plot via plot_traj.py
    logger.info("Generating trajectory plots...")
    plot_out = os.path.join(out_dir, 'trajectory.png')
    
    if os.path.exists(est_traj_path) and os.path.exists(gt_traj_path):
        evo_metrics = plot_trajectory(est_traj_path, gt_traj_path, plot_out)
        metrics.update(evo_metrics)
    else:
        logger.warning("Missing trajectory files, skipping plot generation.")

    # 7. Write Results (JSON)
    # Extract some high-level metrics for the JSON summary
    json_summary = {
        "dataset": dataset_name,
        "slam_mode": slam_mode,
        "ape_rmse_m": metrics.get("APE", {}).get("rmse"),
        "rpe1_rmse_m": metrics.get("RPE_1", {}).get("rmse"),
        "traj_length_m": metrics.get("traj_length_m"),
        "keyframes": metrics.get("keyframes"),
        "vo_rejects_total": metrics.get("vo_rejects_total"),
        "tracking_lost": metrics.get("tracking_lost"),
        "loop_closures": metrics.get("loop_closures")
    }
    
    results_path = os.path.join(out_dir, 'results.json')
    with open(results_path, 'w') as f:
        json.dump(json_summary, f, indent=2)

    # 8. Generate Detailed Markdown Report
    report_path = os.path.join(out_dir, 'report.md')
    
    ape = metrics.get("APE", {})
    rpe1 = metrics.get("RPE_1", {})
    rpe100 = metrics.get("RPE_100")
    t_len = metrics.get("traj_length_m", 0)
    n_poses = metrics.get("n_poses", 0)
    drift_pct = (ape.get("rmse", 0) / t_len * 100) if t_len > 0 else 0

    with open(report_path, 'w') as f:
        f.write(f"# SLAM Evaluation Report\n\n")
        f.write(f"| Field | Value |\n|---|---|\n")
        f.write(f"| Dataset | `{dataset_name}` |\n")
        f.write(f"| SLAM Mode | `{slam_mode}` |\n")
        f.write(f"| Run Date | {timestamp} |\n\n")
        
        f.write(f"## Summary\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| **APE RMSE** | **{ape.get('rmse', 0):.4f} m** |\n")
        f.write(f"| APE mean | {ape.get('mean', 0):.4f} m |\n")
        f.write(f"| APE std | {ape.get('std', 0):.4f} m |\n")
        f.write(f"| APE max | {ape.get('max', 0):.4f} m |\n")
        f.write(f"| **RPE RMSE (Δ=1 frame)** | **{rpe1.get('rmse', 0):.4f} m** |\n")
        f.write(f"| GT trajectory length | {t_len:.2f} m |\n")
        f.write(f"| Estimated poses | {n_poses} |\n")
        f.write(f"| Associated poses | {n_poses} |\n")
        f.write(f"| **Drift (APE RMSE / traj length)** | **{drift_pct:.2f} %** |\n\n")

        f.write(f"## Absolute Pose Error (APE — translation)\n\n")
        f.write(f"| Stat | Value (m) |\n|---|---|\n")
        f.write(f"| rmse | {ape.get('rmse', 0):.4f} |\n")
        f.write(f"| mean | {ape.get('mean', 0):.4f} |\n")
        f.write(f"| std | {ape.get('std', 0):.4f} |\n")
        f.write(f"| min | {ape.get('min', 0):.4f} |\n")
        f.write(f"| max | {ape.get('max', 0):.4f} |\n")
        f.write(f"| sse | {ape.get('sse', 0):.4f} |\n")
        f.write(f"| n_poses | {n_poses} |\n\n")

        f.write(f"## Relative Pose Error (RPE — translation)\n\n")
        f.write(f"### Δ=1 frame (frame-to-frame drift)\n\n")
        f.write(f"| Stat | Value (m) |\n|---|---|\n")
        f.write(f"| rmse | {rpe1.get('rmse', 0):.4f} |\n")
        f.write(f"| mean | {rpe1.get('mean', 0):.4f} |\n")
        f.write(f"| std | {rpe1.get('std', 0):.4f} |\n")
        f.write(f"| max | {rpe1.get('max', 0):.4f} |\n\n")

        if rpe100:
            f.write(f"### Δ=100 frames (medium-range drift)\n\n")
            f.write(f"| Stat | Value (m) |\n|---|---|\n")
            f.write(f"| rmse | {rpe100.get('rmse', 0):.4f} |\n")
            f.write(f"| mean | {rpe100.get('mean', 0):.4f} |\n")
            f.write(f"| std | {rpe100.get('std', 0):.4f} |\n")
            f.write(f"| max | {rpe100.get('max', 0):.4f} |\n\n")

        align = metrics.get('alignment')
        if align:
            R = align.get('rotation', [])
            t = align.get('translation', [])
            s = align.get('scale', 1.0)
            f.write(f"## Trajectory Alignment (Sim3)\n\n")
            f.write(f"The estimated trajectory was aligned to the ground truth using Umeyama Sim3 alignment:\n\n")
            f.write(f"- **Scale ($s$)**: `{s:.6f}`\n\n")
            if len(R) == 3 and len(t) == 3:
                f.write(f"**Rotation Matrix ($R$)**:\n```text\n")
                for row in R:
                    f.write(f"[{row[0]:9.5f}, {row[1]:9.5f}, {row[2]:9.5f}]\n")
                f.write(f"```\n\n")
                f.write(f"**Translation Vector ($t$)**:\n```text\n")
                f.write(f"[{t[0]:9.5f}, {t[1]:9.5f}, {t[2]:9.5f}]^T\n")
                f.write(f"```\n\n")

        f.write(f"## System Behaviour (from logs)\n\n")
        f.write(f"| Event | Count |\n|---|---|\n")
        f.write(f"| Keyframes added | {metrics.get('keyframes', 0)} |\n")
        f.write(f"| Graph edges (est.) | {metrics.get('edges', 0)} |\n")
        f.write(f"| **Local BA ran** | **{metrics.get('ba_runs', 0)}** |\n")
        f.write(f"| Local BA skipped | {metrics.get('ba_skips', 0)} |\n")
        f.write(f"| VO rejects (total) | {metrics.get('vo_rejects_total', 0)} |\n")
        f.write(f"| Tracking LOST events | {metrics.get('tracking_lost', 0)} |\n")
        f.write(f"| Tracking WEAK events | {metrics.get('tracking_weak', 0)} |\n")
        f.write(f"| Tracking recoveries | {metrics.get('tracking_recoveries', 0)} |\n")
        f.write(f"| Loop closures | {metrics.get('loop_closures', 0)} |\n")
        f.write(f"| VINS scale failures | {metrics.get('vins_scale_failures', 0)} |\n\n")

        f.write(f"### VINS Initialization\n\n")
        f.write(f"- Status: **{metrics.get('vins_init_status', 'Not reached')}**\n\n")

        if metrics.get('vo_reject_reasons'):
            f.write(f"### VO Rejection Breakdown\n\n")
            f.write(f"| Reason | Count |\n|---|---|\n")
            for reason, count in metrics['vo_reject_reasons'].items():
                f.write(f"| {reason} | {count} |\n")
            f.write("\n")

        warnings = metrics.get('warnings_unique', {})
        f.write(f"## Warnings ({sum(warnings.values())} total)\n\n")
        for warn, count in list(warnings.items())[:20]: # Cap at 20 unique warnings
            f.write(f"- `{warn}` (x{count})\n")
        if len(warnings) > 20:
            f.write(f"- *(and {len(warnings) - 20} more unique warnings — see run.log)*\n")
        f.write("\n")

        errors = metrics.get('errors_unique', {})
        f.write(f"## Errors ({sum(errors.values())} total)\n\n")
        for err, count in list(errors.items())[:20]:
            f.write(f"- `{err}` (x{count})\n")
        
        f.write(f"\n## Raw Results (JSON)\n\n")
        f.write(f"```json\n{json.dumps(json_summary, indent=2)}\n```\n")

        if os.path.exists(plot_out):
            f.write(f"\n## Visualizations\n\n")
            f.write(f"![Trajectory](./trajectory.png)\n\n")
            error_out = plot_out.replace("trajectory.png", "error.png")
            if os.path.exists(error_out):
                f.write(f"![APE Over Time](./error.png)\n")
                
    logger.info(f"Evaluation complete. Report generated at {out_dir}")

if __name__ == '__main__':
    main()
