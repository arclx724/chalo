# * @author        Yasir Aris M <yasiramunandar@gmail.com>
# * @date          2023-06-21 22:12:27
# * @projectName   MissKatyPyro
# * Copyright ©YasirPedia All rights reserved
import sys
from logging import getLogger
from os import environ

import dotenv

LOGGER = getLogger("MissKaty")

dotenv.load_dotenv("config.env", override=True)

if API_ID := environ.get("API_ID", ""):
    API_ID = int(API_ID)
else:
    LOGGER.error("API_ID variable is missing! Exiting now")
    sys.exit(1)
API_HASH = environ.get("API_HASH", "")
if not API_HASH:
    LOGGER.error("API_HASH variable is missing! Exiting now")
    sys.exit(1)
BOT_TOKEN = environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
    sys.exit(1)
DATABASE_URI = environ.get("DATABASE_URI", "")
if not DATABASE_URI:
    LOGGER.error("DATABASE_URI variable is missing! Exiting now")
    sys.exit(1)
if LOG_CHANNEL := environ.get("LOG_CHANNEL", ""):
    LOG_CHANNEL = int(LOG_CHANNEL)
else:
    LOGGER.error("LOG_CHANNEL variable is missing! Exiting now")
    sys.exit(1)

# Optional ENV
LOG_GROUP_ID = environ.get("LOG_GROUP_ID")
DATABASE_NAME = environ.get("DATABASE_NAME", "MissKatyDB")
TZ = environ.get("TZ", "Asia/Jakarta")
PORT = environ.get("PORT", 80)
COMMAND_HANDLER = environ.get("COMMAND_HANDLER", "! /").split()
SUDO = list(
    {
        int(x)
        for x in environ.get(
            "SUDO",
            "617426792 2024984460",
        ).split()
    }
)
OWNER_ID = int(environ.get("OWNER_ID", 2024984460))
SUPPORT_CHAT = environ.get("SUPPORT_CHAT", "YasirPediaChannel")
AUTO_RESTART = environ.get("AUTO_RESTART", False)
OPENAI_KEY = environ.get("OPENAI_KEY")
GOOGLEAI_KEY = environ.get("GOOGLEAI_KEY")
PAYDISINI_KEY = environ.get("PAYDISINI_KEY")
PAYDISINI_CHANNEL_ID = environ.get("PAYDISINI_CHANNEL_ID", "17")
