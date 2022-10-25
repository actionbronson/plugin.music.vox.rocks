class VoxPlaylist(object):
    def __init__(self, params):
        self.date_added = params["dateAdded"]
        self.last_modified = params["lastModified"]
        self.name = params["name"]
        self.id = params["id"]
        self.tracks_count = params["tracksCount"]
        self.raw = params
        self.items = []


class VoxPlaylistItem(object):
    def __init__(self, params):
        self.date_added = params["dateAdded"]
        self.album_name = params["albumName"]
        self.artist_name = params["artistName"]
        self.last_modified = params["lastModified"]
        self.name = params["name"]
        self.id = params["id"]
        self.file_item_id = params["fileItemId"]
        self.track_id = params["relatedTrackId"]
        self.release_year = params["releaseYear"]
        self.playlist_id = params["playlistId"]
        self.track_number = params["trackNumber"]
        self.disc_number = params["discNumber"]
        self.order_number = params["orderNum"]
        self.raw = params
