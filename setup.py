import os
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    requirements = f.read().splitlines()

setup(
    name="NREL-shift",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="v0.1.0-alpha",
    description="Generate synthetic feeders using open street map data",
    author="Kapil Duwadi",
    author_email="kapil.duwadi@nrel.gov",
    packages=find_packages(),
    url="https://github.com/nrel/shift",
    keywords="Synthetic feeder, Open steet data, OpenDSS",
    install_requires=requirements,
    python_requires=">=3.9",
    package_dir={"shift": "shift"},
    entry_points={"console_scripts": ["shift-internal=shift.cli.shift:cli"]},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
)
