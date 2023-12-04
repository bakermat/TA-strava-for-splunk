import sys
import json
import time
import datetime
import calendar
import requests

import helper_strava_api as hsa
import splunklib import client


class StravaApi(hsa.STRAVA_API):
    """Inherits helper_strava_api class and overwrites collect_events() function."""

    def collect_events(helper, ew):  # pylint: disable=no-self-argument,invalid-name,too-many-statements,too-many-branches
        """Main function to get data into Splunk."""

        def clear_checkbox(session_key, stanza):
            """ Sets the 'reindex_data' value in the REST API to 0 to clear it. Splunk then automatically restarts the input."""
            url = f'https://localhost:8089/servicesNS/nobody/TA-strava-for-splunk/data/inputs/strava_api/{stanza}'
            headers = {'Authorization': f'Splunk {session_key}'}
            payload = 'reindex_data=0'
            helper.send_http_request(url, "POST", headers=headers, payload=payload, verify=False, use_proxy=False)

        def get_activities(ts_activity, token):
            """Gets all activities, 30 per page as per Strava's default."""
            headers = {f'Authorization: Bearer {token}'}
            params = {'after': ts_activity}
            url = "https://www.strava.com/api/v3/activities"
            response = return_json(url, "GET", headers=headers, parameters=params)
            return response

        def get_activity(activity, token):
            """Gets specific activity."""
            url = f'https://www.strava.com/api/v3/activities/{activity}?include_all_efforts=true'
            headers = {'Authorization': f'Bearer {token}'}
            response = return_json(url, "GET", headers=headers, timeout=10)
            return response

        def get_activity_stream(token, activity, types, series_type='time', resolution='high'):
            """Gets the activity stream for given activity id."""
            types = ','.join(types)
            url = f'https://www.strava.com/api/v3/activities/{activity}/streams/{types}&series_type={series_type}&resolution={resolution}&key_by_type='
            headers = {'Authorization': f'Bearer {token}'}
            response = return_json(url, "GET", headers=headers, timeout=10)
            return response

        def get_athlete(token):
            """Gets details on currently logged in athlete."""
            url = "https://www.strava.com/api/v3/athlete"
            headers = {'Authorization': f'Bearer {token}'}
            response = return_json(url, "GET", headers=headers, timeout=10)
            return response

        def get_epoch(timestamp):
            """Converts Strava datetime to epoch timestamp"""
            timestamp_dt = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            epoch = calendar.timegm(timestamp_dt.timetuple())
            return epoch

        def get_secret(session_key, key):
            # Retrieve the password from the storage/passwords endpoint
            service = client.connect(token=session_key, app='TA-strava-for-splunk')
            for storage_password in service.storage_passwords:
                if storage_password.username == key:
                    return json.loads(storage_password.content.clear_password)
            return None


        def get_token(client_id, client_secret, token, renewal):
            """Get or refresh access token from Strava API."""
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

        def kvstore_save_athlete(session_key, athlete_id, firstname, lastname, weight, ftp):  # pylint: disable=too-many-arguments
            """Stores athlete's id, first name, last name, weight and ftp into strava_athlete KV Store collection."""
            url = 'https://localhost:8089/servicesNS/nobody/TA-strava-for-splunk/storage/collections/data/strava_athlete/batch_save'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Splunk {session_key}'}
            payload = [{"_key": athlete_id, "id": athlete_id, "firstname": firstname, "lastname": lastname, "fullname": firstname + " " + lastname, "weight": weight, "ftp": ftp}]
            helper.send_http_request(url, "POST", headers=headers, payload=payload, verify=False, use_proxy=False)

        def parse_data(data, activity_id, activity_start_date):
            """Gets raw JSON data, parses it into events and writes those to Splunk."""
            data_dict = {}
            final_dict = {}
            for i in data:
                data_dict[i['type']] = i['data']

            counter = 1
            nrange = len(data_dict['time'])
            for item in range(1, nrange + 1):
                final_dict[item] = {}

            for key, value in data_dict.items():
                counter = 1
                for i in value:
                    final_dict[counter][key] = i
                    final_dict[counter]['activity_id'] = activity_id

                    if 'time' in key:
                        final_dict[counter]['time'] = final_dict[counter]['time'] + activity_start_date
                        final_dict[counter]['time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(final_dict[counter]['time']))

                    if 'latlng' in key:
                        final_dict[counter]['lat'] = final_dict[counter]['latlng'][0]
                        final_dict[counter]['lon'] = final_dict[counter]['latlng'][1]
                        final_dict[counter].pop('latlng')
                    counter += 1

            result_list = [value for key, value in final_dict.items()]

            for event in result_list:
                write_to_splunk(index=helper.get_output_index(), sourcetype='strava:activities:stream', data=json.dumps(event))

            helper.log_info(f'Added activity stream {activity_id} for {athlete_id}.')
            return True

        def return_json(url, method, **kwargs):
            """Gets JSON from URL and parses it for potential error messages."""
            response = helper.send_http_request(url, method, use_proxy=False, **kwargs)

            try:
                response.raise_for_status()
            except requests.HTTPError as ex:
                # status code 429 means we hit Strava's API limit, wait till next 15 minute mark (+5 seconds) and try again
                if ex.response.status_code == 429:
                    # Get the 15m/24h API limits for this user
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
                if ex.response.status_code in (400, 401):
                    helper.log_error(f'{ex.response.status_code} Error: Strava API credentials invalid or session expired. Make sure Client ID & Client Secret have been added to the Configuration -> Add-On Parameters tab and your access code is valid.')
                    sys.exit(1)
                if ex.response.status_code == 404:
                    helper.log_warning(f'404 Error: no stream data for url {url}, can happen for manually added activities.')
                    return False
                if ex.response.status_code == 500:
                    helper.log_warning(f'500 Error: no data received from Strava API for url {url}, it might be corrupt or invalid. Skipping activity.')
                    return False
                # In case there's any other error than the ones described above, log the error and exit.
                helper.log_error(f'Error: {ex}')
                sys.exit(1)

            # Must have been a 200 status code
            return response.json()

        def set_athlete(response):
            """Creates dict with athlete details, including token expiry."""
            name = response['athlete']['firstname'] + " " + response['athlete']['lastname']
            athlete = {
                'id': response['athlete']['id'],
                'name': name,
                'ts_activity': 0}
            return athlete

        def set_athlete_oauth(response):
            """Returns dict with OAuth details."""
            return {
                "access_token": response['access_token'],
                "refresh_token": response['refresh_token'],
                "expires_at": response['expires_at']}

        def store_secret(session_key, key, secret):
            """Stores OAuth details as Splunk encrypted password in 'key' as dict."""
            service = client.connect(token=session_key, app='TA-strava-for-splunk')

            try:
                for storage_password in service.storage_passwords:
                    if storage_password.username == key:
                        service.storage_passwords.delete(username=storage_password.username)
                        break

                storage_secret = service.storage_passwords.create(json.dumps(secret), key)
                return storage_secret

            except Exception as err: # pylint: disable=broad-except
                raise Exception(f'An error occurred updating credentials. Please ensure your user account has admin_all_objects and/or list_storage_passwords capabilities. Details: {err}') from err


        def write_to_splunk(**kwargs):
            """Writes activity to Splunk index."""
            event = helper.new_event(**kwargs)
            ew.write_event(event)

        # get configuration arguments
        client_id = helper.get_global_setting('client_id')
        client_secret = helper.get_global_setting('client_secret')
        access_code = helper.get_arg('access_code')
        start_time = helper.get_arg('start_time') or 0
        types = ['time', 'distance', 'latlng', 'altitude', 'velocity_smooth', 'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']
        expires_at = False

        # stanza is the name of the input. This is a unique name and will be used as a checkpoint key to save/retrieve details about an athlete
        stanza = list(helper.get_input_stanza())[0]
        # helper.log_debug(f'Athlete: {athlete}')

        # Sometimes KV Store isn't ready yet after a Splunk restart causing a TypeError. Wait 15 seconds when that happens and try again.
        try:
            athlete = helper.get_check_point(stanza)
        except Exception as err:
            helper.log_error(f'Error: {err}. Retrying in 15 seconds in case KV Store is not ready yet.')
            time.sleep(15)
            athlete = helper.get_check_point(stanza)

        # Get the OAuth details from the Splunk storage/passwords REST API endpoint
        athlete_oauth = get_secret(helper.context_meta['session_key'], stanza)

        if athlete_oauth:
            access_token = athlete_oauth['access_token']
            refresh_token = athlete_oauth['refresh_token']
            expires_at = athlete_oauth['expires_at']

        # if reindex_data checkbox is set, update the start_time to be the one specified and clear the checkbox.
        if helper.get_arg('reindex_data'):
            if int(helper.get_arg('reindex_data')) == 1:
                athlete.update({'ts_activity': start_time})
                helper.save_check_point(stanza, athlete)
                # the clear_checkbox function will restart this input as soon as the change is made, so no further code required.
                clear_checkbox(helper.context_meta['session_key'], stanza)

        # if athlete is set, get details & tokens - otherwise fetch tokens with get_token()
        if athlete:
            athlete_id = athlete['id']
            athlete_name = athlete['name']
            # If 'access_token' in athlete, it's from a pre-3.2 install. Get its value and remove it, so it can be stored as a Splunk secret and be backwards-compatible.
            if 'access_token' in athlete and not athlete_oauth:
                access_token = athlete['access_token']
                refresh_token = athlete['refresh_token']
                expires_at = athlete['expires_at']
                athlete_oauth = {"access_token": access_token, "refresh_token": refresh_token, "expires_at": expires_at}
                athlete.pop('access_token')
                athlete.pop('refresh_token')
                athlete.pop('expires_at')

        # Check if expires_at token is set and renew token if token expired. Otherwise fetch token with initial access code.
        if expires_at:
            if time.time() >= expires_at:
                response = get_token(client_id, client_secret, refresh_token, renewal=True)
                athlete_oauth = set_athlete_oauth(response)
        else:
            response = get_token(client_id, client_secret, access_code, renewal=False)
            athlete = set_athlete(response)
            athlete_id = athlete['id']
            athlete_name = athlete['name']
            athlete_oauth = set_athlete_oauth(response)

        # Store athlete data in checkpoint and OAuth data in Splunk storage/passwords endpoint
        helper.save_check_point(stanza, athlete)
        store_secret(helper.context_meta['session_key'], stanza, athlete_oauth)

        access_token = athlete_oauth['access_token']
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
            athlete.pop('ts_newest_activity')
            athlete.pop('get_old_activities')
            athlete.pop('ts_oldest_activity')
            helper.save_check_point(stanza, athlete)
        else:
            ts_activity = athlete['ts_activity'] or start_time

        # webhook_updates contains updated activities that came in via webhook.
        webhook_updates = helper.get_check_point('webhook_updates') or {}

        if str(athlete_id) in webhook_updates:
            for activity in webhook_updates[str(athlete_id)][:]:
                helper.log_info(f'Received update via webhook for activity {activity} from athlete {athlete_id}')
                response = get_activity(activity, access_token)
                ts_activity = get_epoch(response['start_date'])

                # Store the event in Splunk
                write_to_splunk(index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=json.dumps(response))

                # Get stream data for this activity and write to Splunk
                stream_data = get_activity_stream(access_token, activity, types)
                if stream_data:
                    parse_data(stream_data, activity, ts_activity)

                # Remove from dict and save dict
                webhook_updates[str(athlete_id)].remove(activity)
                helper.save_check_point('webhook_updates', webhook_updates)
            helper.log_info(f'Got all webhook events for athlete {athlete_id}')

        helper.log_info(f'Checking if there are new activities for {athlete_name} ({athlete_id})')

        while True:

            response_activities = get_activities(ts_activity, access_token)

            # if all activities retrieved, set get_old_activities, save checkpoint and end loop to finish
            if len(response_activities) == 0:  # pylint: disable=no-else-break
                helper.log_info(f'All done, got all activities for {athlete_name} ({athlete_id})')
                break
            else:
                # Get more details from each activity
                for event in response_activities:
                    activity_id = event['id']
                    response = get_activity(activity_id, access_token)

                    # response = False for a 500 Error, which is likely an invalid Strava API file. In that case skip the activity and continue.
                    if response:
                        data = json.dumps(response)

                        # Get start_date (UTC) and convert to UTC timestamp
                        ts_activity = get_epoch(event['start_date'])

                        # Store the event in Splunk
                        write_to_splunk(index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
                        helper.log_info(f'Added activity {activity_id} for {athlete_id}.')

                        # Get stream data for this activity
                        stream_data = get_activity_stream(access_token, activity_id, types)
                        if stream_data:
                            parse_data(stream_data, activity_id, ts_activity)

                        # Save the timestamp of the last event to a checkpoint
                        athlete.update({'ts_activity': ts_activity})
                        helper.save_check_point(stanza, athlete)


if __name__ == '__main__':
    exit_code = StravaApi().run(sys.argv)
    sys.exit(exit_code)
