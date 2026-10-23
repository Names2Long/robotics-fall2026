from glob import glob
from setuptools import find_packages, setup

package_name = "week08_perception"
setup(name=package_name, version="0.2.0", packages=find_packages(),
      data_files=[("share/ament_index/resource_index/packages", ["resource/"+package_name]),
                  ("share/"+package_name, ["package.xml"]),
                  ("share/"+package_name+"/launch", glob("launch/*.launch.py"))],
      install_requires=["setuptools"], zip_safe=True, maintainer="Robotics Course Staff",
      maintainer_email="robotics@example.edu", description="Lab 7 perception and policy experiments", license="MIT",
      entry_points={"console_scripts": [f"{name} = week08_perception.{name}:main" for name in
                     ("classical_detector", "learned_detector", "target_behavior", "observation_recorder", "policy_demo", "live_vision", "vision_guard")]})
