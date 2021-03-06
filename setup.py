import os
from setuptools import setup, find_packages

with open("README.md","r") as fh:
    long_description = fh.read()

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='SHIFT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    version='v0.0.0',
    description='Generate synthetic feeders using open street map data',
    author='Kapil Duwadi',
    author_email='kapil.duwadi@nrel.gov',
    packages=find_packages("SHIFT"),
    url="https://github.com/nrel/shift",
    keywords="Synthetic feeder, Open steet data, OpenDSS",
    install_requires=requirements,
    package_dir={"": "src"}, 
    # entry_points={
    #     "console_scripts": [
    #         "seeds=cli.cli:run"
    #     ]
    # },  
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent"
    ]
)