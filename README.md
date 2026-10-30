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
- Apache2
## Libraries for the Python metrics collection scripts
- `influxdb-client`
- `psutil`
- `requests`
- `zoneinfo`
## Libraries for the machine learning models
TODO

# Configuration steps
## Setting up the network environment
1. Connect all devices (monitored devices and monitoring server) to
   the switch, assign a static IP address to each device, and test
   connectivity. Configure interfaces on the switch as necessary - all
   devices should be on the same VLAN. Set up SSH on each device to
   simplify configuration and maintenance.
2. Install InfluxDB and Grafana on the device that will act as the
   monitoring server; configure each using the configuration files
   from this repository. Enable the `systemd` services if
   necessary. Create a separate Influx bucket for each monitored
   device.
3. On the 'webserver' device, install Apache and enable the `systemd`
   service (`sudo systemctl enable --now apache2`) to start the server
   process. Confirm that the site is accessible by accessing it from
   another device.
4. On each 'client' device (which send random HTTP requests to the
   'webserver' device to simulate network activity), upload the
   `request.py` Python script (found in the `scripts`
   directory). Modify the IP address in the script so that requests
   are sent to the correct device. Install the `requests` Python
   library and start the script in the background:
   
   ```
   nohup python3 request.py &
   ```

## Setting up metrics collection
### End devices (Raspberry Pis)
5. Upload the metrics collection Python script to each monitored
   device (we did this over SFTP). Alter each script so that the
   metrics are sent to the correct bucket on the monitoring
   server. Generate a unique Influx token for each monitored device
   and update the scripts accordingly.
6. Install the remaining Python dependencies on each monitored device
   using `pip`. Start the script in the background:
   
   ```
   nohup python3 CollectorV2.1.py &
   ```
7. Using the Influx web interface, verify that metrics are being
   pushed to the correct bucket on the database.
### Switch 
8. Connect to the switch over a console connection and enter global
   configuration mode. Enable SNMPv2 using the following command:
   
   ```
   snmp-server community password ro
   ```
9. On the Influx web interface, install the TOML configuration file
   for the SNMP plugin. Generate a new Influx token for the
   switch. Install `telegraf` on the monitoring server.
10. On the monitoring server, execute the following command:

	```
	TODO...
	```
11. Verify that switch metrics are being collected by Influx.

## Setting up the machine learning models and dashboard
TODO

# Specifications of monitored devices
Health and performance metrics were monitored on the following devices
during the development of the project:
- Cisco Catalyst CX 3560-CX switch
- Raspberry Pi 4 Model B (4GB) (Client 1)
- Raspberry Pi 4 Model B (Client 2)
- Raspberry Pi 3B+ (Webserver)

In addition, the monitoring server (on which the Influx database
and Grafana dashboard were hosted) was a Raspberry Pi 3B+.
