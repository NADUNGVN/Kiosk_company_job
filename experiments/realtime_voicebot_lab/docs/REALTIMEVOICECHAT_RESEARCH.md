# Nghiên Cứu Repo KoljaB/RealtimeVoiceChat

## Mục Đích

Tài liệu này ghi lại phần học hỏi ban đầu từ dự án
`https://github.com/KoljaB/RealtimeVoiceChat` để đánh giá khả năng áp dụng vào
kiến trúc kiosk hai máy.

## Kiến Trúc Của RealtimeVoiceChat

Dự án này hướng đến hội thoại giọng nói gần realtime với AI. Theo README, hệ
thống dùng kiến trúc client-server:

- Browser capture voice.
- Audio chunk được gửi qua WebSocket đến Python backend.
- Backend dùng `RealtimeSTT` để chuyển audio thành text.
- Text được gửi vào LLM như Ollama hoặc OpenAI.
- Text response được chuyển thành audio bằng `RealtimeTTS`.
- Audio response được stream về browser.
- Có xử lý interruption để người dùng có thể chen lời.

Stack chính được ghi trong README:

- Backend: Python, FastAPI.
- Frontend: HTML/CSS/JavaScript, Web Audio API, AudioWorklets.
- Communication: WebSockets.
- STT: `RealtimeSTT`.
- TTS: `RealtimeTTS`.
- Turn detection: `turndetect.py`.
- LLM backend: Ollama hoặc OpenAI.
- TTS engine: Kokoro, Coqui, Orpheus.

## Giá Trị Có Thể Học Hỏi

Các phần có thể học để áp dụng vào dự án kiosk:

- Cách stream audio chunk qua WebSocket.
- Cách tổ chức session hội thoại realtime.
- Cách xử lý turn-taking và silence detection.
- Cách thiết kế interruption khi người dùng chen lời.
- Cách tách module STT, LLM và TTS.

## Điểm Không Nên Copy Nguyên

Không nên đưa nguyên framework vào project ở giai đoạn này vì:

- Dự án gốc đã ghi rõ không còn được maintainer hỗ trợ tích cực.
- Stack phụ thuộc nhiều thư viện nặng: `RealtimeSTT`, `RealtimeTTS`, torch,
  torchaudio, transformers.
- Kiosk của mình không cần TTS server-side từ framework đó, vì hướng hiện tại là
  Windows 11 TTS local trên kiosk.
- Dự án gốc dùng browser làm client audio, còn kiosk runtime của mình sẽ là app
  Python local kết hợp camera/vision/ghi âm/TTS.

## Hướng Áp Dụng Đề Xuất

Không dùng nguyên workspace của RealtimeVoiceChat ngay. Thay vào đó:

1. Học protocol và state machine.
2. Tự viết prototype nhỏ phù hợp pipeline hai máy.
3. Dùng faster-whisper + RAG theo định hướng của dự án hiện tại.
4. Chỉ mượn ý tưởng interruption/turn detection sau khi baseline một hỏi một đáp
   chạy ổn định.

## Nguồn Tham Khảo

- GitHub: `https://github.com/KoljaB/RealtimeVoiceChat`
- README: `https://github.com/KoljaB/RealtimeVoiceChat/blob/main/README.md`
