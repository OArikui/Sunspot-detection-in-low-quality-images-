"""Record run configuration, runtime details, and processing results."""

from __future__ import annotations

import copy
import json
import locale
import os
import platform
import sys
import time
import traceback
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from pprint import pformat
from typing import Any

from src.package.config import CONFIG_PATH, resolve_path


PACKAGE_DISTRIBUTIONS = {
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "Pillow": "Pillow",
    "PyYAML": "PyYAML",
    "tifffile": "tifffile",
    "astropy": "astropy",
    "opencv-python": "opencv-python",
    "PyQt6": "PyQt6",
    "scipy": "scipy",
    "scikit-image": "scikit-image",
}


def _collect_environment() -> dict[str, Any]:
    """Collect reproducibility information about the current Python runtime.

    Returns
    -------
    dict[str, Any]
        Operating-system, interpreter, hardware, locale, and package metadata.
    """
    packages: dict[str, str | None] = {}
    for display_name, distribution_name in PACKAGE_DISTRIBUTIONS.items():
        try:
            packages[display_name] = version(distribution_name)
        except PackageNotFoundError:
            packages[display_name] = None

    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "architecture": list(platform.architecture()),
            "processor": platform.processor() or None,
            "cpu_count": os.cpu_count(),
        },
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "build": list(platform.python_build()),
            "executable": sys.executable,
        },
        "locale": {
            "preferred_encoding": locale.getpreferredencoding(False),
            "timezone": datetime.now().astimezone().tzname(),
        },
        "packages": packages,
    }


SENSITIVE_ARGUMENT_MARKERS = (
    "password",
    "passwd",
    "token",
    "secret",
    "api-key",
    "api_key",
    "access-key",
    "access_key",
)


def _redact_arguments(arguments: list[str]) -> list[str]:
    """Mask values passed with common secret-bearing command-line options."""
    redacted: list[str] = []
    mask_next = False
    for argument in arguments:
        if mask_next:
            redacted.append("<redacted>")
            mask_next = False
            continue

        option, separator, value = argument.partition("=")
        is_sensitive = any(
            marker in option.lower() for marker in SENSITIVE_ARGUMENT_MARKERS
        )
        if is_sensitive and separator:
            redacted.append(f"{option}=<redacted>")
        else:
            redacted.append(argument)
            if is_sensitive and not separator:
                mask_next = True
    return redacted


def _redact_config(value: Any) -> Any:
    """Return a copy of configuration data with secret-like keys masked."""
    if isinstance(value, dict):
        sanitized: dict[Any, Any] = {}
        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            sensitive_markers = tuple(
                marker.replace("-", "_") for marker in SENSITIVE_ARGUMENT_MARKERS
            )
            sanitized[key] = (
                "<redacted>"
                if any(marker in normalized_key for marker in sensitive_markers)
                else _redact_config(item)
            )
        return sanitized
    if isinstance(value, list):
        return [_redact_config(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_config(item) for item in value)
    return copy.deepcopy(value)


class RunLogger:
    """Write one human-readable and one JSON log for a processing run."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Create log files and immediately record the effective run settings.

        Parameters
        ----------
        config : dict[str, Any]
            Configuration actually passed to the processing pipeline.
        """
        self.started_at = datetime.now().astimezone()
        self.started_clock = time.perf_counter()

        output_folder = resolve_path(str(config["Paths"]["output_folder"]))
        timestamp = self.started_at.strftime("%Y%m%d_%H%M%S_%f")
        self.run_id = timestamp
        self.session_dir = output_folder / f"session_{self.run_id}"
        self.logs_dir = self.session_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=False)
        self.log_path = self.logs_dir / f"run_{timestamp}.log"
        self.json_path = self.logs_dir / f"run_{timestamp}.json"

        safe_config = _redact_config(config)
        self.data: dict[str, Any] = {
            "run_id": self.run_id,
            "status": "running",
            "started_at": self.started_at.isoformat(),
            "finished_at": None,
            "duration_seconds": None,
            "execution": {
                "entrypoint": str(Path(sys.argv[0]).resolve()),
                "configuration_file": str(CONFIG_PATH),
                "arguments": _redact_arguments(sys.argv[1:]),
                "working_directory": str(Path.cwd()),
                "process_id": os.getpid(),
            },
            "environment": _collect_environment(),
            "output": {
                "base_directory": str(output_folder),
                "session_directory": str(self.session_dir),
                "logs_directory": str(self.logs_dir),
            },
            "config": safe_config,
            "events": [],
            "result": None,
            "error": None,
        }

        self._write_json()
        self._append_text(
            "\n".join(
                [
                    "=== PROCESSING RUN STARTED ===",
                    f"Run ID: {self.run_id}",
                    f"Started at: {self.started_at.isoformat()}",
                    f"Working directory: {Path.cwd()}",
                    f"Python: {sys.version.split()[0]}",
                    f"Platform: {platform.platform()}",
                    f"Session directory: {self.session_dir}",
                    f"Log JSON: {self.json_path}",
                    "",
                    "=== CONFIGURATION ===",
                    pformat(safe_config, sort_dicts=False),
                    "",
                    "=== ENVIRONMENT ===",
                    pformat(self.data["environment"], sort_dicts=False),
                    "",
                ]
            )
        )

    def record_event(self, event_name: str, details: dict[str, Any]) -> None:
        """Append a processing event and its details to both log files.

        Parameters
        ----------
        event_name : str
            Short name identifying the processing event.
        details : dict[str, Any]
            Event-specific values, such as selected ROI coordinates.
        """
        event = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "event": event_name,
            "details": _redact_config(details),
        }
        self.data["events"].append(event)
        self._write_json()
        self._append_text(
            "\n".join(
                [
                    f"=== EVENT: {event_name} ===",
                    f"Timestamp: {event['timestamp']}",
                    pformat(event["details"], sort_dicts=False),
                    "",
                ]
            )
        )

    def finish(self, result: dict[str, Any]) -> None:
        """Record successful completion and the processing result.

        Parameters
        ----------
        result : dict[str, Any]
            Result values returned by the processing pipeline.
        """
        finished_at = datetime.now().astimezone()
        duration = round(time.perf_counter() - self.started_clock, 3)
        self.data.update(
            {
                "status": "success",
                "finished_at": finished_at.isoformat(),
                "duration_seconds": duration,
                "result": result,
            }
        )
        self._write_json()
        self._append_text(
            "\n".join(
                [
                    "=== PROCESSING RUN COMPLETED ===",
                    f"Finished at: {finished_at.isoformat()}",
                    f"Duration: {duration:.3f} seconds",
                    f"Result: {pformat(result, sort_dicts=False)}",
                    f"JSON log: {self.json_path}",
                    "",
                ]
            )
        )

    def fail(self, error: BaseException) -> None:
        """Record an unhandled exception and its traceback.

        Parameters
        ----------
        error : BaseException
            Exception raised while running the processing pipeline.
        """
        finished_at = datetime.now().astimezone()
        duration = round(time.perf_counter() - self.started_clock, 3)
        error_details = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            ),
        }
        self.data.update(
            {
                "status": "failed",
                "finished_at": finished_at.isoformat(),
                "duration_seconds": duration,
                "error": error_details,
            }
        )
        self._write_json()
        self._append_text(
            "\n".join(
                [
                    "=== PROCESSING RUN FAILED ===",
                    f"Finished at: {finished_at.isoformat()}",
                    f"Duration: {duration:.3f} seconds",
                    f"Error: {error_details['type']}: {error_details['message']}",
                    "",
                    error_details["traceback"],
                    f"JSON log: {self.json_path}",
                    "",
                ]
            )
        )

    def _write_json(self) -> None:
        """Atomically update the machine-readable JSON log."""
        temporary_path = self.json_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.json_path)

    def _append_text(self, content: str) -> None:
        """Append text to the human-readable log file."""
        with self.log_path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(content)
            if not content.endswith("\n"):
                file.write("\n")
