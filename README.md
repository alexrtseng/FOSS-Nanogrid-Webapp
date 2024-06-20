**Web Application for the UCY Microgrid**

This project is a RESTful Django backend built to allow the monitoring, control, study, and improved 
decision making of the UCY Smart Grid. 

*Naming:* Although this is named FOSS_Nanogrid_Webapp, it is currently applicable to the entire UCY 
microgrid

*Quick Start:* Python3 required (with pip). Install all dependencies in requirements.txt. To run the program
you must initiate a Celery worker (configured through the Django App) and a Celery Beat. However, 
this can easily be executed by executing the run script located in the top directory (this script
is in zsh). 
