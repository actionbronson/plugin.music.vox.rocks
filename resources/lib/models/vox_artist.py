class VoxArtist:
    def __init__(
        self,
        name: str = None,
        id: str = None,
        ts_added: int = None,
        ts_modified: int = None,
    ):
        self.name = name
        self.id = id
        self.ts_added = ts_added
        self.ts_modified = ts_modified
