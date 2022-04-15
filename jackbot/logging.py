import logging
import os


def create_game_logger(path, file_prefix) -> logging.Logger:
    logger = logging.getLogger('game')
    logger.setLevel(logging.DEBUG)
    fn = f"{path}/{file_prefix}.game.log"
    if not os.path.exists(path):
        os.makedirs(path)
    fh = logging.FileHandler(fn)
    logger.addHandler(fh)
    return logger


def create_wss_api_logger(path, file_prefix) -> logging.Logger:
    logger = logging.getLogger('api_wss')
    logger.setLevel(logging.DEBUG)
    fn = f"{path}/{file_prefix}.wss_api.log"
    if not os.path.exists(path):
        os.makedirs(path)
    fh = logging.FileHandler(fn)
    logger.addHandler(fh)
    return logger
