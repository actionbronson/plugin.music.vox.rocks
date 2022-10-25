from resources.lib.models.vox_album import VoxAlbum
from resources.lib.models.vox_playlist import VoxPlaylist, VoxPlaylistItem
from resources.lib.actions import XbmcAction
from resources.lib.api.library import VoxLibraryCache

import xbmc, xbmcgui, xbmcplugin


class XbmcPlayTracksFromPlaylist(XbmcAction):
    def perform(self, context, args):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        playlist_id = args["playlist_id"]
        track_item_ids = args["track_item_ids"].split(",")
        vox_playlist: VoxPlaylist = context.cache.playlists[playlist_id]
        for track_descriptor in track_item_ids:
            xbmc.log(track_descriptor, xbmc.LOGINFO)
            track_item_id, artwork_url = track_descriptor.split(";")
            file_desc = context.cache.cloud.download_track(track_item_id)
            playlist_item: VoxPlaylistItem = [
                i for i in vox_playlist.items if i.file_item_id == track_item_id
            ][0]
            url = f"http://{file_desc['url']}&d{file_desc['dataSHA1']}&b{file_desc['deltaSHA1']}"
            xbmc.log(f"Adding url: {url}, track: {str(playlist_item)}", xbmc.LOGINFO)
            list_item = xbmcgui.ListItem(playlist_item.name)
            list_item.setArt(
                {
                    "thumb": artwork_url,
                    "icon": artwork_url,
                    "banner": artwork_url,
                    "clearart": artwork_url,
                    "clearlogo": artwork_url,
                }
            )
            list_item.setInfo(
                "music",
                dict(
                    tracknumber=playlist_item.track_number,
                    title=playlist_item.name,
                    discnumber=playlist_item.disc_number,
                    artist=playlist_item.artist_name,
                    mediatype="song",
                ),
            )
            playlist.add(url, list_item)
        xbmc.Player().play(playlist)


class XbmcListPlaylists(XbmcAction):
    def perform(self, context, args):
        items = []
        cache: VoxLibraryCache = context.cache
        all_playlists = list(cache.playlists.values())
        for playlist in reversed(all_playlists):
            list_item = xbmcgui.ListItem(playlist.name)
            list_item.setIsFolder(True)
            list_item.setProperties(dict(id=playlist.id, IsPlayable=False))
            list_item.setInfo("music", dict(playlist=playlist.name, mediatype="music"))
            list_item_url = f"{context.addon_url}?action=list&type=playlist&playlist={playlist.name}&playlist_id={playlist.id}"
            items.append((list_item_url, list_item, True))
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)


class XbmcListPlaylist(XbmcAction):
    def guess_album(self, context, album_name):
        return context.cache.albums_by_name[album_name]

    def perform(self, context, args):
        items = []
        addon = context.addon
        cache: VoxLibraryCache = context.cache
        playlist, playlist_id = args["playlist"], args["playlist_id"]
        xbmc.log(
            f"Fetching tracks for playlist: '{playlist}', id: '{playlist_id}'",
            xbmc.LOGINFO,
        )
        playlist: VoxPlaylist = cache.playlists[playlist_id]
        i = 0
        playable_items = sorted(playlist.items, key=lambda x: x.order_number)
        for item in playable_items:
            list_item = xbmcgui.ListItem(item.name)
            # no album_id, let's try to figure it out from the ids and album_name ...
            album: VoxAlbum = context.cache.albums_by_name[item.album_name]
            artwork_url = (
                f"http://localhost:{addon.getSetting('proxy_port')}/{album.artwork_url}"
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
            list_item.setProperties(dict(id=item.id, IsPlayable=True))
            list_item.setInfo(
                "music",
                dict(album=item.album_name, artist=item.artist_name, mediatype="song"),
            )
            list_item_url = f"""{context.addon_url}?action=play&track_item_ids={','.join([f"{t.file_item_id};{artwork_url}" for t in playable_items[i:]])}&playlist_id={playlist_id}"""
            items.append((list_item_url, list_item, True))
            i += 1
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)
