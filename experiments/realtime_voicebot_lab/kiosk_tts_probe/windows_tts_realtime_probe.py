from __future__ import annotations

import argparse
import asyncio
import queue
import re
import tempfile
import threading
import time
import winreg
import winsound
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STREAM_FILE = SCRIPT_DIR / "sample_reply_stream.txt"


@dataclass
class TextChunk:
    index: int
    text: str
    received_at: float


@dataclass
class VoiceInfo:
    backend: str
    id: str
    name: str
    language: str = ""
    gender: str = ""
    raw: Any | None = None


class TtsBackend(Protocol):
    name: str

    def speak(self, text: str) -> None:
        ...

    def stop(self) -> None:
        ...


class DryRunBackend:
    name = "dry-run"

    def speak(self, text: str) -> None:
        time.sleep(min(max(len(text) / 25.0, 0.2), 3.0))

    def stop(self) -> None:
        return


class SapiBackend:
    name = "sapi"

    def __init__(self, voice: VoiceInfo | None, rate: int, volume: float) -> None:
        pyttsx3 = import_pyttsx3()
        self.engine = pyttsx3.init()
        if voice is not None:
            self.engine.setProperty("voice", voice.id)
        if rate > 0:
            self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", clamp(volume, 0.0, 1.0))
        self.voice = voice

    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()

    def stop(self) -> None:
        self.engine.stop()


class WinRtBackend:
    name = "winrt"

    def __init__(self, voice: VoiceInfo | None, rate: int, volume: float) -> None:
        from winsdk.windows.media.speechsynthesis import SpeechSynthesizer

        self.synthesizer = SpeechSynthesizer()
        self.voice = voice
        if voice is not None and voice.raw is not None:
            self.synthesizer.voice = voice.raw

        # WinRT uses a multiplier. Keep SAPI's default-ish 165 as 1.0.
        if rate > 0:
            self.synthesizer.options.speaking_rate = clamp(rate / 165.0, 0.5, 2.0)
        self.synthesizer.options.audio_volume = clamp(volume, 0.0, 1.0)

    def speak(self, text: str) -> None:
        asyncio.run(self._speak_async(text))

    async def _speak_async(self, text: str) -> None:
        from winsdk.windows.storage.streams import Buffer

        stream = await self.synthesizer.synthesize_text_to_stream_async(text)
        buffer = Buffer(stream.size)
        wav_buffer = await stream.read_async(buffer, stream.size, 0)
        wav_bytes = bytes(wav_buffer)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            wav_path = Path(handle.name)
            handle.write(wav_bytes)

        try:
            winsound.PlaySound(str(wav_path), winsound.SND_FILENAME)
        finally:
            try:
                wav_path.unlink()
            except OSError:
                pass

    def stop(self) -> None:
        winsound.PlaySound(None, winsound.SND_PURGE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe Windows TTS realtime-like chunk playback with SAPI or WinRT voices."
    )
    parser.add_argument("--list-voices", action="store_true", help="List SAPI and WinRT voices and exit.")
    parser.add_argument(
        "--backend",
        choices=("auto", "sapi", "winrt"),
        default="auto",
        help="TTS backend. Use winrt for Windows modern/OneCore voices such as Microsoft An.",
    )
    parser.add_argument(
        "--voice-contains",
        default="",
        help='Pick the first voice whose id/name/language contains this text, e.g. "Microsoft An" or "vi-VN".',
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

    if args.list_voices:
        print_all_voices()
        return 0

    backend = build_backend(args)
    print_backend_config(backend)

    chunks = load_chunks(Path(args.stream_file), args.split_sentences)
    if not chunks:
        raise RuntimeError(f"No text chunks found in {args.stream_file}")

    work_queue: queue.Queue[TextChunk | None] = queue.Queue()
    worker = threading.Thread(
        target=tts_worker,
        args=(backend, work_queue),
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
        backend.stop()
        work_queue.put(None)
        return 130

    total = time.perf_counter() - started_at
    print("")
    print(f"Done. backend={backend.name} chunks={len(chunks)} total_sec={total:.3f}")
    return 0


def build_backend(args: argparse.Namespace) -> TtsBackend:
    if args.dry_run:
        return DryRunBackend()

    sapi_voices = list_sapi_voices(silent=True)
    winrt_voices = list_winrt_voices(silent=True)
    selected = select_voice(args.voice_contains, args.backend, sapi_voices, winrt_voices)

    if args.backend == "sapi" or (args.backend == "auto" and selected.backend == "sapi"):
        return SapiBackend(selected, args.rate, args.volume)
    if args.backend == "winrt" or (args.backend == "auto" and selected.backend == "winrt"):
        return WinRtBackend(selected, args.rate, args.volume)

    # No voice filter: default to SAPI if available because pyttsx3 is the
    # simplest backend. Fall back to WinRT when only OneCore voices exist.
    if args.backend == "auto":
        if sapi_voices:
            return SapiBackend(None, args.rate, args.volume)
        if winrt_voices:
            return WinRtBackend(None, args.rate, args.volume)

    raise RuntimeError("No usable TTS backend found.")


def import_pyttsx3() -> Any:
    try:
        import pyttsx3
    except ImportError as exc:
        raise ImportError(
            "Missing dependency: pyttsx3. Install it with:\n"
            "python -m pip install -r requirements-kiosk.txt"
        ) from exc
    return pyttsx3


def import_winsdk_speech() -> Any:
    try:
        from winsdk.windows.media.speechsynthesis import SpeechSynthesizer
    except ImportError as exc:
        raise ImportError(
            "Missing dependency: winsdk. Install it with:\n"
            "python -m pip install -r requirements-kiosk.txt\n"
            "WinRT backend is required for OneCore voices such as Microsoft An."
        ) from exc
    return SpeechSynthesizer


def print_all_voices() -> None:
    print("SAPI voices visible to pyttsx3:")
    sapi_voices = list_sapi_voices(silent=False)
    print_voice_list(sapi_voices)
    print("")
    print("WinRT / OneCore voices visible to Windows modern TTS:")
    winrt_voices = list_winrt_voices(silent=False)
    print_voice_list(winrt_voices)
    print("")

    print("OneCore voices found directly in Windows registry:")
    registry_voices = list_onecore_registry_voices()
    print_voice_list(registry_voices)
    print("")

    registry_has_an = any("MSTTS_V110_viVN_An".casefold() in v.id.casefold() for v in registry_voices)
    winrt_has_an = any("Microsoft An".casefold() in v.name.casefold() for v in winrt_voices)
    sapi_has_an = any("Microsoft An".casefold() in v.name.casefold() for v in sapi_voices)

    if winrt_has_an and not sapi_has_an:
        print(
            "Note: Microsoft An is commonly a WinRT/OneCore voice. "
            "Use --backend winrt --voice-contains \"Microsoft An\"."
        )
    elif registry_has_an and not winrt_has_an:
        print(
            "Warning: MSTTS_V110_viVN_An exists in the registry, but WinRT "
            "SpeechSynthesizer.all_voices did not expose it to Python. "
            "This is an OS/runtime exposure issue, not a missing registry key."
        )
        print("Try these on the kiosk:")
        print("  1) Restart Windows after installing Vietnamese speech/TTS.")
        print("  2) Run: python -m pip install --force-reinstall winsdk")
        print("  3) Open Windows Settings > Time & language > Speech and confirm Vietnamese voice is usable.")
        print("  4) If WinRT still returns none, use a SAPI voice for this probe or expose/copy OneCore voice to SAPI manually.")


def list_sapi_voices(silent: bool = False) -> list[VoiceInfo]:
    try:
        pyttsx3 = import_pyttsx3()
        engine = pyttsx3.init()
        voices = engine.getProperty("voices") or []
    except Exception as exc:
        if not silent:
            print(f"Could not list SAPI voices: {exc}")
        return []

    result = []
    for voice in voices:
        result.append(
            VoiceInfo(
                backend="sapi",
                id=str(getattr(voice, "id", "")),
                name=str(getattr(voice, "name", "")),
                language=str(getattr(voice, "languages", "")),
                gender=str(getattr(voice, "gender", "")),
                raw=voice,
            )
        )
    return result


def list_winrt_voices(silent: bool = False) -> list[VoiceInfo]:
    try:
        SpeechSynthesizer = import_winsdk_speech()
        voices = list(SpeechSynthesizer.all_voices)
    except Exception as exc:
        if not silent:
            print(f"Could not list WinRT voices: {exc}")
        return []

    result = []
    for voice in voices:
        result.append(
            VoiceInfo(
                backend="winrt",
                id=str(getattr(voice, "id", "")),
                name=str(getattr(voice, "display_name", "")),
                language=str(getattr(voice, "language", "")),
                gender=str(getattr(voice, "gender", "")),
                raw=voice,
            )
        )
    return result


def list_onecore_registry_voices() -> list[VoiceInfo]:
    base_path = r"SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens"
    result: list[VoiceInfo] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path) as base_key:
            index = 0
            while True:
                try:
                    token_name = winreg.EnumKey(base_key, index)
                except OSError:
                    break
                index += 1

                token_path = base_path + "\\" + token_name
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, token_path) as token_key:
                        display_name = read_reg_value(token_key, "")
                        language = read_reg_value(token_key, "Language")
                        if not language:
                            language = language_from_token(token_name)
                        result.append(
                            VoiceInfo(
                                backend="registry",
                                id=token_name,
                                name=display_name or token_name,
                                language=language,
                            )
                        )
                except OSError:
                    continue
    except OSError:
        return []
    return result


def read_reg_value(key: Any, value_name: str) -> str:
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
    except OSError:
        return ""
    return str(value)


def language_from_token(token_name: str) -> str:
    match = re.search(r"_([a-z]{2})([A-Z]{2})_", token_name)
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}"


def print_voice_list(voices: list[VoiceInfo]) -> None:
    if not voices:
        print("  (none)")
        return
    for index, voice in enumerate(voices, start=1):
        print(f"[{index:02d}]")
        print(f"  backend: {voice.backend}")
        print(f"  id: {voice.id}")
        print(f"  name: {voice.name}")
        print(f"  language: {voice.language}")
        print(f"  gender: {voice.gender}")


def select_voice(
    contains: str,
    backend: str,
    sapi_voices: list[VoiceInfo],
    winrt_voices: list[VoiceInfo],
) -> VoiceInfo:
    candidate_groups: list[list[VoiceInfo]]
    if backend == "sapi":
        candidate_groups = [sapi_voices]
    elif backend == "winrt":
        candidate_groups = [winrt_voices]
    else:
        # With an explicit voice filter, prefer modern WinRT/OneCore voices
        # first so `--voice-contains "Microsoft An"` works without requiring
        # `--backend winrt`. Without a filter, keep SAPI as the simple default.
        candidate_groups = [winrt_voices, sapi_voices] if contains else [sapi_voices, winrt_voices]

    if not contains:
        for group in candidate_groups:
            if group:
                return group[0]
        raise RuntimeError("No voices available.")

    needle = contains.casefold()
    for group in candidate_groups:
        for voice in group:
            haystack = " ".join([voice.id, voice.name, voice.language, voice.backend]).casefold()
            if needle in haystack:
                return voice

    available = "; ".join(
        f"{voice.backend}:{voice.name} ({voice.language})"
        for voice in sapi_voices + winrt_voices
    )
    raise RuntimeError(
        f"No {backend} voice contains {contains!r}. Available voices: {available}. "
        "If the voice appears only under WinRT/OneCore, run with --backend winrt. "
        "If WinRT lists none but registry has MSTTS_V110_viVN_An, run "
        "expose_onecore_voice_to_sapi.ps1 as Administrator and then use --backend sapi."
    )


def print_backend_config(backend: TtsBackend) -> None:
    print("Windows TTS realtime probe")
    print(f"backend: {backend.name}")
    voice = getattr(backend, "voice", None)
    if voice is not None:
        print(f"voice: {voice.name} ({voice.language})")


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


def tts_worker(backend: TtsBackend, work_queue: queue.Queue[TextChunk | None]) -> None:
    while True:
        chunk = work_queue.get()
        if chunk is None:
            work_queue.task_done()
            break

        start = time.perf_counter()
        queue_delay = start - chunk.received_at
        print(f"[speak_start {chunk.index:02d}] queue_delay_sec={queue_delay:.3f}")

        backend.speak(chunk.text)

        end = time.perf_counter()
        print(f"[speak_done  {chunk.index:02d}] speak_sec={end - start:.3f}")
        work_queue.task_done()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


if __name__ == "__main__":
    raise SystemExit(main())
