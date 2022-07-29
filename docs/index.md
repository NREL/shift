# Shift

<img src="images/shift.svg" width="500">

Generate distribution feeder model from OpenStreet data.

Getting free distribution feeder models for your reasearch has never been easier.
SHIFT helps you build synthetic distribution feeders models using just the OpenStreet data e.g. buildings and road network. You can configure lots of
parameters and design choices when building these models and even create multiple versions of them and choose the one that fits your needs. If you are utility no worries we 
have you covered as well. As a utility you can also integrate your data when building these models. 


## Installation Instruction

We are in the processing of releasing a stable version to PyPI. Until it is ready for installing via pip,
you can install this tool by cloning or downloading code from [here](https://github.com/nrel/shift).

We recommend using Anaconda or Miniconda to create the environment for windows user. 
Use the commands below to create environment and install the shift tool.

=== "Windows 10"

    ``` cmd
    conda create -n shift python==3.9
    conda install osmnx
    cd <cloned_repo>
    pip install -e.
    ```

=== "Mac OS & linux"

    ``` cmd
    conda create -n shift python==3.9
    cd <cloned_repo>
    pip install -e.
    ```


