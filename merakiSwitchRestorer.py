import meraki
import pandas as pd
from tabulate import tabulate
import config
import batch_helper
import sys
import numpy as np

dashboard = meraki.DashboardAPI(config.api_key)

def to_camel_case(string):
    """
    Converts a string from any case to camelCase
    :param string: String to convert
    :return: camel[0].lower() + camel[1:] camelCase string
    """
    # Remove spaces
    camel = ''.join(x for x in string.title() if not x.isspace())
    # Remove non-alphanumeric characters
    camel = ''.join(letter for letter in camel if letter.isalnum())
    return camel[0].lower() + camel[1:]

def update_nan_to_none(some_dict):
    """
    Updates nan values to None
    :param some_dict: dictionary with nan values
    :return: some_dict: dictionary with nan values converted to None
    """
    for key, value in some_dict.items():
        # If the value is a float and is NaN, update it to None
        if isinstance(value, float) and np.isnan(value):
            some_dict[key] = None
        # If the value is a nested dictionary, recursively update it
        elif isinstance(value, dict):
            update_nan_to_none(value)
    return some_dict

def print_tabulate(data):
    """
    Outputs a list of dictionaries in table format
    :param data: Dictionary to output
    :return:
    """
    print(tabulate(pd.DataFrame(data), headers='keys', tablefmt='fancy_grid'))

def csv_df_manipulation(csv_df):
    """
    Converts data in DataFrame to a format closer to the Meraki API
    :param csv_df:
    :return:
    """
    # Convert headers to camel case
    csv_df.columns = map(to_camel_case, csv_df.columns)
    # Retrieves only the name of the switch from the CSV switchPort column
    csv_df['switchPort'] = csv_df['switchPort'].str.split().str[0]
    # Renames columns to match Meraki API
    csv_df.rename(columns={"switchPort": "switch_name", "port": "portId", "rstp": "rstpEnabled"}, inplace=True)
    # Adds stpGuard and voiceVlan columns
    csv_df["stpGuard"] = 0
    csv_df["voiceVlan"] = 0
    return csv_df

def list_of_dicts_manipulation(list_of_dicts):
    """
    Manipulates list of dictionaries to a format closer to that required by the Meraki API
    :param list_of_dicts: Original list of dictionaries with values incompatible with the Meraki API
    :return: list_of_dicts: Compatible list of dicts
    """
    for port in list_of_dicts:
        port = update_nan_to_none(port)
        if port["tags"]!=None:
            tag_list = port["tags"].split()
            port["tags"]=tag_list
        if port["module"] != None:
            if ("x10G" in port["module"]) or ("x40G" in port["module"]):
                port["portId"] = f"1_MA-MOD-{port['module'].upper()}_{port['portId']}"
            else:
                port["portId"] = f"1_{port['module'].upper()}_{port['portId']}"
        if port["enabled"] == "enabled":
            port["enabled"] = True
        else:
            port["enabled"] = False
        if port["rstpEnabled"] != "Disabled":
            rstp = port["rstpEnabled"]
            if "Loop guard" in rstp:
                port["stpGuard"] = "loop guard"
            elif "Root guard" in rstp:
                port["stpGuard"] = "root guard"
            elif "BPDU guard" in rstp:
                port["stpGuard"] = "bpdu guard"
            else:
                port["stpGuard"] = "disabled"
            port["rstpEnabled"] = True
        else:
            port["rstpEnabled"] = False
            port["stpGuard"] = "disabled"
        if port["type"] == "trunk":
            vlans = str.split(port["vlan"])
            port["vlan"] = int(vlans[1])
            port["voiceVlan"] = None
        elif port["type"] == "access":
            vlans = str.split(port["vlan"])
            if len(vlans) > 1:
                port["voiceVlan"] = int(vlans[2])
                port["vlan"] = int(vlans[0].replace(",", ""))
            else:
                port["voiceVlan"] = None
                port["vlan"] = int(vlans[0])
    return list_of_dicts


# Reads CSV file
switch_ports_df = pd.read_csv(f"./{config.switch_ports_csv}")
# Manipulates DataFrame to shape it closer to Meraki API
switch_ports_df = csv_df_manipulation(switch_ports_df)
# Converts DataFrame to a list of dictionaries
switch_ports_list_of_dicts = switch_ports_df.to_dict("records")
# Modify list of dicts to format compatible with Meraki API
switch_ports_list_of_dicts = list_of_dicts_manipulation(switch_ports_list_of_dicts)

switch_ports_df = pd.DataFrame(switch_ports_list_of_dicts)
print_tabulate(switch_ports_df)

org_ports_all = dashboard.switch.getOrganizationSwitchPortsBySwitch(config.org_id, total_pages=-1)
org_ports_flattened = []
for switch in org_ports_all:
    if switch["network"]["id"] == config.network_id:
        base_dict = {
            "switch_name": switch["name"],
            "switch_serial": switch["serial"],
            "switch_net_id": switch["network"]["id"],
            "switch_model": switch["model"],
        }
        for port in switch["ports"]:
            new_dict = dict(base_dict, **port)
            org_ports_flattened.append(new_dict)

print_tabulate(org_ports_flattened)


update_ports = []
# Do not update stack ports or ports with Port Profiles, as this is not supported
# Skip Aggregation Group ports as well, as this is not supported
for csv_port in switch_ports_list_of_dicts:
    if ("Dedicated" not in csv_port["portId"]) and (csv_port["portProfile"]!="Enabled") and (csv_port["aggregationGroup"]==None):
        for org_port in org_ports_flattened:
            if (csv_port["switch_name"]==org_port["switch_name"]) and (csv_port["portId"]==org_port["portId"]):
                for key in csv_port:
                    if key in org_port:
                        org_port[key]=csv_port[key]
                update_ports.append(org_port)

update_ports_flattened_df = pd.DataFrame(update_ports)

update_port_actions = []
for port in update_ports:
    kwargs = {k: port[k] for k in port.keys() - {"switch_name", "switch_serial",
                                                 "switch_net_id", "switch_model", "portId"}}
    update_port_action = dashboard.batch.switch.updateDeviceSwitchPort(serial=port["switch_serial"],
                                                                       portId=port["portId"],
                                                                       **kwargs)
    update_port_actions.append(update_port_action)

print("These configurations will be applied to your switch ports:")
print_tabulate(update_port_actions)

proceed = input("Do you wish to proceed? (Y/N)")

if proceed == "Y":
    port_helper = batch_helper.BatchHelper(dashboard, config.org_id, update_port_actions,
                                           linear_new_batches=False, actions_per_new_batch=100)
    port_helper.prepare()
    port_helper.generate_preview()
    port_helper.execute()

    print(f"Helper status is {port_helper.status}")

    batches_report = dashboard.organizations.getOrganizationActionBatches(config.org_id)
    new_batches_statuses = [{'id': batch['id'], 'status': batch['status']} for batch
                            in batches_report if batch['id'] in port_helper.submitted_new_batches_ids]
    failed_batch_ids = [batch['id'] for batch in new_batches_statuses if batch['status']['failed']]
    print(f'Failed batch IDs are as follows: {failed_batch_ids}')
elif proceed == "N":
    sys.exit()
else:
    sys.exit()