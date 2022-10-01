from .plugin_view import PluginView
import xbmcgui, xbmcplugin, xbmc
import os

from .vox_api import VoxAlbum, VoxLibraryCache, VoxTrack

class XbmcAction(PluginView):
    def perform(self, context, args):
        pass

class XbmcPlayTracks(XbmcAction):
    def perform(self, context, args):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        album_id = args['album_id']
        album: VoxAlbum = context.cache.albums[album_id]
        context.cache.fetch_tracks(album_id)
        tracks: list(VoxTrack) = album.tracks
        xbmc.log(f"tracks: {str(tracks)}", xbmc.LOGINFO)
        track_item_ids = args['track_item_ids'].split(',')
        for track_item_id in track_item_ids:
            file_desc = context.cache.download_track(track_item_id)
            track = [track for track in tracks if track.file_item_id == track_item_id][0]
            url = f"http://{file_desc['url']}&d{file_desc['dataSHA1']}&b{file_desc['deltaSHA1']}"
            xbmc.log(f"adding url: {url}, track: {str(track)}", xbmc.LOGINFO)
            list_item = xbmcgui.ListItem(track.name)
            list_item.setInfo('music', dict(tracknumber=track.track_number,title=track.name,discnumber=track.disc_number,artist=track.artist,mediatype='song'))
            artwork_url = f"http://localhost:59876/{album.artwork_url}"
            list_item.setArt({'thumb': artwork_url, 'icon': artwork_url, 'banner': artwork_url, 'clearart': artwork_url, 'clearlogo':artwork_url})
            playlist.add(url, list_item)
        xbmc.Player().play(playlist)

class XbmcListAlbums(XbmcAction):
    def perform(self, context, args):
        items = []
        cache: VoxLibraryCache = context.cache
        for album in cache.albums.values():
            artwork_url = f"http://localhost:59876/{album.artwork_url}"
            artist_name = cache.artists[album.artist_id].name
            list_item = xbmcgui.ListItem(album.name, artist_name)
            #xbmc.log(f"Artwork URL: {artwork_url}", xbmc.LOGINFO)
            list_item.setArt({'thumb': artwork_url, 'icon': artwork_url, 'banner': artwork_url, 'clearart': artwork_url, 'clearlogo':artwork_url})
            list_item.setIsFolder(True)
            list_item.setProperties(dict(id=album.id, IsPlayable=False))
            list_item.setInfo('music', dict(album=album.name,artist=artist_name,year=album.release_year,mediatype='album'))
            list_item_url = f"{context.addon_url}?action=list&type=album&album={album.name}&album_id={album.id}"
            items.append((list_item_url, list_item, True))
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)

class XbmcListAlbum(XbmcAction):
    def perform(self, context, args):
        items = []
        cache: VoxLibraryCache = context.cache
        album, album_id = args['album'], args['album_id']
        xbmc.log(f"Fetching tracks for album: '{album}', id: '{album_id}'", xbmc.LOGINFO)
        cache.fetch_tracks(album_id)
        tracks = cache.albums[album_id].tracks
        items = []
        i = 0
        for track in tracks:
            list_item = xbmcgui.ListItem(track.name)
            list_item.setProperties(dict(id=track.id, IsPlayable=True))
            list_item.setInfo('music', dict(album=album,artist=track.artist,mediatype='song'))
            list_item.setIsFolder(False)
            list_item_url = f"{context.addon_url}?action=play&track_item_ids={','.join([t.file_item_id for t in tracks[i:]])}&album_id={album_id}"
            items.append((list_item_url, list_item, True))
            i+=1
        ok = xbmcplugin.addDirectoryItems(context.addon_handle, items, len(items))
        xbmcplugin.endOfDirectory(context.addon_handle, True)

class XbmcActionFactory(object):
    @staticmethod
    def from_name(args: dict) -> XbmcAction:
        xbmc.log(f"Trying to determine action from args: {str(args)}", xbmc.LOGINFO)
        if args['action'].lower() == 'list' and args['type'].lower() == 'albums':
            xbmc.log(f"Listing all albums", xbmc.LOGINFO)
            return XbmcListAlbums()
        elif args['action'].lower() == 'list' and args['type'].lower() == 'album':
            xbmc.log(f"Listing an album", xbmc.LOGINFO)
            return XbmcListAlbum()
        elif args['action'].lower() == 'play':
            xbmc.log(f"Playing tracks", xbmc.LOGINFO)            
            return XbmcPlayTracks()