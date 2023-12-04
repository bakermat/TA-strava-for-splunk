import sys
import json
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from threading import Thread
import requests

import helper_strava_webhook as hsw

unicode = str  # pylint: disable=invalid-name


class StravaWebhook(hsw.STRAVA_WEBHOOK):
    """Inherits helper_strava_api class and overwrites collect_events() function."""

    def collect_events(helper, ew):  # pylint: disable=no-self-argument,invalid-name,too-many-statements
        """Main function to get webhook data into Splunk"""

        class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
            """Handles incoming requests from the browser"""

            SESSION_KEY = helper.context_meta['session_key']
            SSL_VERIFY = False

            def handle_request(self):
                """Parses incoming POST, saves as checkpoint and sends data to Splunk"""
                try:
                    content_type = self.headers.get('content-type')

                    if content_type != 'application/json':
                        self.write_empty_response(400)
                        return

                    content_len = int(self.headers.get('content-length', 0))

                    # If content was provided, then parse it
                    if content_len > 0:
                        message = json.loads(self.rfile.read(content_len))
                    else:
                        self.write_empty_response(400)
                        return

                    helper.log_info(f'Incoming POST from {self.client_address[0]}: {message}')

                    aspect_type = message['aspect_type']
                    object_id = message['object_id']
                    object_type = message['object_type']
                    # make owner_id a str to avoid issues with athlete_checkpoint dict
                    owner_id = str(message['owner_id'])

                    athlete_checkpoint = helper.get_check_point("webhook_updates") or {}

                    # We only care about activity updates. New activities are pulled in automatically as strava_api input restarts.
                    if aspect_type == 'update' and object_type == 'activity':
                        if owner_id not in athlete_checkpoint:
                            athlete_checkpoint[owner_id] = []
                            athlete_checkpoint[owner_id].append(object_id)
                            helper.save_check_point("webhook_updates", athlete_checkpoint)
                        else:
                            athlete_checkpoint[owner_id].append(object_id)
                            helper.save_check_point("webhook_updates", athlete_checkpoint)
                        helper.log_debug(f'webhooks_updates checkpoint: {helper.get_check_point("webhook_updates")}')

                    # Send data to Splunk
                    data = json.dumps(message)
                    event = helper.new_event(source=helper.get_input_type(), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
                    ew.write_event(event)

                    # Strava API expects a 200 response
                    self.write_empty_response(200)

                    # Restart strava_api inputs to pull in the data unless it's a delete, as the input doesn't do anything with that anyway.
                    if aspect_type != 'delete':
                        self.restart_input('strava_api', self.SESSION_KEY)
                        helper.log_info(f'Reloading Strava API input to retrieve updated activity {object_id} for athlete {owner_id}.')

                except Exception as ex:
                    helper.log_error(f'Something went wrong in handle request: {ex}')

            def do_GET(self):  # pylint: disable=invalid-name
                """Responds to incoming GET request from Strava with challenge token"""
                parsed_url = urlparse(self.path)
                parsed_query = parse_qs(parsed_url.query)

                helper.log_info(f'Incoming request from {self.client_address[0]} - {self.path}')

                # Strava webhook expects a reply with the hub.challenge parameter
                challenge = parsed_query['hub.challenge'][0]
                request_verify_token = parsed_query['hub.verify_token'][0]

                # Respond with hub.challenge parameter if verify_token is correct
                if request_verify_token == verify_token:
                    self.write_response(200, {"hub.challenge": challenge})
                else:
                    self.write_empty_response(400)

            def do_POST(self):  # pylint: disable=invalid-name
                """Used for incoming POST request"""
                self.handle_request()

            def restart_input(self, modinput, session_key):
                """Restarts modinput, used to trigger the Strava Activities input to pull in update."""
                rest_url = f'https://localhost:8089/services/data/inputs/{modinput}/_reload'
                headers = {'Authorization': f'Splunk {session_key}'}

                response = requests.get(rest_url, headers=headers, verify=self.SSL_VERIFY)
                try:
                    response.raise_for_status()
                except Exception as ex:
                    helper.log_error(f'Something went wrong in input function: {ex}')

            def write_response(self, status_code, json_body):
                """Craft response header with status code and json_body"""
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.write_json(json_body)

            def write_empty_response(self, status_code):
                """Craft empty response with status code."""
                self.send_response(status_code)
                self.end_headers()

            def write_json(self, json_dict):
                """Write json_dict to string and encode it."""
                content = json.dumps(json_dict)

                if isinstance(content, unicode):
                    content = content.encode('utf-8')

                self.wfile.write(content)

        def create_webhook(client_id, client_secret, verify_token, callback_url):
            """Creates webhook, raises error if one already exists"""
            url = 'https://www.strava.com/api/v3/push_subscriptions'
            payload = {
                'client_id': client_id,
                'client_secret': client_secret,
                'verify_token': verify_token,
                'callback_url': callback_url}
            response = helper.send_http_request(url, "POST", payload=payload, use_proxy=False)

            try:
                response.raise_for_status()
            except Exception:
                if 'already exists' in response.text:
                    webhook_details = get_webhook(client_id, client_secret)
                    helper.log_info(webhook_details)
                if 'GET to callback URL does not return 200' in response.text:
                    helper.log_error(f'Error: Strava can\'t reach {callback_url}')
                if 'not verifiable' in response.text:
                    helper.log_error(f'Error: Strava can\'t verify {callback_url}. URL incorrect or server not using public CA certificate.')
                else:
                    helper.log_error(f'{response.status_code} Error: {response.text}')
            else:
                response = response.json()
                helper.log_info(f"Webhook created successfully: ID {response['id']}")

        def get_webhook(client_id, client_secret):
            """Gets webhook details"""
            url = 'https://www.strava.com/api/v3/push_subscriptions'
            payload = {
                'client_id': client_id,
                'client_secret': client_secret}
            response = helper.send_http_request(url, "GET", payload=payload, use_proxy=False)

            try:
                response.raise_for_status()
            except Exception as ex:
                helper.log_error(f'Something went wrong: {ex}')
                return False
            else:
                return response.json()

        # Get global arguments
        stanza = list(helper.get_input_stanza())[0]
        dict_port = helper.get_arg('port')
        port = int(dict_port[stanza])
        verify_token = helper.get_arg('verify_token')[stanza]
        cert_file = helper.get_arg('cert_file')[stanza]
        callback_url = helper.get_arg('callback_url')[stanza]
        key_file = helper.get_arg('key_file')[stanza]
        client_id = helper.get_global_setting('client_id')
        client_secret = helper.get_global_setting('client_secret')

        # Setup HTTP Server instance
        try:
            httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
            sslctx = ssl.SSLContext()
            sslctx.check_hostname = False
            sslctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
            httpd.socket = sslctx.wrap_socket(httpd.socket, server_side=True)
        except Exception as err:
            helper.log_error(err)
            raise

        helper.log_info(f'Starting HTTPS web server on port {port}.')
        thread = Thread(target=httpd.serve_forever)
        thread.start()

        # Get webhook details. If it doesn't exist, create it.
        get_webhook = get_webhook(client_id, client_secret)
        if get_webhook:
            helper.log_info(f'Existing webhook: {get_webhook}')
        else:
            create_webhook(client_id, client_secret, verify_token, callback_url)


if __name__ == '__main__':
    exit_code = StravaWebhook().run(sys.argv)
    sys.exit(exit_code)
