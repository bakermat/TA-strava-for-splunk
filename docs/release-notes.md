#### 3.1.0
- Added a custom command `weather` in order to get a 3-hour weather report for a location. Returns coordinates, weather description, temperature and wind degrees & speed. Requires an OpenWeatherMap API key to be added under Configuration -> Add-On Settings.
- Added a panel in the Sample Dashboard to leverage the `weather` command, showing which completed segments within ~5 miles/~8 kilometres currently have a tailwind.
- Added a `strava_segments` KV Store lookup with details of each segment, along with a total count of each segment and the direction of the segment (text and degrees). A saved search populates the lookup daily at 3am.
- Removed deprecated references to TCX files in sample dashboard and replaced it with code based on `strava:activities:stream` sourcetype.
- Migrated the app to Splunk's UCC Framework.
- Updated logos to high-res versions.

#### 3.0.2
- Added `fullname` to `strava_athlete` KV Store lookup and made it an automatic lookup, adding the `firstname, lastname, fullname` fields.
- Added `strava_types.csv` CSV lookup (automatic) for prettier activity types, e.g. the `VirtualRide` type becomes `Virtual Ride` using a new `type_full` field for backwards-compatibility.
- Added `strava_index` macro, which is set to `index=strava` by default.
- Updated the Sample Dashboard to improve search efficiency.

#### 3.0.1
- Added support for activities of up to 9125 days old (~25 years).
- Updated TLS handling of webhook.
- Cleaned up README and moved documentation to <https://bakermat.github.io/TA-strava-for-splunk>.

#### 3.0.0
- Added support for activity streams, which allow for second-by-second analysis of all sensor data in an activity (time, distance, heart rate, power, altitude and more). Requires reindexing data if you want it for activities already in Splunk.
- Removed support for undocumented feature to retrieve raw workout files in favour of the stream support for a universal approach.
- Improved documentation and logging for the webhook input.
- Removed hardcoded host and source inputs to comply with best practices.
- Improved Strava API rate limit handling.
- Python 3 only version, so only supported on Splunk Enterprise 8.0 or later.
- Minor bug fixes & some code clean-up.

#### 2.6.0
- Added 'strava_athlete' lookup table to store athlete id, firstname, lastname, ftp and weight. 
By default the lookup table will be populated with athlete ID, firstname and lastname. To get FTP and weight, you will have to get a new access token as it requires additional Strava's permissions (`profile:read_all`).

#### 2.5.3
- Include efforts for hidden segments when downloading detailed activity.

#### 2.5.2
- Added option to reindex data from certain timestamp onwards.
- Added `garminActivityId` field extraction to assist with mapping Garmin Connect workout with Strava activity.
- Added `strava_id` field alias

#### 2.5.1
- Removed invalid validation check from 2.5.0, which prevented new installations from working correctly.

#### 2.5.0
- Added support for webhooks to get notified immediately if activity has been created or modified.
- UI changes to reduce clutter and align with Splunk's new UI.
- Simplified code to reduce complexity.

#### 2.1.5
- Minor fix to speed up Strava token refresh after expiry.

#### 2.1.4
- Added check to skip invalid or corrupt activities that get returned from the API.

#### 2.1.3
- Added support for multiple Strava accounts. Please read the details page before upgrading from 1.x as additional steps are required to avoid reingesting events already in Splunk.
- Improved error messages in case of Strava authentication failures.

#### 1.2.6
- Added check to skip invalid or corrupt activities that get returned from the API.

#### 1.2.5
- Made script compatible again with Python 2 & 3, after previous release used a module that was Python 3 only.

#### 1.2.4a
- Fixed issue where an empty timestamp string and timezone/DST mismatch could result in duplicate events.

#### 1.2.3
- Cosmetic update to make certain fields required at initial setup.

#### 1.2.2
- Fixed issue causing duplicate events when server timezone not set to GMT/UTC.

#### 1.2.0
- Fixed issue that would cause certain events to get indexed twice.

#### 1.1.3
- Minor bugfixes.

#### 1.1.2
- Minor bugfixes.

#### 1.1.1
- Compatible with Python 2 & 3

#### 1.0
- Added support for retrieving all activities, instead of maximum 200 in earlier versions.
- Added support for activities older than 2,000 days.
- Improved Strava API rate limiting support (max. 600 requests/15 minutes or 30,000/day)