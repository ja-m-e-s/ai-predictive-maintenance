# Overview
The objective of this project was to develop an AI-based predictive
maintenance system to predict faults in network devices. A small
isolated network, consisting of four Raspberry Pis and one switch, was
built for the purpose of collecting training data for the machine
learning models and testing the capability of each trained
model. Metrics were collected as time series data from three of the
Raspberry Pis via Python scripts, with the fourth hosting a central
Influx database for storing metrics samples, and a monitoring
dashboard (Grafana) to display insights produced by the AI model, in
addition to other information about the network. Metrics were also
collected from the switch over SNMP, using the Influx SNMP plugin.

While we were able to develop an anomaly detection model to identify
anomalies in device metrics over time, the system is not yet capable
of predicting potential faults in the monitored devices. Therefore,
future research efforts should be primarily focused on using the
outputs of the anomaly detection model as a basis for device fault
prediction. The machine learning models and collection scripts may
also need to be refined in future.

# Description of repository contents
This repository contains all of the artifacts required for continued
development and testing of the experimental predictive maintenance
system:
- Source code for the machine learning models (one-class SVM and LSTM)
  in the `models` directory, in Jupyter notebook format (`ipynb`). The
  results of the training and testing of these models are also
  included in the notebooks, in graphical and tabular format.
- Device collection scripts, (in the `scripts/collection` directory)
  which collect samples from each of the three monitored Raspberry Pi
  devices every ten seconds. It is recommended to use version 2.1,
  which supports the most metrics and is the most reliable version of
  the script; however, older versions of the script may be used for
  compatibility with older devices.
- The anomaly pipeline script (`scripts/anomaly2influx.py`), which
  is used to push predictions made by the anomaly detection models to the
  Influx database in real time.
- The YAML configuration file for the Influx SNMP plugin (also in the
  `scripts/collection` directory), used to query various metrics from
  the switch's MIB over SNMPv2 every ten seconds.
- The web traffic simulation script (`scripts/request.py`), which
  sends an HTTP request to one of the Raspberry Pis (the 'web server'
  Pi, running an Apache2 server) at random every 0-30 seconds.
  
The CSV files containing samples collected from the three Raspberry
Pis and switch can be found [here] (TBD), as they are too large to be
stored in this repository.

# Dependencies
## Software
- Python 3
- InfluxDB
- Grafana
## Libraries for the Python metrics collection scripts
- `psutil`
- `influxdb-client`
- `zoneinfo`
## Libraries for the machine learning models
TODO

# Setting up the testing environment
TODO - instructions for configuring the testing environment

# Setting up the machine learning models
TODO
