import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class Song:
    title: str
    channel: str
    duration: int
    url: str
    requester: str
    requester_id: int
    thumbnail: Optional[str] = None


class GroupQueueManager:
    def __init__(self):
        self._queues: dict[int, list[Song]] = {}
        self._current: dict[int, Song] = {}
        self._loop_modes: dict[int, str] = {}

    def get_queue(self, chat_id: int) -> list[Song]:
        return self._queues.setdefault(chat_id, [])

    def get_current(self, chat_id: int) -> Optional[Song]:
        return self._current.get(chat_id)

    def set_current(
        self,
        chat_id: int,
        song: Optional[Song],
    ) -> None:
        if song is None:
            self._current.pop(chat_id, None)
        else:
            self._current[chat_id] = song

    def add_song(self, chat_id: int, song: Song) -> int:
        queue = self.get_queue(chat_id)

        # Don't add the same song twice consecutively.
        if queue and queue[-1].url == song.url:
            return len(queue)

        current = self.get_current(chat_id)

        # Don't queue the exact currently playing song again
        # unless it is intentionally being looped.
        if (
            current
            and current.url == song.url
            and self.get_loop_mode(chat_id) == "OFF"
        ):
            return len(queue)

        queue.append(song)
        return len(queue)

    def pop_next(self, chat_id: int) -> Optional[Song]:
        """Get and remove the next queued song."""

        queue = self.get_queue(chat_id)

        if not queue:
            return None

        song = queue.pop(0)
        self.set_current(chat_id, song)
        return song

    def next_song(self, chat_id: int) -> Optional[Song]:
        """
        Decide what should play after the current song.
        """

        current = self.get_current(chat_id)
        mode = self.get_loop_mode(chat_id)

        # Repeat current song.
        if mode == "SONG" and current:
            return current

        # Normal queue progression.
        next_song = self.pop_next(chat_id)

        if next_song:
            return next_song

        # Queue mode: restart with the previous current song
        # only when there is no other queued song.
        if mode == "QUEUE" and current:
            return current

        self.set_current(chat_id, None)
        return None

    def clear(self, chat_id: int) -> None:
        self._queues.pop(chat_id, None)
        self._current.pop(chat_id, None)
        self._loop_modes.pop(chat_id, None)

    def shuffle(self, chat_id: int) -> bool:
        queue = self.get_queue(chat_id)

        if len(queue) < 2:
            return False

        random.shuffle(queue)
        return True

    def set_loop_mode(
        self,
        chat_id: int,
        mode: str,
    ) -> bool:
        mode = mode.upper()

        if mode not in {"OFF", "SONG", "QUEUE"}:
            return False

        self._loop_modes[chat_id] = mode
        return True

    def cycle_loop_mode(self, chat_id: int) -> str:
        modes = ["OFF", "SONG", "QUEUE"]
        current = self.get_loop_mode(chat_id)

        next_index = (
            modes.index(current) + 1
        ) % len(modes)

        new_mode = modes[next_index]
        self._loop_modes[chat_id] = new_mode

        return new_mode

    def get_loop_mode(self, chat_id: int) -> str:
        return self._loop_modes.get(chat_id, "OFF")

    def remove_first(self, chat_id: int) -> Optional[Song]:
        """Remove and return the first queued song."""

        queue = self.get_queue(chat_id)

        if not queue:
            return None

        return queue.pop(0)

    def queue_size(self, chat_id: int) -> int:
        return len(self.get_queue(chat_id))


queue_manager = GroupQueueManager()
