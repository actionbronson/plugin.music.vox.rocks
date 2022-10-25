from resources.lib.actions.album import (
    XbmcListAlbums,
    XbmcListAlbum,
    XbmcPlayTracksFromAlbum,
)
from resources.lib.actions.artists import XbmcListArtist, XbmcListArtists
from resources.lib.actions.playlist import (
    XbmcListPlaylist,
    XbmcListPlaylists,
    XbmcPlayTracksFromPlaylist,
)
from resources.lib.actions import XbmcAction

import xbmc


class XbmcActionFactory(object):
    @staticmethod
    def from_name(args: dict) -> XbmcAction:
        xbmc.log(f"Trying to determine action from args: {str(args)}", xbmc.LOGINFO)
        if args["action"].lower() == "list" and args["type"].lower() == "albums":
            xbmc.log(f"Listing all albums", xbmc.LOGINFO)
            return XbmcListAlbums()
        elif args["action"].lower() == "list" and args["type"].lower() == "artists":
            xbmc.log(f"Listing all artists", xbmc.LOGINFO)
            return XbmcListArtists()
        elif args["action"].lower() == "list" and args["type"].lower() == "playlists":
            xbmc.log(f"Listing playlists", xbmc.LOGINFO)
            return XbmcListPlaylists()
        elif args["action"].lower() == "list" and args["type"].lower() == "album":
            xbmc.log(f"Listing an album", xbmc.LOGINFO)
            return XbmcListAlbum()
        elif args["action"].lower() == "list" and args["type"].lower() == "artist":
            xbmc.log(f"Listing an artist", xbmc.LOGINFO)
            return XbmcListArtist()
        elif args["action"].lower() == "list" and args["type"].lower() == "playlist":
            xbmc.log(f"Listing a playlist", xbmc.LOGINFO)
            return XbmcListPlaylist()
        elif args["action"].lower() == "play" and "album_id" in args:
            xbmc.log(f"Playing tracks", xbmc.LOGINFO)
            return XbmcPlayTracksFromAlbum()
        elif args["action"].lower() == "play" and "playlist_id" in args:
            xbmc.log(f"Playing tracks", xbmc.LOGINFO)
            return XbmcPlayTracksFromPlaylist()
