import requests
import xbmc

from .oauth.provider import OAuthProvider


class VoxOAuthLogin(object):
    def __init__(
        self, oauth_provider: OAuthProvider, client_id: str, client_secret: str
    ) -> None:
        self.oauth_provider = oauth_provider
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        pass

    def get_session(self) -> requests.Session:
        return self.session

    def get_bearer_token(self) -> dict:
        return self.vox_oauth_bearer_token

    def login(self, username: str, password: str):
        self.oauth_provider.login_provider(username, password, self.session)
        vox_oauth_code = (
            "https://my.vox.rocks/oauth/authorize/decision/premium?"
            "response_type=code&"
            f"client_id={self.client_id}&"
            "redirect_uri=com.coppertino.voxcloud%3A%2F%2Foauth"
        )
        try:
            xbmc.log(
                f"Trying to obtain VOX OAuth code from url '{vox_oauth_code}'",
                xbmc.LOGINFO,
            )
            premium_oauth_code_resp = self.session.get(
                vox_oauth_code, headers={"Accept": "application/json"}
            )
            premium_oauth_code_resp.raise_for_status()
            xbmc.log(
                f"Obtained VOX Premium OAuth code: '${premium_oauth_code_resp.json()}'",
                xbmc.LOGINFO,
            )
        except requests.exceptions.HTTPError as e:
            xbmc.log(
                f"Could not obtain VOX Premium code with client_id: {self.client_id}.  Check subscription.",
                xbmc.LOGERROR,
            )
            raise e

        data = dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=premium_oauth_code_resp.json()["code"],
            deviceId="Python Client",
            deviceName="Python Client",
            grant_type="authorization_code",
            platform=0,
            redirect_uri="com.coppertino.voxcloud://oauth",
            response_type="token",
        )
        try:
            oauth_token_resp = self.session.post(
                "https://my.vox.rocks/oauth/token", data=data
            )
            oauth_token_resp.raise_for_status()
            self.vox_oauth_bearer_token = oauth_token_resp.json()
            xbmc.log(
                f"Obtained oauth_token_resp: {self.vox_oauth_bearer_token}",
                xbmc.LOGINFO,
            )
            return oauth_token_resp
        except requests.exceptions.HTTPError as e:
            xbmc.log(f"Could not obtain VOX oauth token.", xbmc.LOGERROR)
