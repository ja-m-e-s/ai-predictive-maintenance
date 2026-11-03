# Overview
The objective of this project was to develop an AI-based predictive
maintenance system to predict faults in network devices. A small
isolated network, consisting of four Raspberry Pis and one switch, was
built for the purpose of collecting training data for the machine
learning models and testing the capability of each trained
model. Metrics were collected as time series data from three of the
Raspberry Pis via Python scripts, with the fourth hosting a central
InfluxDB instance for storing metrics samples, and a monitoring
dashboard (Grafana) to display insights produced by the AI model, in
addition to other information about the network. Metrics were also
collected from the switch over SNMP, using the Telegraf SNMP plugin
for Influx.

While we were able to develop an anomaly detection model to identify
anomalies in device metrics over time, the system is not yet capable
of predicting potential faults in the monitored devices. We were also
unable to implement real-time anomaly detection - currently, the AI
models rely on local CSV files, exported from the Influx database, to
generate anomaly predictions, but the final system should be able to
query samples directly from Influx for processing by the model.

Therefore, future efforts should be focused on implementing real-time
anomaly detection, and using the outputs of the anomaly detection
model as a basis for device fault prediction. The machine learning
models and collection scripts may also need to be refined in future.

![System diagram](diagram.png)

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
- The web traffic simulation script (`scripts/request.py`), which
  sends an HTTP request to one of the Raspberry Pis (the 'web server'
  Pi, running an Apache2 server) at random every 0-30 seconds.
- The TOML configuration file for the Influx SNMP plugin
  (`influx/switch_snmp.conf`), used to query various metrics from the
  switch's MIB over SNMPv2 every ten seconds.
- JSON configuration files for Grafana in the `grafana`
  directory. `Machine learning dashboard.json` was used for a
  dashboard that displays anomaly detection information about a
  particular device. It is a template that can be used for all
  monitored devices with minimal modification. `Client1
  dashboard.json`, was used for a dashboard that displays other key
  information about a particular device (e.g., latency,
  throughput). This too can be used for all monitored devices
  (provided they support the four metrics displayed on the dashboard).
  
CSV files containing samples collected from the three Raspberry Pis
and switch can be accessed by contacting the project sponsor, as they
are too large to be stored in this repository.

# Dependencies
## Software
- Python 3
- [InfluxDB](https://www.influxdata.com/products/influxdb/)
- [Grafana](https://grafana.com/oss/grafana/)
- [Apache2](https://httpd.apache.org/download.cgi)
- [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/)
## Libraries for the Python scripts
- `influxdb-client`
- `numpy`
- `pandas`
- `psutil`
- `requests`
- `zoneinfo`
## Libraries for the machine learning models
- `joblib`
- `matplotlib`
- `numpy`
- `pandas`
- `scikit-learn` (`sklearn`)
- `tensorflow`

# Configuration steps
## Setting up the network environment
1. Connect all devices (monitored devices and monitoring server) to
   the switch, assign a static IP address to each device, and test
   connectivity. Configure interfaces on the switch as necessary - all
   devices should be on the same VLAN. Set up SSH on each device to
   simplify configuration and maintenance.
2. Install InfluxDB and Grafana on the device that will act as the
   monitoring server. Enable the `systemd` services if
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
   configuration mode. Configure an IP address on the default VLAN
   (all devices on the network should be connected to this VLAN).
9. Enable SNMPv2 on the switch using the following command:
   
   ```
   snmp-server community password ro
   ```
   
   Write the changes to memory (`copy run start`).
10. On the Influx web interface, install the configuration file for
   the SNMP plugin (`switch_snmp.conf`). Generate a new Influx token
   for the switch. Update the IP addresses and Influx token in the
   configuration file. Install `telegraf` on the monitoring server.
11. On the monitoring server, execute the following command (replacing
	`<token>` with a valid Influx token, and `<server_ip>` with the IP
    address of the monitoring server):

	```
	INFLUX_TOKEN=<token> nohup telegraf --config http://<server_ip>:8086/api/v2/telegrafs/11710df86cd1a000 &
	```
	
	This command can also be generated automatically in the Influx web
    interface - try doing it this way if you run into problems.
12. Verify that switch metrics are being collected by Influx.

## Setting up the dashboard
1. Install Grafana on the monitoring server if it has not already been
   installed.
2. From the Grafana web interface (http://<server_ip>:3000), install
   the two JSON dashboard configuration files for each monitored
   device. Change the device name and other fields of the files as
   necessary.
3. Verify that real-time metrics from each monitored device are being
   displayed on the dashboard. 

## Setting up the machine learning models and dashboard
### Dependencies
The following CSV files were used to train and test the machine
learning models:
- Client1(all).csv
- Client2(all).csv
- Client3(all).csv
- Switch(all).csv
- Client1(original).csv
- Client2(original).csv
- Client3(original).csv
- Switch(original).csv
These files can be provided by the project sponsor upon request.

Python 3.12 or higher is recommended for running the machine learning
models, as well as an up to date VS Code environment.

### Running models
The models are stored in three Jupyter notebook (`.ipynb`) files: 

- `LSTM(all metrics).ipynb` - runs LSTM model using all csv metrics
- `LSTM(original metrics).ipynb` - runs LSTM model using core 7 metrics
- `OCSVM(all + original metrics).ipynb` - runs OCSVM for both
  depending on which the user would like, by changing a variable from
  "original" to "all" or vice versa.

To run each model the user can run each cell individually, or run all.

### Analysing findings
To view the results of all models without rerunning the code, each
model's results are stored within folders:
- LSTM (all metrics) - found in folder `Expanded_LSTM_Results`
- LSTM (original metrics) - found in folder `LSTM_Results`
- OCSVM (all + original metrics) - found in folders
  `OCSVM_All_Metrics_Results` (for all metrics) and
  `OCSVM_Original_Results` (for original metrics)

### Sending anomaly detection information to Influx
1. Create a new bucket on Influx to store the anomaly predictions (in
   the script, a bucket named `MLCL1` is used by default.
2. Generate a new Influx token and add it to `anomaly2influx.py` (or
   as an environment variable on the machine on which the model is
   hosted).
3. Run the script (`python3 anomaly2influx.py`) to begin pushing
   predictions to Influx.x

# Specifications of Monitored Devices
Health and performance metrics were monitored on the following devices
during the development of the project:
- Cisco Catalyst CX 3560-CX switch
- Raspberry Pi 4 Model B (4GB) (Client 1)
- Raspberry Pi 4 Model B (Client 2)
- Raspberry Pi 3B+ (Webserver)

In addition, the monitoring server (on which the Influx database
and Grafana dashboard were hosted) was a Raspberry Pi 3B+.

# Metrics observed on the monitored devices
## Raspberry Pis
* Uptime (seconds)
* CPU utilisation (%)
* CPU temperature (C°)
* CPU voltage
* CPU clock speed (MHz)
* Disk usage
* Packet loss rate (%)
* Packet error rate (%)
* Latency (ms)
* Throughput (bps)
* Reachability
* CPU throttled (boolean)
* CPU speed capped (boolean)
* Low voltage (boolean)
* Estimated power draw (Watts)

## Switch
* Uptime (seconds)
* CPU usage (%)
* Free memory (bytes)
* Temperature (C°)
* Power supply state
* Inbound bytes count for each interface
* Outbound bytes count for each interface
* Inbound error count for each interface
* Outbound error count for each interface

## AI Usage
OpenAI's GPT-6 was used to produce the machine learning models for the
sake of clarity and structure. It was also used to format the dataset
files into more readable forms.
