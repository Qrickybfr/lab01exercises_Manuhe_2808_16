from setuptools import find_packages, setup
import os
from glob import glob
package_name = 'my_robot_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='manuhe',
    maintainer_email='manuhe.ugr-2808-16@aau.edu.et',
    description='Nodes and launch file that drive diffdrive_bo',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turn_away = my_robot_nodes.turn_away:main',
            'rotate_server = my_robot_nodes.rotate_server:main',
            'square_driver = my_robot_nodes.square_driver:main',
        ],
    },
)
