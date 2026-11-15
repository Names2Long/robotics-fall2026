from glob import glob
from setuptools import setup

setup(name="course_hri", version="1.0.0", packages=["course_hri"],
      data_files=[
          ("share/ament_index/resource_index/packages", ["resource/course_hri"]),
          ("share/course_hri", ["package.xml"]),
          ("share/course_hri/launch", glob("launch/*.launch.py")),
      ], install_requires=["setuptools"], zip_safe=True,
      maintainer="Robotics Course Staff", maintainer_email="robotics@example.edu",
      description="ROS interaction controller for Lab 10", license="MIT",
      entry_points={"console_scripts": ["interaction = course_hri.controller:main"]})
