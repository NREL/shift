
## Generating synthetic feeder using OpenStreet data

**Developed by: [Kapil Duwadi](https://github.com/KapilDuwadi), 2022-07-31**

In this tutorial you will build synthetic feeder for Chennai, India. You will perform following tasks to achieve final goal.

### <p style="color:green">1. Preparing sandbox environment </p>

To proceed with this tutorial, let's create a `sandbox` environment. 
It will take about a minute to make the environment ready.

[Create a sandbox :fontawesome-brands-python:](https://mybinder.org/v2/gh/NREL/shift/develop){ .md-button .md-button--primary target:_blank }


??? "Verify the screen you are seeing."

    ![](images/binder-snapshot.png){ width: 300}

???+ "Creating your own environment (optional)" 

    If you encounter problem launching sandbox or prefer using jupyter notebook in 
    your own computer please follow the following steps. In windows we recommend
    using `Anaconda` or `Miniconda` to create the environment. 

    If you need help installing `Anaconda` please follow the instructions 
    [here](https://www.anaconda.com/products/distribution). 

    === ":fontawesome-brands-windows: Windows 10"

        ``` cmd
        conda create -n shift python==3.9
        conda activate shift
        conda install -c conda-forge osmnx
        git clone https://github.com/NREL/shift.git
        cd shift
        pip install -e.
        pip install jupyterlab
        jupyter lab
        ```

    === ":fontawesome-brands-apple: + :fontawesome-brands-linux: Mac OS & linux"

        ``` cmd
        conda create -n shift python==3.9
        conda activate shift
        git clone https://github.com/NREL/shift.git
        cd shift
        pip install -e.
        pip install jupyterlab
        jupyter lab
        ```
!!! tip
    If you are using python virtual environment make sure you have 
    `python 3.9 or greater` installed in your system.

Click on `+` symbol or Python Kernel to create a Jupyter Notebook.

!!! success "You have sucessfully created an environment."

---
### <p style="color:green"> 2. Get all the buildings data and create geometry object for all buildings. </p>

Let's get all the geometries from Chennai, India. Copy and paste the following code 
in your jupyter notebook.

```python
from shift.geometry import BuildingsFromPlace
g = BuildingsFromPlace("Chennai, India", max_dist=100)
geometries = g.get_geometries()
print(geometries[0])
```

??? "Verify the output you are seeing."

    ``` 
    Building( Latitude = 13.084701581995573,  Longitude = 80.27018322041822, Area = 5.47) 49
    ```

!!! success "You have sucessfully fetched all the buildings."

---
### <p style="color:green"> 3. Convert building geometries into load objects </p>

In order to create power system loads from geometries we need to tell how to assign phases, voltages and connection type for loads. In this case let's use `RandomPhaseAllocator` class to allocate phases to all geometries. Here we are saying all geometries are of single phase type and there are no two phase and three phase loads and finally pass all the geometries.

Similarly we initialize simple voltage setter by passing line to line voltage of 13.2 kV. `DefaultConnSetter` class is created which will set the connection type to `wye` for all geometries.

```python
from shift.load_builder import (RandomPhaseAllocator, 
                                SimpleVoltageSetter, DefaultConnSetter)
rpa = RandomPhaseAllocator(100, 0, 0, geometries)
svs = SimpleVoltageSetter(13.2)
dcs = DefaultConnSetter()
```

But wait how do we get power consumption data for the load. In order get consumption let's use building area info to get the kw. Let's say we know there is a piecewise linear function that relates building area with peak kW consumption.

```python
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd

area_to_kw_curve = [(0,5), (10, 5.0), (20, 18), (50, 30)]

df = pd.DataFrame({
    'Area in meter square' : [x[0] for x in area_to_kw_curve],
    'Peak consumption in kW' : [x[1] for x in area_to_kw_curve]
})
fig = px.line(df, x="Area in meter square", y="Peak consumption in kW") 
fig.show()
```

??? "Verify the output you are seeing."

    ![](images/tutorial_1_piecewiselinear.png)

In order to use this piecewise linear function we can invoke `PiecewiseBuildingAreaToConsumptionConverter` class from load_builder and pass it as an argument to build the load. Let's see this class in action.

```python
from shift.load_builder import PiecewiseBuildingAreaToConsumptionConverter
pbacc = PiecewiseBuildingAreaToConsumptionConverter(area_to_kw_curve)
area = 15
print(f"For area of {area} m^2 the consumption would be {pbacc.convert(area)}")
```

??? "Verify the output you are seeing."

    ``` 
    For area of 15 m^2 the consumption would be 11.5
    ```

Let's build the loads from the geometries and print one them. Here let's try to build constant power factor of 1.0 type loads for simplicity.

```python
from shift.load_builder import ConstantPowerFactorBuildingGeometryLoadBuilder
from shift.load_builder import LoadBuilderEngineer
loads = []
for g in geometries:
    builder = ConstantPowerFactorBuildingGeometryLoadBuilder(g, 
                            rpa, pbacc, svs, dcs, 1.0)
    b = LoadBuilderEngineer(builder)
    loads.append(b.get_load())
print(len(loads), loads[0], loads[1])
```

??? "Verify the output you are seeing."

    ```
    49 ConstantPowerFactorLoad(Name = 80.2700197_13.083833949999997_load, Latitude = 13.083833949999997, Longitude = 80.2700197, Phase = Phase.AN NumPhase = NumPhase.SINGLE, Connection Type = LoadConnection.STAR, kw = 5.0, pf = 1.0, kv = 7.621) ConstantPowerFactorLoad(Name = 80.26948865_13.08433095_load, Latitude = 13.08433095, Longitude = 80.26948865, Phase = Phase.AN NumPhase = NumPhase.SINGLE, Connection Type = LoadConnection.STAR, kw = 5.0, pf = 1.0, kv = 7.621)
    ```

Let's visualize these loads on top of GIS map. That would be cool right ?. In order to do that let's invoke two layer distribution network first.

```python
from shift.feeder_network import (SimpleTwoLayerDistributionNetworkBuilder, 
                                  TwoLayerNetworkBuilderDirector)
from shift.network_plots import PlotlyGISNetworkPlot
from shift.constants import PLOTLY_FORMAT_CUSTOMERS_ONLY

network_builder = SimpleTwoLayerDistributionNetworkBuilder()
network = TwoLayerNetworkBuilderDirector(loads, [], [], [], network_builder)

API_KEY = None
p = PlotlyGISNetworkPlot(
        network.get_network(),
        API_KEY,
        'carto-darkmatter',
        asset_specific_style=PLOTLY_FORMAT_CUSTOMERS_ONLY
    )
p.show()
```

??? "Verify the output you are seeing."

    ![](images/tutorial_1_loads.png)
!!! success "You have sucessfully converted buildings to power system loads."

---
### <p style="color:green"> 4. Use clustering algorithm to cluster loads </p>

Next step is to use clustering algorithm to figure out best location for positioning distribution transformers. Kmeans clustering is one way of doing this. Let's say we want to have 20 disribution transformers for this feeder.

```python
from shift.clustering import KmeansClustering
import numpy as np

x_array = np.array([[load.longitude, load.latitude] 
                    for load in loads])
cluster_ = KmeansClustering(2)
clusters = cluster_.get_clusters(x_array)
cluster_.plot_clusters()
```

??? "Verify the output you are seeing."

    ![](images/tutorial_1_cluster.png)

!!! success "You have sucessfully clustered the load objects."

* Convert cluster center into distribution transformer objects
* Get road network and create primary network
* Convert primary network into list of primary line sections
* Update transformer objects to use nearest primary node from primary network
* Develop secondary network for all transformer objects
* Convert secondary networks into list of secondary line segments
* Create a substation transformer object
* Export OpenDSS model 
* Visualize the distribution model 
