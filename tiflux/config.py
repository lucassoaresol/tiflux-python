import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST_TIFLUX")
USER = os.getenv("USER_TIFLUX")
PASSWORD = os.getenv("PASSWORD_TIFLUX")
