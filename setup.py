from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'slam_evaluator'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'datasets'), glob('datasets/*.yaml')),
    ],
    install_requires=[
        'setuptools',
        'numpy',
        'PyYAML',
        'matplotlib',
        'evo',
    ],
    zip_safe=True,
    maintainer='Tarun',
    maintainer_email='tarunmpc@gmail.com',
    description='A robust SLAM evaluation and validation toolkit for ROS 2.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'run_evaluation = evaluator_core.runner:main',
        ],
    },
)
