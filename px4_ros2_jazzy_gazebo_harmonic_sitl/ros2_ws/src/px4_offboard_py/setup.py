from setuptools import find_packages, setup

package_name = "px4_offboard_py"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="User",
    maintainer_email="user@todo.todo",
    description="PX4 Offboard control node in Python using rclpy for ROS 2 Jazzy",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "offboard_control = px4_offboard_py.offboard_control:main",
        ],
    },
)
