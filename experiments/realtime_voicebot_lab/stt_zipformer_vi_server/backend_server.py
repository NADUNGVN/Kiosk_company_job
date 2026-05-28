import argparse
import json
import logging
import os
import sys
from dataclasses import fields
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = PROJECT_ROOT / "backend_config.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server_app.server import ServerSettings, create_app  # noqa: E402


def load_config(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Backend config must be a JSON object")
    return data


def resolve_project_path(value):
    if value in (None, ""):
        return value
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((PROJECT_ROOT / path).resolve())


def settings_from_config(config, host=None, port=None, log_level=None):
    allowed = {field.name for field in fields(ServerSettings)}
    unknown = sorted(set(config) - allowed)
    if unknown:
        raise ValueError("Unknown backend config key(s): " + ", ".join(unknown))

    data = dict(config)
    data["download_root"] = resolve_project_path(data.get("download_root"))

    if host is not None:
        data["host"] = host
    if port is not None:
        data["port"] = port
    if log_level is not None:
        data["log_level"] = log_level

    return ServerSettings(**data)


def configure_runtime_paths():
    os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / ".hf-cache"))
    os.environ.setdefault("HF_HUB_CACHE", str(PROJECT_ROOT / ".hf-cache" / "hub"))
    os.environ.setdefault("TORCH_HOME", str(PROJECT_ROOT / ".torch-cache"))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="RealtimeSTT Zipformer VI WebSocket backend")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to backend_config.json")
    parser.add_argument("--host", help="Override host from config")
    parser.add_argument("--port", type=int, help="Override port from config")
    parser.add_argument("--log-level", help="Override log level from config")
    parser.add_argument("--print-config", action="store_true", help="Print resolved public settings and exit")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    configure_runtime_paths()

    settings = settings_from_config(
        load_config(args.config),
        host=args.host,
        port=args.port,
        log_level=args.log_level.upper() if args.log_level else None,
    )

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.print_config:
        print(json.dumps(settings.public_dict(), indent=2, ensure_ascii=False))
        return

    import uvicorn

    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
