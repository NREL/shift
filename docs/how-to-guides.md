## List of commands available

Use command `shift-internal --help` to view all the commands available.

* `create-config-file` : Creates a default config yaml file
* `create-feeder`: Uses the config yaml file to create synthetic feeder


## Use yaml file to generate the feeder

Use the following commands to create the feeder from yaml file.

```cmd
shift-internal create-config-file -c config.yaml
shift-internal create-feeder -c config.yaml
```

## Understanding and updating yaml file

```yaml
location:
  # can be string or tuple with lat lon pair
  address: "chennai, india" 
  # distance must be in m, represents a bounding box distance form the address
  distance: 300


# Coefficients for defining diversity factor: x[0]*log(num_cust) + x[1]
div_func_coeff: [0.3908524, 1.65180707]

substation:
  
  # Substation must be (lon, lat) pair 
  location: [80.2786311, 13.091658]
  
  # Name of the circuit
  circuit_name: "chennai"

  # kV for circuit
  kv: 33.0

  # Frequency in Hz
  freq: 50

  # Initial pu voltage for circuit
  pu: 1.0
    
  # Phase info for building substation
  phase:
    neutral_present: true
    num_phase: 3
    phase_type: null

  # Sequence impedances
  z1: [0.001, 0.001]
  z0: [0.001, 0.001]

  # kv voltage levels
  kv_levels: [0.415, 11.0, 33.0]

substation_xfmr:

  # voltage levels for dist xfmrs
  kv:
    ht: 33.0 # High tension kv
    lt: 11.0 # Low tension kv

  # Phase for dist xfmrs
  phase:
    num_phase: 3
    phase_type: null
  
  # Connection type for dist xfmrs
  conn:
    ht: "delta"
    lt: "star_grounded"

  # Design factors
  design_factors:
    
    # Adjustment factor
    adj_factor: 1.25

    # planned growth rate in percentage
    planned_avg_annual_growth: 2

    # actual growth rate
    actual_avg_annual_growth: 4

    # actual years in operation
    actual_years_in_operation: 15

    # planned years in operation:
    planned_years_in_operation: 10

    # Catalog type to select type of catalog used
    catalog_type: "all"

    # Power factor used to compute kva for transformer
    pf: 0.9 


# Settings for loads
loads:
  # Decided how to assign phases to loads
  phase: 
    # Method for allocating phase
    method: "random"
    pct_single_phase: 100
    pct_two_phase: 0
    pct_three_phase: 0
  # Deciding voltage level for loads
  kv:
    # Method for setting voltage to loads
    method: "simple"
    kv: 0.415
  # Deciding connection type for loads
  conn:
    # Method for setting connection type to loads
    method: "default"
  # Deciding kw for loads
  kw:
    # Method for setting kw for loads
    method: "piecewiselinear"
    # Tuple must be in this format (area in m^2, non coincident kw)
    curve: [[0,0], [10, 15.0], [20, 35], [50, 80]]
  # Load type
  type:
    # load type
    name: "constantpowerfactor"
    pf: 1.0

# Setting for distribution transformers
dist_xfmrs:
  # Decide how to to come up with distribution transformers
  method: 
    name: "clustering"
    # Decide cluster method
    cluster_method: "location_kmeans"
    # Number of clusters is required for kmeans
    estimated_customers_per_transformer: 100

  # voltage levels for dist xfmrs
  kv:
    ht: 11.0 # High tension kv
    lt: 0.415 # Low tension kv

  # Phase for dist xfmrs
  phase:
    num_phase: 3
    phase_type: null
  
  # Connection type for dist xfmrs
  conn:
    ht: "delta"
    lt: "star_grounded"

  # Design factors
  design_factors:
    
    # Adjustment factor
    adj_factor: 1.25

    # planned growth rate in percentage
    planned_avg_annual_growth: 2

    # actual growth rate
    actual_avg_annual_growth: 4

    # actual years in operation
    actual_years_in_operation: 15

    # planned years in operation:
    planned_years_in_operation: 10

    # Catalog type to select type of catalog used
    catalog_type: "all"

    # Power factor used to compute kva for transformer
    pf: 0.9 

# Settings for primary/HT conductors
primary_network:

  # Voltage level for primary network
  kv: 11.0

  # Maximum pole to pole distance in meter
  max_pp_distance: 100

  # Conductor type used
  cond_type: "overhead"

  # Phase settings
  phase:
    num_phase: 3
    neutral_present: false
    phase_type: null

  # Conductor configuration
  configuration:

    # Configuration for three phase conductors
    three_phase:
      height_of_top_conductor: 9 
      space_between_conductors: 0.4
      unit: "m"
      type: "horizontal"

  # Design factors
  design_factors:
    
    # Adjustment factor
    adj_factor: 1.25

    # planned growth rate in percentage
    planned_avg_annual_growth: 2

    # actual growth rate
    actual_avg_annual_growth: 4

    # actual years in operation
    actual_years_in_operation: 15

    # planned years in operation:
    planned_years_in_operation: 10

    # Allowed voltage drop used in drop estimation to find conductor
    voltage_drop: 2

    # Catalog type to select type of catalog used
    catalog_type: "ACSR"

    # Power factor
    pf: 0.9

# Settings for primary/HT conductors
secondary_network:

  # Voltage level for primary network
  kv: 0.415

  # Maximum pole to pole distance in meter
  max_pp_distance: 100

  # Conductor type used
  cond_type: "overhead"

  # Phase settings
  phase:
    num_phase: 3
    neutral_present: false
    phase_type: null
    service_drop_neutral: false

  # Conductor configuration
  configuration:

    # Configuration for three phase conductors
    three_phase:
      height_of_top_conductor: 9 
      height_of_neutral_conductor: 9.4
      space_between_conductors: 0.4
      unit: "m"
      type: "horizontal"
     
    # Configuration for single phase conductors
    single_phase:
      height_of_top_conductor: 9 
      unit: "m"
      type: "horizontal"

  # Design factors
  design_factors:
    
    # Adjustment factor
    adj_factor: 1.25

    # planned growth rate in percentage
    planned_avg_annual_growth: 2

    # actual growth rate
    actual_avg_annual_growth: 4

    # actual years in operation
    actual_years_in_operation: 15

    # planned years in operation:
    planned_years_in_operation: 10

    # Allowed voltage drop used in drop estimation to find conductor
    voltage_drop: 5

    # Catalog type to select type of catalog used
    catalog_type: "ACSR"

    # Catalog type to be used for lateral
    catalog_type_lateral: all

    # Power factor
    pf: 0.9

exporter:
  type: "opendss"
  path: "."

```

