import xbmc
import pickle
from typing import Callable

from .cloud import VoxCloud
from .vox_access import VoxAccess
from ..models.vox_album import VoxAlbum
from ..models.vox_artist import VoxArtist
from ..models.vox_playlist import VoxPlaylist, VoxPlaylistItem
from ..models.vox_track import VoxTrack


class VoxLibraryCache(VoxAccess):
    def __init__(
        self,
        session,
        vox_bearer_token,
        artists: dict = {},
        albums: dict = {},
        playlists: dict = {},
        reload: bool = True,
    ):
        super().__init__(session, vox_bearer_token)
        self.artists = artists
        self.albums = albums
        self.playlists = playlists
        self.cloud = VoxCloud(session, vox_bearer_token)

        if reload:
            self.albums, self.artists, self.playlists = {}, {}, {}
            self._generic_vox_api_fetcher(
                "https://api.vox.rocks/api/artists", self._add_artists
            )
            self._generic_vox_api_fetcher(
                "https://api.vox.rocks/api/albums", self._add_albums
            )
            self._generic_vox_api_fetcher(
                "https://api.vox.rocks/api/playlists", self._add_playlists
            )
            self._generic_vox_api_fetcher(
                "https://api.vox.rocks/api/playlistitems", self._add_playlist_items
            )

        self.artist_to_albums = self._build_artist_to_albums_view()
        self.albums_by_name = self._build_albums_by_name_view()

    def _build_artist_to_albums_view(self):
        artist_to_albums = {}
        for album in self.albums.values():
            albums = artist_to_albums.setdefault(album.artist_id, [])
            albums.append(album)
        return artist_to_albums

    def _build_albums_by_name_view(self):
        return {album.name: album for album in self.albums.values()}

    @staticmethod
    def from_file(session, vox_bearer_token, albums_file, artists_file, playlists_file):
        xbmc.log(
            f"Reading pickled albums from: '{albums_file}', pickled artists from: '{artists_file}', pickled tracks from: '{tracks_file}', playlists from: '{playlists_file}'",
            xbmc.LOGINFO,
        )
        with open(albums_file, "rb") as file:
            albums = pickle.load(file)
        with open(artists_file, "rb") as file:
            artists = pickle.load(file)
        with open(playlists_file, "rb") as file:
            playlists = pickle.load(file)
        return VoxLibraryCache(
            session, vox_bearer_token, artists, albums, playlists, False
        )

    def to_file(self, albums_file, artists_file, playlists_file):
        xbmc.log(
            f"Writing pickled albums to: '{albums_file}', pickled artists to: '{artists_file}', pickled playlists to: '{playlists_file}'",
            xbmc.LOGINFO,
        )
        with open(albums_file, "wb") as file:
            pickle.dump(self.albums, file)
        with open(artists_file, "wb") as file:
            pickle.dump(self.artists, file)
        with open(playlists_file, "wb") as file:
            pickle.dump(self.playlists, file)

    def get_album_tracks(self, album_id):
        album: VoxAlbum = self.albums[album_id]

        def _get_album_tracks(tracks_json, _):
            album.set_tracks(
                [
                    VoxTrack(track, album.artwork_url)
                    for track in sorted(
                        tracks_json, key=lambda t: (t["discNumber"], t["trackNumber"])
                    )
                    if not (track["isDeleted"])
                ]
            )

        if len(album.tracks) != album.tracks_count:
            self._generic_vox_api_fetcher(
                "https://api.vox.rocks/api/tracks",
                _get_album_tracks,
                params={"filter[where][albumId][inq][]": album_id},
            )

    def _add_artists(self, artists_json, len_artists):
        artists = [
            VoxArtist(
                id=artist["id"],
                name=artist["name"],
                ts_added=artist["dateAdded"],
                ts_modified=artist["lastModified"],
            )
            for artist in artists_json
        ]
        xbmc.log(f"Adding {len_artists} artists to library.", xbmc.LOGINFO)
        self.artists = {**self.artists, **{artist.id: artist for artist in artists}}

    def _add_albums(self, albums_json, _):
        albums = {
            album["id"]: VoxAlbum(
                id=album["id"],
                name=album["name"],
                ts_added=album["dateAdded"],
                ts_modified=album["lastModified"],
                format=album["format"],
                release_year=album["releaseYear"],
                tracks_count=album["tracksCount"],
                artwork_url=album["artworkUrl"],
                artist_id=album["artistId"],
            )
            for album in albums_json
        }
        self.albums = {**self.albums, **albums}

    def _add_playlists(self, playlist_json, _):
        playlists = {
            playlist["id"]: VoxPlaylist(playlist) for playlist in playlist_json
        }
        self.playlists = {**self.playlists, **playlists}

    def _add_playlist_items(self, playlist_items_json, _):
        for item in playlist_items_json:
            xbmc.log(str(item), xbmc.LOGINFO)
            playlist_item = VoxPlaylistItem(item)
            self.playlists[playlist_item.playlist_id].items.append(playlist_item)

    def _generic_vox_api_fetcher(
        self, url: str, func: Callable[[list, int], None], params: dict = {}
    ):
        skip = 0
        while True:
            resp = self.session.get(
                url,
                params={
                    **{
                        "filter[limit]": 1000,
                        "filter[skip]": skip,
                        "filter[where][isDeleted]": "false",
                    },
                    **params,
                },
                headers=self.headers(),
            )
            resp.raise_for_status()
            items: list = resp.json()
            len_items: int = len(items)
            func(items, len_items)
            if len_items < 1000:
                xbmc.log(f"Received {len_items} items.  Breaking out.", xbmc.LOGINFO)
                break
            else:
                skip += 1000
                xbmc.log(
                    f"We reached the limit on {url}, length={len_items}.  Fetching more and skipping first {skip}.",
                    xbmc.LOGINFO,
                )
