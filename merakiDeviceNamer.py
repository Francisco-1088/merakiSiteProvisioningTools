import meraki
import pandas as pd
import config
import batch_helper
from tabulate import tabulate
import sys

dashboard = meraki.DashboardAPI(config.api_key)

def print_tabulate(data):
    """
    Outputs a list of dictionaries in table format
    :param data: Dictionary to output
    :return:
    """
    print(tabulate(pd.DataFrame(data), headers='keys', tablefmt='fancy_grid'))

device_names_df = pd.read_csv(f"./{config.device_names_csv}")
device_names_list_of_dicts = device_names_df.to_dict("records")

update_name_actions = []
for device in device_names_list_of_dicts:
    update_name_action = dashboard.batch.devices.updateDevice(serial=device['serial'], name=device['name'])
    update_name_actions.append(update_name_action)

print("These names will be applied to your serial numbers:")
print_tabulate(update_name_actions)

proceed = input("Do you wish to proceed? (Y/N)")

if proceed == "Y":
    name_helper = batch_helper.BatchHelper(dashboard, config.org_id, update_name_actions,
                                           linear_new_batches=False, actions_per_new_batch=100)

    name_helper.prepare()
    name_helper.generate_preview()
    name_helper.execute()

    print(f"Helper status is {name_helper.status}")

    batches_report = dashboard.organizations.getOrganizationActionBatches(config.org_id)
    new_batches_statuses = [{'id': batch['id'], 'status': batch['status']} for batch
                            in batches_report if batch['id'] in name_helper.submitted_new_batches_ids]
    failed_batch_ids = [batch['id'] for batch in new_batches_statuses if batch['status']['failed']]
    print(f'Failed batch IDs are as follows: {failed_batch_ids}')
elif proceed == "N":
    sys.exit()
else:
    sys.exit()