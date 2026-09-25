from dataclasses import dataclass
from typing import Optional


@dataclass
class GroupMusicGroup:
    group_id: int
    title: str
    added_by: Optional[int] = None
    active: bool = True


@dataclass
class GroupMusicSubscription:
    id: int
    group_id: int
    purchased_by: int
    price: int
    started_at: str
    expires_at: str
    status: str


@dataclass
class GroupMusicMember:
    group_id: int
    user_id: int
    bot_started: bool
    channel_1_joined: bool
    channel_2_joined: bool
    access_granted: bool


@dataclass
class GroupMusicRoom:
    id: int
    group_id: int
    room_id: str
    created_by: int
    created_at: str
    active: bool = True