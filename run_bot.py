#!/usr/bin/env python
import logging
from bot import watchbot

root = logging.getLogger()
root.setLevel(logging.INFO)
# need to "kick off" root logger for some reason
logging.info("Starting root logger")

watchbot = watchbot.WatchBot()
watchbot.run()
