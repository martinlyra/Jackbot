from enum import Flag, IntEnum


class JoinReason(IntEnum):
    GAME_NOT_SUPPORTED = 0,     # Playing is not supported
    GAME_NOT_AUDIENCE = 1,      # Audience is not supported
    GAME_NOT_HOST = 2,          # Hosting is not supported
    GAME_IS_FULL = 3,           # If audience is disabled
    GAME_CAN_JOIN = 4


class JoinableFlags(Flag):
    PLAYER_SUPPORTED = 1,
    HOST_SUPPORTED = 2,
    AUDIENCE_SUPPORTED = 3
