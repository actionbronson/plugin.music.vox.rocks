import datetime
import xbmc


class VoxLibraryDetails(object):
    def __init__(self, session):
        self.session = session
        details = self._get_details()
        self.expiration_date = datetime.datetime.fromtimestamp(
            details["userSubscriptionExpiration"]
        )
        self.is_apple = details["isAppleSubscription"]
        self.subscription_status = details["status"]
        self.size = details["size"]
        self.artists_count = details["artistsCount"]
        self.albums_count = details["albumsCount"]
        self.tracks_count = details["tracksCount"]
        xbmc.log(
            f"VOX Library last modified: '{details['lastModified']}'", xbmc.LOGINFO
        )
        self.last_modified = datetime.datetime.fromisoformat(
            details["lastModified"].replace("Z", "+00:00")
        )

    def _get_details(self):
        resp = self.session.get(f"https://my.vox.rocks/account/accountSummary")
        resp.raise_for_status()
        return resp.json()
