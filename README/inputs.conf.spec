[strava_webhook://<name>]
port = 
verify_token = Used to configure and verify incoming requests from Strava's webhook for authentication.
callback_url = Callback URL for Strava to reach this webserver, needs to be publicly reachable.
cert_file = 
key_file = 

[strava_api://<name>]
access_code = Go https://www.strava.com/oauth/authorize?client_id=<client_id>&redirect_uri=http://localhost&response_type=code&scope=activity:read_all, change Client ID in URL and copy string after 'code=' here.
start_time = Leave empty to get all activities. Enter the epoch timestamp (UTC time) of the first activity you want to capture. Conversion can be done http://www.epochconverter.com.
reindex_data = Advanced use only: enable this to reindex data, starting from the Start Time specified above.