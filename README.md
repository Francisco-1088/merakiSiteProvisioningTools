# merakiSiteProvisioningTools
This repo contains tools to aid in provisioning meraki sites.

## How to Use

1. Clone repo to your working directory with `git clone https://github.com/Francisco-1088/merakiSiteProvisioningTools.git`
2. Edit `config.py`
* Add your API Key under `api_key` in line 2
* Add your Organization ID under `org_id` in line 3. This will be the Organization ID for the target organization where the switches will be configured, and it can be obtained by scrolling all the way down in your Meraki Dashboard and making note of the organization ID value at the bottom.
* Add your Network ID under `network_id` in line 4. This will be the Network ID for the target network where the switches will be configured and it can be obtained by right-clicking anywhere in your Dashboard and selecting View Page Source (in Google Chrome). You would then search the HTML code of the page for the value `Mkiconf.locale_id`, and copy the numeric value next to this flag to your `config.py` file. You would then add `L_` to the front of the numeric value. For example, if your Meraki Dashboard HTML page says that the network's ID is `Mkiconf.locale_id = "56612345678913"`, your corresponding network ID in your config file would be `network_id = "L_56612345678913"`.
* Modify the name of the configuration CSV files in lines 7 and 8 if needed
* Leave the rest in default
3. Run `pip install -r requirements.txt` to install required libraries
4. Navigate to your Meraki network with your switch port configurations by going to Switching --> Switch ports, and in the top right select Download As.
* Only the columns listed in the sample `switchports_sample.csv` file are supported
5. Add the `switchports.csv` file to your working folder and make sure the name matches the name specified in your `config.py` file
6. Add the serial numbers and corresponding names for your devices to the `device_names.csv` file.
7. Once the switches have been moved to the desired network, run the `merakiDeviceNamer.py` script first by executing `python merakiDeviceNamer.py`, this will proceed to name all devices according to your CSV file. Any devices missing from the CSV file will not be named.
8. After this, run the `merakiSwitchRestorer.py` file by executing `python merakiSwitchRestorer.py`. This will proceed to configure all ports in your network according to the CSV file provided.
