import xbmc


class VoxAccess(object):
    def __init__(self, session, vox_bearer_token):
        self.vox_bearer_token = vox_bearer_token
        xbmc.log(str(vox_bearer_token), xbmc.LOGINFO)
        self.access_token = vox_bearer_token["access_token"]
        self.user_id = vox_bearer_token["userId"]
        self.session = session

    def headers(self):
        return {
            "Authorization": self.access_token,
            "User-Agent": "Loop/0.15 (Mac OS X Version 12.1 (Build 21C52))",
            "x-api-version": "2",
        }
