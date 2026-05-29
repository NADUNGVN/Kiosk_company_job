import argparse
import asyncio
import json
import os
import struct
import sys
import time
import wave
from pathlib import Path
from colorama import init, Fore, Back, Style

# Initialize colorama for terminal styling
init(autoreset=True)

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_SIZE = 1024

def generate_sample_wav(output_path: Path) -> None:
    """Generate a 3-second audio wave file (sine waves) for testing if no input is provided."""
    import numpy as np
    
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Không tìm thấy file âm thanh mẫu. Tự động sinh file test chất lượng cao...")
    duration = 3.0  # seconds
    sample_rate = DEFAULT_SAMPLE_RATE
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Create a combination of sine waves (chord)
    frequencies = [440, 554.37, 659.25]  # A major chord (A4, C#5, E5)
    audio_signal = np.zeros_like(t)
    for freq in frequencies:
        audio_signal += 0.3 * np.sin(2 * np.pi * freq * t)
        
    # Normalize to 16-bit range
    audio_signal = (audio_signal * 32767).astype(np.int16)
    
    # Save as WAV file
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(DEFAULT_CHANNELS)
        wf.setsampwidth(2)  # 2 bytes for 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_signal.tobytes())
    
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Đã tạo file âm thanh mẫu: {Fore.YELLOW}{output_path.absolute()}")

import threading
import queue
import tempfile
import wave as _wave

try:
    import winsound
    from winsdk.windows.media.speechsynthesis import SpeechSynthesizer
    from winsdk.windows.storage.streams import Buffer
    WINRT_AVAILABLE = True
except ImportError:
    WINRT_AVAILABLE = False

class KioskTTSPlayer:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = None
        self._stop_event = threading.Event()
        self._is_active = False
        self._is_speaking = False
        self._wav_path = None

    def start(self):
        self._is_active = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._is_active = False
        self.interrupt()
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def play_wav_bytes(self, wav_bytes: bytes):
        if self._is_active:
            self._queue.put(wav_bytes)

    def is_speaking(self) -> bool:
        return self._is_speaking or not self._queue.empty()

    def interrupt(self):
        # Hủy toàn bộ câu chưa phát trong hàng đợi
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        
        # Ngắt lập tức âm thanh đang phát
        self._stop_event.set()
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

        # Dọn dẹp file tạm nếu đang phát
        if self._wav_path and Path(self._wav_path).exists():
            try:
                Path(self._wav_path).unlink()
            except OSError:
                pass
            self._wav_path = None

    def _worker(self):
        while self._is_active:
            try:
                wav_bytes = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if wav_bytes:
                self._stop_event.clear()
                self._is_speaking = True
                try:
                    # Viết bytes WAV vào tệp tạm thời trên đĩa để phát bất đồng bộ an toàn
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                        wav_path = Path(handle.name)
                        handle.write(wav_bytes)
                    self._wav_path = wav_path
                    
                    if not self._stop_event.is_set():
                        # Phát âm thanh bất đồng bộ bằng tên tệp cực kỳ an toàn
                        winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                        
                        # Tính toán thời lượng phát của file WAV từ header để biết khi nào xong
                        duration = 5.0
                        try:
                            with _wave.open(str(wav_path), "rb") as wf:
                                duration = wf.getnframes() / float(wf.getframerate())
                        except Exception:
                            pass
                        
                        deadline = time.perf_counter() + duration + 0.5
                        while time.perf_counter() < deadline and not self._stop_event.is_set():
                            time.sleep(0.05)
                except Exception as e:
                    print(f"{Fore.RED}[TTS ERROR]{Style.RESET_ALL} Lỗi phát loa tại Kiosk: {e}")
                finally:
                    self._is_speaking = False
                    try:
                        if self._wav_path and Path(self._wav_path).exists():
                            Path(self._wav_path).unlink()
                    except OSError:
                        pass
                    self._wav_path = None
                    self._queue.task_done()

class ConnectionTestClient:
    def __init__(self, server_url: str, mode: str) -> None:
        self.server_url = server_url
        self.mode = mode
        self.stop_event = asyncio.Event()
        self.tts_player = None
        if mode == "stt":
            self.tts_player = KioskTTSPlayer()
            self.tts_player.start()

    async def run(self, source_mode: str, wav_path: Path | None = None) -> None:
        import websockets
        
        print(f"\n{Fore.GREEN}[CLIENT]{Style.RESET_ALL} Kết nối đến Server: {Fore.YELLOW}{self.server_url}")
        print(f"{Fore.GREEN}[CLIENT]{Style.RESET_ALL} Chế độ chạy: {Fore.CYAN}{self.mode.upper()}")
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"{Fore.GREEN}[CLIENT]{Style.RESET_ALL} {Back.GREEN}{Fore.BLACK} KẾT NỐI THÀNH CÔNG! {Style.RESET_ALL}")
                
                # Start background receiver task
                receiver_task = asyncio.create_task(self.receive_messages(websocket))
                
                if self.mode == "echo":
                    await self.run_echo_scenario(websocket)
                elif self.mode == "stt":
                    await self.run_stt_scenario(websocket, source_mode, wav_path)
                
                # Wait for receiver to finish or stop event to trigger
                await self.stop_event.wait()
                receiver_task.cancel()
                try:
                    await receiver_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            print(f"{Fore.RED}[CONNECTION ERROR] Không thể kết nối hoặc duy trì liên lạc với server: {e}")
            print(f"  {Fore.YELLOW}Gợi ý: Kiểm tra IP máy tính chạy server, cổng mạng (8010/8020) và cấu hình Firewall.")
        finally:
            if self.tts_player:
                self.tts_player.stop()

    async def receive_messages(self, websocket) -> None:
        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                
                # Handle connection bootstrap events from Zipformer server
                if msg_type == "hello":
                    print(f"\n{Fore.BLUE}[SERVER -> BOOTSTRAP]{Style.RESET_ALL} Session ID: {Fore.YELLOW}{data.get('sessionId')}")
                    print(f"  ASR Engines: {Fore.WHITE}{', '.join(data.get('engines', []))}")
                elif msg_type == "ready":
                    print(f"{Fore.GREEN}[SERVER -> READY]{Style.RESET_ALL} Server STT đã sẵn sàng nhận dữ liệu âm thanh.")
                
                # Handle test echo responses
                elif msg_type == "pong":
                    now = time.time()
                    client_ts = data.get("client_timestamp", 0.0)
                    rtt = (now - client_ts) * 1000.0
                    print(f"{Fore.GREEN}[PONG]{Style.RESET_ALL} Nhận Pong từ Laptop: '{data.get('message')}' | {Fore.YELLOW}RTT: {rtt:.2f} ms")
                
                # Handle mock echo stream chunks
                elif msg_type == "chunk":
                    chunk_idx = data.get("index", 0)
                    text = data.get("text", "")
                    is_final = data.get("is_final", False)
                    print(f"{Fore.CYAN}[STREAM CHUNK {chunk_idx:02d}]{Style.RESET_ALL} {Fore.WHITE}{text}")
                    if is_final:
                        print(f"{Fore.GREEN}[INFO] Luồng stream hoàn thành. Đóng kết nối.")
                        self.stop_event.set()
 
                # Handle ASR acknowledgement
                elif msg_type == "audio_received":
                    # Silent acknowledgement in STT mode to avoid terminal spam
                    pass
 
                # Handle actual STT realtime/final transcripts from Zipformer Server
                elif msg_type == "realtime":
                    text = data.get("text", "").strip()
                    if text:
                        # Print realtime with carriage return to overwrite previous line
                        sys.stdout.write(f"\r{Fore.YELLOW}[STT REALTIME] {Style.RESET_ALL}{text}")
                        sys.stdout.flush()
                        
                elif msg_type == "final":
                    text = data.get("text", "").strip()
                    if text:
                        # Overwrite the line and write final output in green/bold
                        sys.stdout.write(f"\r{Style.RESET_ALL}" + " " * 80 + "\r")  # clear line
                        print(f"{Fore.GREEN}{Style.BRIGHT}[STT FINAL] {Fore.WHITE}{text}")
                        sys.stdout.flush()
 
                elif msg_type == "llm_response":
                    text = data.get("text", "").strip()
                    if text:
                        print(f"{Fore.CYAN}{Style.BRIGHT}[LLM RESPONSE] {Fore.WHITE}{text}")
                        sys.stdout.flush()

                # Nhận sự kiện tts_audio từ server để phát loa cục bộ tại Kiosk từ bộ nhớ
                elif msg_type == "tts_audio":
                    audio_b64 = data.get("audio", "")
                    text = data.get("text", "").strip()
                    if audio_b64 and self.tts_player:
                        import base64
                        sys.stdout.write(f"\r{Style.RESET_ALL}" + " " * 80 + "\r")  # clear line
                        print(f"{Fore.MAGENTA}{Style.BRIGHT}[KIOSK SPEAKING] {Fore.WHITE}{text}")
                        sys.stdout.flush()
                        wav_bytes = base64.b64decode(audio_b64)
                        self.tts_player.play_wav_bytes(wav_bytes)

                # Nhận lệnh ngắt loa chủ động khi người dùng bắt đầu nói câu mới
                elif msg_type == "tts_interrupt":
                    if self.tts_player:
                        sys.stdout.write(f"\r{Style.RESET_ALL}" + " " * 80 + "\r")  # clear line
                        print(f"{Fore.RED}{Style.BRIGHT}[KIOSK TTS INTERRUPTED]{Style.RESET_ALL}")
                        sys.stdout.flush()
                        self.tts_player.interrupt()
 
                # Handle errors/warnings
                elif msg_type in ("error", "warning"):
                    color = Fore.RED if msg_type == "error" else Fore.YELLOW
                    print(f"\n{color}[SERVER {msg_type.upper()}]{Style.RESET_ALL} {data.get('message')}")
                    if msg_type == "error":
                        self.stop_event.set()
                        
        except Exception as e:
            print(f"\n{Fore.RED}[RECEIVER ERROR]{Style.RESET_ALL} Lỗi luồng nhận: {e}")
            self.stop_event.set()

    async def run_echo_scenario(self, websocket) -> None:
        print(f"\n{Fore.BLUE}[ECHO SCENARIO]{Style.RESET_ALL} Đang gửi tin nhắn Ping để kiểm tra độ trễ mạng...")
        ping_msg = {
            "type": "ping",
            "timestamp": time.time()
        }
        await websocket.send(json.dumps(ping_msg))
        
        # Also request a test simulated stream response
        await asyncio.sleep(0.5)
        print(f"\n{Fore.BLUE}[ECHO SCENARIO]{Style.RESET_ALL} Đang gửi yêu cầu 'start_test' nhận stream từ Laptop...")
        await websocket.send(json.dumps({"type": "start_test"}))

    async def run_stt_scenario(self, websocket, source_mode: str, wav_path: Path | None) -> None:
        # Zipformer STT server requires starting command
        print(f"\n{Fore.BLUE}[STT SCENARIO]{Style.RESET_ALL} Gửi lệnh khởi động STT...")
        await websocket.send(json.dumps({"type": "start"}))
        await asyncio.sleep(0.5) # Wait for backend ready

        if source_mode == "file":
            await self.stream_wav_file(websocket, wav_path)
        elif source_mode == "mic":
            await self.stream_microphone(websocket)

    async def stream_wav_file(self, websocket, wav_path: Path) -> None:
        print(f"\n{Fore.BLUE}[FILE STREAM]{Style.RESET_ALL} Đang đọc file: {Fore.YELLOW}{wav_path.name}")
        
        try:
            with wave.open(str(wav_path), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                
                print(f"  {Fore.CYAN}Chi tiết WAV:{Style.RESET_ALL} {sample_rate}Hz | {channels} channels | {sample_width * 8}-bit | {n_frames} frames")
                
                # Check format compatibility (Zipformer expects 16kHz, mono, s16le)
                if channels != 1 or sample_rate != 16000 or sample_width != 2:
                    print(f"  {Fore.YELLOW}[WARNING]{Style.RESET_ALL} File WAV không phải định dạng chuẩn (16kHz, Mono, 16-bit). "
                          f"Zipformer Server có thể tự động resample nhưng nên đổi sang chuẩn 16kHz mono để tối ưu RTT.")

                # Read and send in chunks
                metadata = {
                    "sampleRate": sample_rate,
                    "channels": channels,
                    "format": "pcm_s16le"
                }
                metadata_bytes = json.dumps(metadata).encode("utf-8")
                metadata_len = len(metadata_bytes)

                chunk_duration = DEFAULT_CHUNK_SIZE / sample_rate
                bytes_sent = 0

                print(f"  {Fore.BLUE}[INFO]{Style.RESET_ALL} Bắt đầu truyền dữ liệu âm thanh nhị phân...")
                
                while True:
                    data = wf.readframes(DEFAULT_CHUNK_SIZE)
                    if not data:
                        break
                    
                    # Package packet: [4B metadata len] + [metadata bytes] + [raw pcm bytes]
                    header = struct.pack("<I", metadata_len)
                    packet = header + metadata_bytes + data
                    
                    await websocket.send(packet)
                    bytes_sent += len(data)
                    
                    # Sleep to simulate real-time playback streaming speed
                    await asyncio.sleep(chunk_duration)
                
                print(f"  {Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Truyền xong toàn bộ file: {Fore.YELLOW}{bytes_sent} bytes audio data.")
                
                # Send stop command after finishing file transmission
                await asyncio.sleep(1.5) # Wait for final processing
                print(f"\n{Fore.BLUE}[STT SCENARIO]{Style.RESET_ALL} Gửi lệnh dừng STT...")
                await websocket.send(json.dumps({"type": "stop"}))
                await asyncio.sleep(0.5)
                self.stop_event.set()

        except Exception as e:
            print(f"{Fore.RED}[FILE STREAM ERROR]{Style.RESET_ALL} Lỗi truyền file WAV: {e}")
            self.stop_event.set()

    async def stream_microphone(self, websocket) -> None:
        try:
            import pyaudio
        except ImportError:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Thư viện PyAudio chưa được cài đặt. Không thể sử dụng mic.")
            print(f"  {Fore.YELLOW}Hãy cài đặt bằng: pip install pyaudio")
            self.stop_event.set()
            return

        p = pyaudio.PyAudio()
        
        try:
            # Open mic stream: 16kHz, mono, 16-bit PCM
            stream = p.open(
                format=pyaudio.paInt16,
                channels=DEFAULT_CHANNELS,
                rate=DEFAULT_SAMPLE_RATE,
                input=True,
                frames_per_buffer=DEFAULT_CHUNK_SIZE
            )
        except Exception as e:
            print(f"{Fore.RED}[MIC ERROR] Không thể mở thiết bị Microphone: {e}")
            print(f"  {Fore.YELLOW}Gợi ý: Kiểm tra xem thiết bị Microphone đã được bật và cấp quyền trên Windows chưa.")
            p.terminate()
            self.stop_event.set()
            return

        print(f"\n{Fore.MAGENTA}[MICROPHONE STREAM]{Style.RESET_ALL} Microphone đang BẬT! Nói điều gì đó bằng Tiếng Việt...")
        print(f"  {Fore.YELLOW}Nhấn Ctrl+C để kết thúc ghi âm và xem kết quả.")
        
        metadata = {
            "sampleRate": DEFAULT_SAMPLE_RATE,
            "channels": DEFAULT_CHANNELS,
            "format": "pcm_s16le"
        }
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        metadata_len = len(metadata_bytes)

        try:
            while not self.stop_event.is_set():
                # Read raw frames from mic (non-blocking chunk fetch)
                # Using exception_on_overflow=False prevents crashes when network hiccups occur
                data = stream.read(DEFAULT_CHUNK_SIZE, exception_on_overflow=False)
                
                # NẾU KIOSK ĐANG PHÁT LOA (TTS), KHÔNG GỬI LUỒNG GHI ÂM SANG SERVER
                # Điều này giúp loại bỏ 100% tiếng vọng từ loa phát (speaker driver/acoustic)
                if self.tts_player and self.tts_player.is_speaking():
                    await asyncio.sleep(0.01)
                    continue

                header = struct.pack("<I", metadata_len)
                packet = header + metadata_bytes + data
                await websocket.send(packet)
                
                # yield control to let receiver task process server replies
                await asyncio.sleep(0.001)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n{Fore.RED}[MIC STREAM ERROR]{Style.RESET_ALL} Lỗi ghi âm/stream: {e}")
        finally:
            print(f"\n{Fore.BLUE}[SYSTEM]{Style.RESET_ALL} Đang tắt Microphone...")
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            p.terminate()
            
            # Send stop command to gracefully stop STT on server
            try:
                await websocket.send(json.dumps({"type": "stop"}))
            except Exception:
                pass
            self.stop_event.set()

def main() -> None:
    parser = argparse.ArgumentParser(description="WebSocket client to test connectivity and audio streaming between Kiosk and Laptop.")
    parser.add_argument(
        "--server", 
        default="ws://127.0.0.1:8020", 
        help="Server WebSocket URL, e.g. ws://127.0.0.1:8020 (echo server) or ws://127.0.0.1:8010/ws/transcribe (Zipformer server)"
    )
    parser.add_argument(
        "--mode", 
        choices=("echo", "stt"), 
        default="echo", 
        help="Testing mode: 'echo' for simple network RTT test, 'stt' to stream audio and receive ASR text."
    )
    parser.add_argument(
        "--source", 
        choices=("file", "mic"), 
        default="file", 
        help="Audio source in STT mode: 'file' (local wav) or 'mic' (microphone input)."
    )
    parser.add_argument(
        "--file", 
        default="sample_voice_input.wav", 
        help="Path to WAV file to send in 'file' source mode. Will be auto-generated if missing."
    )
    
    args = parser.parse_args()
    
    # Auto-generate wav file if source is file and target path does not exist
    wav_path = Path(args.file)
    if args.mode == "stt" and args.source == "file" and not wav_path.exists():
        try:
            generate_sample_wav(wav_path)
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Không thể tự sinh file WAV mẫu: {e}. Vui lòng chuẩn bị một file WAV 16kHz mono.")
            sys.exit(1)

    client = ConnectionTestClient(args.server, args.mode)
    
    try:
        asyncio.run(client.run(args.source, wav_path))
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[CLIENT]{Style.RESET_ALL} Đã dừng chương trình client.")
        client.stop_event.set()

if __name__ == "__main__":
    main()
