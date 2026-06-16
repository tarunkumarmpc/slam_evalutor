# slam_evaluator

**Maintainer**: Tarun

## Overview

`slam_evaluator` is an automated testing and validation toolkit designed to benchmark Simultaneous Localization and Mapping (SLAM) systems within a ROS 2 environment. It standardizes the evaluation pipeline by orchestrating dataset playback, capturing trajectory estimates, computing standard metric errors (APE/RPE), and aggregating runtime system diagnostics.

By parsing logs and extracting critical runtime events—such as loop-closure counts, Bundle Adjustment (BA) activity, tracking losses, and VINS initialization scale—it goes beyond simple trajectory comparison to provide actionable insights into the algorithm's behavior.

## Key Capabilities

- **Automated Data Processing**: Captures live estimated trajectories (via `nav_msgs/Path`) during rosbag playback.
- **Trajectory Alignment & Metrics**: Integrates with [`evo`](https://github.com/MichaelGrupp/evo) to compute Absolute Pose Error (APE) and Relative Pose Error (RPE), utilizing Sim3 alignment which is essential for monocular SLAM setups.
- **Format Interoperability**: Handles necessary format conversions, such as transforming KITTI ground-truth data to TUM format for metric evaluation.
- **Deep Log Analytics**: Parses SLAM node logs to extract mission-critical events, including tracking states (LOST, WEAK, recovered), VO rejections, and initialization stability.
- **Comprehensive Reporting**: Automatically generates a timestamped report directory containing a human-readable `report.md`, machine-readable `results.json`, and visualization plots (`trajectory.png`, `error.png`).

## Architecture

The toolkit is built on a modular Python architecture designed for robustness:

1. **`runner.py` (The Orchestrator)**: Acts as the primary ROS 2 node. It dynamically loads dataset configurations, spawns subprocesses to run the SLAM pipeline and `rosbag play` in parallel, and actively subscribes to the trajectory topics to capture live data.
2. **`log_parser.py`**: A generic, regex-driven diagnostics parser. It scans the raw terminal output generated during the run for standard warnings, errors, and system-specific tracking alerts.
3. **`plot_traj.py`**: A hardened `evo` integration wrapper that handles trajectory synchronization and Sim3 alignment securely, returning graceful failures instead of crashing when metric computation fails.

## System Requirements

- **Python**: 3.8+ (3.10 recommended)
- **ROS 2**: Required for system launch and rosbag playback.
- **Dependencies**: Python packages listed in `requirements.txt`.

*Note: System and ROS packages must be installed separately depending on your target ROS 2 distribution.*

## Installation

1. **Clone the repository:**

   ```bash
   # SSH (Recommended)
   git clone git@github.com:tarunkumarmpc/slam_evaluator.git

   # HTTPS
   git clone https://github.com/tarunkumarmpc/slam_evaluator.git
   ```

2. **Workspace Setup:**
   Place the cloned package into the `src/` directory of your existing ROS 2 workspace.

3. **Install ROS dependencies:**

   ```bash
   cd <your_ros2_workspace_root>
   rosdep update
   rosdep install --from-paths src --ignore-src -r -y
   ```

4. **Install Python dependencies:**

   ```bash
   python3 -m pip install --upgrade pip
   pip install -r src/slam_evaluator/requirements.txt
   ```
   *Note: [`evo`](https://github.com/MichaelGrupp/evo) and `matplotlib` are required for full trajectory plotting and metric calculation. If `evo` is unavailable, the pipeline falls back to a reduced summary without plots.*

5. **Build the package:**

   ```bash
   cd <your_ros2_workspace_root>
   colcon build --packages-select slam_evaluator
   source install/setup.bash
   ```

6. **Verify installation (Dry Run):**

   ```bash
   ros2 launch slam_evaluator evaluate.launch.py dry_run:=true
   ```
   If the dry run completes successfully, the pipeline is ready for deployment.

## Pipeline Output

For each evaluation run, a timestamped directory is created (e.g., `reports/kitti_2011_09_30_drive_0033_mono_20260602_114000/`) containing:

- `report.md`: A high-level, readable summary of the evaluation.
- `results.json`: Full metrics serialized for automated CI/CD parsing.
- `estimated_traj.txt`: The SLAM trajectory output in TUM format.
- `gt_traj.txt`: The corresponding ground truth in TUM format.
- `run.log`: Raw stdout/stderr from the SLAM node for deeper debugging.

If `evo` and `matplotlib` are installed, the toolkit also produces:
- `trajectory.png`: Sim3-aligned XY trajectory overlay (Ground Truth vs. Estimate).
- `error.png`: Absolute pose translation error over time.

## Custom SLAM Integration

To integrate a custom SLAM system, define a dataset YAML configuration that matches your setup. The evaluator expects the SLAM node to publish its estimated path to a `nav_msgs/Path` topic.

**Configuration Keys:**
- `bag_path`: Absolute path to the rosbag.
- `slam_mode`: Sensor configuration (e.g., `mono`, `mono_imu`, `stereo`).
- `topics`: Remapping for essential topics (`slam_path`, `image`, `gt_path`, `gps`, `imu`).
- `launch_args`: Additional arguments forwarded to the SLAM launch file.

**Example `datasets/my_dataset.yaml`:**
```yaml
name: my_custom_dataset
bag_path: /data/rosbags/my_bag.db3
slam_mode: mono
topics:
  slam_path: /vslam/pose_path
  image: /camera/image_raw
launch_args:
  use_sim_time: true
```

## Adding a New Dataset

1. Create a configuration file in the `datasets/` directory:

```yaml
name: sequence_00
bag_path: /data/rosbags/seq_00
gt_poses_path: /data/gt/poses.txt   # KITTI SE3 format (N x 12)
gt_times_path: /data/gt/times.txt   # Timestamps (seconds)
slam_mode: mono
```

2. Launch the evaluation:
```bash
ros2 launch slam_evaluator evaluate.launch.py dataset:=datasets/sequence_00.yaml
```

## Understanding the Metrics

| Metric | Description |
|---|---|
| **APE RMSE** | Absolute Pose Error (Root Mean Square). Indicates global trajectory drift and overall accuracy. |
| **RPE Δ=1** | Relative Pose Error (step=1). Measures frame-to-frame odometry noise and local tracking smoothness. |
| **RPE Δ=100** | Relative Pose Error (step=100). Highlights medium-range structural consistency. |
| **Drift %** | `(APE RMSE / trajectory_length) × 100`. Normalized drift percentage. |
| **Tracking LOST count** | Number of times the visual odometry (VO) tracker lost the feature track. |
| **VINS Init scale** | Metric scale estimated during initialization (specific to `mono_imu` mode). |
| **VO reject reasons** | Categorized reasons for discarding VO frames, useful for tuning outlier rejection logic. |
