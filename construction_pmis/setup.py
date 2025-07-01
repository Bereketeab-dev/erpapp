from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in construction_pmis/__init__.py
from construction_pmis import __version__ as version

setup(
	name="construction_pmis",
	version=version,
	description="Project Management Information System for Construction Companies",
	author="Jules",
	author_email="jules@example.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
