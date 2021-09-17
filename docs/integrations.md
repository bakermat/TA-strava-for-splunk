### Sourcetypes

1. `strava:activities` contains the summary data for all activities in JSON format.
2. `strava:activities:stream` contains the second-by-second data for an activity, including altitude, lat/long coordinates, heartrate, power, cadence, temperature and speed if the respective sensor data is present.

### Field Aliases
The TA creates two aliases for the `id` field in the sourcetype `strava:activities`:

1. `strava_id`
2. `activity_id`

### Lookups
The TA uses three lookups:

1. `strava_athlete` (KV Store lookup) contains the `firstname`, `lastname`, `fullname`, `ftp` and `weight` fields. For getting the latter two metrics, make sure that the scope of the initial request for an access code from Strava includes the `profile:read_all` permission, e.g. like `scope=activity:read_all,profile:read_all` otherwise you would only get the name.
2. `strava_segments` (KV Store lookup) contains all segments and their details, along with a total amount of times the segment has been ridden. It gets populated by a scheduled search daily at 3am.
3. `strava_types` (CSV lookup) contains a list of all Strava activity types, pretty-printing the sport's name. For example `VirtualRide` becomes `Virtual Ride`, `VirtualRun` becomes `Virtual Run` etc, automatically added to a `type_full` field. This is an automatic lookup.

### Macros
The TA has one macro: `strava_index`, which is set to `index=strava` by default.

### Garmin Add-On for Splunk integration
The TA will automatically extract the Garmin Connect activity ID as the `garminActivityId` field. This makes it easy to correlate data from Garmin and Strava activities when using the <a href="https://splunkbase.splunk.com/app/5035/" target="_blank">Garmin Add-On for Splunk</a>.