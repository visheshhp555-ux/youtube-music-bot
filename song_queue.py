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

        # OFF   = normal playback
        # SONG  = repeat current song
        # QUEUE = repeat the whole queue
        self._loop_modes: dict[int, str] = {}

        # Songs that have already played in the current
        # QUEUE loop cycle.
        self._queue_history: dict[int, list[Song]] = {}

    # ---------------------------------------------------------
    # Queue
    # ---------------------------------------------------------

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

    def add_song(
        self,
        chat_id: int,
        song: Song,
    ) -> int:
        queue = self.get_queue(chat_id)

        # Avoid adding the exact same song twice
        # consecutively.
        if queue and queue[-1].url == song.url:
            return len(queue)

        current = self.get_current(chat_id)

        if current and current.url == song.url:
            return len(queue)

        queue.append(song)

        return len(queue)

    # ---------------------------------------------------------
    # Next song
    # ---------------------------------------------------------

    def next_song(
        self,
        chat_id: int,
    ) -> Optional[Song]:

        current = self.get_current(chat_id)
        mode = self.get_loop_mode(chat_id)
        queue = self.get_queue(chat_id)

        # Repeat the currently playing song.
        if mode == "SONG" and current:
            return current

        # Normal queue playback.
        if queue:
            next_song = queue.pop(0)

            if mode == "QUEUE":
                self._queue_history.setdefault(
                    chat_id,
                    [],
                ).append(next_song)

            self.set_current(
                chat_id,
                next_song,
            )

            return next_song

        # -----------------------------------------------------
        # QUEUE LOOP
        # -----------------------------------------------------

        if mode == "QUEUE":

            history = self._queue_history.get(
                chat_id,
                [],
            )

            if history:

                # Start another complete cycle.
                next_song = history.pop(0)

                self._queue_history[chat_id] = history

                # Put the song back into history so it will
                # eventually repeat again.
                history.append(next_song)

                self.set_current(
                    chat_id,
                    next_song,
                )

                return next_song

        # Nothing left to play.
        self.set_current(
            chat_id,
            None,
        )

        return None

    # ---------------------------------------------------------
    # Clear
    # ---------------------------------------------------------

    def clear(
        self,
        chat_id: int,
    ) -> None:
        self._queues.pop(
            chat_id,
            None,
        )

        self._current.pop(
            chat_id,
            None,
        )

        self._loop_modes.pop(
            chat_id,
            None,
        )

        self._queue_history.pop(
            chat_id,
            None,
        )

    # ---------------------------------------------------------
    # Shuffle
    # ---------------------------------------------------------

    def shuffle(
        self,
        chat_id: int,
    ) -> bool:

        queue = self.get_queue(
            chat_id
        )

        if len(queue) < 2:
            return False

        random.shuffle(queue)

        return True

    # ---------------------------------------------------------
    # Loop
    # ---------------------------------------------------------

    def set_loop_mode(
        self,
        chat_id: int,
        mode: str,
    ) -> bool:

        mode = mode.upper()

        if mode not in {
            "OFF",
            "SONG",
            "QUEUE",
        }:
            return False

        self._loop_modes[chat_id] = mode

        # Starting a new queue-loop cycle.
        if mode == "QUEUE":
            self._queue_history.setdefault(
                chat_id,
                [],
            )

        # No need to keep loop history when disabled.
        if mode == "OFF":
            self._queue_history.pop(
                chat_id,
                None,
            )

        return True

    def cycle_loop_mode(
        self,
        chat_id: int,
    ) -> str:

        modes = [
            "OFF",
            "SONG",
            "QUEUE",
        ]

        current = self.get_loop_mode(
            chat_id
        )

        next_index = (
            modes.index(current) + 1
        ) % len(modes)

        new_mode = modes[next_index]

        self.set_loop_mode(
            chat_id,
            new_mode,
        )

        return new_mode

    def get_loop_mode(
        self,
        chat_id: int,
    ) -> str:

        return self._loop_modes.get(
            chat_id,
            "OFF",
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def remove_first(
        self,
        chat_id: int,
    ) -> Optional[Song]:

        queue = self.get_queue(
            chat_id
        )

        if not queue:
            return None

        return queue.pop(0)

    def queue_size(
        self,
        chat_id: int,
    ) -> int:

        return len(
            self.get_queue(chat_id)
        )


queue_manager = GroupQueueManager()
