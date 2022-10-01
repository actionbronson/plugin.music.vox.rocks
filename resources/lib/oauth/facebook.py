from .. import htmlelement as HE
import requests
import datetime
import xbmc

import xml.etree.ElementTree as Etree
from .provider import OAuthProvider
from urllib.parse import urljoin

class FacebookOauthProvider(OAuthProvider):
    def __init__(self, config):
        self.fb_login_config = config
        pass
    
    def get_session(self):
        return self.session

    def __get_facebook_login_form(self, headers: dict, fb_url: str) -> dict:
        xbmc.log("Obtaining facebook login form.", xbmc.LOGINFO)
        resp = self.session.get(fb_url)
        resp.raise_for_status()
        html_doc = HE.fromstring(resp.content)
        #xbmc.log(f"Obtained html doc {html_doc}", xbmc.LOGINFO)
        #xbmc.log(str(Etree.tostring(html_doc)), xbmc.LOGINFO)
        html_login_forms = html_doc.findall('.//form')
        if len(html_login_forms) == 0:
            raise Exception(f"No login forms found on {fb_url}")
        
        html_login_form = html_login_forms[0]
        form_fields = html_login_form.findall(".//input")
        # for field in form_fields:
        #     xbmc.log(f"{field.tag}, {field.attrib}", xbmc.LOGINFO)

        html_form = dict(url=urljoin(fb_url, html_login_form.attrib["action"]),
                    form_fields={field.attrib['name']: field.attrib['value'] for field in form_fields if 'value' in field.attrib})
        xbmc.log(f"HTML form: {html_form}", xbmc.LOGINFO)
        return html_form

    def __get_oauth_response(self, session: requests.Session) -> None:#, ext: str, hash: str):
        fb_url = self.fb_login_config["url"]
        vox_api_key =  self.fb_login_config["api_key"]
        vox_redirect_url = self.fb_login_config["redirect_url"]
        oauth_url = urljoin(fb_url, "/dialog/oauth")
        xbmc.log(f"Requesting OAuth url: {oauth_url}", xbmc.LOGINFO)
        oauth_params = dict(auth_type="rerequest", response_type="code", redirect_uri=vox_redirect_url, scope="email", 
                        client_id=vox_api_key, ret="login", fbapp_pres=0, tp="unspecified", 
                        cbt=datetime.datetime.now().timestamp() * 1000)
        oauth_resp = self.session.get(oauth_url, params=oauth_params, headers=self.fb_login_config['headers'])
        #xbmc.log(session.cookies.values(), xbmc.LOGINFO)
        oauth_resp.raise_for_status()

    def login_provider(self, username: str, password: str, session: requests.Session) -> None:
        self.session = session
        fb_url = self.fb_login_config["url"]
        fb_login_headers = self.fb_login_config['headers']
        xbmc.log(f"Logging in {username} using Facebook {fb_url}.", xbmc.LOGINFO)
        fb_login = self.__get_facebook_login_form(session, fb_url)
        login_response = self.session.post(
                fb_login['url'], 
                {**fb_login['form_fields'], **{"email": username, "pass": password}},
                headers = fb_login_headers)
        login_response.raise_for_status()
        xbmc.log(f"{username} is logged in to Facebook {fb_url}.", xbmc.LOGINFO)
        self.__get_oauth_response(session)
