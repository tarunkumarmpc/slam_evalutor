# SLAM Evaluation Report

| Field | Value |
|---|---|
| Dataset | `test_bag_dataset` |
| SLAM Mode | `mono` |
| Run Date | 20260616_144714 |

## Summary

| Metric | Value |
|---|---|
| **APE RMSE** | **0.1465 m** |
| APE mean | 0.1336 m |
| APE std | 0.0602 m |
| APE max | 0.3056 m |
| **RPE RMSE (Δ=1 frame)** | **0.2098 m** |
| GT trajectory length | 37.08 m |
| Estimated poses | 300 |
| Associated poses | 300 |
| **Drift (APE RMSE / traj length)** | **0.40 %** |

## Absolute Pose Error (APE — translation)

| Stat | Value (m) |
|---|---|
| rmse | 0.1465 |
| mean | 0.1336 |
| std | 0.0602 |
| min | 0.0217 |
| max | 0.3056 |
| sse | 6.4414 |
| n_poses | 300 |

## Relative Pose Error (RPE — translation)

### Δ=1 frame (frame-to-frame drift)

| Stat | Value (m) |
|---|---|
| rmse | 0.2098 |
| mean | 0.1918 |
| std | 0.0849 |
| max | 0.5745 |

### Δ=100 frames (medium-range drift)

| Stat | Value (m) |
|---|---|
| rmse | 0.1159 |
| mean | 0.1149 |
| std | 0.0151 |
| max | 0.1300 |

## Trajectory Alignment (Sim3)

The estimated trajectory was aligned to the ground truth using Umeyama Sim3 alignment:

- **Scale ($s$)**: `0.995906`

**Rotation Matrix ($R$)**:
```text
[  1.00000,   0.00297,  -0.00011]
[ -0.00297,   0.99999,  -0.00135]
[  0.00011,   0.00135,   1.00000]
```

**Translation Vector ($t$)**:
```text
[  0.00374,  -0.00569,  -0.00644]^T
```

## System Behaviour (from logs)

| Event | Count |
|---|---|
| Keyframes added | 0 |
| Graph edges (est.) | 0 |
| **Local BA ran** | **0** |
| Local BA skipped | 0 |
| VO rejects (total) | 0 |
| Tracking LOST events | 0 |
| Tracking WEAK events | 0 |
| Tracking recoveries | 0 |
| Loop closures | 0 |
| VINS scale failures | 0 |

### VINS Initialization

- Status: **Not reached**

## Warnings (0 total)


## Errors (0 total)


## Raw Results (JSON)

```json
{
  "dataset": "test_bag_dataset",
  "slam_mode": "mono",
  "ape_rmse_m": 0.14653089504523636,
  "rpe1_rmse_m": 0.20977531554982892,
  "traj_length_m": 37.07906727265899,
  "keyframes": 0,
  "vo_rejects_total": 0,
  "tracking_lost": 0,
  "loop_closures": 0
}
```

## Visualizations

![Trajectory](./trajectory.png)

![APE Over Time](./error.png)
