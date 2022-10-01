from abc import ABC, abstractmethod
import requests

class OAuthProvider(ABC):
    @abstractmethod
    def get_session(self) -> requests.Session:
        ... 

    @abstractmethod
    def login_provider(self, username: str, password: str, session: requests.Session) -> None:
        ... 
