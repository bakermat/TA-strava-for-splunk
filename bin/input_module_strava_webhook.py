# encoding = utf-8

try:
    # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urlparse import parse_qs, urlparse
except ImportError:
    # Python 3
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse
    unicode = str

import json
import ssl
import requests
from threading import Thread


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    pass


def collect_events(helper, ew):

    # This class will handles any incoming request from the browser
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

        session_key = helper.context_meta['session_key']
        host = 'strava_for_splunk'

        def handle_request(self):
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

                helper.log_info("Incoming POST from {}: {}".format(self.client_address[0], message))

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
                    helper.log_debug("webhooks_updates checkpoint: {}".format(helper.get_check_point("webhook_updates")))

                # Send data to Splunk
                data = json.dumps(message)
                event = helper.new_event(source=helper.get_input_type(), host=self.host, index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
                ew.write_event(event)

                # Strava API expects a 200 response
                self.write_empty_response(200)

                # Restart strava_api inputs to pull in the data unless it's a delete, as the input doesn't do anything with that anyway.
                if aspect_type != 'delete':
                    self.restart_input('strava_api', self.session_key)
                    helper.log_info("Reloading Strava API input to retrieve updated activity {} for athlete {}.".format(object_id, owner_id))

            except Exception as e:
                helper.log_error("Something went wrong in handle request: {}".format(e))

        def do_GET(self):
            parsedURL = urlparse(self.path)
            parsed_query = parse_qs(parsedURL.query)

            helper.log_info("Incoming request from {} - {}".format(self.client_address[0], self.path, parsed_query))

            # Strava webhook expects a reply with the hub.challenge parameter
            challenge = parsed_query['hub.challenge'][0]
            request_verify_token = parsed_query['hub.verify_token'][0]

            # Respond with hub.challenge parameter if verify_token is correct
            if request_verify_token == verify_token:
                self.write_response(200, {"hub.challenge": challenge})
            else:
                self.write_empty_response(400)

        def do_POST(self):
            self.handle_request()

        def restart_input(self, input, session_key):
            rest_url = 'https://localhost:8089/services/data/inputs/{}/_reload'.format(input)
            headers = {'Authorization': 'Splunk {}'.format(session_key)}

            r = requests.get(rest_url, headers=headers, verify=False)
            try:
                r.raise_for_status()
            except Exception as e:
                helper.log_error("Something went wrong in input function: {}".format(e))

        def write_response(self, status_code, json_body):
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.write_json(json_body)

        def write_empty_response(self, status_code):
            self.send_response(status_code)
            self.end_headers()

        def write_json(self, json_dict):
            content = json.dumps(json_dict)

            if isinstance(content, unicode):
                content = content.encode('utf-8')

            self.wfile.write(content)

    def create_webhook(client_id, client_secret, verify_token, callback_url):
        url = 'https://www.strava.com/api/v3/push_subscriptions'
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'verify_token': verify_token,
            'callback_url': callback_url}
        response = helper.send_http_request(url, "POST", payload=payload, use_proxy=False)

        try:
            response.raise_for_status()
        except Exception as e:
            if 'already exists' in response.text:
                return get_webhook(client_id, client_secret)
            elif 'GET to callback URL does not return 200':
                helper.log_error("Error: Strava can't reach {}.".format(callback_url))
                return response.json()
        else:
            return "Webhook created: {}".format(response.json)

    def get_webhook(client_id, client_secret):
        url = 'https://www.strava.com/api/v3/push_subscriptions'
        params = {
            'client_id': client_id,
            'client_secret': client_secret}
        response = helper.send_http_request(url, "GET", parameters=params, use_proxy=False)

        try:
            response.raise_for_status()
        except Exception as e:
            helper.log_error("Something went wrong: {}".format(e))
            return False
        else:
            return response.json()

    port = int(helper.get_arg('port'))
    verify_token = helper.get_arg('verify_token')
    cert_file = helper.get_arg('cert_file')
    callback_url = helper.get_arg('callback_url')
    key_file = helper.get_arg('key_file')
    client_id = helper.get_global_setting('client_id')
    client_secret = helper.get_global_setting('client_secret')

    httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=key_file, certfile=cert_file, server_side=True)

    helper.log_info('Starting HTTPS web server on port {}'.format(port))
    thread = Thread(target=httpd.serve_forever)
    thread.start()

    get_webhook = get_webhook(client_id, client_secret)
    if not get_webhook:
        response = create_webhook(client_id, client_secret, verify_token, callback_url)
        helper.log_info(response)
    else:
        helper.log_info("Existing webhook: {}".format(get_webhook))
