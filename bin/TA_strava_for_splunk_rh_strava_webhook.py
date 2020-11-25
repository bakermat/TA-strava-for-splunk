
import ta_strava_for_splunk_declare

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunk_aoblib.rest_migration import ConfigMigrationHandler

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'interval',
        required=True,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""^\-[1-9]\d*$|^\d*$""", 
        )
    ), 
    field.RestField(
        'index',
        required=True,
        encrypted=False,
        default='default',
        validator=validator.String(
            min_len=1, 
            max_len=80, 
        )
    ), 
    field.RestField(
        'port',
        required=True,
        encrypted=False,
        default='4443',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'verify_token',
        required=True,
        encrypted=False,
        default='sTr4va',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'callback_url',
        required=True,
        encrypted=False,
        default='https://webhook.mywebsite.com:4443',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'cert_file',
        required=True,
        encrypted=False,
        default='/opt/splunk/etc/auth/YOUR_DIR/fullchain.pem',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'key_file',
        required=True,
        encrypted=False,
        default='/opt/splunk/etc/auth/YOUR_DIR/privkey.pem',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 

    field.RestField(
        'disabled',
        required=False,
        validator=None
    )

]
model = RestModel(fields, name=None)



endpoint = DataInputModel(
    'strava_webhook',
    model,
)


if __name__ == '__main__':
    admin_external.handle(
        endpoint,
        handler=ConfigMigrationHandler,
    )
