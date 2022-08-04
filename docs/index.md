# Shift

<p align="center"> 
<img src="images/shift.svg" width="400" style="display:flex;justify-content:center;">
<p align="center">Generate distribution feeder model from OpenStreet data.</p>
</p>

![GitHub all releases](https://img.shields.io/github/downloads/NREL/shift/total?logo=Github&logoColor=%2300ff00&style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/nrel/shift?style=flat-square)
![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/nrel/shift?color=%23ff0000&logo=python&logoColor=%2300ff00&style=flat-square)
[![GitHub license](https://img.shields.io/github/license/NREL/shift?style=flat-square)](https://github.com/NREL/shift/blob/main/LICENSE.txt)
[![GitHub issues](https://img.shields.io/github/issues/NREL/shift?style=flat-square)](https://github.com/NREL/shift/issues)
![GitHub top language](https://img.shields.io/github/languages/top/nrel/shift?style=flat-square)
![Snyk Vulnerabilities for GitHub Repo](https://img.shields.io/snyk/vulnerabilities/github/nrel/shift?style=flat-square)


---
## Installation Instruction

We recommend using Anaconda or Miniconda to create the environment for windows user. 
Use the commands below to create environment and install the shift tool.

=== ":fontawesome-brands-windows: Windows 10"

    ``` cmd
    conda create -n shift python==3.9
    conda activate shift
    conda install -c conda-forge osmnx
    git clone https://github.com/NREL/shift.git
    cd shift
    pip install -e.
    ```

=== ":fontawesome-brands-apple: + :fontawesome-brands-linux: Mac OS & linux"

    ``` cmd
    conda create -n shift python==3.9
    conda activate shift
    git clone https://github.com/NREL/shift.git
    cd shift
    pip install -e.
    ```


