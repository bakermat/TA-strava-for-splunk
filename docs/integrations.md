To enable integration and improve the ability to correlate different sources together, the TA has a few integrations.

###Field Aliases###
The TA creates two aliases for the `id` field in the sourcetype `strava:activities`:

1. `strava_id`
2. `activity_id`

###Lookups###
There is a KV Store lookup named `strava_athlete` that retrieves the athlete's name, weight and FTP. For getting the latter two metrics, make sure that the scope of the initial request for an access code from Strava includes the `profile:read_all` permission, e.g. like `scope=activity:read_all,profile:read_all` otherwise you would only get the name.

###Garmin###
The TA will automatically extract the Garmin Connect activity ID as `garminActivityId`. This makes it easy to correlate data from Garmin and Strava activities when using the <a href="https://splunkbase.splunk.com/app/5035/" target="_blank">Garmin Add-On for Splunk</a>, 