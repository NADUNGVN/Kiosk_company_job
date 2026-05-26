"""
Collect a short PASSING_BY video for customer-presence analysis.

This script is intentionally standalone and does not import Django code.
It opens the camera, waits for Enter, then records a person walking back and
forth through the frame for 10 seconds.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "data"

PHASE = {
    "phase": "passing_by",
    "label": "PASSING_BY",
    "duration_seconds": 10,
    "instruction": "Stand near the door/outside frame, press Enter, then walk back and forth.",
}


@dataclass
class SessionMetadata:
    session_id: str
    camera_index: int
    width: int
    height: int
    fps_requested: float
    fps_actual: float
    passing_by_seconds: int
    started_at: str
    session_note: str


@dataclass
class SegmentMetadata:
    session_id: str
    phase: str
    label: str
    duration_seconds: int
    video_path: str
    started_at: str
    ended_at: str
    width: int
    height: int
    fps_actual: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record a PASSING_BY video for kiosk presence analysis."
    )
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory. Defaults to the data folder next to this script.",
    )
    parser.add_argument("--session-note", default="")
    parser.add_argument("--fps", type=float, default=20.0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--passing-by-seconds", type=int, default=10)
    return parser


def ensure_dirs(base_dir: Path) -> dict[str, Path]:
    paths = {
        "videos": base_dir / "videos",
        "metadata": base_dir / "metadata",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    for phase in ("passing_by",):
        (paths["videos"] / phase).mkdir(parents=True, exist_ok=True)
    return paths


def append_jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_event(path: Path, row: dict) -> None:
    fieldnames = [
        "timestamp",
        "session_id",
        "event",
        "phase",
        "label",
        "duration_seconds",
        "video_path",
        "note",
    ]
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def make_video_writer(cv2, path: Path, fps: float, width: int, height: int):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Cannot open video writer: {path}")
    return writer


def open_camera(cv2, camera_index: int, width: int, height: int, fps: float):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {camera_index}")

    if width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if fps > 0:
        cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or width
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or height
    actual_fps = float(cap.get(cv2.CAP_PROP_FPS)) or fps
    if actual_fps <= 1:
        actual_fps = fps

    return cap, actual_width, actual_height, actual_fps


def overlay_status(cv2, frame, line1: str, line2: str, recording: bool) -> None:
    color = (0, 0, 255) if recording else (80, 180, 80)
    cv2.rectangle(frame, (10, 10), (1220, 106), (0, 0, 0), -1)
    cv2.putText(frame, line1, (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.72, color, 2)
    cv2.putText(frame, line2, (24, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (230, 230, 230), 1)
    cv2.putText(
        frame,
        "Enter=start recording | q=quit",
        (24, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (210, 210, 210),
        1,
    )


def read_preview_until_enter(cv2, cap, phase: dict, session_id: str) -> bool:
    print("")
    print(f"READY: {phase['label']}")
    print(phase["instruction"])
    print("Focus the camera window and press Enter to start. Press q to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("Camera frame read failed during preview.")

        overlay_status(
            cv2,
            frame,
            f"READY_{phase['label']} session={session_id}",
            phase["instruction"],
            recording=False,
        )
        cv2.imshow("customer_presence_collection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (13, 10):
            return True
        if key == ord("q"):
            return False


def record_phase(
    cv2,
    cap,
    paths: dict[str, Path],
    session_id: str,
    phase: dict,
    duration_seconds: int,
    fps: float,
    width: int,
    height: int,
) -> Optional[SegmentMetadata]:
    video_path = paths["videos"] / phase["phase"] / f"{session_id}_{phase['phase']}.mp4"
    writer = make_video_writer(cv2, video_path, fps, width, height)
    started_at = datetime.now()
    started_monotonic = time.monotonic()
    frame_count = 0

    print(f"Recording {phase['label']} for {duration_seconds}s: {video_path}")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f"Camera frame read failed while recording {phase['label']}.")

            elapsed = time.monotonic() - started_monotonic
            remaining = max(0, duration_seconds - int(elapsed))
            writer.write(frame)
            frame_count += 1

            overlay_status(
                cv2,
                frame,
                f"REC_{phase['label']} remaining={remaining}s",
                "Keep following the current scenario. Press q to abort.",
                recording=True,
            )
            cv2.imshow("customer_presence_collection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Recording aborted by user.")
                return None
            if elapsed >= duration_seconds:
                break
    finally:
        writer.release()

    ended_at = datetime.now()
    print(f"Finished {phase['label']}: {frame_count} frames")
    return SegmentMetadata(
        session_id=session_id,
        phase=phase["phase"],
        label=phase["label"],
        duration_seconds=duration_seconds,
        video_path=str(video_path),
        started_at=started_at.isoformat(timespec="seconds"),
        ended_at=ended_at.isoformat(timespec="seconds"),
        width=width,
        height=height,
        fps_actual=fps,
    )


def run_collection(args: argparse.Namespace) -> None:
    import cv2

    started = datetime.now()
    session_id = f"{started.strftime('%Y%m%d_%H%M%S')}_passing_by"
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = (Path.cwd() / output_dir).resolve()
    paths = ensure_dirs(output_dir)

    cap, width, height, actual_fps = open_camera(
        cv2, args.camera_index, args.width, args.height, args.fps
    )

    metadata = SessionMetadata(
        session_id=session_id,
        camera_index=args.camera_index,
        width=width,
        height=height,
        fps_requested=args.fps,
        fps_actual=actual_fps,
        passing_by_seconds=args.passing_by_seconds,
        started_at=started.isoformat(timespec="seconds"),
        session_note=args.session_note,
    )
    append_jsonl(paths["metadata"] / "sessions.jsonl", asdict(metadata))
    append_event(
        paths["metadata"] / "events.csv",
        {
            "timestamp": metadata.started_at,
            "session_id": session_id,
            "event": "session_start",
            "note": args.session_note,
        },
    )

    print(f"Session: {session_id}")
    print("Camera is open. The script will record PASSING_BY.")
    print(f"Output directory: {output_dir}")

    try:
        should_start = read_preview_until_enter(cv2, cap, PHASE, session_id)
        if not should_start:
            append_event(
                paths["metadata"] / "events.csv",
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "session_id": session_id,
                    "event": "session_aborted",
                    "phase": PHASE["phase"],
                    "label": PHASE["label"],
                },
            )
            return

        append_event(
            paths["metadata"] / "events.csv",
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "session_id": session_id,
                "event": "segment_start",
                "phase": PHASE["phase"],
                "label": PHASE["label"],
                "duration_seconds": args.passing_by_seconds,
            },
        )

        segment = record_phase(
            cv2,
            cap,
            paths,
            session_id,
            PHASE,
            args.passing_by_seconds,
            actual_fps,
            width,
            height,
        )
        if segment is None:
            append_event(
                paths["metadata"] / "events.csv",
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "session_id": session_id,
                    "event": "session_aborted",
                    "phase": PHASE["phase"],
                    "label": PHASE["label"],
                },
            )
            return

        append_jsonl(paths["metadata"] / "segments.jsonl", asdict(segment))
        append_event(
            paths["metadata"] / "events.csv",
            {
                "timestamp": segment.ended_at,
                "session_id": session_id,
                "event": "segment_end",
                "phase": segment.phase,
                "label": segment.label,
                "duration_seconds": segment.duration_seconds,
                "video_path": segment.video_path,
            },
        )

        append_event(
            paths["metadata"] / "events.csv",
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "session_id": session_id,
                "event": "session_end",
            },
        )
        print("Done. Recorded PASSING_BY video.")
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_collection(args)


if __name__ == "__main__":
    main()
