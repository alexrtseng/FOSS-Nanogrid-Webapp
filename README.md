# Backend for UCY Microgrid Control Web App

This project is a RESTful Django backend built to allow the monitoring, control, study, and improved 
decision making of the UCY Smart Grid.

## Notes
### Non-PHAETHON CoE Viewers
This application was developed under and for the PHAETHON Centor of Excellence. This is a research center aimed at examining questions critical to decarbonization – namely intelligent power system management, photovoltaics, and green hydrogen. Likewise, this application was developed for the University of Cyprus (UCY) microgrid; the institution within PHAETHON operates. Although the naming and general application are aimed at this specific microgrid, it has a much broader scope (as stated below), and was developed with research pursuits in mind. 

### Status
This backend is fully functional and provides real time forecasting and energy storage system (ESS) 
optimization. It is also fully compatible with the frontend portion of the web-application which will 
display real-time/future data about the UCY microgrid. Although this application is functional, it has not
been deployed to production and is currently configured to run locally. Future steps for this application would
be to deploy this to a server and to set up permanent AWS and Xweather accounts to allow the applicatoin to run. 
The only critical functionality that would need to be changed by future editors is the database storage of 
time series data. It was requested to keep the backend data in JSON format, but some form of time-series 
specific data storage would be preferable.

### Scope
Although this is named FOSS_Nanogrid_Webapp, it is applicable to the entire UCY microgrid, and 
more broadly *any* microgrid. Models and functions have been written abstractly to allow this program
to be applied easily to other microgrids through simple repopulation of the database to match that of
another system. 

### Authors
Developer: *Alex Tseng*

Supervisor: *Stavros Afxentis*

## Quick Start
The web app was developed for Python 3.11, but should be compatible with 3.11+. All dependencies can be installed with pip from the requirements.txt file. The django project folder is "foss_nanogrid": all django commands (using manage.py) should be executed from this directory. However, this application also uses Celery Workers and Celery Beat. These can be started manually, or more simply, a user can run the "run_foss_nanogrid_webapp.zsh" file: this will start the worker, beat, and run the django server. If a scheduler already exists, this will automatically start running. If not, an endpoint exists to create one. 

## Structure
The structure can best be descriped by a brief understanding of the project's apps: 

### Data Collection
This app is concerned with the collection, storing, and cleaning of real-time data. This app houses the logic for modbus communication with smart-meters stored in the database. It also periodically cleans this data up into thirty-minute averages which are stored for long periods. Although JSON is not a particularly smart way to store long term time-series data, this closely matched the assignment at hand. 
### Forecasting
Forecasting uses pre-trained gradient boost regression models to predict PV, load, and net load. These models are stored in the XGBoost native format and loaded in when required. Forecasting also houses the logic for XWeather batching – this is an efficient way to request weather information from the API by generating http requests which batch up to 31 "normal calls". This weather data – and several time features – are then used to generate the forecast. URL endpoints are heavily customizable with params, which can control resolution, duration of forecast, and even what models to use. 
### Metrics
This app is concerned with providing data metrics. This predominately includes database queries and request handling. 
### Optimization
This app is conerned with providing real time optimization of charge control. Although this app houses the logic for optimization, it is (in the project's current state) primarily an addition to the forecasting features (and is accessed via a forecasting endpoint). The core logic is to take the forecasts for net load and use these points to optimize the control of a battery (stored in the database). To do this, the app uses SciPy minimize with an SLSQP solver to find the charge amounts at each timestep to reduce the total cost of electricity for the University. Although this functionality feels trivial given Cyrpus's fixed tariff, the optimization is built to handle variable rates (and/or export rates). If Cyprus switches to time-of-use or critical-peak-pricing then this optimization will become much more interesting and less intuitive. 
## ML Training 
The training scripts for the ML models are in ucy-forecasting which should also be accessible via github. The models which exist currently in the web application have been trained on generic data and should therefor do an adequate job for any given PV system. However, it would be preferable to provide tailored models for individual use. The load models have been trained on the UCY microgrid and cannot be applied so generally. Thus, this web application does not include the training logic, but instead allows users to plug in models that they have already trained through XGBoost. XGBoost was the best regression model out of two other model architectures with LSTM and LSTM + FNN.
## Endpoints
### data-collection/
**start/**: If Celery Beat does not have schedulers for 30-min cleaning or 10 second data retrieval, create those schedulers. <br>
### forecasting/
**forecast-pv/**: Provides forecast for PV output for up to two weeks.<br>
*Required*<br>
start=:string | Start of requested forecasting period(ISO format)<br>
end=:string | End of requested forecasting period (ISO format)<br>
pv=:string | Name of PV system for which to forecast<br>
*Optional*<br>
resulotion=:int | Size of timesteps in forecast (in hour or minute). 30 by default.<br>
min_resolution=:bool | If true, resolution is in minutes. If not, resolution is in hours. Minute resolution can only be forecasted for 24 hours. Hour resolution can be forecasted for up to 14 days. True by default.<br>
all_models=:bool | If true, the program will take the weighted average of all model folds. If not, it will take the best models prediction. True by default.<br>
<br>
**forecast_ucy_load/**: Provides forecast for UCY load.<br>
*Required*<br>
start=:string | Start of requested forecasting period(ISO format)<br>
end=:string | End of requested forecasting period (ISO format)<br>
*Optional*<br>
resulotion=:int | Size of timesteps in forecast (in hour or minute). 30 by default.<br>
min_resolution=:bool | If true, resolution is in minutes. If not, resolution is in hours. Minute resolution can only be forecasted for 24 hours. Hour resolution can be forecasted for up to 14 days. True by default.<br>
<br>
**forecast_net_load/**: Provides forecast for UCY net load and optimization.<br>
*Required*<br>
start=:string | Start of requested forecasting period(ISO format)<br>
end=:string | End of requested forecasting period (ISO format)<br>
*Optional*<br>
pv=:string | Name of PV system for which to forecast. Default is UCY hypothetical PV system.<br>
resulotion=:int | Size of timesteps in forecast (in hour or minute). 30 by default.<br>
min_resolution=:bool | If true, resolution is in minutes. If not, resolution is in hours. Minute resolution can only be forecasted for 24 hours. Hour resolution can be forecasted for up to 14 days. True by default.<br>
ess_optimization=:string If this param is included, the returned object will return the optimal charge controls and SOC for each timestamp. The argument to this parameter specifies the objective of the optimization. Currentely, the only option is "energy_export" which will minimize energy export. 

### metrics/
**devices/**: Returns information about all smart meters in database. <br>
**rt-all-meters/**: Returns real time information recieved from smart meters<br>



