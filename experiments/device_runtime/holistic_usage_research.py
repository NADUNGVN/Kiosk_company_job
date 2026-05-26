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


DEVICE_RUNTIME_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = DEVICE_RUNTIME_DIR / "outputs" / "holistic_usage_tests"


@dataclass
class PoseObservation:
    detected: bool = False
    left_shoulder: tuple[int, int] | None = None
    right_shoulder: tuple[int, int] | None = None
    center: tuple[int, int] | None = None
    shoulder_width_ratio: float = 0.0
    shoulder_y_delta_ratio: float = 0.0
    center_dx_ratio: float = 0.0
    shoulders_facing: bool = False
    zone: str = "UNKNOWN"
    active_zone: bool = False


@dataclass
class EyeObservation:
    eye_points: dict[str, tuple[int, int]] = field(default_factory=dict)
    iris_points: dict[str, tuple[int, int]] = field(default_factory=dict)
    gaze_vectors: dict[str, tuple[tuple[int, int], tuple[int, int]]] = field(default_factory=dict)
    left_gaze_dx: float = 0.0
    right_gaze_dx: float = 0.0
    avg_gaze_dx: float = 0.0
    gaze_centered: bool = False
    eyes_visible: bool = False


@dataclass
class FaceObservation:
    detected: bool = False
    bbox: tuple[int, int, int, int] | None = None
    area_ratio: float = 0.0
    zone: str = "UNKNOWN"
    active_zone: bool = False
    eyes: EyeObservation = field(default_factory=EyeObservation)


@dataclass
class ResearchState:
    label: str
    person_present: bool
    active_zone: bool
    attention_candidate: bool
    sustained_sec: float
    movement_speed_ratio_per_sec: float
    moving_fast: bool
    pose: PoseObservation
    face: FaceObservation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research MediaPipe Holistic for kiosk usage detection.")
    parser.add_argument("--camera", default="0", help="Camera index or OpenCV camera source.")
    parser.add_argument("--duration", type=float, default=60.0, help="Seconds to run the holistic research test.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory. Relative paths are resolved from this script's folder.",
    )
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--capture-fps", type=float, default=30.0)
    parser.add_argument("--usage-hold-sec", type=float, default=3.0)
    parser.add_argument(
        "--passing-speed-ratio-per-sec",
        type=float,
        default=0.45,
        help="Body center speed threshold used to mark passing-by movement.",
    )
    parser.add_argument("--show", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-raw", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-annotated", default=True, action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import cv2
    import mediapipe as mp
    import psutil

    output_root = resolve_path(args.output, DEVICE_RUNTIME_DIR)
    run_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    config = vars(args).copy()
    config["run_dir"] = str(run_dir)
    config["device_runtime_dir"] = str(DEVICE_RUNTIME_DIR)
    config["output_root"] = str(output_root)
    write_json(run_dir / "config.json", config)

    cap = open_camera(cv2, args.camera, args.width, args.height, args.capture_fps)
    ok, first_frame = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError("Could not read first frame from webcam.")

    frame_h, frame_w = first_frame.shape[:2]
    frame_size = (frame_w, frame_h)
    raw_writer, raw_path = maybe_writer(cv2, run_dir / "raw.mp4", frame_size, args.capture_fps, args.save_raw)
    annotated_writer, annotated_path = maybe_writer(
        cv2,
        run_dir / "annotated.mp4",
        frame_size,
        args.capture_fps,
        args.save_annotated,
    )

    process = psutil.Process()
    process.cpu_percent(None)

    holistic = mp.solutions.holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    events: list[dict[str, Any]] = []
    frame_samples: list[dict[str, Any]] = []
    latencies: list[float] = []
    fps_samples: list[float] = []
    cpu_samples: list[float] = []
    ram_samples: list[float] = []
    state_counts: dict[str, int] = {}
    frames = 0
    sustained_sec = 0.0
    support_first_sec: float | None = None
    attention_first_sec: float | None = None
    previous_label = ""
    previous_center: tuple[int, int] | None = None
    started = time.perf_counter()
    previous_frame_t = started
    last_sample_sec = -1
    frame = first_frame

    try:
        if args.show:
            cv2.namedWindow("holistic_usage_research", cv2.WINDOW_NORMAL)

        while True:
            now = time.perf_counter()
            if now - started >= args.duration:
                break

            if raw_writer:
                raw_writer.write(frame)

            frame_start = time.perf_counter()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)
            latency_ms = (time.perf_counter() - frame_start) * 1000.0
            latencies.append(latency_ms)

            current_t = time.perf_counter()
            dt = max(current_t - previous_frame_t, 0.001)
            previous_frame_t = current_t
            t_sec = current_t - started

            pose = observe_pose(mp, results, frame_w, frame_h)
            face = observe_face(results, frame_w, frame_h)
            speed = movement_speed_ratio(previous_center, pose.center, frame_w, dt)
            previous_center = pose.center if pose.center else previous_center

            attention_candidate = is_attention_candidate(pose, face, speed, args.passing_speed_ratio_per_sec)
            if attention_candidate:
                sustained_sec += dt
            else:
                sustained_sec = 0.0

            state = classify_state(
                pose=pose,
                face=face,
                sustained_sec=sustained_sec,
                movement_speed=speed,
                speed_threshold=args.passing_speed_ratio_per_sec,
                usage_hold_sec=args.usage_hold_sec,
            )

            if state.label != previous_label:
                events.append(event_row(t_sec, "state_changed", f"{previous_label or 'START'} -> {state.label}"))
                previous_label = state.label

            if attention_candidate and attention_first_sec is None:
                attention_first_sec = t_sec
                events.append(event_row(t_sec, "attention_candidate_started", "holistic_rule"))

            if state.label == "NEED_SUPPORT" and support_first_sec is None:
                support_first_sec = t_sec
                events.append(event_row(t_sec, "need_support_detected", f"attention_sustained_{args.usage_hold_sec:.1f}s"))

            frames += 1
            state_counts[state.label] = state_counts.get(state.label, 0) + 1
            fps_now = frames / max(time.perf_counter() - started, 0.001)
            fps_samples.append(fps_now)
            cpu = process.cpu_percent(None)
            ram = rss_mb(process)
            cpu_samples.append(cpu)
            ram_samples.append(ram)

            sample_sec = int(t_sec)
            if sample_sec != last_sample_sec:
                last_sample_sec = sample_sec
                frame_samples.append(frame_sample(t_sec, fps_now, latency_ms, cpu, ram, state))

            annotated = frame.copy()
            draw_overlay(cv2, annotated, state, fps_now, latency_ms, cpu, ram, args.usage_hold_sec)
            if annotated_writer:
                annotated_writer.write(annotated)
            if args.show:
                cv2.imshow("holistic_usage_research", annotated)
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
        holistic.close()
        if args.show:
            cv2.destroyWindow("holistic_usage_research")

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
            "attention_first_sec": round(attention_first_sec, 3) if attention_first_sec is not None else "",
            "support_first_sec": round(support_first_sec, 3) if support_first_sec is not None else "",
            "state_counts_json": json.dumps(state_counts, sort_keys=True),
            "raw_video_path": str(raw_path),
            "annotated_video_path": str(annotated_path),
        }
    ]
    write_csv(run_dir / "metrics.csv", metrics)
    write_csv(run_dir / "frame_metrics.csv", frame_samples)
    write_csv(run_dir / "events.csv", events)
    write_summary(run_dir / "summary.md", metrics[0], events, state_counts, args)
    print(f"Wrote {run_dir}")
    return 0


def observe_pose(mp, results: Any, width: int, height: int) -> PoseObservation:
    landmarks = getattr(getattr(results, "pose_landmarks", None), "landmark", None)
    if not landmarks:
        return PoseObservation()

    left = landmarks[mp.solutions.holistic.PoseLandmark.LEFT_SHOULDER.value]
    right = landmarks[mp.solutions.holistic.PoseLandmark.RIGHT_SHOULDER.value]
    left_point = point(left, width, height)
    right_point = point(right, width, height)
    center = ((left_point[0] + right_point[0]) // 2, (left_point[1] + right_point[1]) // 2)
    width_ratio = abs(left_point[0] - right_point[0]) / float(width)
    y_delta_ratio = abs(left_point[1] - right_point[1]) / float(height)
    center_dx_ratio = abs(center[0] - width / 2.0) / float(width)
    shoulders_facing = width_ratio >= 0.12 and y_delta_ratio <= 0.12 and center_dx_ratio <= 0.35

    if width_ratio > 0.75:
        zone = "TOO_CLOSE"
    elif width_ratio < 0.12:
        zone = "TOO_FAR"
    else:
        zone = "ACTIVE"

    return PoseObservation(
        detected=True,
        left_shoulder=left_point,
        right_shoulder=right_point,
        center=center,
        shoulder_width_ratio=round(width_ratio, 4),
        shoulder_y_delta_ratio=round(y_delta_ratio, 4),
        center_dx_ratio=round(center_dx_ratio, 4),
        shoulders_facing=shoulders_facing,
        zone=zone,
        active_zone=zone == "ACTIVE",
    )


def observe_face(results: Any, width: int, height: int) -> FaceObservation:
    landmarks = getattr(getattr(results, "face_landmarks", None), "landmark", None)
    if not landmarks:
        return FaceObservation()

    bbox = landmarks_bbox(landmarks, width, height)
    area_ratio = bbox_area_ratio(bbox, width * height)
    eyes = observe_eyes(landmarks, width, height)
    if area_ratio > 0.35:
        zone = "TOO_CLOSE"
    elif area_ratio < 0.01:
        zone = "TOO_FAR"
    else:
        zone = "ACTIVE"

    return FaceObservation(
        detected=True,
        bbox=bbox,
        area_ratio=round(area_ratio, 4),
        zone=zone,
        active_zone=zone == "ACTIVE",
        eyes=eyes,
    )


def observe_eyes(landmarks: list[Any], width: int, height: int) -> EyeObservation:
    if len(landmarks) <= 477:
        return EyeObservation()

    left_outer = point(landmarks[33], width, height)
    left_inner = point(landmarks[133], width, height)
    right_inner = point(landmarks[362], width, height)
    right_outer = point(landmarks[263], width, height)
    left_eye = average([left_outer, left_inner])
    right_eye = average([right_inner, right_outer])
    left_iris = average([point(landmarks[i], width, height) for i in range(468, 473)])
    right_iris = average([point(landmarks[i], width, height) for i in range(473, 478)])
    left_width = max(distance(left_outer, left_inner), 1.0)
    right_width = max(distance(right_inner, right_outer), 1.0)
    left_gaze_dx = (left_iris[0] - left_eye[0]) / left_width
    right_gaze_dx = (right_iris[0] - right_eye[0]) / right_width
    avg_gaze_dx = (left_gaze_dx + right_gaze_dx) / 2.0

    scale = 4.0
    left_end = (
        int(left_eye[0] + (left_iris[0] - left_eye[0]) * scale),
        int(left_eye[1] + (left_iris[1] - left_eye[1]) * scale),
    )
    right_end = (
        int(right_eye[0] + (right_iris[0] - right_eye[0]) * scale),
        int(right_eye[1] + (right_iris[1] - right_eye[1]) * scale),
    )

    return EyeObservation(
        eye_points={"left_eye": left_eye, "right_eye": right_eye},
        iris_points={"left_iris": left_iris, "right_iris": right_iris},
        gaze_vectors={"left_eye": (left_eye, left_end), "right_eye": (right_eye, right_end)},
        left_gaze_dx=round(left_gaze_dx, 4),
        right_gaze_dx=round(right_gaze_dx, 4),
        avg_gaze_dx=round(avg_gaze_dx, 4),
        gaze_centered=abs(avg_gaze_dx) <= 0.18,
        eyes_visible=True,
    )


def classify_state(
    pose: PoseObservation,
    face: FaceObservation,
    sustained_sec: float,
    movement_speed: float,
    speed_threshold: float,
    usage_hold_sec: float,
) -> ResearchState:
    person_present = pose.detected or face.detected
    active_zone = pose.active_zone if pose.detected else face.active_zone
    moving_fast = movement_speed > speed_threshold
    attention_candidate = is_attention_candidate(pose, face, movement_speed, speed_threshold)

    if not person_present:
        label = "NO_PERSON"
    elif moving_fast:
        label = "PASSING_BY"
    elif not active_zone:
        label = pose.zone if pose.detected else face.zone
    elif attention_candidate and sustained_sec >= usage_hold_sec:
        label = "NEED_SUPPORT"
    elif attention_candidate:
        label = "POTENTIAL_USER"
    else:
        label = "PERSON_PRESENT_NOT_ATTENDING"

    return ResearchState(
        label=label,
        person_present=person_present,
        active_zone=active_zone,
        attention_candidate=attention_candidate,
        sustained_sec=sustained_sec,
        movement_speed_ratio_per_sec=round(movement_speed, 4),
        moving_fast=moving_fast,
        pose=pose,
        face=face,
    )


def is_attention_candidate(
    pose: PoseObservation,
    face: FaceObservation,
    movement_speed: float,
    speed_threshold: float,
) -> bool:
    return (
        pose.detected
        and pose.active_zone
        and pose.shoulders_facing
        and face.detected
        and face.eyes.eyes_visible
        and face.eyes.gaze_centered
        and movement_speed <= speed_threshold
    )


def frame_sample(
    t_sec: float,
    fps: float,
    latency_ms: float,
    cpu: float,
    ram: float,
    state: ResearchState,
) -> dict[str, Any]:
    return {
        "time_sec": round(t_sec, 3),
        "fps": round(fps, 2),
        "latency_ms": round(latency_ms, 2),
        "cpu_usage_percent": round(cpu, 2),
        "ram_mb": round(ram, 2),
        "label": state.label,
        "person_present": state.person_present,
        "active_zone": state.active_zone,
        "attention_candidate": state.attention_candidate,
        "sustained_sec": round(state.sustained_sec, 3),
        "movement_speed_ratio_per_sec": state.movement_speed_ratio_per_sec,
        "moving_fast": state.moving_fast,
        "pose_zone": state.pose.zone,
        "face_zone": state.face.zone,
        "shoulder_width_ratio": state.pose.shoulder_width_ratio,
        "face_area_ratio": state.face.area_ratio,
        "eyes_visible": state.face.eyes.eyes_visible,
        "gaze_centered": state.face.eyes.gaze_centered,
        "left_gaze_dx": state.face.eyes.left_gaze_dx,
        "right_gaze_dx": state.face.eyes.right_gaze_dx,
        "avg_gaze_dx": state.face.eyes.avg_gaze_dx,
    }


def draw_overlay(cv2, frame: Any, state: ResearchState, fps: float, latency_ms: float, cpu: float, ram: float, usage_hold_sec: float) -> None:
    h, w = frame.shape[:2]
    draw_center_band(cv2, frame)
    draw_pose(cv2, frame, state.pose)
    draw_face(cv2, frame, state.face)

    color = {
        "NO_PERSON": (180, 180, 180),
        "PASSING_BY": (0, 165, 255),
        "PERSON_PRESENT_NOT_ATTENDING": (0, 210, 255),
        "POTENTIAL_USER": (0, 220, 255),
        "NEED_SUPPORT": (0, 210, 0),
        "TOO_FAR": (0, 165, 255),
        "TOO_CLOSE": (0, 165, 255),
    }.get(state.label, (255, 255, 255))

    cv2.rectangle(frame, (0, 0), (w, 180), (20, 20, 20), -1)
    cv2.putText(frame, state.label, (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.82, color, 2, cv2.LINE_AA)
    lines = [
        f"FPS {fps:.2f} | latency {latency_ms:.1f} ms | CPU {cpu:.1f}% | RAM {ram:.1f} MB",
        f"person {state.person_present} | active {state.active_zone} | candidate {state.attention_candidate}",
        f"sustain {state.sustained_sec:.1f}/{usage_hold_sec:.1f}s | speed {state.movement_speed_ratio_per_sec:.3f}",
        f"shoulder {state.pose.shoulder_width_ratio:.3f} | face {state.face.area_ratio:.3f}",
        f"eyes {state.face.eyes.eyes_visible} | gaze centered {state.face.eyes.gaze_centered} | avg dx {state.face.eyes.avg_gaze_dx:.3f}",
    ]
    y = 66
    for line in lines:
        cv2.putText(frame, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
        y += 25


def draw_center_band(cv2, frame: Any) -> None:
    h, w = frame.shape[:2]
    left = int(w * 0.15)
    right = int(w * 0.85)
    overlay = frame.copy()
    cv2.rectangle(overlay, (left, 180), (right, h), (40, 80, 40), -1)
    cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)
    cv2.line(frame, (left, 180), (left, h), (70, 150, 70), 1)
    cv2.line(frame, (right, 180), (right, h), (70, 150, 70), 1)


def draw_pose(cv2, frame: Any, pose: PoseObservation) -> None:
    if not pose.detected or not pose.left_shoulder or not pose.right_shoulder:
        return
    color = (0, 210, 0) if pose.active_zone and pose.shoulders_facing else (0, 165, 255)
    cv2.line(frame, pose.left_shoulder, pose.right_shoulder, color, 3)
    cv2.circle(frame, pose.left_shoulder, 6, color, -1)
    cv2.circle(frame, pose.right_shoulder, 6, color, -1)
    if pose.center:
        cv2.circle(frame, pose.center, 5, (255, 255, 255), -1)


def draw_face(cv2, frame: Any, face: FaceObservation) -> None:
    if face.bbox:
        color = (0, 210, 0) if face.active_zone and face.eyes.gaze_centered else (0, 165, 255)
        x1, y1, x2, y2 = face.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    if face.eyes.eye_points:
        left = face.eyes.eye_points["left_eye"]
        right = face.eyes.eye_points["right_eye"]
        cv2.line(frame, left, right, (255, 255, 0), 2)
        cv2.circle(frame, left, 4, (255, 255, 0), -1)
        cv2.circle(frame, right, 4, (255, 255, 0), -1)
    for point_xy in face.eyes.iris_points.values():
        cv2.circle(frame, point_xy, 5, (0, 255, 255), 2)
    for start, end in face.eyes.gaze_vectors.values():
        cv2.arrowedLine(frame, start, end, (0, 255, 255), 2, cv2.LINE_AA, tipLength=0.25)


def resolve_path(path_value: str | Path, base_dir: Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def open_camera(cv2, camera: str, width: int, height: int, fps: float):
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


def maybe_writer(cv2, path: Path, frame_size: tuple[int, int], fps: float, enabled: bool):
    if not enabled:
        return None, ""
    return open_video_writer(cv2, path, frame_size, fps)


def open_video_writer(cv2, path: Path, frame_size: tuple[int, int], fps: float) -> tuple[Any, Path]:
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


def point(landmark: Any, width: int, height: int) -> tuple[int, int]:
    return int(landmark.x * width), int(landmark.y * height)


def average(points: list[tuple[int, int]]) -> tuple[int, int]:
    return int(sum(p[0] for p in points) / len(points)), int(sum(p[1] for p in points) / len(points))


def distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def movement_speed_ratio(
    previous_center: tuple[int, int] | None,
    current_center: tuple[int, int] | None,
    frame_width: int,
    dt: float,
) -> float:
    if previous_center is None or current_center is None or frame_width <= 0:
        return 0.0
    return distance(previous_center, current_center) / frame_width / max(dt, 0.001)


def landmarks_bbox(landmarks: list[Any], width: int, height: int) -> tuple[int, int, int, int]:
    xs = [max(0, min(width - 1, int(p.x * width))) for p in landmarks]
    ys = [max(0, min(height - 1, int(p.y * height))) for p in landmarks]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_area(bbox: tuple[int, int, int, int]) -> int:
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def bbox_area_ratio(bbox: tuple[int, int, int, int] | None, frame_area: float) -> float:
    if bbox is None or frame_area <= 0:
        return 0.0
    return bbox_area(bbox) / frame_area


def rss_mb(process: Any) -> float:
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


def write_summary(
    path: Path,
    metrics: dict[str, Any],
    events: list[dict[str, Any]],
    state_counts: dict[str, int],
    args: argparse.Namespace,
) -> None:
    event_lines = [f"- {row['time_sec']}s: `{row['event']}` - {row['detail']}" for row in events]
    if not event_lines:
        event_lines = ["- No state transition events were recorded."]

    state_lines = [f"- `{label}`: `{count}` frames" for label, count in sorted(state_counts.items())]
    if not state_lines:
        state_lines = ["- No frames were processed."]

    lines = [
        "# Holistic Usage Research Summary",
        "",
        "This run studies MediaPipe Holistic for kiosk person usage detection.",
        "",
        "## Config",
        "",
        f"- Camera: `{args.camera}`",
        f"- Duration target: `{args.duration}` seconds",
        f"- Usage hold: `{args.usage_hold_sec}` seconds",
        f"- Passing speed threshold: `{args.passing_speed_ratio_per_sec}` frame-width/sec",
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
        f"- Attention first sec: `{metrics['attention_first_sec']}`",
        f"- Support first sec: `{metrics['support_first_sec']}`",
        "",
        "## State Counts",
        "",
        *state_lines,
        "",
        "## Events",
        "",
        *event_lines,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
