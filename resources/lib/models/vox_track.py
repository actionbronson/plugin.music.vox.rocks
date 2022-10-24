class VoxTrack(object):
    def __init__(self, params, artwork_url):
        self.album_artist_name = params["albumArtistName"]
        self.album_id = params.get("albumId", None)
        self.album_name = params["albumName"]
        self.artist = params["artistName"]
        self.bitrate = params["bitrate"]
        self.sample_rate = params["sampleRate"]
        self.date_added = params["dateAdded"]
        self.name = params["name"]
        self.track_number = params["trackNumber"]
        self.disc_number = params["discNumber"]
        self.id = params["id"]
        self.file_item_id = params["fileItemId"]
        self.raw = params
        self.artwork_url = artwork_url
