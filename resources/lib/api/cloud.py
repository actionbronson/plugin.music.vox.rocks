import xbmc
from .vox_access import VoxAccess


class VoxCloud(VoxAccess):
    def __init__(self, session, vox_bearer_token):
        super().__init__(session, vox_bearer_token)

    def download_track(self, file_item_id):
        file_cloud = self.vox_bearer_token["fileCloud"]
        clouds: list = file_cloud["clouds"]
        token = file_cloud["token"]
        download = {
            "download": {
                "id": file_item_id,
                "loop_client_version": "0.15",
                "token": token,
            }
        }
        headers = {
            **self.headers(),
            **{
                "content-type": "application/json",
                "Accept-Encoding": "gzip, deflate, br",
            },
        }
        for file_cloud in clouds:
            file_cloud_url = f"https://{file_cloud}"
            try:
                resp = self.session.post(
                    f"{file_cloud_url}/json/", json=download, headers=headers
                )
                resp.raise_for_status()
                sync_data = resp.json()
                answer: dict = sync_data["answer"]
                xbmc.log(f"Downloaded track, got: {answer['file']}", xbmc.LOGINFO)
                return answer["file"]
            except Exception as e:
                xbmc.log(
                    f"Caught an exception while fetching from cloud url: {file_cloud_url}, will try the next one.",
                    xbmc.LOGERROR,
                )
        xbmc.log(
            f"Guess it didn't work out, could not reach your cloud URLs.", xbmc.LOGERROR
        )
