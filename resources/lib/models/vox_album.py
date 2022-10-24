class VoxAlbum(object):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        ts_added: int = None,
        ts_modified: int = None,
        format: str = None,
        release_year: int = None,
        tracks_count: int = None,
        artwork_url: str = None,
        artist_id: str = None,
    ):
        self.name = name
        self.id = id
        self.ts_added = ts_added
        self.ts_modified = ts_modified
        self.format = format
        self.release_year = release_year
        self.tracks_count = tracks_count
        self.artwork_url = artwork_url
        self.artist_id = artist_id
        self.tracks = []

    def set_tracks(self, tracks):
        self.tracks = tracks
