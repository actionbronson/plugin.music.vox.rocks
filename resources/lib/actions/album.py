from resources.lib.actions import XbmcAction
from resources.lib.api.library import VoxLibraryCache
from resources.lib.models.vox_album import VoxAlbum
from resources.lib.models.vox_track import VoxTrack

import xbmc, xbmcgui, xbmcplugin


class XbmcListAlbum(XbmcAction):
    def perform(self, context, args):
        items = []
        cache: VoxLibraryCache = context.cache
        addon = context.addon
        album, album_id = args["album"], args["album_id"]
        xbmc.log(
            f"Fetching tracks for album: '{album}', id: '{album_id}'", xbmc.LOGINFO
        )
        cache.get_album_tracks(album_id)
        tracks = cache.albums[album_id].tracks
        artwork_url = (
            f"http://localhost:{addon.getSetting('proxy_port')}/{cache.albums[album_id].artwork_url}"
        )        
        items = []
        i = 0
        for track in tracks:
            list_item = xbmcgui.ListItem(track.name)
            list_item.setProperties(dict(id=track.id, IsPlayable=True))
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
                "music", dict(album=album, artist=track.artist, mediatype="song")
            )
            list_item.setIsFolder(False)
            list_item_url = f"{context.addon_url}?action=play&track_item_ids={','.join([t.file_item_id for t in tracks[i:]])}&album_id={album_id}"
            items.append((list_item_url, list_item, True))
            i += 1
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)


class XbmcListAlbums(XbmcAction):
    def perform(self, context, args):
        items = []
        cache: VoxLibraryCache = context.cache
        addon = context.addon
        all_albums = list(cache.albums.values())
        xbmc.log(f"Will display {len(all_albums)} albums.", xbmc.LOGINFO)
        for album in reversed(all_albums):
            artwork_url = (
                f"http://localhost:{addon.getSetting('proxy_port')}/{album.artwork_url}"
            )
            artist_name = cache.artists[album.artist_id].name
            list_item = xbmcgui.ListItem(album.name, artist_name)
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
            list_item.setIsFolder(True)
            list_item.setProperties(dict(id=album.id, IsPlayable=False))
            list_item.setInfo(
                "music",
                dict(
                    album=album.name,
                    artist=artist_name,
                    year=album.release_year,
                    mediatype="album",
                ),
            )
            list_item_url = f"{context.addon_url}?action=list&type=album&album={album.name}&album_id={album.id}"
            items.append((list_item_url, list_item, True))
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)


class XbmcPlayTracksFromAlbum(XbmcAction):
    def _load_album_tracks(self, context, album_id):
        album: VoxAlbum = context.cache.albums[album_id]
        context.cache.get_album_tracks(album_id)
        tracks: list(VoxTrack) = album.tracks
        xbmc.log(f"album tracks: {str(tracks)}", xbmc.LOGINFO)
        return tracks

    def perform(self, context, args):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        addon = context.addon
        album_id = args["album_id"]
        track_item_ids = args["track_item_ids"].split(",")
        tracks = self._load_album_tracks(context, album_id)
        for track_item_id in track_item_ids:
            file_desc = context.cache.cloud.download_track(track_item_id)
            track = [track for track in tracks if track.file_item_id == track_item_id][
                0
            ]
            url = f"http://{file_desc['url']}&d{file_desc['dataSHA1']}&b{file_desc['deltaSHA1']}"
            xbmc.log(f"adding url: {url}, track: {str(track)}", xbmc.LOGINFO)
            list_item = xbmcgui.ListItem(track.name)
            list_item.setInfo(
                "music",
                dict(
                    tracknumber=track.track_number,
                    title=track.name,
                    discnumber=track.disc_number,
                    artist=track.artist,
                    mediatype="song",
                ),
            )
            artwork_url = (
                f"http://localhost:{addon.getSetting('proxy_port')}/{track.artwork_url}"
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
            playlist.add(url, list_item)
        xbmc.Player().play(playlist)
