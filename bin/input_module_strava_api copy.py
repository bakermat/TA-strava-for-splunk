# encoding = utf-8

import sys
import time
import datetime
import calendar
import json
import requests

import exec_anaconda
exec_anaconda.exec_anaconda()

# Gracefully handle missing pandas module
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def collect_events(helper, ew):
    """Main function to get data into Splunk"""

    def split_lat(series):
        """Return latitude for series."""
        lat = series[0]
        return lat

    def split_long(series):
        """Return longitude for series."""
        long = series[1]
        return long

    def get_start_time(activity, token):
        params = {'access_token': token}
        url = f'https://www.strava.com/api/v3/activities/{activity}'
        response = return_json(url, 'GET', parameters=params, timeout=10)
        start_date = response['start_date']
        time_format = '%Y-%m-%dT%H:%M:%SZ'
        start_date = int(datetime.datetime.strptime(start_date, time_format).timestamp())
        return start_date

    def get_activity(activity, token):
        """Gets specific activity"""
        url = f'https://www.strava.com/api/v3/activities/{activity}?include_all_efforts=true'
        params = {'access_token': token}
        response = return_json(url, "GET", parameters=params, timeout=10)
        return response

    def clear_checkbox(session_key, stanza):
        """ Sets the 'reindex_data' value in the REST API to 0 to clear it. Splunk then automatically restarts the input."""
        url = f'https://localhost:8089/servicesNS/nobody/TA-strava-for-splunk/data/inputs/strava_api/{stanza}'
        headers = {'Authorization': f'Splunk {session_key}'}
        payload = 'reindex_data=0'
        helper.send_http_request(url, "POST", headers=headers, payload=payload, verify=False)

    def get_activities(ts_activity, access_token):
        """Gets all activities, 30 per page as per Strava's default. """
        params = {'after': ts_activity, 'access_token': access_token}
        url = "https://www.strava.com/api/v3/activities"
        response = return_json(url, "GET", parameters=params)
        return response

    def get_activity_stream(token, activity, types, series_type='time', resolution='high'):
        types = ','.join(types)
        params = {'access_token': token}
        url = f'https://www.strava.com/api/v3/activities/{activity}/streams/{types}&series_type={series_type}&resolution={resolution}&key_by_type='
        response = return_json(url, "GET", parameters=params, timeout=10)
        return response

    def get_athlete(token):
        """Gets details on currently logged in athlete"""
        url = "https://www.strava.com/api/v3/athlete"
        params = {'access_token': token}
        response = return_json(url, "GET", parameters=params, timeout=10)
        return response

    def kvstore_save_athlete(session_key, athlete_id, firstname, lastname, weight, ftp):
        """ Stores athlete's id, first name, last name, weight and ftp into strava_athlete KV Store collection."""
        url = 'https://localhost:8089/servicesNS/nobody/TA-strava-for-splunk/storage/collections/data/strava_athlete/batch_save'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Splunk {session_key}'}
        payload = [{"_key": athlete_id, "id": athlete_id, "firstname": firstname, "lastname": lastname, "weight": weight, "ftp": ftp}]
        helper.send_http_request(url, "POST", headers=headers, payload=payload, verify=False)

    def parse_data(data, types, activity_id, activity_start_date):
        data_dict = {}

        for i in data:
            data_dict[i['type']] = i['data']

        df = pd.DataFrame()

        helper.log_debug(f'Activity {activity_id} types: {data_dict.keys()}')

        for item in types:
            if item in data_dict.keys():
                df[item] = pd.Series(data_dict[item])
                pd.to_datetime(1490195805, unit='s')

        df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%dT%H:%M:%S%Z',unit='s')
        #epoch = int(df['time'])
        #2019-10-12T07:20:50.52Z
        #2017-05-08T19:25:19Z
        #df['proper_time'] = time.strftime('%Y-%M-%dT%H:%M:%SZ', time.gmtime(epoch))
        df['activity_id'] = activity_id
        if 'latlng' in df:
            df['lat'] = list(map(split_lat, (df['latlng'])))
            df['lon'] = list(map(split_long, (df['latlng'])))
            df.drop(['latlng'], axis=1, inplace=True)

        # result = df.to_json(orient='records', lines=True)
        result = df.to_json(orient='records', lines=True)
        #result_json = json.loads(result)
        #result_json = json.dumps(result_json)
        return result

    def get_token(client_id, client_secret, token, renewal):
        """Get or refresh access token from Strava API"""
        url = "https://www.strava.com/api/v3/oauth/token"

        if renewal:
            payload = {
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': token,
                'grant_type': 'refresh_token'}
            message = "Successfully refreshed Strava token."
        else:
            payload = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': token,
                'grant_type': 'authorization_code'}
            message = "Successfully authenticated with Strava using access code."

        response = return_json(url, "POST", payload=payload)

        helper.log_info(message)

        return response

    def return_json(url, method, **kwargs):
        """Gets JSON from URL and parses it for potential error messages."""
        response = helper.send_http_request(url, method, use_proxy=False, **kwargs)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            # status code 429 means we hit Strava's API limit, wait till next 15 minute mark (+5 seconds) and try again
            if e.response.status_code == 429:
                # Get the API limits for this user
                helper.log_info(response.headers)
                api_usage_15m = response.headers['X-RateLimit-Usage'].split(",")[0]
                api_usage_24h = response.headers['X-RateLimit-Usage'].split(",")[1]
                api_limit_15m = response.headers['X-RateLimit-Limit'].split(",")[0]
                api_limit_24h = response.headers['X-RateLimit-Limit'].split(",")[1]

                timestamp_now = int(time.time())
                modulus_time = timestamp_now % 900
                sleepy_time = 0 if modulus_time == 0 else (900 - modulus_time + 5)
                helper.log_warning(f'Strava API rate limit hit. Used {api_usage_15m}/15min (limit {api_limit_15m}), {api_usage_24h}/24h (limit {api_limit_24h}). Sleeping for {sleepy_time} seconds.')
                time.sleep(sleepy_time)
                response = return_json(url, method, **kwargs)
                helper.log_debug(f'429 detail: {response}')
                return response
            elif e.response.status_code == 400 or e.response.status_code == 401:
                helper.log_error('Strava API credentials invalid or session expired. If issue persists, make sure Client ID & Client Secret have been added to the Configuration -> Add-On Parameters tab and your access code & timestamp are valid.')
                sys.exit(1)
            elif e.response.status_code == 404:
                helper.log_warning(f'404 Error: likely no stream data for activity {url}')
                return False
            elif e.response.status_code == 500:
                helper.log_warning(f'500 Error: no data received from Strava API for url {url}, it might be corrupt or invalid. Skipping activity.')
                return False
            else:
                helper.log_error(f'Error: {e}')
                sys.exit(1)

        # Must have been a 200 status code
        return response.json()

    def set_athlete(response):
        """Creates dict with athlete details, including token expiry"""
        name = response['athlete']['firstname'] + " " + response['athlete']['lastname']
        athlete = {
            'id': response['athlete']['id'],
            'name': name,
            'access_token': response['access_token'],
            'refresh_token': response['refresh_token'],
            'expires_at': response['expires_at'],
            'ts_activity': 0}
        return athlete

    def write_to_splunk(**kwargs):
        event = helper.new_event(**kwargs)
        ew.write_event(event)

    # set Splunk host
    # host = "strava_for_splunk"

    # get configuration arguments
    client_id = helper.get_global_setting('client_id')
    client_secret = helper.get_global_setting('client_secret')
    access_code = helper.get_arg('access_code')
    start_time = helper.get_arg('start_time') or 0

    # stanza is the name of the input. This is a unique name and will be used as a checkpoint key to save/retrieve details about an athlete
    stanza = list(helper.get_input_stanza())[0]
    athlete = helper.get_check_point(stanza)
    helper.log_debug('Athlete: {athlete}')

    # if reindex_data checkbox is set, update the start_time to be the one specified and clear the checkbox.
    if helper.get_arg('reindex_data'):
        athlete.update({'ts_activity': start_time})
        helper.save_check_point(stanza, athlete)
        # the clear_checkbox function will restart this input as soon as the change is made, so no further code required.
        clear_checkbox(helper.context_meta['session_key'], stanza)

    # if athlete is set, get details & tokens - otherwise fetch tokens with get_token()
    if athlete:
        athlete_id = athlete['id']
        athlete_name = athlete['name']
        expires_at = athlete['expires_at']
        refresh_token = athlete['refresh_token']
    else:
        expires_at = ""
        refresh_token = ""

    # Check if expires_at token is set and renew token if token expired. Otherwise fetch token with initial access code.
    if expires_at:
        if time.time() >= expires_at:
            response = get_token(client_id, client_secret, refresh_token, renewal=True)
            helper.log_debug(f"Access token: {response['access_token']}, refresh token: {response['refresh_token']}")
            athlete.update({'access_token': response['access_token'], 'refresh_token': response['refresh_token'], 'expires_at': response['expires_at']})
    else:
        response = get_token(client_id, client_secret, access_code, renewal=False)
        athlete = set_athlete(response)
        athlete_id = athlete['id']
        athlete_name = athlete['name']

    helper.save_check_point(stanza, athlete)

    access_token = athlete['access_token']
    athlete_detail = get_athlete(access_token)
    athlete_firstname = athlete_detail['firstname']
    athlete_lastname = athlete_detail['lastname']
    athlete_weight = ''
    athlete_ftp = ''
    if athlete_detail['resource_state'] == 3:
        athlete_weight = athlete_detail['weight']
        athlete_ftp = athlete_detail['ftp']

    helper.log_debug("Saving athlete's details to KV Store.")
    kvstore_save_athlete(helper.context_meta['session_key'], str(athlete_id), athlete_firstname, athlete_lastname, str(athlete_weight), str(athlete_ftp))

    # For backwards compatibility with upgrades from pre-2.5.0, which uses athlete['ts_newest_activity']. If there, clean them up.
    if 'ts_newest_activity' in athlete:
        helper.log_info(f"Found existing timestamp {athlete['ts_newest_activity']}! Will remove it now.")
        ts_activity = athlete['ts_newest_activity']
        athlete.update({'ts_activity': ts_activity})
        del athlete['ts_newest_activity']
        del athlete['get_old_activities']
        del athlete['ts_oldest_activity']
        helper.save_check_point(stanza, athlete)
    else:
        ts_activity = athlete['ts_activity'] or start_time

    # webhook_updates contains updated activities that came in via webhook.
    webhook_updates = helper.get_check_point("webhook_updates") or {}

    if str(athlete_id) in webhook_updates:
        for activity in webhook_updates[str(athlete_id)][:]:
            helper.log_info(f'Received update via webhook for activity {activity} from athlete {athlete_id}')
            response = get_activity(activity, access_token)

            # Store the event in Splunk
            write_to_splunk(index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=json.dumps(response))

            # Remove from dict and save dict
            webhook_updates[str(athlete_id)].remove(activity)
            helper.save_check_point("webhook_updates", webhook_updates)

    helper.log_info(f'Checking if there are new activities for {athlete_name} ({athlete_id})')

    types = ['time', 'distance', 'latlng', 'altitude', 'velocity_smooth', 'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']

    while True:

        download_tcx_id = helper.get_check_point("download_tcx_id") or {}
        if athlete_id not in download_tcx_id:
            download_tcx_id[athlete_id] = []

        response_activities = get_activities(ts_activity, access_token)

        # if all activities retrieved, set get_old_activities, save checkpoint and end loop to finish
        if len(response_activities) == 0:
            helper.log_info(f'All done, got all activities for {athlete_name} ({athlete_id})')
        else:
            # Get more details from each activity
            for event in response_activities:
                activity_id = event['id']
                response = get_activity(activity_id, access_token)

                # response = False for a 500 Error, which is likely an invalid Strava API file. In that case skip the activity and continue.
                if not response:
                    continue
                else:
                    data = json.dumps(response)
                    helper.log_info(f'Retrieved activity {activity_id} for {athlete_id}')

                    # Get start_date (UTC) and convert to UTC timestamp
                    timestamp = event['start_date']
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                    ts_activity = calendar.timegm(dt.timetuple())
                    ts_activity = int(ts_activity)

                    # Store the event in Splunk
                    write_to_splunk(index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)

                    # Get stream data for this activity
                    if HAS_PANDAS:
                        stream_data = get_activity_stream(access_token, activity_id, types)
                        if stream_data:
                            parsed_data = parse_data(stream_data, types, activity_id, ts_activity)
                            helper.log_info("DATA")
                            helper.log_info(parsed_data)
                            write_to_splunk(index=helper.get_output_index(), sourcetype='strava:activities:stream', data=parsed_data)
                            helper.log_info(f'Added activity stream {activity_id} to Splunk')
                    else:
                        # If not HAS_PANDAS, append checkpoint that tracks which streams need to be downloaded in case PSC gets installed at a later date.
                        download_tcx_id[athlete_id].append(activity_id)
                        helper.save_check_point("download_tcx_id", download_tcx_id)

                    # Save the timestamp of the last event to a checkpoint
                    athlete.update({'ts_activity': ts_activity})
                    helper.save_check_point(stanza, athlete)

    if HAS_PANDAS:
        # Users upgrading from < 3.0 will have 'old' activities to download, so instead of doing it for one activity (as above) this will download streams for old activities.
        # When done, the 'download_tcx_id' checkpoint should be empty and this block will be redundant.
        list_activities = helper.get_check_point("download_tcx_id") or {}

        athlete_id = str(athlete_id)
        if athlete_id in list_activities:
            for activity_id in list_activities[athlete_id][:]:
                # Additional API call to get the start date of the activity, needs to be included in the stream data.
                activity_start_date = get_start_time(activity_id, access_token)
                helper.log_info(f'Getting stream for activity {activity_id}')
                stream_data = get_activity_stream(access_token, activity_id, types)
                if stream_data:
                    parsed_data = parse_data(stream_data, types, activity_id, activity_start_date)
                    write_to_splunk(index=helper.get_output_index(), sourcetype='strava:activities:stream', data=parsed_data)
                    helper.log_info(f'Added activity stream for activity {activity_id} to Splunk')
                else:
                    helper.log_info(f'No activity stream for activity {activity_id}')
                list_activities[athlete_id].remove(activity_id)
                helper.save_check_point("download_tcx_id", list_activities)
