# Credentials
api_key = "YOUR-API-KEY"
org_id = "YOUR-ORG-ID"
network_id = "YOUR-NET-ID"

# Device Config files
switch_ports_csv = "switchports.csv"
device_names_csv = "device_names.csv"

# Logging, Verbosity and Supervision
verbose = True # Will display information gathered about networks
supervised = False # Will ask before applying any configuration changes
console_logging = True # Will print API output to the console
max_retries = 100 # Number of times the API will retry when finding errors like 429
max_requests = 10 # Number of concurrent requests to the API