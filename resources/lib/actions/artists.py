from resources.lib.models.vox_album import VoxAlbum
from resources.lib.actions import XbmcAction
from resources.lib.api.library import VoxLibraryCache

import xbmc, xbmcgui, xbmcplugin


class XbmcListArtists(XbmcAction):
    def perform(self, context, args):
        items = []
        cache: VoxLibraryCache = context.cache
        addon = context.addon
        for artist in sorted(cache.artists.values(), key=lambda a: a.name):
            list_item = xbmcgui.ListItem(artist.name)
            list_item.setIsFolder(True)
            list_item.setProperties(dict(id=artist.id, IsPlayable=False))
            list_item.setInfo("music", dict(artist=artist.name, mediatype="artist"))
            list_item_url = f"{context.addon_url}?action=list&type=artist&artist={artist.name}&artist_id={artist.id}"
            items.append((list_item_url, list_item, True))
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)


class XbmcListArtist(XbmcAction):
    def perform(self, context, args):
        items = []
        artist, artist_id = args["artist"], args["artist_id"]
        addon = context.addon
        cache: VoxLibraryCache = context.cache
        albums: list(VoxAlbum) = cache.artist_to_albums[artist_id]
        for album in sorted(albums, key=lambda a: (a.release_year, a.name)):
            list_item = xbmcgui.ListItem(album.name)
            artwork_url = (
                f"http://localhost:{addon.getSetting('proxy_port')}/{album.artwork_url}"
            )
            xbmc.log(
                f"Will try to proxy the album artwork '{album.name}' to '{artwork_url}'",
                xbmc.LOGINFO,
            )
            list_item.setArt(
                {
                    "thumb": artwork_url,
                    "icon": artwork_url,
                    "banner": artwork_url,
                    "clearart": artwork_url,
                    "clearlogo": artwork_url,
                }
            )
            list_item.setProperties(dict(id=album.id, IsPlayable=False))
            list_item.setInfo(
                "music",
                dict(
                    album=album.name,
                    artist=artist,
                    year=album.release_year,
                    mediatype="album",
                ),
            )
            list_item_url = f"{context.addon_url}?action=list&type=album&album={album.name}&album_id={album.id}"
            items.append((list_item_url, list_item, True))
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)
