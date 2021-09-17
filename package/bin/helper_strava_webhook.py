import import_declare_test
import sys

from splunklib import modularinput as smi
from splunktaucclib.modinput_wrapper import base_modinput as ucc


class STRAVA_WEBHOOK(ucc.BaseModInput):

    def __init__(self):
        use_single_instance = True
        super(STRAVA_WEBHOOK, self).__init__("ta_strava_for_splunk", "strava_webhook", use_single_instance)

    def get_scheme(self):
        scheme = super(STRAVA_WEBHOOK, self).get_scheme()
        scheme.description = 'Strava Webhook'
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True

        scheme.add_argument(
            smi.Argument(
                'name',
                title='Name',
                description='Name',
                required_on_create=True
            )
        )

        scheme.add_argument(
            smi.Argument(
                'port',
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                'verify_token',
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                'callback_url',
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                'cert_file',
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                'key_file',
                required_on_create=True,
            )
        )

        return scheme

    def get_app_name(self):
        return "TA-strava-for-splunk"

    def get_account_fields(self):
        account_fields = []
        return account_fields

    def get_checkbox_fields(self):
        checkbox_fields = []
        return checkbox_fields

    def get_global_checkbox_fields(self):
        self.global_checkbox_fields = []
        return self.global_checkbox_fields

    def validate_input(self, definition):
        return

    def collect_events(helper, ew):
        return


if __name__ == '__main__':
    exit_code = STRAVA_WEBHOOK().run(sys.argv)
    sys.exit(exit_code)
