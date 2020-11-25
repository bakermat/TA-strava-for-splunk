[strava_api://<name>]
access_code = Go https://www.strava.com/oauth/authorize?client_id=<client_id>&redirect_uri=http://localhost&response_type=code&scope=activity:read_all, change Client ID in URL and copy string after 'code=' here.
start_time = Leave empty to get all activities. Enter the epoch timestamp (UTC time) of the first activity you want to capture. Conversion can be done http://www.epochconverter.com.
reindex_data = Advanced use only: enable this to reindex data, starting from the Start Time specified above.

[strava_webhook://<name>]
port = Port for the local webserver to listen on.
verify_token = Used to configure and verify incoming requests from Strava's webhook for authentication.
callback_url = URL of your webserver for Strava to connect to, this needs to be HTTPS and publicly reachable.
cert_file = The certificate or certificate chain file used for responding to incoming HTTPS requests. Required to be signed by a public CA.
key_file = Private key that corresponds with the public key above.