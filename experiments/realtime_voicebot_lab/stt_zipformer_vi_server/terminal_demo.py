import argparse
import threading
import time
import wave
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from scipy.signal import resample_poly

from RealtimeSTT import AudioToTextRecorder
from RealtimeSTT.transcription_engines import TranscriptionEngineConfig
from RealtimeSTT.transcription_engines.sherpa_onnx_engine import (
    DEFAULT_SHERPA_ONNX_ZIPFORMER_VI_MODEL,
    SherpaOnnxZipformerEngine,
)


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = (
    REPO_ROOT
    / "models"
    / DEFAULT_SHERPA_ONNX_ZIPFORMER_VI_MODEL
)
DEFAULT_SAMPLE_WAV = REPO_ROOT / "models" / "vi.wav"


def normalize_display_text(text, raw_case=False):
    text = " ".join((text or "").strip().split())
    if raw_case or not text:
        return text
    text = text.lower()
    return text[0].upper() + text[1:]


def read_wav(path):
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width != 2:
        raise ValueError(f"{path} must be 16-bit PCM WAV")

    audio = np.frombuffer(frames, dtype=np.int16)
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
    audio = audio.astype(np.float32) / 32768.0

    if sample_rate != 16000:
        audio = resample_poly(audio, 16000, sample_rate).astype(np.float32)
        sample_rate = 16000

    return audio, sample_rate


def make_engine(model_dir, threads):
    return SherpaOnnxZipformerEngine(
        TranscriptionEngineConfig(
            model=str(model_dir),
            device="cpu",
            engine_options={
                "num_threads": threads,
                "provider": "cpu",
                "language": "vi",
            },
        )
    )


def transcribe_wav(args):
    audio, sample_rate = read_wav(args.wav)
    engine = make_engine(args.model_dir, args.threads)
    started = time.time()
    result = engine.transcribe(audio, language="vi")
    elapsed = time.time() - started
    duration = len(audio) / float(sample_rate)

    console = Console()
    console.print(normalize_display_text(result.text, raw_case=args.raw_case), style="bold cyan")
    console.print(f"duration={duration:.3f}s elapsed={elapsed:.3f}s rtf={elapsed / duration:.3f}")


class DemoDisplay:
    def __init__(self, raw_case=False):
        self.raw_case = raw_case
        self.console = Console()
        self.lock = threading.Lock()
        self.final_segments = []
        self.live_text = ""
        self.status = "Speak Vietnamese. Press Ctrl+C to stop."
        self.live = Live(self.render(), console=self.console, refresh_per_second=12, screen=False)

    def __enter__(self):
        self.live.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.live.stop()

    def set_live(self, text):
        with self.lock:
            self.live_text = normalize_display_text(text, raw_case=self.raw_case)
            self.live.update(self.render())

    def add_final(self, text):
        text = normalize_display_text(text, raw_case=self.raw_case)
        if not text:
            return
        with self.lock:
            self.final_segments.append(text)
            self.live_text = ""
            self.live.update(self.render())

    def render(self):
        output = Text()
        if not self.final_segments and not self.live_text:
            output.append(self.status, style="bold cyan")
        else:
            for index, segment in enumerate(self.final_segments[-8:]):
                style = "yellow" if index % 2 == 0 else "cyan"
                output.append(segment, style=style)
                output.append(" ")
            if self.live_text:
                output.append(self.live_text, style="bold yellow")
        return Panel(output, title="[bold green]Vietnamese Zipformer Realtime STT[/bold green]", border_style="green")


def run_microphone(args):
    with DemoDisplay(raw_case=args.raw_case) as display:
        recorder = AudioToTextRecorder(
            transcription_engine="sherpa_onnx_zipformer",
            model=str(args.model_dir),
            realtime_transcription_engine="sherpa_onnx_zipformer",
            realtime_model_type=str(args.model_dir),
            language="vi",
            device="cpu",
            input_device_index=args.input_device_index,
            enable_realtime_transcription=True,
            on_realtime_transcription_update=display.set_live,
            spinner=False,
            no_log_file=True,
            silero_sensitivity=args.silero_sensitivity,
            webrtc_sensitivity=args.webrtc_sensitivity,
            post_speech_silence_duration=args.post_speech_silence_duration,
            min_length_of_recording=args.min_length_of_recording,
            min_gap_between_recordings=0,
            realtime_processing_pause=args.realtime_processing_pause,
            realtime_transcription_use_syllable_boundaries=True,
            realtime_boundary_detector_sensitivity=0.6,
            realtime_boundary_followup_delays=(0.1, 0.2, 0.4),
            transcription_engine_options={
                "num_threads": args.threads,
                "provider": "cpu",
                "language": "vi",
            },
            realtime_transcription_engine_options={
                "num_threads": args.realtime_threads,
                "provider": "cpu",
                "language": "vi",
            },
        )

        try:
            while True:
                recorder.text(display.add_final)
        except KeyboardInterrupt:
            pass
        finally:
            recorder.shutdown()


def parse_args():
    parser = argparse.ArgumentParser(description="Clean Vietnamese Zipformer realtime STT demo")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--wav", type=Path)
    parser.add_argument("--sample", action="store_true", help="Transcribe the bundled Vietnamese sample wav")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--realtime-threads", type=int, default=2)
    parser.add_argument("--input-device-index", type=int)
    parser.add_argument("--raw-case", action="store_true", help="Keep model casing instead of sentence-style display")
    parser.add_argument("--silero-sensitivity", type=float, default=0.05)
    parser.add_argument("--webrtc-sensitivity", type=int, default=3)
    parser.add_argument("--post-speech-silence-duration", type=float, default=0.55)
    parser.add_argument("--min-length-of-recording", type=float, default=0.2)
    parser.add_argument("--realtime-processing-pause", type=float, default=0.2)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.sample and args.wav is None:
        args.wav = DEFAULT_SAMPLE_WAV
    if not args.model_dir.is_dir():
        raise SystemExit(f"Model directory not found: {args.model_dir}")
    if args.wav:
        transcribe_wav(args)
    else:
        run_microphone(args)
