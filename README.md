# slam_evaluator

SLAM performance evaluation pipeline for ROS 2.

Maintainer: Tarun 

Note: This documentation is written from the perspective of an experienced
SLAM engineer and aims to be pragmatic and unambiguous for robotics teams.

## Overview

This repository contains a pragmatic SLAM evaluation pipeline designed for
benchmarking visual SLAM systems in ROS 2. The evaluator performs the
following steps in a repeatable, scriptable workflow:

1. Play a rosbag dataset against the live SLAM system under test.
2. Capture the estimated trajectory published on `/slam/path`.
3. Convert KITTI ground-truth poses to TUM format (when applicable).
4. Compute standard trajectory metrics (APE and RPE) using `evo`.
5. Parse SLAM runtime logs to extract diagnostic events (VINS init, tracking
    losses, VO rejects, loop closures, warnings and errors).
6. Produce a structured Markdown report and a machine-readable JSON file for
    automated ingestion.

## Requirements

This project requires:

- Python 3.8+ (3.10 recommended)
- ROS 2 (for full evaluation that launches the SLAM system)
- Python packages listed in `requirements.txt` (install below)

System packages (for ROS 2) must be installed separately — see your ROS 2
distribution's installation guide.

Install Python dependencies:

```bash
cd path/to/your/ros2_workspace/src/slam_evaluator
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- `evo` is required for full APE/RPE metrics and plotting. If `evo` is not
    available the evaluator will run a small fallback mode and skip detailed
    plots.
- ROS Python packages (for running inside a ROS 2 workspace) are declared in
    `package.xml` (e.g. `rclpy`, `nav_msgs`, `geometry_msgs`). These are provided
    by your ROS 2 installation and do not come from PyPI.

## Quick Start

```bash
# Prepare ROS 2 workspace (if not already built)
cd <your_ros2_workspace_root>
colcon build --packages-select slam_evaluator
source install/setup.bash

# Dry run (validates GT conversion + report structure, no SLAM needed)
ros2 launch slam_evaluator evaluate.launch.py dry_run:=true

# Full evaluation (plays the rosbag and runs your SLAM system)
ros2 launch slam_evaluator evaluate.launch.py \
    dataset:=datasets/kitti_0033.yaml \
    mode:=mono \
    report_dir:=./reports
```

## Output (per run)

```
reports/kitti_2011_09_30_drive_0033_mono_20260602_114000/
├── report.md           ← readable report
├── results.json        ← machine-readable all metrics
├── estimated_traj.txt  ← TUM format estimated trajectory
├── gt_traj.txt         ← TUM format ground truth
└── run.log             ← full SLAM stdout/stderr
```

The report generation step also attempts to create two plots in the report
folder:

- `trajectory.png` — Sim3-aligned XY trajectory overlay (GT vs estimate)
- `error.png` — Absolute pose error over time (translation)

These plots require `evo` and `matplotlib` to be installed. If plotting
fails the report generator will continue and print a warning; the JSON
results are still written when possible.

## Custom SLAM integration

The evaluator is designed to run against any visual SLAM system that publishes
an estimated trajectory as a `nav_msgs/Path` message. To integrate your custom
SLAM implementation:

- Ensure your SLAM publishes the estimated trajectory on a topic (default
    `/slam/path`).
- In your dataset YAML (under `topics`) set `slam_path` to the topic your
    system uses. Example keys supported by the dataset config: `image`,
    `slam_path`, `gt_path`, `gps`, `imu`.
- If your SLAM requires specific launch arguments, pass them through the
    dataset `launch_args` map — these are forwarded to the SLAM launch command.

Example dataset YAML snippet:

```yaml
name: my_dataset
bag_path: /path/to/bag
slam_mode: mono
topics:
    slam_path: /my_slam/pose_path
    image: /camera/image_raw
launch_args:
    use_sim_time: true
```

## Monitoring and diagnostics

The evaluator captures SLAM stdout/stderr to `run.log` and extracts
diagnostic information (counts and short-message lists) during report
generation. The following are monitored and reported:

- Warnings and errors (unique messages are listed in the report)
- VO rejection reasons and counts
- Tracking events (LOST, WEAK, recovered)
- Local BA runs and skips
- VINS initialization status and scale diagnostics

To ensure diagnostics are captured:

- Run your SLAM with console logging enabled (INFO/WARN/ERROR). The parser
    relies on textual log lines; different SLAMs may require small adjustments
    to the parsing rules in `slam_evaluator/log_parser.py`.
- If your SLAM uses non-standard log prefixes, adjust `log_parser._strip_ros_prefix`
    or add regexes to capture your messages.

The generated `report.md` and `results.json` include summaries and counts of
these events; `run.log` contains the full output for detailed offline analysis.

## Adding a New Dataset

Create a new YAML file in `datasets/`, following the `kitti_0033.yaml` template:

```yaml
name: my_dataset
bag_path: /path/to/bag
gt_poses_path: /path/to/poses.txt   # KITTI SE3 format (N x 12)
gt_times_path: /path/to/times.txt   # one timestamp per line (seconds)
slam_mode: mono
```

Then run:
```bash
ros2 launch slam_evaluator evaluate.launch.py dataset:=datasets/my_dataset.yaml
```

## Report Fields Explained

| Metric | Meaning |
|---|---|
| **APE RMSE** | Overall trajectory accuracy — global drift |
| **RPE Δ=1** | Frame-to-frame odometry noise |
| **RPE Δ=100** | Medium-range consistency |
| **Drift %** | `APE RMSE / trajectory_length × 100` |
| Tracking LOST count | Times the VO tracker completely failed |
| VINS Init scale | VINS estimated metric scale (mono_imu only) |
| VO reject reasons | Why VO frames were discarded |
