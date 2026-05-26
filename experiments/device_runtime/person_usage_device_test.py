from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import fmean, median
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
import psutil
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


DEVICE_RUNTIME_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = DEVICE_RUNTIME_DIR / "models"
DEFAULT_OUTPUT_DIR = DEVICE_RUNTIME_DIR / "outputs" / "device_usage_tests"
POSE_MODEL_FILENAME = "pose_landmarker_lite.task"
FACE_MODEL_FILENAME = "face_landmarker.task"


@dataclass
class PoseState:
    detected: bool = False
    left_shoulder: tuple[int, int] | None = None
    right_shoulder: tuple[int, int] | None = None
    center: tuple[int, int] | None = None
    shoulder_width_ratio: float = 0.0
    shoulder_y_delta_ratio: float = 0.0
    center_dx_ratio: float = 0.0
    shoulders_facing: bool = False
    active_zone: bool = False
    zone: str = "UNKNOWN"


@dataclass
class FaceState:
    detected: bool = False
    bbox: tuple[int, int, int, int] | None = None
    area_ratio: float = 0.0
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    eyes_visible: bool = False
    head_facing: bool = False
    active_zone: bool = False
    zone: str = "UNKNOWN"
    eye_points: dict[str, tuple[int, int]] = field(default_factory=dict)
    iris_points: dict[str, tuple[int, int]] = field(default_factory=dict)
    axis_points: dict[str, tuple[tuple[int, int], tuple[int, int]]] = field(default_factory=dict)


@dataclass
class RuntimeState:
    person_present: bool
    active_zone: bool
    attention: bool
    zone: str
    countdown_sec: float
    voicebot_mock_opened: bool
    pose: PoseState
    face: FaceState


class PoseDetector:
    def __init__(self, model_path: Path, min_conf: float = 0.5) -> None:
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_conf,
            min_pose_presence_confidence=min_conf,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def close(self) -> None:
        self.landmarker.close()

    def detect(self, frame) -> PoseState:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        landmarks = first_landmark_list(result.pose_landmarks)
        if not landmarks or len(landmarks) <= 12:
            return PoseState()

        left = landmarks[int(vision.PoseLandmark.LEFT_SHOULDER)]
        right = landmarks[int(vision.PoseLandmark.RIGHT_SHOULDER)]
        left_point = (int(left.x * w), int(left.y * h))
        right_point = (int(right.x * w), int(right.y * h))
        center = ((left_point[0] + right_point[0]) // 2, (left_point[1] + right_point[1]) // 2)
        width_ratio = abs(left_point[0] - right_point[0]) / float(w)
        y_delta_ratio = abs(left_point[1] - right_point[1]) / float(h)
        center_dx = abs(center[0] - w / 2.0) / float(w)
        facing = width_ratio >= 0.12 and y_delta_ratio <= 0.12 and center_dx <= 0.35

        if width_ratio > 0.75:
            zone = "TOO_CLOSE"
        elif width_ratio < 0.12:
            zone = "TOO_FAR"
        else:
            zone = "ACTIVE"

        return PoseState(
            detected=True,
            left_shoulder=left_point,
            right_shoulder=right_point,
            center=center,
            shoulder_width_ratio=round(width_ratio, 4),
            shoulder_y_delta_ratio=round(y_delta_ratio, 4),
            center_dx_ratio=round(center_dx, 4),
            shoulders_facing=facing,
            active_zone=zone == "ACTIVE",
            zone=zone,
        )


class FaceLandmarkerDetector:
    def __init__(self, model_path: Path, min_conf: float = 0.5) -> None:
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=min_conf,
            min_face_presence_confidence=min_conf,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=True,
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

    def close(self) -> None:
        self.landmarker.close()

    def detect(self, frame) -> FaceState:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        landmarks = first_landmark_list(result.face_landmarks)
        if not landmarks:
            return FaceState()

        bbox = landmarks_bbox(landmarks, w, h)
        area_ratio = bbox_area_ratio(bbox, w * h)
        eye_points = eye_points_from_landmarks(landmarks, w, h)
        iris_points = iris_points_from_landmarks(landmarks, w, h)
        yaw = pitch = roll = 0.0
        axis_points = {}
        matrices = getattr(result, "facial_transformation_matrixes", None) or []
        if matrices:
            matrix = np.asarray(matrices[0], dtype=float)
            if matrix.shape == (4, 4):
                rotation = matrix[:3, :3]
                pitch, yaw, roll = rotation_matrix_to_euler_degrees(rotation)
                axis_points = make_axis_points(point(landmarks, 1, w, h), rotation, min(w, h) * 0.14)

        head_facing = abs(yaw) <= 25 and abs(pitch) <= 20
        if area_ratio > 0.35:
            zone = "TOO_CLOSE"
        elif area_ratio < 0.01:
            zone = "TOO_FAR"
        else:
            zone = "ACTIVE"

        return FaceState(
            detected=True,
            bbox=bbox,
            area_ratio=round(area_ratio, 4),
            yaw_deg=round(yaw, 2),
            pitch_deg=round(pitch, 2),
            roll_deg=round(roll, 2),
            eyes_visible=bool(eye_points),
            head_facing=head_facing,
            active_zone=zone == "ACTIVE",
            zone=zone,
            eye_points=eye_points,
            iris_points=iris_points,
            axis_points=axis_points,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run webcam-only person usage test on the target device.")
    parser.add_argument("--camera", default="0", help="Camera index or OpenCV camera source.")
    parser.add_argument("--duration", type=float, default=60.0, help="Seconds to run the device test.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory. Relative paths are resolved from this script's folder.",
    )
    parser.add_argument(
        "--model-dir",
        default=str(DEFAULT_MODEL_DIR),
        help="Directory containing MediaPipe .task models. Relative paths are resolved from this script's folder.",
    )
    parser.add_argument(
        "--pose-model",
        default=POSE_MODEL_FILENAME,
        help="Pose model filename/path. Relative filenames are resolved inside --model-dir.",
    )
    parser.add_argument(
        "--face-model",
        default=FACE_MODEL_FILENAME,
        help="Face model filename/path. Relative filenames are resolved inside --model-dir.",
    )
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--capture-fps", type=float, default=30.0)
    parser.add_argument("--usage-hold-sec", type=float, default=3.0)
    parser.add_argument("--show", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-raw", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-annotated", default=True, action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def resolve_path(path_value: str | Path, base_dir: Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def resolve_model_path(model_value: str | Path, model_dir: Path) -> Path:
    path = Path(model_value).expanduser()
    if path.is_absolute():
        return path
    if len(path.parts) == 1:
        return (model_dir / path).resolve()
    return (DEVICE_RUNTIME_DIR / path).resolve()


def ensure_required_file(path: Path, label: str) -> None:
    if path.is_file():
        return
    raise FileNotFoundError(
        f"Missing {label}: {path}. "
        f"Put model files in {DEFAULT_MODEL_DIR} or pass --model-dir/--{label.replace(' ', '-')}."
    )


def main() -> int:
    args = parse_args()
    output_root = resolve_path(args.output, DEVICE_RUNTIME_DIR)
    model_dir = resolve_path(args.model_dir, DEVICE_RUNTIME_DIR)
    pose_model_path = resolve_model_path(args.pose_model, model_dir)
    face_model_path = resolve_model_path(args.face_model, model_dir)
    ensure_required_file(pose_model_path, "pose model")
    ensure_required_file(face_model_path, "face model")

    run_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    process = psutil.Process()
    process.cpu_percent(None)

    config = vars(args).copy()
    config["run_dir"] = str(run_dir)
    config["device_runtime_dir"] = str(DEVICE_RUNTIME_DIR)
    config["output_root"] = str(output_root)
    config["model_dir"] = str(model_dir)
    config["pose_model"] = str(pose_model_path)
    config["face_model"] = str(face_model_path)
    write_json(run_dir / "config.json", config)

    cap = open_camera(args.camera, args.width, args.height, args.capture_fps)
    ok, first_frame = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError("Could not read first frame from webcam.")

    frame_h, frame_w = first_frame.shape[:2]
    frame_size = (frame_w, frame_h)
    raw_writer, raw_path = maybe_writer(run_dir / "raw.mp4", frame_size, args.capture_fps, args.save_raw)
    annotated_writer, annotated_path = maybe_writer(run_dir / "annotated.mp4", frame_size, args.capture_fps, args.save_annotated)

    pose = PoseDetector(pose_model_path)
    face = FaceLandmarkerDetector(face_model_path)

    events: list[dict[str, Any]] = []
    frame_samples: list[dict[str, Any]] = []
    latencies: list[float] = []
    fps_samples: list[float] = []
    cpu_samples: list[float] = []
    ram_samples: list[float] = []
    active_frames = attention_frames = frames = 0
    active_zone_first_sec: float | None = None
    attention_first_sec: float | None = None
    voicebot_open_sec: float | None = None
    in_active_zone = False
    in_attention = False
    sustained_sec = 0.0
    voicebot_mock_opened = False
    started = time.perf_counter()
    prev_frame_t = started
    last_sample_sec = -1
    frame = first_frame

    try:
        if args.show:
            cv2.namedWindow("person_usage_device_test", cv2.WINDOW_NORMAL)

        while True:
            now = time.perf_counter()
            elapsed_sec = now - started
            if elapsed_sec >= args.duration:
                break

            frame_start = time.perf_counter()
            if raw_writer:
                raw_writer.write(frame)

            pose_state = pose.detect(frame)
            face_state = face.detect(frame)
            latency_ms = (time.perf_counter() - frame_start) * 1000.0
            latencies.append(latency_ms)

            current_t = time.perf_counter()
            dt = max(current_t - prev_frame_t, 0.0)
            prev_frame_t = current_t
            state = evaluate_state(pose_state, face_state, sustained_sec, voicebot_mock_opened)
            if state.attention:
                sustained_sec += dt
            else:
                sustained_sec = 0.0
            state.countdown_sec = sustained_sec

            t_sec = current_t - started
            if state.active_zone and not in_active_zone:
                active_zone_first_sec = t_sec if active_zone_first_sec is None else active_zone_first_sec
                events.append(event_row(t_sec, "active_zone_entered", state.zone))
            if not state.active_zone and in_active_zone:
                events.append(event_row(t_sec, "active_zone_exited", state.zone))
            in_active_zone = state.active_zone

            if state.attention and not in_attention:
                attention_first_sec = t_sec if attention_first_sec is None else attention_first_sec
                events.append(event_row(t_sec, "attention_started", "zone_attention_rule"))
            if not state.attention and in_attention:
                events.append(event_row(t_sec, "attention_lost", f"countdown_reset_at_{sustained_sec:.2f}s"))
            in_attention = state.attention

            if state.attention and not voicebot_mock_opened and sustained_sec >= args.usage_hold_sec:
                voicebot_mock_opened = True
                voicebot_open_sec = t_sec
                events.append(event_row(t_sec, "greeting_triggered", f"attention_sustained_{args.usage_hold_sec:.1f}s"))
                events.append(event_row(t_sec, "voicebot_mock_opened", "mock_only_no_voicebot_integration"))
            state.voicebot_mock_opened = voicebot_mock_opened

            frames += 1
            active_frames += int(state.active_zone)
            attention_frames += int(state.attention)
            fps_now = frames / max(time.perf_counter() - started, 0.001)
            fps_samples.append(fps_now)

            cpu = process.cpu_percent(None)
            ram = rss_mb(process)
            cpu_samples.append(cpu)
            ram_samples.append(ram)

            sample_sec = int(t_sec)
            if sample_sec != last_sample_sec:
                last_sample_sec = sample_sec
                frame_samples.append(
                    {
                        "time_sec": round(t_sec, 3),
                        "fps": round(fps_now, 2),
                        "latency_ms": round(latency_ms, 2),
                        "cpu_usage_percent": round(cpu, 2),
                        "ram_mb": round(ram, 2),
                        "zone": state.zone,
                        "person_present": state.person_present,
                        "active_zone": state.active_zone,
                        "attention": state.attention,
                        "countdown_sec": round(sustained_sec, 3),
                        "voicebot_mock_opened": voicebot_mock_opened,
                        "shoulder_width_ratio": pose_state.shoulder_width_ratio,
                        "face_area_ratio": face_state.area_ratio,
                        "yaw_deg": face_state.yaw_deg,
                        "pitch_deg": face_state.pitch_deg,
                    }
                )

            annotated = frame.copy()
            draw_overlay(annotated, state, fps_now, latency_ms, cpu, ram, args.usage_hold_sec)
            if annotated_writer:
                annotated_writer.write(annotated)
            if args.show:
                cv2.imshow("person_usage_device_test", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    events.append(event_row(t_sec, "manual_stop", "q_or_escape"))
                    break

            ok, frame = cap.read()
            if not ok:
                events.append(event_row(t_sec, "camera_read_failed", "stopped"))
                break
    finally:
        cap.release()
        if raw_writer:
            raw_writer.release()
        if annotated_writer:
            annotated_writer.release()
        pose.close()
        face.close()
        if args.show:
            cv2.destroyWindow("person_usage_device_test")

    elapsed = max(time.perf_counter() - started, 0.001)
    metrics = [
        {
            "frames": frames,
            "elapsed_sec": round(elapsed, 3),
            "fps": round(frames / elapsed, 2),
            "avg_latency_ms": safe_mean(latencies),
            "median_latency_ms": safe_median(latencies),
            "avg_cpu_usage_percent": safe_mean(cpu_samples),
            "max_cpu_usage_percent": round(max(cpu_samples), 2) if cpu_samples else 0.0,
            "avg_ram_mb": safe_mean(ram_samples),
            "max_ram_mb": round(max(ram_samples), 2) if ram_samples else 0.0,
            "active_zone_frames": active_frames,
            "attention_frames": attention_frames,
            "active_zone_first_sec": round(active_zone_first_sec, 3) if active_zone_first_sec is not None else "",
            "attention_first_sec": round(attention_first_sec, 3) if attention_first_sec is not None else "",
            "voicebot_open_sec": round(voicebot_open_sec, 3) if voicebot_open_sec is not None else "",
            "voicebot_mock_opened": voicebot_mock_opened,
            "raw_video_path": str(raw_path),
            "annotated_video_path": str(annotated_path),
        }
    ]
    write_csv(run_dir / "metrics.csv", metrics)
    write_csv(run_dir / "frame_metrics.csv", frame_samples)
    write_csv(run_dir / "events.csv", events)
    write_summary(run_dir / "summary.md", metrics[0], events, args)
    print(f"Wrote {run_dir}")
    return 0


def evaluate_state(pose: PoseState, face: FaceState, countdown_sec: float, voicebot_opened: bool) -> RuntimeState:
    person_present = pose.detected or face.detected
    active_zone = pose.active_zone if pose.detected else face.active_zone
    zone = pose.zone if pose.detected else face.zone
    attention = (
        person_present
        and active_zone
        and pose.detected
        and pose.shoulders_facing
        and face.detected
        and face.head_facing
        and face.eyes_visible
    )
    return RuntimeState(person_present, active_zone, attention, zone, countdown_sec, voicebot_opened, pose, face)


def draw_overlay(frame, state: RuntimeState, fps: float, latency_ms: float, cpu: float, ram: float, usage_hold_sec: float) -> None:
    h, w = frame.shape[:2]
    draw_center_band(frame)
    draw_face(frame, state.face)
    draw_pose(frame, state.pose)
    draw_zone_gauge(frame, state.pose, state.face)

    if state.voicebot_mock_opened:
        status = "VOICEBOT MOCK OPEN"
        color = (255, 120, 0)
    elif state.attention:
        status = "ATTENTION COUNTING"
        color = (0, 220, 255)
    elif state.active_zone:
        status = "ACTIVE ZONE"
        color = (0, 210, 0)
    elif state.person_present:
        status = state.zone
        color = (0, 165, 255)
    else:
        status = "NO_PERSON"
        color = (180, 180, 180)

    cv2.rectangle(frame, (0, 0), (w, 154), (20, 20, 20), -1)
    cv2.putText(frame, status, (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2, cv2.LINE_AA)
    lines = [
        f"FPS {fps:.2f} | latency {latency_ms:.1f} ms | CPU {cpu:.1f}% | RAM {ram:.1f} MB",
        f"person {state.person_present} | active {state.active_zone} | attention {state.attention}",
        f"countdown {state.countdown_sec:.1f}/{usage_hold_sec:.1f}s | zone {state.zone}",
        f"shoulder {state.pose.shoulder_width_ratio:.3f} | face {state.face.area_ratio:.3f} | yaw/pitch {state.face.yaw_deg:.1f}/{state.face.pitch_deg:.1f}",
    ]
    y = 66
    for line in lines:
        cv2.putText(frame, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)
        y += 27


def draw_center_band(frame) -> None:
    h, w = frame.shape[:2]
    left = int(w * 0.15)
    right = int(w * 0.85)
    overlay = frame.copy()
    cv2.rectangle(overlay, (left, 154), (right, h), (40, 80, 40), -1)
    cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)
    cv2.line(frame, (left, 154), (left, h), (70, 150, 70), 1)
    cv2.line(frame, (right, 154), (right, h), (70, 150, 70), 1)


def draw_pose(frame, pose: PoseState) -> None:
    if not pose.detected or not pose.left_shoulder or not pose.right_shoulder:
        return
    color = (0, 210, 0) if pose.active_zone and pose.shoulders_facing else (0, 165, 255)
    cv2.line(frame, pose.left_shoulder, pose.right_shoulder, color, 3)
    cv2.circle(frame, pose.left_shoulder, 6, color, -1)
    cv2.circle(frame, pose.right_shoulder, 6, color, -1)
    if pose.center:
        cv2.circle(frame, pose.center, 5, (255, 255, 255), -1)


def draw_face(frame, face: FaceState) -> None:
    if face.bbox:
        color = (0, 210, 0) if face.active_zone and face.head_facing else (0, 165, 255)
        x1, y1, x2, y2 = face.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    if face.eye_points:
        left = face.eye_points["left_eye"]
        right = face.eye_points["right_eye"]
        cv2.line(frame, left, right, (255, 255, 0), 2)
        cv2.circle(frame, left, 4, (255, 255, 0), -1)
        cv2.circle(frame, right, 4, (255, 255, 0), -1)
    for point_xy in face.iris_points.values():
        cv2.circle(frame, point_xy, 5, (0, 255, 255), 2)
    for axis, (start, end) in face.axis_points.items():
        color = {"x": (0, 0, 255), "y": (0, 255, 0), "z": (255, 0, 0)}.get(axis, (255, 255, 255))
        cv2.arrowedLine(frame, start, end, color, 2, cv2.LINE_AA, tipLength=0.2)


def draw_zone_gauge(frame, pose: PoseState, face: FaceState) -> None:
    h, w = frame.shape[:2]
    x = w - 106
    y = 178
    height = 250
    cv2.rectangle(frame, (x, y), (x + 70, y + height), (30, 30, 30), -1)
    cv2.rectangle(frame, (x + 8, y + 12), (x + 62, y + 72), (0, 80, 180), 1)
    cv2.rectangle(frame, (x + 8, y + 76), (x + 62, y + 176), (0, 150, 0), 1)
    cv2.rectangle(frame, (x + 8, y + 180), (x + 62, y + 238), (0, 80, 180), 1)
    cv2.putText(frame, "CLOSE", (x + 10, y + 34), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "ACTIVE", (x + 9, y + 126), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "FAR", (x + 20, y + 216), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)

    if pose.detected:
        value = pose.shoulder_width_ratio
        marker_y = int(np.interp(value, [0.02, 0.75], [y + 238, y + 12]))
    elif face.detected:
        value = face.area_ratio
        marker_y = int(np.interp(value, [0.002, 0.35], [y + 238, y + 12]))
    else:
        return
    marker_y = max(y + 12, min(y + 238, marker_y))
    cv2.arrowedLine(frame, (x - 6, marker_y), (x + 8, marker_y), (255, 255, 255), 2, cv2.LINE_AA, tipLength=0.4)


def open_camera(camera: str, width: int, height: int, fps: float) -> cv2.VideoCapture:
    source: int | str = int(camera) if camera.isdecimal() else camera
    backends = [cv2.CAP_DSHOW, cv2.CAP_ANY] if isinstance(source, int) else [cv2.CAP_ANY]
    for backend in backends:
        cap = cv2.VideoCapture(source, backend)
        if not cap.isOpened():
            cap.release()
            continue
        if width > 0:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height > 0:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if fps > 0:
            cap.set(cv2.CAP_PROP_FPS, fps)
        ok, _ = cap.read()
        if ok:
            return cap
        cap.release()
    raise RuntimeError(f"Could not open webcam: {camera}")


def maybe_writer(path: Path, frame_size: tuple[int, int], fps: float, enabled: bool):
    if not enabled:
        return None, ""
    return open_video_writer(path, frame_size, fps)


def open_video_writer(path: Path, frame_size: tuple[int, int], fps: float) -> tuple[cv2.VideoWriter, Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidates = [
        (path.with_suffix(".mp4"), cv2.VideoWriter_fourcc(*"mp4v")),
        (path.with_suffix(".avi"), cv2.VideoWriter_fourcc(*"XVID")),
    ]
    for candidate, fourcc in candidates:
        writer = cv2.VideoWriter(str(candidate), fourcc, fps, frame_size)
        if writer.isOpened():
            return writer, candidate
        writer.release()
    raise RuntimeError(f"Could not create video writer for {path}")


def first_landmark_list(container: list) -> list:
    if not container:
        return []
    first = container[0]
    if hasattr(first, "x") and hasattr(first, "y"):
        return container
    return first


def landmarks_bbox(landmarks, width: int, height: int) -> tuple[int, int, int, int]:
    xs = [max(0, min(width - 1, int(p.x * width))) for p in landmarks]
    ys = [max(0, min(height - 1, int(p.y * height))) for p in landmarks]
    return min(xs), min(ys), max(xs), max(ys)


def point(landmarks, index: int, width: int, height: int) -> tuple[int, int]:
    landmark = landmarks[index]
    return int(landmark.x * width), int(landmark.y * height)


def average(points: list[tuple[int, int]]) -> tuple[int, int]:
    return int(sum(p[0] for p in points) / len(points)), int(sum(p[1] for p in points) / len(points))


def eye_points_from_landmarks(landmarks, width: int, height: int) -> dict[str, tuple[int, int]]:
    if len(landmarks) <= 362:
        return {}
    return {
        "left_eye": average([point(landmarks, 33, width, height), point(landmarks, 133, width, height)]),
        "right_eye": average([point(landmarks, 362, width, height), point(landmarks, 263, width, height)]),
    }


def iris_points_from_landmarks(landmarks, width: int, height: int) -> dict[str, tuple[int, int]]:
    if len(landmarks) <= 477:
        return {}
    return {
        "left_iris": average([point(landmarks, i, width, height) for i in range(468, 473)]),
        "right_iris": average([point(landmarks, i, width, height) for i in range(473, 478)]),
    }


def make_axis_points(origin: tuple[int, int], rotation: np.ndarray, axis_length: float):
    origin_arr = np.asarray(origin, dtype=float)
    axes = {
        "x": np.asarray([rotation[0, 0], rotation[1, 0]], dtype=float),
        "y": np.asarray([rotation[0, 1], rotation[1, 1]], dtype=float),
        "z": np.asarray([rotation[0, 2], rotation[1, 2]], dtype=float),
    }
    result = {}
    for name, direction in axes.items():
        norm = np.linalg.norm(direction)
        if norm > 1e-6:
            direction = direction / norm
        end = origin_arr + direction * axis_length
        result[name] = (origin, (int(end[0]), int(end[1])))
    return result


def rotation_matrix_to_euler_degrees(rotation: np.ndarray) -> tuple[float, float, float]:
    sy = math.sqrt(rotation[0, 0] * rotation[0, 0] + rotation[1, 0] * rotation[1, 0])
    if sy >= 1e-6:
        pitch = math.atan2(rotation[2, 1], rotation[2, 2])
        yaw = math.atan2(-rotation[2, 0], sy)
        roll = math.atan2(rotation[1, 0], rotation[0, 0])
    else:
        pitch = math.atan2(-rotation[1, 2], rotation[1, 1])
        yaw = math.atan2(-rotation[2, 0], sy)
        roll = 0.0
    return math.degrees(pitch), math.degrees(yaw), math.degrees(roll)


def bbox_area(bbox: tuple[int, int, int, int]) -> int:
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def bbox_area_ratio(bbox: tuple[int, int, int, int] | None, frame_area: float) -> float:
    if bbox is None or frame_area <= 0:
        return 0.0
    return bbox_area(bbox) / frame_area


def rss_mb(process: psutil.Process) -> float:
    return process.memory_info().rss / (1024 * 1024)


def safe_mean(values: list[float]) -> float:
    return round(fmean(values), 2) if values else 0.0


def safe_median(values: list[float]) -> float:
    return round(median(values), 2) if values else 0.0


def event_row(time_sec: float, event: str, detail: str) -> dict[str, Any]:
    return {"time_sec": round(time_sec, 3), "event": event, "detail": detail}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def write_summary(path: Path, metrics: dict[str, Any], events: list[dict[str, Any]], args: argparse.Namespace) -> None:
    event_lines = [f"- {row['time_sec']}s: `{row['event']}` - {row['detail']}" for row in events]
    if not event_lines:
        event_lines = ["- No state transition events were recorded."]
    lines = [
        "# Device Usage Test Summary",
        "",
        "This run is a webcam-only device feasibility test. Voicebot integration is mocked by events only.",
        "",
        "## Config",
        "",
        f"- Camera: `{args.camera}`",
        f"- Duration target: `{args.duration}` seconds",
        f"- Usage hold: `{args.usage_hold_sec}` seconds",
        "",
        "## Metrics",
        "",
        f"- FPS: `{metrics['fps']}`",
        f"- Avg latency ms/frame: `{metrics['avg_latency_ms']}`",
        f"- Median latency ms/frame: `{metrics['median_latency_ms']}`",
        f"- Avg CPU usage: `{metrics['avg_cpu_usage_percent']}%`",
        f"- Max CPU usage: `{metrics['max_cpu_usage_percent']}%`",
        f"- Avg RAM: `{metrics['avg_ram_mb']} MB`",
        f"- Max RAM: `{metrics['max_ram_mb']} MB`",
        f"- Active-zone frames: `{metrics['active_zone_frames']}`",
        f"- Attention frames: `{metrics['attention_frames']}`",
        f"- Active zone first sec: `{metrics['active_zone_first_sec']}`",
        f"- Attention first sec: `{metrics['attention_first_sec']}`",
        f"- Voicebot mock open sec: `{metrics['voicebot_open_sec']}`",
        f"- Voicebot mock opened: `{metrics['voicebot_mock_opened']}`",
        "",
        "## Events",
        "",
        *event_lines,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
