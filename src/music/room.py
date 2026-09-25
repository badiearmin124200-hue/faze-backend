class MusicRoom:

    def __init__(self, room_id, creator_id, guest_id, genre):
        self.room_id = room_id
        self.creator_id = creator_id
        self.guest_id = guest_id
        self.genre = genre

        self.status = "active"

        self.creator_ready = False
        self.guest_ready = False

        self.current_track = None
        self.is_playing = False
        self.position = 0


class MusicRoomManager:

    def __init__(self):
        self.rooms = {}

    def create_room(self, room_id, creator_id, guest_id, genre):
        room = MusicRoom(
            room_id,
            creator_id,
            guest_id,
            genre
        )

        self.rooms[room_id] = room

        return room

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def remove_room(self, room_id):
        if room_id in self.rooms:
            del self.rooms[room_id]


music_rooms = MusicRoomManager()