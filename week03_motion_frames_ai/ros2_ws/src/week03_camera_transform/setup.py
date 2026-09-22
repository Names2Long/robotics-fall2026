from setuptools import find_packages,setup
name="week03_camera_transform"
setup(name=name,version="0.1.0",packages=find_packages(),data_files=[("share/ament_index/resource_index/packages",[f"resource/{name}"]),(f"share/{name}",["package.xml"])],install_requires=["setuptools"],zip_safe=True,maintainer="Course Instructor",maintainer_email="instructor@example.edu",description="Student camera transform exercise",license="Apache-2.0")
