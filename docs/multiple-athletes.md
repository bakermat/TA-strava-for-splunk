Version 2.0 added support for multiple athletes, which allows you to build dashboards or leaderboards and compare yourself against others. Fortunately it's very easy to setup:

1. The Splunk Admin is the only one that has to create an app, as per the steps in [Getting Started](getting-started.md).
2. The Splunk Admin then configures the `Client ID` and `Client Secret` in the Strava for Splunk app.
3. To each athlete they want to get the data from, the Splunk Admin sends the OAuth link, e.g. <https://www.strava.com/oauth/authorize?client_id=123456890&redirect_uri=http://localhost&response_type=code&scope=activity:read_all,profile:read_all>. **Make sure to change the Client ID to the one configured in step 2**.
4. Once the user authorizes your app to read their data, they are presented with a URL with an access code. They will have to send the Splunk Admin the access code, or add it themselves as an input as described in the [Setup section](setup/activities.md) if they have those permissions.
5. You're all set!

> **_NOTE:_**  In the example above, the redirect URL is set to `localhost` meaning that a user going to that URL will only see the code in his own browser's address bar. If you create a web page or service to automatically capture this for a better user experience, make sure to change the `redirect_url` and `Authorization Callback Domain` in the Strava API settings page to reflect that.
