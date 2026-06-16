# SLAM Evaluation Report

| Field | Value |
|---|---|
| Dataset | `kitti_2011_09_30_drive_0033` |
| SLAM Mode | `mono_imu` |
| Run Date | 2026-06-16 11:18:27 |
| Evaluation Duration | 179.3 s |

## Summary

| Metric | Value |
|---|---|
| **APE RMSE** | **89.6143 m** |
| APE mean | 81.271 m |
| APE std | 37.7589 m |
| APE max | 191.6975 m |
| **RPE RMSE (Δ=1 frame)** | **2.8758 m** |
| GT trajectory length | 1709.24 m |
| Estimated poses | 1083 |
| Associated poses | 1083 |
| **Drift (APE RMSE / traj length)** | **5.24 %** |

## Absolute Pose Error (APE — translation)

| Stat | Value (m) |
|---|---|
| rmse | 89.6143 |
| mean | 81.271 |
| std | 37.7589 |
| min | 36.991 |
| max | 191.6975 |
| sse | 8697263.8415 |
| n_poses | 1083 |

## Relative Pose Error (RPE — translation)

### Δ=1 frame (frame-to-frame drift)

| Stat | Value (m) |
|---|---|
| rmse | 2.8758 |
| mean | 2.6826 |
| std | 1.0362 |
| max | 8.9172 |

### Δ=100 frames (medium-range drift)

| Stat | Value (m) |
|---|---|
| rmse | 236.1032 |
| mean | 230.4894 |
| std | 51.1796 |
| max | 339.0966 |

## System Behaviour (from logs)

| Event | Count |
|---|---|
| Keyframes added | 1083 |
| Graph edges (est.) | 1082 |
| **Local BA ran** | **1** |
| Local BA skipped (immature geometry) | 0 |
| VO rejects (total) | 7 |
| Tracking LOST events | 0 |
| Tracking WEAK events | 12 |
| Tracking recoveries | 6 |
| Loop closures | 279 |
| VINS scale failures | 10 |

### VINS Initialization

- Status: **Not reached** (insufficient keyframes or no IMU)

### VO Rejection Breakdown

| Reason | Count |
|---|---|
| quality_gate | 7 |

## Warnings (51145 unique)

- `[graph_slam-3] [WARN] [1781605120.795442686] [graph_slam]: Loop closure rejected by geometry gate: 5 -> 17 (inliers=10 ratio=0.77)`
- `[graph_slam-3] [WARN] [1781605121.215870746] [optimizer_gtsam]: Processing IMU edge 0 -> 1 with dt=0.199987, raw_samples=3`
- `[graph_slam-3] [WARN] [1781605121.215971655] [optimizer_gtsam]: Added ImuFactor between node 0 and 1`
- `[graph_slam-3] [WARN] [1781605121.215982525] [optimizer_gtsam]: Processing IMU edge 1 -> 2 with dt=0.000000, raw_samples=1`
- `[graph_slam-3] [WARN] [1781605121.215994155] [optimizer_gtsam]: Processing IMU edge 2 -> 3 with dt=0.099985, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216010774] [optimizer_gtsam]: Added ImuFactor between node 2 and 3`
- `[graph_slam-3] [WARN] [1781605121.216021384] [optimizer_gtsam]: Processing IMU edge 3 -> 4 with dt=0.200088, raw_samples=3`
- `[graph_slam-3] [WARN] [1781605121.216037264] [optimizer_gtsam]: Added ImuFactor between node 3 and 4`
- `[graph_slam-3] [WARN] [1781605121.216045414] [optimizer_gtsam]: Processing IMU edge 4 -> 5 with dt=0.100030, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216059014] [optimizer_gtsam]: Added ImuFactor between node 4 and 5`
- `[graph_slam-3] [WARN] [1781605121.216066914] [optimizer_gtsam]: Processing IMU edge 5 -> 6 with dt=0.000000, raw_samples=1`
- `[graph_slam-3] [WARN] [1781605121.216076444] [optimizer_gtsam]: Processing IMU edge 6 -> 7 with dt=0.099814, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216090083] [optimizer_gtsam]: Added ImuFactor between node 6 and 7`
- `[graph_slam-3] [WARN] [1781605121.216098203] [optimizer_gtsam]: Processing IMU edge 7 -> 8 with dt=0.100029, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216111453] [optimizer_gtsam]: Added ImuFactor between node 7 and 8`
- `[graph_slam-3] [WARN] [1781605121.216119353] [optimizer_gtsam]: Processing IMU edge 8 -> 9 with dt=0.000000, raw_samples=1`
- `[graph_slam-3] [WARN] [1781605121.216128563] [optimizer_gtsam]: Processing IMU edge 9 -> 10 with dt=0.099863, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216142633] [optimizer_gtsam]: Added ImuFactor between node 9 and 10`
- `[graph_slam-3] [WARN] [1781605121.216150273] [optimizer_gtsam]: Processing IMU edge 10 -> 11 with dt=0.200000, raw_samples=3`
- `[graph_slam-3] [WARN] [1781605121.216164842] [optimizer_gtsam]: Added ImuFactor between node 10 and 11`
- `[graph_slam-3] [WARN] [1781605121.216172662] [optimizer_gtsam]: Processing IMU edge 11 -> 12 with dt=0.099900, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216185822] [optimizer_gtsam]: Added ImuFactor between node 11 and 12`
- `[graph_slam-3] [WARN] [1781605121.216193472] [optimizer_gtsam]: Processing IMU edge 12 -> 13 with dt=0.100050, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216206542] [optimizer_gtsam]: Added ImuFactor between node 12 and 13`
- `[graph_slam-3] [WARN] [1781605121.216216672] [optimizer_gtsam]: Processing IMU edge 13 -> 14 with dt=0.000000, raw_samples=1`
- `[graph_slam-3] [WARN] [1781605121.216226152] [optimizer_gtsam]: Processing IMU edge 14 -> 15 with dt=0.099947, raw_samples=2`
- `[graph_slam-3] [WARN] [1781605121.216239761] [optimizer_gtsam]: Added ImuFactor between node 14 and 15`
- `[graph_slam-3] [WARN] [1781605121.216247591] [optimizer_gtsam]: Processing IMU edge 15 -> 16 with dt=0.199972, raw_samples=3`
- `[graph_slam-3] [WARN] [1781605121.216261921] [optimizer_gtsam]: Added ImuFactor between node 15 and 16`
- `[graph_slam-3] [WARN] [1781605121.216269601] [optimizer_gtsam]: Processing IMU edge 16 -> 17 with dt=0.099991, raw_samples=2`
- *(and 51115 more — see run.log)*

## Errors (4 unique)

- `[ERROR] [static_transform_publisher-2]: process has died [pid 17924, exit code -2, cmd '/opt/ros/jazzy/lib/tf2_ros/static_transform_publisher --x 0 --y 0 --z 0 --yaw 0 --pitch 0 --roll 0 --frame-id base_link --child-frame-id oxts_link --ros-args -r __node:=kitti_base_to_imu_static_tf'].`
- `[ERROR] [static_transform_publisher-1]: process has died [pid 17923, exit code -2, cmd '/opt/ros/jazzy/lib/tf2_ros/static_transform_publisher --x -0.08 --y 0.0 --z -0.035 --yaw -1.57079632679 --pitch 0.0 --roll -1.57079632679 --frame-id base_link --child-frame-id cam0_link --ros-args -r __node:=kitti_base_to_cam_static_tf'].`
- `[ERROR] [graph_slam-3]: process has died [pid 17925, exit code -2, cmd '/home/tarun/Desktop/new_websit/slam_ws/install/visual_graph_slam/lib/visual_graph_slam/graph_slam --ros-args --params-file /home/tarun/Desktop/new_websit/slam_ws/install/visual_graph_slam/share/visual_graph_slam/config/common_params.yaml --params-file /home/tarun/Desktop/new_websit/slam_ws/install/visual_graph_slam/share/visual_graph_slam/config/modes/mono_imu.yaml --params-file /tmp/launch_params_eoaj0_dy --params-file /home/tarun/Desktop/new_websit/slam_ws/install/visual_graph_slam/share/visual_graph_slam/config/slam_params.yaml --params-file /tmp/launch_params_dj6mblpd --params-file /tmp/launch_params_f530_85y'].`
- `[ERROR] [gps_visualizer_node.py-4]: process has died [pid 17926, exit code -2, cmd '/home/tarun/Desktop/new_websit/slam_ws/install/visual_graph_slam/lib/visual_graph_slam/gps_visualizer_node.py --ros-args -r __node:=gps_visualizer_node'].`

## Raw Results (JSON)

```json
{
  "dataset": "kitti_2011_09_30_drive_0033",
  "slam_mode": "mono_imu",
  "ape_rmse_m": 89.6143,
  "rpe1_rmse_m": 2.8758,
  "traj_length_m": 1709.24,
  "keyframes": 1083,
  "vo_rejects_total": 7,
  "tracking_lost": 0,
  "loop_closures": 279
}
```
