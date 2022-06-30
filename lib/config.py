import os
from dotenv import load_dotenv


class EnvConfig:
    def __init__(self, path=None):
        """
        Get environment variables
        """
        if path:
            load_dotenv(path)
        else:
            try:
                load_dotenv('.env')
            except:
                load_dotenv('../.env')

    @staticmethod
    def get(name: str) -> str:
        return os.environ.get(name)
