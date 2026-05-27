from __future__ import annotations

import argparse
import queue
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STREAM_FILE = SCRIPT_DIR / "sample_reply_stream.txt"


@dataclass
class TextChunk:
    index: int
    text: str
    received_at: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe Windows TTS realtime-like chunk playback using pyttsx3/SAPI."
    )
    parser.add_argument("--list-voices", action="store_true", help="List installed Windows/SAPI voices and exit.")
    parser.add_argument(
        "--voice-contains",
        default="",
        help='Pick the first voice whose id/name contains this text, e.g. "Microsoft An".',
    )
    parser.add_argument("--rate", type=int, default=165, help="TTS speaking rate. Use 0 to keep engine default.")
    parser.add_argument("--volume", type=float, default=1.0, help="TTS volume from 0.0 to 1.0.")
    parser.add_argument(
        "--stream-file",
        default=str(DEFAULT_STREAM_FILE),
        help="Text file used to simulate realtime reply chunks. One non-empty line is one chunk.",
    )
    parser.add_argument(
        "--chunk-delay-sec",
        type=float,
        default=0.7,
        help="Delay between simulated incoming chunks.",
    )
    parser.add_argument(
        "--split-sentences",
        action="store_true",
        help="Split the whole stream file into sentence-like chunks instead of one line per chunk.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not speak; only print timing events.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    engine = None
    selected_voice = None
    if not args.dry_run or args.list_voices:
        pyttsx3 = import_pyttsx3()
        engine = pyttsx3.init()

        if args.list_voices:
            list_voices(engine)
            return 0

        selected_voice = select_voice(engine, args.voice_contains)
        configure_engine(engine, selected_voice, args.rate, args.volume)

    print_engine_config(engine, selected_voice, args.dry_run)

    chunks = load_chunks(Path(args.stream_file), args.split_sentences)
    if not chunks:
        raise RuntimeError(f"No text chunks found in {args.stream_file}")

    work_queue: queue.Queue[TextChunk | None] = queue.Queue()
    worker = threading.Thread(
        target=tts_worker,
        args=(engine, work_queue, args.dry_run),
        daemon=True,
        name="windows-tts-worker",
    )
    started_at = time.perf_counter()
    worker.start()

    print("")
    print("Simulating realtime reply_text chunks...")
    print("Press Ctrl+C to stop.")
    print("")

    try:
        for index, text in enumerate(chunks, start=1):
            time.sleep(max(args.chunk_delay_sec, 0.0))
            now = time.perf_counter()
            elapsed = now - started_at
            print(f"[recv {index:02d} +{elapsed:7.3f}s] {text}")
            work_queue.put(TextChunk(index=index, text=text, received_at=now))

        work_queue.put(None)
        worker.join()
    except KeyboardInterrupt:
        print("")
        print("Interrupted by user. Stopping TTS engine...")
        try:
            engine.stop()
        except Exception:
            pass
        work_queue.put(None)
        return 130

    total = time.perf_counter() - started_at
    print("")
    print(f"Done. chunks={len(chunks)} total_sec={total:.3f}")
    return 0


def import_pyttsx3() -> Any:
    try:
        import pyttsx3
    except ImportError as exc:
        raise ImportError(
            "Missing dependency: pyttsx3. Install it with:\n"
            "python -m pip install -r requirements-kiosk.txt"
        ) from exc
    return pyttsx3


def list_voices(engine: Any) -> None:
    voices = engine.getProperty("voices") or []
    if not voices:
        print("No SAPI voices found.")
        return

    for index, voice in enumerate(voices, start=1):
        print(f"[{index:02d}]")
        print(f"  id: {getattr(voice, 'id', '')}")
        print(f"  name: {getattr(voice, 'name', '')}")
        print(f"  languages: {getattr(voice, 'languages', '')}")
        print(f"  gender: {getattr(voice, 'gender', '')}")
        print(f"  age: {getattr(voice, 'age', '')}")


def select_voice(engine: Any, contains: str) -> Any | None:
    voices = engine.getProperty("voices") or []
    if not contains:
        return None

    needle = contains.casefold()
    for voice in voices:
        haystack = " ".join(
            str(value)
            for value in (
                getattr(voice, "id", ""),
                getattr(voice, "name", ""),
                getattr(voice, "languages", ""),
            )
        ).casefold()
        if needle in haystack:
            return voice

    available = ", ".join(str(getattr(voice, "name", "")) for voice in voices)
    raise RuntimeError(f"No voice contains {contains!r}. Available voices: {available}")


def configure_engine(engine: Any, selected_voice: Any | None, rate: int, volume: float) -> None:
    if selected_voice is not None:
        engine.setProperty("voice", selected_voice.id)
    if rate > 0:
        engine.setProperty("rate", rate)
    engine.setProperty("volume", min(max(volume, 0.0), 1.0))


def print_engine_config(engine: Any | None, selected_voice: Any | None, dry_run: bool) -> None:
    current_voice = selected_voice.name if selected_voice is not None else "(engine default)"
    print("Windows TTS probe")
    if dry_run:
        print("mode: dry-run (no audio, no pyttsx3 engine required)")
        return
    print(f"voice: {current_voice}")
    print(f"rate: {engine.getProperty('rate')}")
    print(f"volume: {engine.getProperty('volume')}")


def load_chunks(path: Path, split_sentences: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if split_sentences:
        return split_text_to_sentences(text)
    return [line.strip() for line in text.splitlines() if line.strip()]


def split_text_to_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    parts = re.split(r"(?<=[.!?。！？])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def tts_worker(engine: Any, work_queue: queue.Queue[TextChunk | None], dry_run: bool) -> None:
    while True:
        chunk = work_queue.get()
        if chunk is None:
            work_queue.task_done()
            break

        start = time.perf_counter()
        queue_delay = start - chunk.received_at
        print(f"[speak_start {chunk.index:02d}] queue_delay_sec={queue_delay:.3f}")

        if not dry_run:
            engine.say(chunk.text)
            engine.runAndWait()
        else:
            time.sleep(min(max(len(chunk.text) / 25.0, 0.2), 3.0))

        end = time.perf_counter()
        print(f"[speak_done  {chunk.index:02d}] speak_sec={end - start:.3f}")
        work_queue.task_done()


if __name__ == "__main__":
    raise SystemExit(main())
