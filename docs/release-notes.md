####3.0.1####
- Added support for activities of up to 9125 days old (~25 years).
- Updated TLS handling of webhook.
- Cleaned up README and moved documentation to <https://bakermat.github.io/TA-strava-for-splunk>.

####3.0.0####
- Added support for activity streams, which allow for second-by-second analysis of all sensor data in an activity (time, distance, heart rate, power, altitude and more). Requires reindexing data if you want it for activities already in Splunk.
- Removed support for undocumented feature to retrieve raw workout files in favour of the stream support for a universal approach.
- Improved documentation and logging for the webhook input.
- Removed hardcoded host and source inputs to comply with best practices.
- Improved Strava API rate limit handling.
- Python 3 only version, so only supported on Splunk Enterprise 8.0 or later.
- Minor bug fixes & some code clean-up.

####2.6.0####
- Added 'strava_athlete' lookup table to store athlete id, firstname, lastname, ftp and weight. 
By default the lookup table will be populated with athlete ID, firstname and lastname. To get FTP and weight, you will have to get a new access token as it requires additional Strava's permissions (`profile:read_all`).

####2.5.3####
- Include efforts for hidden segments when downloading detailed activity.

####2.5.2####
- Added option to reindex data from certain timestamp onwards.
- Added `garminActivityId` field extraction to assist with mapping Garmin Connect workout with Strava activity.
- Added `strava_id` field alias

####2.5.1####
- Removed invalid validation check from 2.5.0, which prevented new installations from working correctly.

####2.5.0####
- Added support for webhooks to get notified immediately if activity has been created or modified.
- UI changes to reduce clutter and align with Splunk's new UI.
- Simplified code to reduce complexity.

####2.1.5####
- Minor fix to speed up Strava token refresh after expiry.

####2.1.4####
- Added check to skip invalid or corrupt activities that get returned from the API.

####2.1.3####
- Added support for multiple Strava accounts. Please read the details page before upgrading from 1.x as additional steps are required to avoid reingesting events already in Splunk.
- Improved error messages in case of Strava authentication failures.

####1.2.6####
- Added check to skip invalid or corrupt activities that get returned from the API.

####1.2.5####
- Made script compatible again with Python 2 & 3, after previous release used a module that was Python 3 only.

####1.2.4a####
- Fixed issue where an empty timestamp string and timezone/DST mismatch could result in duplicate events.

####1.2.3####
- Cosmetic update to make certain fields required at initial setup.

####1.2.2####
- Fixed issue causing duplicate events when server timezone not set to GMT/UTC.

####1.2.0####
- Fixed issue that would cause certain events to get indexed twice.

####1.1.3####
- Minor bugfixes.

####1.1.2####
- Minor bugfixes.

####1.1.1####
- Compatible with Python 2 & 3

####1.0####
- Added support for retrieving all activities, instead of maximum 200 in earlier versions.
- Added support for activities older than 2,000 days.
- Improved Strava API rate limiting support (max. 600 requests/15 minutes or 30,000/day)