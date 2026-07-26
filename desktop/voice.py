"""Non-blocking text-to-speech for voice alerts.

Runs an offline TTS engine (``pyttsx3``) on a dedicated daemon thread fed by a
queue, so speech never blocks the Qt event loop or the inference thread. If
``pyttsx3`` is not installed the announcer degrades to a silent no-op.
"""

from __future__ import annotations

import queue
import threading


class VoiceAnnouncer:
    def __init__(self) -> None:
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._enabled = True
        self._available = False
        self._thread: threading.Thread | None = None
        self._start()

    def _start(self) -> None:
        try:
            import pyttsx3  # noqa: F401
        except ImportError:
            self._available = False
            return
        self._available = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:  # pragma: no cover - audio side effects
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass

    @property
    def available(self) -> bool:
        return self._available

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def announce(self, text: str) -> None:
        if not text or not self._enabled or not self._available:
            return
        # Drop backlog so we always speak the freshest alert.
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._queue.put(text)

    def stop(self) -> None:
        if self._available:
            self._queue.put(None)
