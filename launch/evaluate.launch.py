"""
evaluate.launch.py
==================
Single entry point for the SLAM evaluation pipeline.

Usage:
    ros2 launch slam_evaluator evaluate.launch.py \
        dataset:=datasets/kitti_0033.yaml \
        mode:=mono \
        report_dir:=./reports

Arguments
---------
dataset    : path to dataset YAML config (relative to package share or absolute)
mode       : override slam_mode from dataset config  [default: use config value]
report_dir : output directory for report files       [default: ./reports]
dry_run    : if 'true', skip SLAM execution          [default: false]
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('slam_evaluator')

    dataset_arg = DeclareLaunchArgument(
        'dataset',
        default_value=os.path.join(pkg_share, 'datasets', 'kitti_0033.yaml'),
        description='Path to dataset YAML config'
    )

    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='',
        description='Override slam_mode (leave empty to use dataset config value)'
    )

    report_dir_arg = DeclareLaunchArgument(
        'report_dir',
        default_value='reports',
        description='Output directory for evaluation reports'
    )

    dry_run_arg = DeclareLaunchArgument(
        'dry_run',
        default_value='false',
        description='If true, skip SLAM execution (only generate GT + report skeleton)'
    )

    def launch_setup(context, *args, **kwargs):
        dataset = context.launch_configurations['dataset']
        mode = context.launch_configurations['mode'] or None
        report_dir = context.launch_configurations['report_dir']
        dry_run_str = context.launch_configurations['dry_run']
        dry_run = dry_run_str.lower() in ('true', '1', 'yes')

        cmd = [
            'python3', '-m', 'evaluator_core.runner',
            '--dataset', dataset,
            '--report-dir', report_dir,
        ]
        if mode:
            cmd += ['--mode', mode]
        if dry_run:
            cmd.append('--dry-run')

        # Run as an ExecuteProcess so launch manages its lifecycle
        return [
            ExecuteProcess(
                cmd=cmd,
                output='screen',
                name='slam_evaluator',
            )
        ]

    return LaunchDescription([
        dataset_arg,
        mode_arg,
        report_dir_arg,
        dry_run_arg,
        OpaqueFunction(function=launch_setup),
    ])
