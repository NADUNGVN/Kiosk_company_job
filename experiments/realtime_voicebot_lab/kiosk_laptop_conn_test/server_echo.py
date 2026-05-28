import argparse
import asyncio
import json
import struct
import time
import wave
from colorama import init, Fore, Style
import websockets


# Initialize colorama for Windows terminal colors
init(autoreset=True)

class ConnectionTestServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.output_dir = Path(__file__).resolve().parent / "received_audio"
        self.output_dir.mkdir(exist_ok=True)
        self.active_sessions = {}

    async def start(self) -> None:
        print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} Khởi tạo Server Echo Test trên {self.host}:{self.port}...")
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} Server đang lắng nghe. Nhấn Ctrl+C để dừng.")
            await asyncio.Future()  # run forever

    async def handler(self, websocket) -> None:
        peer = websocket.remote_address
        session_id = f"{peer[0]}:{peer[1]}"
        print(f"\n{Fore.CYAN}[CONN]{Style.RESET_ALL} Client kết nối từ: {Fore.YELLOW}{session_id}")
        
        # Initialize storage for potential audio recording
        self.active_sessions[session_id] = {
            "audio_frames": [],
            "metadata": None,
            "connected_at": time.time(),
            "bytes_received": 0
        }

        try:
            async for message in websocket:
                if isinstance(message, str):
                    await self.handle_text(websocket, session_id, message)
                elif isinstance(message, bytes):
                    await self.handle_binary(websocket, session_id, message)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"{Fore.RED}[DISCONN]{Style.RESET_ALL} Client {session_id} ngắt kết nối ({e.code}: {e.reason})")
        finally:
            await self.cleanup_session(session_id)

    async def handle_text(self, websocket, session_id: str, message: str) -> None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print(f"{Fore.RED}[ERROR] [{session_id}]{Style.RESET_ALL} Tin nhắn văn bản không hợp lệ: {message}")
            return

        msg_type = data.get("type")
        print(f"{Fore.BLUE}[TEXT] [{session_id}]{Style.RESET_ALL} Nhận JSON: {Fore.WHITE}{message}")

        if msg_type == "ping":
            client_ts = data.get("timestamp", 0.0)
            now = time.time()
            rtt_est = (now - client_ts) * 1000.0
            response = {
                "type": "pong",
                "timestamp": now,
                "client_timestamp": client_ts,
                "message": "Chào Kiosk! Kết nối mạng hoạt động tốt."
            }
            await websocket.send(json.dumps(response))
            print(f"  {Fore.GREEN}->[SEND]{Style.RESET_ALL} Phản hồi Pong. Ước tính RTT mạng 1 chiều: {Fore.YELLOW}{rtt_est:.2f}ms")

        elif msg_type == "start_test":
            print(f"{Fore.GREEN}[START] [{session_id}]{Style.RESET_ALL} Bắt đầu kịch bản test STT giả lập...")
            # Stream simulated ASR response chunks back to client to test streaming receipt
            response_chunks = [
                "Xin chào Kiosk,",
                " đây là phản hồi kiểm tra",
                " kết nối mạng LAN.",
                " Tín hiệu truyền nhị phân và",
                " điều hướng gói tin hoạt động ổn định!",
                " Sẵn sàng kết nối với",
                " server STT Zipformer thật!"
            ]
            
            for i, chunk in enumerate(response_chunks, start=1):
                await asyncio.sleep(0.4)  # Simulate processing/network delay
                is_final = (i == len(response_chunks))
                payload = {
                    "type": "chunk",
                    "index": i,
                    "text": chunk,
                    "is_final": is_final
                }
                await websocket.send(json.dumps(payload))
                print(f"  {Fore.GREEN}->[SEND_CHUNK {i:02d}]{Style.RESET_ALL} {Fore.WHITE}{chunk}")
            
            print(f"{Fore.GREEN}[DONE] [{session_id}]{Style.RESET_ALL} Hoàn thành gửi stream giả lập.")

        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Không hỗ trợ command: {msg_type}"
            }))

    async def handle_binary(self, websocket, session_id: str, message: bytes) -> None:
        session = self.active_sessions.get(session_id)
        if not session:
            return

        t_start = time.perf_counter()
        # Parse standard Zipformer-like packet: [4 bytes json_len] + [JSON Metadata] + [PCM bytes]
        if len(message) < 4:
            print(f"{Fore.RED}[BINARY] [{session_id}]{Style.RESET_ALL} Gói tin quá ngắn (< 4 bytes)")
            return

        json_len = struct.unpack("<I", message[:4])[0]
        if len(message) < 4 + json_len:
            print(f"{Fore.RED}[BINARY] [{session_id}]{Style.RESET_ALL} Gói tin bị vỡ hoặc thiếu JSON metadata")
            return

        try:
            metadata_str = message[4:4+json_len].decode("utf-8")
            metadata = json.loads(metadata_str)
        except Exception as e:
            print(f"{Fore.RED}[BINARY] [{session_id}]{Style.RESET_ALL} Lỗi parse JSON metadata: {e}")
            return

        audio_data = message[4+json_len:]
        session["bytes_received"] += len(audio_data)

        # Print telemetry
        t_elapsed = (time.perf_counter() - t_start) * 1000.0
        print(f"{Fore.MAGENTA}[AUDIO] [{session_id}]{Style.RESET_ALL} "
              f"Nhận gói {Fore.YELLOW}{len(message)} B{Style.RESET_ALL} "
              f"(Meta={json_len}B, Audio={len(audio_data)}B) "
              f"trong {Fore.YELLOW}{t_elapsed:.2f}ms. "
              f"Tổng nhận: {Fore.CYAN}{session['bytes_received']} B")

        # Save metadata and accumulate audio frames
        if not session["metadata"]:
            session["metadata"] = metadata
            print(f"  {Fore.BLUE}[INFO]{Style.RESET_ALL} Cấu hình âm thanh client gửi: {metadata}")

        session["audio_frames"].append(audio_data)

        # Echo acknowledgement back to client
        ack = {
            "type": "audio_received",
            "bytes": len(audio_data),
            "total_bytes": session["bytes_received"]
        }
        await websocket.send(json.dumps(ack))

    async def cleanup_session(self, session_id: str) -> None:
        session = self.active_sessions.pop(session_id, None)
        if not session or not session["audio_frames"]:
            return

        metadata = session["metadata"] or {"sampleRate": 16000, "channels": 1, "format": "pcm_s16le"}
        sample_rate = metadata.get("sampleRate", 16000)
        channels = metadata.get("channels", 1)

        # Write accumulated audio to a wave file
        filename = f"test_record_{int(time.time())}_{session_id.replace(':', '_')}.wav"
        file_path = self.output_dir / filename
        
        try:
            with wave.open(str(file_path), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit PCM (pcm_s16le)
                wf.setframerate(sample_rate)
                wf.writeframes(b"".join(session["audio_frames"]))
            
            print(f"{Fore.GREEN}[SAVE]{Style.RESET_ALL} Đã lưu file âm thanh truyền nhận hoàn tất tại:")
            print(f"  {Fore.YELLOW}{file_path.absolute()}")
            print(f"  Dung lượng: {len(b''.join(session['audio_frames']))} bytes | Kênh: {channels} | Tần số: {sample_rate}Hz")
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Không thể lưu file WAV: {e}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Echo WebSocket server for network and packet format testing.")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8020, help="Port to bind (default: 8020)")
    args = parser.parse_args()

    server = ConnectionTestServer(args.host, args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[SYSTEM]{Style.RESET_ALL} Server đã tắt.")

if __name__ == "__main__":
    main()
