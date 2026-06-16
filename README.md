# slam_evaluator

SLAM evaluation toolkit for ROS 2.

Maintainer: Tarun — Senior Robotics Engineer

## Overview

`slam_evaluator` runs controlled dataset playbacks, captures the SLAM
estimate, computes standard trajectory metrics, extracts runtime diagnostics,
and produces a compact evaluation report and machine-readable summary for
benchmarking and troubleshooting.

Capabilities
-----------
- Capture estimated trajectory from a `nav_msgs/Path` topic.
- Convert KITTI ground-truth to TUM format when required.
- Compute APE and RPE using `evo` with Sim3 alignment for monocular setups.
- Parse runtime logs for warnings, errors, VO rejects, tracking events, BA
    activity, loop-closure counts, and VINS initialization diagnostics.
- Produce `report.md`, `results.json`, and plots (`trajectory.png`,
    `error.png`) in a timestamped report directory.

## Requirements

Requirements
------------
- Python 3.8 or later (3.10 recommended).
- ROS 2 (required for launching SLAM and playing bags).
- Python packages listed in `requirements.txt`.

System/ROS packages must be installed separately; consult the target ROS 2
distribution documentation for platform-specific instructions.

Install Python dependencies (from repository root):

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

`evo` and `matplotlib` are required for full metrics and plot generation. If
`evo` is not present the evaluator will produce a reduced summary without
plots.


Installation and build
----------------------

1. Clone the repository (SSH or HTTPS):

```bash
# SSH (recommended for contributors)
git clone git@github.com:tarunkumarmpc/slam_evalutor.git

# or HTTPS
git clone https://github.com/tarunkumarmpc/slam_evalutor.git
```

2. Place the package in a ROS 2 workspace `src/` directory or clone directly
   inside the workspace.

3. Install ROS package dependencies (recommended):

```bash
cd <your_ros2_workspace_root>
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

4. Install Python dependencies:

```bash
python3 -m pip install --upgrade pip
pip install -r src/slam_evalutor/requirements.txt
```

5. Build and source the workspace:

```bash
cd <your_ros2_workspace_root>
colcon build --packages-select slam_evaluator
source install/setup.bash
```

Verification (dry run):

```bash
ros2 launch slam_evaluator evaluate.launch.py dry_run:=true
```

If the dry run completes the package is ready for full evaluations.

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

Configure the dataset YAML to match the SLAM under test. The evaluator expects
the SLAM to publish an estimated trajectory as a `nav_msgs/Path` topic.

Relevant dataset keys:

- `bag_path`: path to the rosbag used for playback.
- `slam_mode`: e.g., `mono`, `mono_imu`, `stereo`.
- `topics`: map of topic names (`slam_path`, `image`, `gt_path`, `gps`, `imu`).
- `launch_args`: additional launch arguments forwarded to the SLAM launch.

Sample dataset configuration:

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

During a run the evaluator captures stdout/stderr to `run.log` and extracts
structured diagnostics for the report. Extracted items include:

- Unique warnings and errors.
- VO rejection counts and reason breakdown.
- Tracking events: LOST, WEAK, recovered.
- Local BA runs and skips.
- VINS initialization and scale diagnostics.

If your SLAM uses non-standard logging, extend `slam_evaluator/log_parser.py`
to match implementation-specific messages.

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
