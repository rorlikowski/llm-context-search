from __future__ import annotations

from time import monotonic


class Timer:
    def __init__(self) -> None:
        self._start = monotonic()

    def elapsed_ms(self) -> int:
        return int((monotonic() - self._start) * 1000)
