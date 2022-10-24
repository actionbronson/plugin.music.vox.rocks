import xbmcaddon, xbmcgui, xbmcplugin, xbmc, xbmcvfs
import sys, os
import yaml
import pickle
import time
import requests
from urllib.parse import parse_qsl
import datetime
from dateutil.tz import tzlocal

from .plugin_view import PluginView as viewtype
from .login import VoxOAuthLogin
from .oauth.facebook import FacebookOauthProvider
from .api.library import VoxLibraryCache
from .api.library_details import VoxLibraryDetails
from .actions.factory import XbmcActionFactory
from .actions import XbmcAction

addon = xbmcaddon.Addon(id="plugin.music.vox.rocks")
addon_handle = int(sys.argv[1])
addon_url = sys.argv[0]
addon_path = addon.getAddonInfo("path")
addon_name = addon.getAddonInfo("name")
addon_cache = None
localtimezone = tzlocal()

try:
    addon_cache = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
except:
    addon_cache = xbmc.translatePath(addon.getAddonInfo("profile"))

config = None
with open(os.path.join(addon_path, "resources", "vox_rocks.yaml"), "r") as file:
    config = yaml.load(file)
    xbmc.log(f"Config file sucessfully loaded.", xbmc.LOGINFO)


def older_than(path: str, days=1):
    file_time = os.path.getmtime(path)
    return (time.time() - file_time) / 3600 > 24 * days


def login():
    vox_cloud_bearer_token = os.path.join(addon_cache, "bearer_token")
    session_coookies = os.path.join(addon_cache, "cookies")
    session, vox_bearer_token = None, None
    if not (os.path.exists(vox_cloud_bearer_token)) or older_than(
        vox_cloud_bearer_token, days=0.1
    ):
        username = addon.getSetting("facebook_username")
        password = addon.getSetting("facebook_password")
        xbmc.log(
            f"Will attempt to login to Facebook with username: '{username}'",
            xbmc.LOGINFO,
        )
        vox_oauth_config = config["oauth"]
        client_id, client_secret = (
            vox_oauth_config["client_id"],
            vox_oauth_config["client_secret"],
        )
        oauth_login = VoxOAuthLogin(
            FacebookOauthProvider(vox_oauth_config["facebook"]),
            client_id,
            client_secret,
        )
        oauth_login.login(username, password)
        xbmcgui.Dialog().notification(
            "Login",
            f"Facebook login with username {username} succeeded.",
            icon=xbmcgui.NOTIFICATION_INFO,
        )
        vox_bearer_token = oauth_login.get_bearer_token()
        session = oauth_login.get_session()
        with open(vox_cloud_bearer_token, "wb") as file:
            pickle.dump(vox_bearer_token, file)
            xbmc.log(f"Writing pickled bearer token to: '{vox_cloud_bearer_token}'")
        with open(session_coookies, "wb") as file:
            pickle.dump(oauth_login.get_session().cookies.get_dict(), file)
            xbmc.log(f"Writing pickled cookies to: '{session_coookies}'")
    else:
        xbmc.log(f"Fetching bearer token and cookies from cache", xbmc.LOGINFO)
        with open(vox_cloud_bearer_token, "rb") as file:
            vox_bearer_token = pickle.load(file)
        with open(session_coookies, "rb") as file:
            cookies: dict = pickle.load(file)
            session = requests.Session()
            # xbmc.log(str(cookies), xbmc.LOGINFO)
            for k in cookies.keys():
                session.cookies.set(k, cookies[k])

    return (session, vox_bearer_token)


def create_caches(session, vox_cloud_bearer_token):
    def _create_and_store_cache():
        cache = VoxLibraryCache(session, vox_cloud_bearer_token)
        xbmc.log(f"Attempting to store VOX Library to cache.", xbmc.LOGINFO)
        cache.to_file(
            albums_file=vox_cloud_albums_db,
            artists_file=vox_cloud_artists_db,
            playlists_file=vox_cloud_playlists_db,
        )
        return cache

    def _is_stale_cache():
        date_fmt = "%Y-%m-%d %H:%M:%S"
        cache_mtime = datetime.datetime.fromtimestamp(
            os.path.getmtime(vox_cloud_albums_db)
        ).astimezone()
        vox_time = details.last_modified.astimezone()
        formatted_cache_time = cache_mtime.strftime(date_fmt)
        formatted_vox_time = vox_time.strftime(date_fmt)
        xbmc.log(
            f"""Cache created on {formatted_cache_time}.  VOX Library last modified on: {formatted_vox_time}""",
            xbmc.LOGINFO,
        )
        return cache_mtime < vox_time

    vox_cloud_artists_db = os.path.join(addon_cache, "vox_cloud.artists.db")
    vox_cloud_albums_db = os.path.join(addon_cache, "vox_cloud.albums.db")
    vox_cloud_tracks_db = os.path.join(addon_cache, "vox_cloud.tracks.db")
    vox_cloud_playlists_db = os.path.join(addon_cache, "vox_cloud.playlists.db")
    details = VoxLibraryDetails(session)
    cache = None
    file_caches_exist = (
        os.path.exists(vox_cloud_artists_db)
        and os.path.exists(vox_cloud_albums_db)
        and os.path.exists(vox_cloud_tracks_db)
    )
    if not (file_caches_exist) or _is_stale_cache():
        return _create_and_store_cache()
    else:
        xbmc.log(f"Attempting to restore VOX Library from caches.", xbmc.LOGINFO)
        cache = VoxLibraryCache.from_file(
            session,
            vox_cloud_bearer_token,
            albums_file=vox_cloud_albums_db,
            artists_file=vox_cloud_artists_db,
            playlists_file=vox_cloud_playlists_db,
        )
    return cache


class Context(object):
    def __init__(self, cache, session, vox_cloud_bearer_token):
        self.cache: VoxLibraryCache = cache
        self.session = session
        self.vox_cloud_bearer_token = vox_cloud_bearer_token
        self.addon = addon
        self.addon_handle = addon_handle
        self.addon_url = addon_url
        self.addon_path = addon_path
        self.addon_name = addon_name


class Router(viewtype):
    def __init__(self, args):
        viewtype.__init__(self)
        session, vox_cloud_bearer_token = login()
        library_cache = create_caches(session, vox_cloud_bearer_token)
        context = Context(library_cache, session, vox_cloud_bearer_token)
        xbmc.log(
            f"Successfully created Router class for addon: {addon_name} with args: {args}, bearer token: {vox_cloud_bearer_token}",
            xbmc.LOGINFO,
        )

        if not (args):
            self._add_directory_root_extra()
        else:
            params = dict(parse_qsl(args))
            xbmc.log(f"processing params: {params}", xbmc.LOGINFO)
            action: XbmcAction = XbmcActionFactory.from_name(params)
            action.perform(context, params)

    def _add_directory_root_extra(self):
        items = []
        for item_type in ["Artists", "Albums", "Playlists"]:
            list_item = xbmcgui.ListItem(label=item_type)
            list_item.setInfo(type="Music", infoLabels=dict(Title=item_type))
            list_item_url = f"{addon_url}?action=list&type={item_type}"
            items.append((list_item_url, list_item, True))
        ok = xbmcplugin.addDirectoryItems(addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(addon_handle)


if __name__ == "__main__":
    Router(sys.argv[2][1:])
