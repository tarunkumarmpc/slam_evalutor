import sys
import argparse
import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

try:
    from evo.tools import file_interface
    from evo.core import sync, metrics
except ImportError:
    logger.error("The 'evo' package is required but not installed. Please install it using 'pip install evo'.")
    sys.exit(1)

def plot_trajectory(est_file: str, gt_file: str, out_file: str) -> dict:
    """
    Reads TUM trajectory files, synchronizes them, performs Sim3 alignment, 
    generates a 2D XY trajectory plot, and calculates APE/RPE metrics.

    Args:
        est_file: Path to the estimated TUM trajectory file.
        gt_file: Path to the ground truth TUM trajectory file.
        out_file: Path where the output PNG plot will be saved.

    Returns:
        dict: A dictionary of computed metrics (APE, RPE). Empty if failed.
    """
    try:
        traj_est = file_interface.read_tum_trajectory_file(est_file)
        traj_ref = file_interface.read_tum_trajectory_file(gt_file)
    except Exception as e:
        logger.error(f"Failed to read trajectory files: {e}")
        return {}

    try:
        # Synchronize and align trajectories (Sim3 alignment for scale correction)
        traj_ref_s, traj_est_s = sync.associate_trajectories(traj_ref, traj_est, max_diff=0.5)
        if traj_ref_s.num_poses == 0:
            logger.error("No matching timestamps found between estimated and ground truth trajectories.")
            return {}

        R, t, s = traj_est_s.align(traj_ref_s, correct_scale=True)
    except Exception as e:
        logger.error(f"Failed to synchronize or align trajectories: {e}")
        return {}

    computed_metrics = {}
    
    # Save the alignment properties
    computed_metrics["alignment"] = {
        "rotation": R.tolist(),
        "translation": t.tolist(),
        "scale": s
    }
    
    try:
        # APE Metrics
        ape_metric = metrics.APE(metrics.PoseRelation.translation_part)
        ape_metric.process_data((traj_ref_s, traj_est_s))
        ape_stats = ape_metric.get_all_statistics()
        computed_metrics["APE"] = {
            "rmse": float(ape_stats["rmse"]),
            "mean": float(ape_stats["mean"]),
            "std": float(ape_stats["std"]),
            "min": float(ape_stats["min"]),
            "max": float(ape_stats["max"]),
            "sse": float(ape_stats["sse"]),
        }

        # RPE (delta=1) Metrics
        rpe_metric_1 = metrics.RPE(metrics.PoseRelation.translation_part, delta=1, delta_unit=metrics.Unit.frames, all_pairs=False)
        rpe_metric_1.process_data((traj_ref_s, traj_est_s))
        rpe_stats_1 = rpe_metric_1.get_all_statistics()
        computed_metrics["RPE_1"] = {
            "rmse": float(rpe_stats_1["rmse"]),
            "mean": float(rpe_stats_1["mean"]),
            "std": float(rpe_stats_1["std"]),
            "max": float(rpe_stats_1["max"]),
        }

        # RPE (delta=100) Metrics
        try:
            rpe_metric_100 = metrics.RPE(metrics.PoseRelation.translation_part, delta=100, delta_unit=metrics.Unit.frames, all_pairs=False)
            rpe_metric_100.process_data((traj_ref_s, traj_est_s))
            rpe_stats_100 = rpe_metric_100.get_all_statistics()
            computed_metrics["RPE_100"] = {
                "rmse": float(rpe_stats_100["rmse"]),
                "mean": float(rpe_stats_100["mean"]),
                "std": float(rpe_stats_100["std"]),
                "max": float(rpe_stats_100["max"]),
            }
        except Exception:
            computed_metrics["RPE_100"] = None
            
        # General Trajectory Metrics
        computed_metrics["traj_length_m"] = float(traj_ref_s.path_length)
        computed_metrics["n_poses"] = traj_est_s.num_poses

    except Exception as e:
        logger.error(f"Failed to compute evo metrics: {e}")

    try:
        pe = traj_est_s.positions_xyz
        pr = traj_ref_s.positions_xyz

        # Plot 1: Trajectory (XY Plane)
        plt.figure(figsize=(10, 10))
        plt.plot(pr[:, 0], pr[:, 1], 'k--', label='Ground Truth')
        plt.plot(pe[:, 0], pe[:, 1], 'b-', label='Estimated (Sim3 Aligned)')
        
        plt.legend()
        plt.title("Trajectory Comparison (XY Plane)")
        plt.xlabel("X (m)")
        plt.ylabel("Y (m)")
        plt.axis('equal')
        plt.grid(True, linestyle=':', alpha=0.7)
        
        plt.savefig(out_file, dpi=300, bbox_inches='tight')
        logger.info(f"Trajectory plot successfully saved to: {out_file}")
        
        # Plot 2: APE Error over time
        if 'ape_metric' in locals() and ape_metric is not None:
            # We bypass evo.tools.plot completely because it has compatibility issues
            # with some matplotlib versions (missing matplotlib.tri.triangulation).
            error_out_file = out_file.replace("trajectory.png", "error.png")
            fig = plt.figure(figsize=(10, 5))
            ax = fig.add_subplot(111)
            
            ape_res = ape_metric.get_result()
            
            # Extract timestamps and error arrays
            timestamps = traj_est_s.timestamps - traj_est_s.timestamps[0]
            
            # In evo, the raw error data is stored in the np_arrays dict
            if "error_array" in ape_res.np_arrays:
                error_array = ape_res.np_arrays["error_array"]
                
                ax.plot(timestamps, error_array, 'r-', linewidth=1.5)
                ax.set_title("Absolute Pose Error (Translation) Over Time")
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("APE (m)")
                ax.grid(True, linestyle=':', alpha=0.7)
                
                # Highlight the mean error line
                mean_error = computed_metrics.get("APE", {}).get("mean", 0.0)
                ax.axhline(mean_error, color='k', linestyle='--', alpha=0.5, label=f'Mean: {mean_error:.2f}m')
                ax.legend()
                
                fig.savefig(error_out_file, dpi=300, bbox_inches='tight')
                logger.info(f"Error plot successfully saved to: {error_out_file}")
            
            plt.close('all')

        return computed_metrics
        
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        return computed_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot and compare SLAM trajectories using evo.")
    parser.add_argument("--est", required=True, type=str, help="Path to estimated trajectory (TUM format)")
    parser.add_argument("--gt", required=True, type=str, help="Path to ground truth trajectory (TUM format)")
    parser.add_argument("--out", required=True, type=str, help="Path to output plot image (e.g., trajectory.png)")
    
    args = parser.parse_args()
    
    success = plot_trajectory(args.est, args.gt, args.out)
    if not success:
        sys.exit(1)
