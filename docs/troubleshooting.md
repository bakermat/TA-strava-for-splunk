####Logs####
If you want to troubleshoot you can check the logs:

1. In Splunk: `index=_internal sourcetype="tastravaforsplunk:log"`
2. In the CLI: `$SPLUNK_HOME/var/log/splunk/ta_strava_for_splunk_strava_api.log`

####Invalid or expired access code####
The most common issue is that the access code is invalid or has expired. To solve this, request a new access code using `https://www.strava.com/oauth/authorize?client_id=[client_id]&redirect_uri=http://localhost&response_type=code&scope=activity:read_all,profile:read_all` and replace `[client_id]` with your Client ID. Alternatively, make sure that your Client ID and Client Secret have been set correctly, **before** you make the change as each access code is only valid once.

####Reindexing data####
If you want to reindex events, you can either delete the input and create another one with a different name (important!) or edit the current one and select the 'Reindex data' checkbox, which will reindex the data from the specified starting time.