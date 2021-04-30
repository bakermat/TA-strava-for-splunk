## Overview
The Strava Add-on for Splunk let's you retrieve activity data from Strava's API to do fitness analysis. It uses Splunk checkpoints to ensure that only new activities are indexed.
 
Strava uses OAuth2 authentication, which requires a few initial steps. This is only required once.

## How to use this add-on
#### Getting started
- Create a Strava app if you haven't done so yet, go to https://www.strava.com/settings/api. This is how Splunk will interact with the Strava API.
- You can use anything (e.g.) for `Website`. For `Authorization Callback Domain` you can use `localhost` if you don't know what to fill in here.
- Make note of the `Client ID` and `Client Secret`, you'll need this in Splunk.
- Go to https://www.strava.com/oauth/authorize?client_id=[client_id]&redirect_uri=http://localhost&response_type=code&scope=activity:read_all,profile:read_all and make sure you replace [client_id] with your Client ID.
- Click Authorize, you'll then get the access code that's required to start using Strava's API.
- The access code is in the URL, for example if the URL = `http://localhost/?state=&code=1263bc141604aaaddfc30a3161558b34c00d9e56&scope=read,activity:read_all,profile:read_all` then the access code is `1263bc141604aaaddfc30a3161558b34c00d9e56`.
- Copy that string along with the `Client ID` and `Client Secret` into the Strava for Splunk add-on's configuration -> Add-on parameters page.

### New in v3.0: getting second-by-second data for existing and new activities.
Version 3.0.0 introduces the ability to download activity streams from Strava, which contains all your sensor data (e.g. heart rate, cadence, coordinates, distance, altitude, power and others) for your activities.

### Getting FTP & weight into a lookup table
The TA will populate a lookup table named `strava_athlete` with athlete ID, firstname and lastname. If you don't care about FTP or weight, no action is required. If you do want to get FTP and weight, Strava requires additional security permissions (`profile:read_all`) so you will have to get a new access token if you're upgrading from pre-2.6.0 to 2.6.0. Follow step 2 in the detailed instructions, delete your current input and create a new input with a different name and the updated access code. Make sure to put in a starting time that's after your last activity in Splunk to avoid ingesting older activities.

### Troubleshooting
- Logs are in `$SPLUNK_HOME/var/log/splunk/ta_strava_for_splunk_strava_api.log`.
- Most common issue is the access code being invalid or expired. If that's the case, go to step 2 to get a new access code.
- If you want to reindex events, you can either delete the input and create another one with a different name or edit the current one and select the 'reindex data' checkbox, which will reindex the data from the specified starting time.

### Release Notes
v3.0.1
- Added support for activities of up to 9125 days old (~25 years).
- Updated SSL handling of webhook.
- Simplified README

v3.0.0
- Added support for activity streams, which allow for second-by-second analysis of all sensor data in an activity (time, distance, heart rate, power, altitude and more). Requires reindexing data if you want it for activities already in Splunk.
- Removed support for undocumented feature to retrieve raw workout files in favour of the stream support for a universal approach.
- Improved documentation and logging for the webhook input.
- Removed hardcoded host and source inputs to comply with best practices.
- Improved Strava API rate limit handling.
- Python 3 only version, so only supported on Splunk Enterprise 8.0 or later.
- Minor bug fixes & some code clean-up.

v2.6.0
- Added 'strava_athlete' lookup table to store athlete id, firstname, lastname, ftp and weight. 
By default the lookup table will be populated with athlete ID, firstname and lastname. To get FTP and weight, you will have to get a new access token as it requires additional Strava's permissions (`profile:read_all`), so please follow step 2 above which has the updated URL that includes that step.

v2.5.3
- Include efforts for hidden segments when downloading detailed activity.

v2.5.2
- Added option to reindex data from certain timestamp onwards.
- Added 'garminActivityId' field extraction to assist with mapping Garmin Connect workout with Strava activity.
- Added 'strava_id' field alias

v2.5.1
- Removed invalid validation check from 2.5.0, which prevented new installations from working correctly.

v2.5.0
- Added support for webhooks to get notified immediately if activity has been created or modified.
- UI changes to reduce clutter and align with Splunk's new UI.
- Simplified code to reduce complexity.

v2.1.5
- Minor fix to speed up Strava token refresh after expiry.

v2.1.4
- Added check to skip invalid or corrupt activities that get returned from the API.

v2.1.3
- Added support for multiple Strava accounts. Please read the details page before upgrading from v1.x as additional steps are required to avoid reingesting events already in Splunk.
- Improved error messages in case of Strava authentication failures.

v1.2.6
- Added check to skip invalid or corrupt activities that get returned from the API.

v1.2.5
- Made script compatible again with Python 2 & 3, after previous release used a module that was Python 3 only.

v1.2.4a
- Fixed issue where an empty timestamp string and timezone/DST mismatch could result in duplicate events.

v1.2.3
- Cosmetic update to make certain fields required at initial setup.

v1.2.2
- Fixed issue causing duplicate events when server timezone not set to GMT/UTC.

v1.2.0
- Fixed issue that would cause certain events to get indexed twice.

v1.1.3
- Minor bugfixes.

v1.1.2
- Minor bugfixes.

v1.1.1
- Compatible with Python 2 & 3

v1.0
- Added support for retrieving all activities, instead of maximum 200 in earlier versions.
- Added support for activities older than 2,000 days.
- Improved Strava API rate limiting support (max. 600 requests/15 minutes or 30,000/day)

