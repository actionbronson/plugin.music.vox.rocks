import requests
import xbmc
import pickle
import datetime
from typing import Callable
import logging

class VoxArtist:
    def __init__(self, name: str=None, id: str=None, ts_added: int=None, ts_modified: int=None):
        self.name = name
        self.id = id
        self.ts_added = ts_added
        self.ts_modified = ts_modified

class VoxTrack(object):
    def __init__(self, params, artwork_url):
        self.album_artist_name = params['albumArtistName']
        self.album_id = params['albumId']
        self.album_name = params['albumName']
        self.artist = params['artistName']
        self.bitrate = params['bitrate']
        self.sample_rate = params['sampleRate']
        self.date_added = params['dateAdded']
        self.name = params['name']
        self.track_number = params['trackNumber']
        self.disc_number = params['discNumber']
        self.id = params['id']
        self.file_item_id = params['fileItemId']
        self.artwork_url = artwork_url
        
class VoxAlbum(object):
    def __init__(self, name: str=None, id: str=None, ts_added: int=None, ts_modified: int=None, 
                format: str=None, release_year: int=None, tracks_count: int=None, artwork_url: str=None,
                artist_id: str=None):
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
        xbmc.log(f"Setting {len(tracks)} tracks: {str(tracks)}", xbmc.LOGINFO)
        self.tracks = tracks

class VoxAccess(object):
    def __init__(self, session, vox_bearer_token):
        self.vox_bearer_token = vox_bearer_token
        xbmc.log(str(vox_bearer_token), xbmc.LOGINFO)
        self.access_token = vox_bearer_token['access_token']
        self.user_id = vox_bearer_token['userId']
        self.session = session

    def headers(self):
        return {"Authorization": self.access_token,
                "User-Agent": "Loop/0.15 (Mac OS X Version 12.1 (Build 21C52))",
                "x-api-version": "2"}

class VoxLibraryDetails(object):
    def __init__(self, session):
        self.session = session
        details = self._get_details()
        self.expiration_date = datetime.datetime.fromtimestamp(details['userSubscriptionExpiration'])
        self.is_apple = details['isAppleSubscription']
        self.subscription_status = details['status']
        self.size = details['size']
        self.artists_count = details['artistsCount']
        self.albums_count = details['albumsCount']
        self.tracks_count = details['tracksCount']
        xbmc.log(f"VOX Library last modified: '{details['lastModified']}'", xbmc.LOGINFO)
        self.last_modified = datetime.datetime.fromisoformat(details['lastModified'].replace('Z', '+00:00'))

    def _get_details(self):
        resp = self.session.get(f"https://my.vox.rocks/account/accountSummary")
        resp.raise_for_status()
        return resp.json()

class VoxLibraryCache(VoxAccess):
    def __init__(self, session, vox_bearer_token, artists: dict={}, albums: dict={}, tracks: dict={}, reload: bool=True):
        super().__init__(session, vox_bearer_token)
        self.artists = artists
        self.albums = albums
        self.tracks = tracks
        self.artist_to_albums = self._build_artist_to_albums_rel()
        if reload:
            self.albums = {}
            self.artists = {}
            self.tracks = {}
            self._generic_vox_api_fetcher("https://api.vox.rocks/api/artists", self._add_artists)
            self._generic_vox_api_fetcher("https://api.vox.rocks/api/albums", self._add_albums)
            self._store_tracks()
    
    def _build_artist_to_albums_rel(self):
        artist_to_albums = {}
        for album in self.albums.values():
            albums = artist_to_albums.setdefault(album.artist_id, []) 
            albums.append(album)
        return artist_to_albums

    @staticmethod
    def from_file(session, vox_bearer_token, albums_file, artists_file, tracks_file):
        artists, albums = {}, {}
        xbmc.log(f"Reading pickled albums from: '{albums_file}', pickled artists from: '{artists_file}', pickled tracks from: '{tracks_file}'", xbmc.LOGINFO)
        with open(albums_file, 'rb') as file:
            albums = pickle.load(file)
        with open(artists_file, 'rb') as file:
            artists = pickle.load(file)
        with open(tracks_file, 'rb') as file:
            tracks = pickle.load(file)            
    
        return VoxLibraryCache(session, vox_bearer_token, artists, albums, tracks, False)

    def to_file(self, albums_file, artists_file, tracks_file):
        xbmc.log(f"Writing pickled albums to: '{albums_file}', pickled artists to: '{artists_file}', pickled tracks to: '{tracks_file}'", xbmc.LOGINFO)
        with open(albums_file, 'wb') as file:
            pickle.dump(self.albums, file)
        with open(artists_file, 'wb') as file:
            pickle.dump(self.artists, file)
        with open(tracks_file, 'wb') as file:
            pickle.dump(self.tracks, file)            

    def fetch_tracks(self, album_id):
        album: VoxAlbum = self.albums[album_id]
        def _get_album_tracks(tracks_json, _):
            album.set_tracks([VoxTrack(track, album.artwork_url) for track in sorted(tracks_json, key=lambda t: (t["discNumber"],t["trackNumber"])) if not(track['isDeleted'])])

        if len(album.tracks) != album.tracks_count:
            self._generic_vox_api_fetcher("https://api.vox.rocks/api/tracks", _get_album_tracks, 
                                        params={"filter[where][albumId][inq][]": album_id})

    def download_track(self, file_item_id):
        file_cloud = self.vox_bearer_token['fileCloud']
        clouds: list = file_cloud['clouds']
        token = file_cloud['token']
        download={
            "download": {
                "id": file_item_id,
                "loop_client_version": "0.15",
                "token": token
            }
        }
        headers = {**self.headers(), **{'content-type': 'application/json', 'Accept-Encoding': 'gzip, deflate, br'}}
        for file_cloud in clouds:
            file_cloud_url = f"https://{file_cloud}"
            try:
                resp = self.session.post(f"{file_cloud_url}/json/", json=download, headers=headers)
                resp.raise_for_status()
                sync_data = resp.json()
                answer: dict = sync_data['answer']
                xbmc.log(f"Downloaded track, got: {answer['file']}", xbmc.LOGINFO)
                return answer['file']
            except Exception as e:
                xbmc.log(f"Caught an exception while fetching from cloud url: {file_cloud_url}, will try another on.", xbmc.LOGERROR)
        xbmc.log(f"Guess it didn't work out, could not reach your cloud URLs.", xbmc.LOGERROR)

    def _store_tracks(self):
        file_cloud = self.vox_bearer_token['fileCloud']
        clouds: list = file_cloud['clouds']
        token = file_cloud['token']
        file_cloud_url = f"https://{clouds[0]}"
        last_change, last_file_id, last = 0, 0, False
        self.tracks = {}
        def _process_dir(directory):
            if 'download' in directory:
                downloadable_tracks = directory['download']
                for track in downloadable_tracks:
                    self.tracks[track['id']] = track
            elif 'count' not in directory:
                for subdir in directory.keys():
                    _process_dir(subdir)
            
        while not(last):
            data= {
                "syncUpstream": {
                    "deviceID": 0,
                    "lastChange": last_change,
                    "lastFileId": last_file_id,
                    "loop_client_version": "0.14.34",
                    "maxItems": 1000,
                    "token": token
                }
            }
            headers = {**self.headers(), **{'content-type': 'application/json', 'Accept-Encoding': 'gzip, deflate, br'}}
            resp = self.session.post(f"{file_cloud_url}/json/", json=data, headers=headers)
            resp.raise_for_status()
            sync_data = resp.json()
            answer: dict = sync_data['answer']
            all_dirs: dict = answer['/root']
            for directory in all_dirs.keys():
                if directory == "/.__medialibrary" or not(directory.startswith('/')):
                    continue
                _process_dir(all_dirs[directory])

            xbmc.log(f"Downloadable tracks database has size: {len(self.tracks.keys())}", xbmc.LOGINFO)
            last_file_id = answer['lastFileId']
            last_change = answer['lastChange']
            last = answer.get('last', 0) == 1

    def _add_artists(self, artists_json, len_artists):
        artists = [VoxArtist(id=artist['id'],
                            name=artist['name'],
                            ts_added=artist['dateAdded'],
                            ts_modified=artist['lastModified']) for artist in artists_json]
        xbmc.log(f'Adding {len_artists} artists to library.', xbmc.LOGINFO)
        self.artists = {**self.artists, **{artist.id: artist for artist in artists}}

    def _add_albums(self, albums_json, _):
        albums = {album['id']: VoxAlbum(id=album['id'],
                            name=album['name'], 
                            ts_added=album['dateAdded'],
                            ts_modified=album['lastModified'],
                            format=album['format'],
                            release_year=album['releaseYear'],
                            tracks_count=album['tracksCount'],
                            artwork_url=album['artworkUrl'],
                            artist_id=album['artistId']) for album in albums_json}
        self.albums = {**self.albums, **albums}

    def _generic_vox_api_fetcher(self, url: str, func: Callable[[list,int], None], params: dict={}):
        skip = 0 
        while True:
            resp = self.session.get(url,
                                params={**{"filter[limit]": 1000, 
                                        "filter[skip]": skip, 
                                        "filter[where][isDeleted]": "false"}, **params},
                                headers=self.headers())
            resp.raise_for_status()
            items: list = resp.json()
            len_items: int = len(items)
            func(items, len_items)
            if len_items < 1000:
                xbmc.log(f"Received {len_items} items.  Breaking out.", xbmc.LOGINFO)
                break
            else:
                skip += 1000
                xbmc.log(f"We reached the limit on {url}, length={len_items}.  Fetching more and skipping first {skip}.", xbmc.LOGINFO)
