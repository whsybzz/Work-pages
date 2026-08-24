"""Local and remote agent for the PCB B/S integration page.

The browser cannot start a Windows executable directly. This service exposes
only the two known desktop launch actions and protects remote requests with a
generated access token.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
import secrets
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


BASE_DIR = Path(__file__).resolve().parent
APP_NAME = "PCB_Defect_Detection.exe"
EVERYTHING_APP_NAME = "Everything.exe"
ACTIVE_PROCESS: subprocess.Popen[bytes] | None = None
EVERYTHING_PROCESS: subprocess.Popen[bytes] | None = None
TOKEN_FILE = BASE_DIR / ".remote_access_token"
REMOTE_MODE = False
REMOTE_ACCESS_TOKEN: str | None = None
ALLOWED_ORIGINS: set[str] = set()


def _is_loopback_host(host: str) -> bool:
    return host.casefold() in {"127.0.0.1", "localhost", "::1"}


def _configured_token_file() -> Path:
    return Path(os.environ.get("PCB_BS_TOKEN_FILE", str(TOKEN_FILE))).expanduser()


def _load_remote_access_token(remote_mode: bool) -> tuple[str | None, Path]:
    """Load a token or create one for a remote agent without committing it."""
    configured = os.environ.get("PCB_BS_ACCESS_TOKEN", "").strip()
    token_file = _configured_token_file()
    if configured:
        return configured, token_file

    if token_file.is_file():
        saved = token_file.read_text(encoding="utf-8").strip()
        if saved:
            return saved, token_file

    if not remote_mode:
        return None, token_file

    token = secrets.token_urlsafe(32)
    try:
        token_file.write_text(token + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Warning: could not persist remote access token: {exc}")
    return token, token_file


def _configured_origins() -> set[str]:
    raw = os.environ.get("PCB_BS_ALLOWED_ORIGINS", "https://whsybzz.github.io")
    return {origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()}


def executable_candidates() -> list[Path]:
    configured = os.environ.get("PCB_DEFECT_EXE")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend(
        [
            BASE_DIR / APP_NAME,
            BASE_DIR / "PCB_Defect_Detection" / APP_NAME,
            BASE_DIR / "release" / "PCB_Defect_Detection" / APP_NAME,
            BASE_DIR.parent / "release" / "PCB_Defect_Detection" / APP_NAME,
            BASE_DIR.parent.parent / "PCB_yolo_detection_20260817_exe" / "release" / "PCB_Defect_Detection" / APP_NAME,
            BASE_DIR.parent.parent / "PCB_yolo_detection_20260817_exe" / "build_exe" / "PCB_Defect_Detection" / APP_NAME,
        ]
    )
    return candidates


def find_executable() -> Path | None:
    for candidate in executable_candidates():
        if candidate.is_file():
            return candidate.resolve()
    return None


def everything_executable_candidates() -> list[Path]:
    configured = os.environ.get("EVERYTHING_EXE")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend(
        [
            # Target of the Everything shortcut installed on this desktop.
            Path(r"D:\AppGallery\Downloads\everything\Everything.exe"),
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "Everything"
            / EVERYTHING_APP_NAME,
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
            / "Everything"
            / EVERYTHING_APP_NAME,
            Path.home() / "AppData" / "Local" / "Everything" / EVERYTHING_APP_NAME,
            Path.home() / "AppData" / "Roaming" / "Everything" / EVERYTHING_APP_NAME,
        ]
    )
    return candidates


def find_everything_executable() -> Path | None:
    for candidate in everything_executable_candidates():
        if candidate.is_file():
            return candidate.resolve()
    return None


def everything_shortcut_candidates() -> list[Path]:
    configured = os.environ.get("EVERYTHING_LNK")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend(
        [
            Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Everything.lnk"),
            Path.home() / "Desktop" / "Everything.lnk",
            Path.home() / "OneDrive" / "Desktop" / "Everything.lnk",
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Everything.lnk",
        ]
    )
    return candidates


def find_everything_shortcut() -> Path | None:
    for candidate in everything_shortcut_candidates():
        if candidate.is_file():
            return candidate.resolve()
    return None


def _desktop_name(handle) -> str | None:
    user32 = ctypes.windll.user32
    required = wintypes.DWORD()
    buffer = ctypes.create_unicode_buffer(256)
    if not handle or not user32.GetUserObjectInformationW(
        handle, 2, buffer, ctypes.sizeof(buffer), ctypes.byref(required)
    ):
        return None
    return buffer.value or None


def _desktop_candidates() -> list[str]:
    """Return visible desktop candidates in the safest launch order."""
    if sys.platform != "win32":
        return []

    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        station_name = _desktop_name(user32.GetProcessWindowStation())
        if not station_name:
            return []
        candidates = []

        # The server may run on a helper desktop. OpenInputDesktop identifies
        # the desktop currently visible to the logged-in user instead.
        input_desktop = user32.OpenInputDesktop(0, False, 0x01FF)
        input_name = _desktop_name(input_desktop)
        if input_desktop and hasattr(user32, "CloseDesktop"):
            user32.CloseDesktop(input_desktop)
        if input_name:
            candidates.append(f"{station_name}\\{input_name}")

        thread_desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
        thread_name = _desktop_name(thread_desktop)
        if thread_name:
            thread_path = f"{station_name}\\{thread_name}"
            if thread_path not in candidates:
                candidates.append(thread_path)

        return candidates or [f"{station_name}\\Default"]
    except (AttributeError, OSError):
        return [r"WinSta0\Default"]


def _has_visible_window(pid: int | None, desktop_path: str | None = None) -> bool:
    """Check whether the launched desktop process owns a visible window."""
    if sys.platform != "win32" or not pid:
        return False

    try:
        user32 = ctypes.windll.user32
        found = False
        if desktop_path and "\\" in desktop_path:
            desktop_name = desktop_path.rsplit("\\", 1)[1]
            desktop = user32.OpenDesktopW(desktop_name, 0, False, 0x01FF)
        else:
            desktop = user32.OpenInputDesktop(0, False, 0x01FF)
        if not desktop:
            return False
        enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def inspect_window(hwnd, _lparam):
            nonlocal found
            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            if process_id.value == pid and user32.IsWindowVisible(hwnd):
                found = True
                user32.ShowWindow(hwnd, 1)
                user32.SetForegroundWindow(hwnd)
                return False
            return True

        user32.EnumDesktopWindows(desktop, enum_windows_proc(inspect_window), 0)
        user32.CloseDesktop(desktop)
        return found
    except (AttributeError, OSError):
        return False


def _shell_process_id() -> int | None:
    """Find the Explorer process in this Windows session."""
    if sys.platform != "win32":
        return None
    try:
        import psutil

        current_session = ctypes.wintypes.DWORD()
        ctypes.windll.kernel32.ProcessIdToSessionId(
            ctypes.windll.kernel32.GetCurrentProcessId(),
            ctypes.byref(current_session),
        )
        for process in psutil.process_iter(["name"]):
            if (process.info.get("name") or "").casefold() != "explorer.exe":
                continue
            process_session = ctypes.wintypes.DWORD()
            ctypes.windll.kernel32.ProcessIdToSessionId(
                process.pid,
                ctypes.byref(process_session),
            )
            if process_session.value == current_session.value:
                return process.pid
    except ImportError:
        return None
    except Exception:
        return None


def _desktop_user_matches() -> bool:
    """Check that the service and the visible Windows desktop share a user."""
    shell_pid = _shell_process_id()
    if shell_pid is None:
        return True
    try:
        import psutil

        return psutil.Process().username().casefold() == psutil.Process(shell_pid).username().casefold()
    except ImportError:
        return True
    except Exception:
        return True


def _windows_process_pid(process_name: str) -> int | None:
    """Return the PID of a named desktop client with a visible window."""
    candidate_pids = _process_pids(process_name)
    if not candidate_pids:
        return None

    for pid in candidate_pids:
        if any(_has_visible_window(pid, desktop) for desktop in _desktop_candidates()):
            return pid
    return None


def _running_process_pid(process_name: str) -> int | None:
    """Return a PID for a named process, even if its UI is elevated."""
    pids = _process_pids(process_name)
    return pids[0] if pids else None


def _process_pids(process_name: str) -> list[int]:
    """List process IDs without spawning a potentially slow system command."""
    if sys.platform != "win32":
        return []

    try:
        import psutil

        return [
            process.pid
            for process in psutil.process_iter(["name"])
            if (process.info.get("name") or "").casefold() == process_name.casefold()
        ]
    except ImportError:
        pass
    except Exception:
        return []

    try:
        class ProcessEntry32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        invalid_handle = ctypes.c_void_p(-1).value
        if not snapshot or snapshot == invalid_handle:
            return []

        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        pids: list[int] = []
        try:
            if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                return []
            while True:
                if entry.szExeFile.casefold() == process_name.casefold():
                    pids.append(entry.th32ProcessID)
                if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
        finally:
            kernel32.CloseHandle(snapshot)
        return pids
    except (AttributeError, OSError, TypeError):
        return []


def _shell_open(target: Path, arguments: str, working_directory: Path) -> None:
    """Ask Windows Shell to open a shortcut without blocking the HTTP request."""
    if sys.platform != "win32":
        raise OSError("Windows Shell 仅在 Windows 系统可用")

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "open",
        str(target),
        arguments,
        str(working_directory),
        1,
    )
    if result <= 32:
        raise OSError(f"ShellExecuteW 返回错误码 {result}")


def _shell_open_async(target: Path, arguments: str, working_directory: Path) -> None:
    """Run ShellExecute outside the single-threaded HTTP request handler."""
    threading.Thread(
        target=_shell_open,
        args=(target, arguments, working_directory),
        daemon=True,
    ).start()


def _process_status(
    process_name: str,
    active_process: subprocess.Popen[bytes] | None,
) -> tuple[bool, int | None, subprocess.Popen[bytes] | None]:
    shell_pid = _windows_process_pid(process_name)
    if shell_pid is not None:
        return True, shell_pid, active_process

    if active_process is None:
        return False, None, None
    if active_process.poll() is None:
        if sys.platform == "win32" and not any(
            _has_visible_window(active_process.pid, desktop)
            for desktop in _desktop_candidates()
        ):
            return False, None, active_process
        return True, active_process.pid, active_process
    return False, None, None


def process_status() -> tuple[bool, int | None]:
    global ACTIVE_PROCESS
    running, pid, ACTIVE_PROCESS = _process_status(APP_NAME, ACTIVE_PROCESS)
    return running, pid


def everything_process_status() -> tuple[bool, int | None]:
    global EVERYTHING_PROCESS
    pid = _running_process_pid(EVERYTHING_APP_NAME)
    if pid is not None:
        return True, pid
    if EVERYTHING_PROCESS is None:
        return False, None
    if EVERYTHING_PROCESS.poll() is None:
        return True, EVERYTHING_PROCESS.pid
    EVERYTHING_PROCESS = None
    return False, None


def _launch_named_executable(
    executable: Path,
    process_name: str,
    active_process: subprocess.Popen[bytes] | None,
    user_mismatch_message: str,
) -> tuple[bool, int | None, bool, subprocess.Popen[bytes] | None, str | None]:
    running, pid, active_process = _process_status(process_name, active_process)
    if running:
        return True, pid, True, active_process, None

    if sys.platform == "win32":
        if not _desktop_user_matches():
            return False, None, False, active_process, user_mismatch_message

        last_pid = None
        for desktop_path in _desktop_candidates():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.lpDesktop = desktop_path
            candidate_process = subprocess.Popen(
                [str(executable)],
                cwd=str(executable.parent),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            last_pid = candidate_process.pid
            for _ in range(60):
                time.sleep(0.1)
                if candidate_process.poll() is not None:
                    break
                if _has_visible_window(candidate_process.pid, desktop_path):
                    return True, candidate_process.pid, False, candidate_process, None

            # A process without a visible window is not a successful launch.
            # Retry on the next user desktop instead of leaving a hidden copy.
            if candidate_process.poll() is None:
                candidate_process.terminate()
                try:
                    candidate_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    candidate_process.kill()

        return (
            False,
            last_pid,
            False,
            active_process,
            "客户端进程已创建，但没有检测到可见窗口，请确认服务和桌面客户端属于同一 Windows 用户。",
        )

    active_process = subprocess.Popen(
        [str(executable)],
        cwd=str(executable.parent),
        close_fds=True,
    )
    return True, active_process.pid, False, active_process, None


def launch_executable() -> tuple[bool, int | None, bool, str | None, str | None]:
    global ACTIVE_PROCESS
    executable = find_executable()
    if executable is None:
        return False, None, False, None, "未找到 PCB_Defect_Detection.exe。"

    launched, pid, already_running, ACTIVE_PROCESS, launch_message = _launch_named_executable(
        executable,
        APP_NAME,
        ACTIVE_PROCESS,
        "当前网页服务不是以 Windows 桌面用户启动的，请双击 BS\\start_server.bat 后再点击“缺陷图片库”。",
    )
    return launched, pid, already_running, str(executable), launch_message


def launch_everything() -> tuple[bool, int | None, bool, str | None, str | None]:
    global EVERYTHING_PROCESS
    executable = find_everything_executable()
    if executable is None:
        return False, None, False, None, "未找到 Everything.exe，请确认桌面 Everything 快捷方式仍然有效。"

    running, pid = everything_process_status()
    if sys.platform == "win32":
        if not _desktop_user_matches():
            return (
                False,
                None,
                False,
                str(executable),
                "当前网页服务不是以 Windows 桌面用户启动的，请双击 BS\\start_server.bat 后再点击“文档管理”。",
            )

        launch_target = find_everything_shortcut() or executable
        try:
            # ShellExecute is required because this Everything installation is
            # configured to run as administrator. -newwindow also activates
            # the search UI when an Everything process is already running.
            _shell_open_async(launch_target, "-newwindow", executable.parent)
        except OSError as exc:
            return False, pid, running, str(executable), f"启动 Everything 失败：{exc}"

        time.sleep(0.4)
        return True, _running_process_pid(EVERYTHING_APP_NAME) or pid, running, str(executable), None

    EVERYTHING_PROCESS = subprocess.Popen(
        [str(executable), "-newwindow"],
        cwd=str(executable.parent),
        close_fds=True,
    )
    return True, EVERYTHING_PROCESS.pid, running, str(executable), None


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class RequestHandler(SimpleHTTPRequestHandler):
    """Serve the UI and the narrowly scoped desktop launch endpoints."""

    server_version = "PCB-BS/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin", "").rstrip("/")
        return not origin or origin in ALLOWED_ORIGINS

    def _add_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "").rstrip("/")
        if origin and origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _request_token(self) -> str:
        authorization = self.headers.get("Authorization", "")
        if authorization.casefold().startswith("bearer "):
            return authorization[7:].strip()
        return self.headers.get("X-PCB-Access-Token", "").strip()

    def _remote_authorized(self) -> tuple[bool, str | None]:
        client_host = self.client_address[0]
        if not REMOTE_MODE and _is_loopback_host(client_host):
            return True, None
        if not REMOTE_ACCESS_TOKEN:
            return False, "远程代理未配置访问令牌。"
        if not secrets.compare_digest(self._request_token(), REMOTE_ACCESS_TOKEN):
            return False, "访问令牌无效。"
        if not self._origin_allowed():
            return False, "请求来源未被允许。"
        return True, None

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("请求体长度无效") from exc
        if content_length <= 0 or content_length > 4096:
            raise ValueError("请求体大小无效")
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("请求体不是有效 JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象")
        return payload

    def _handle_launch(self, launch_target) -> None:
        try:
            launched, pid, already_running, executable, launch_message = launch_target()
        except OSError as exc:
            self._send_json(
                {"ok": False, "message": f"启动桌面程序失败：{exc}"},
                status=500,
            )
            return

        if not launched:
            self._send_json(
                {
                    "ok": False,
                    "message": (
                        launch_message
                        or "客户端进程已创建，但没有检测到可见窗口，请确认服务和桌面客户端属于同一 Windows 用户。"
                    ),
                    "pid": pid,
                    "executable": executable,
                },
                status=404 if executable is None else 500,
            )
            return

        self._send_json(
            {
                "ok": True,
                "pid": pid,
                "already_running": already_running,
                "executable": executable,
            }
        )

    def _require_remote_access(self) -> bool:
        authorized, message = self._remote_authorized()
        if authorized:
            return True
        self._send_json({"ok": False, "message": message}, status=401)
        return False

    def do_OPTIONS(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path not in {"/api/remote/status", "/api/remote/launch"}:
            self._send_json({"ok": False, "message": "接口不存在"}, status=404)
            return
        if not self._origin_allowed():
            self._send_json({"ok": False, "message": "请求来源未被允许。"}, status=403)
            return
        self.send_response(204)
        self._add_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-PCB-Access-Token, bypass-tunnel-reminder")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        request = urlsplit(self.path)
        path = request.path
        if path == "/api/remote/status":
            if not self._require_remote_access():
                return
            executable = find_executable()
            everything_executable = find_everything_executable()
            self._send_json(
                {
                    "ok": True,
                    "available": executable is not None,
                    "everything_available": everything_executable is not None,
                    "remote": REMOTE_MODE,
                }
            )
            return
        if path == "/api/launcher-status":
            if REMOTE_MODE and not self._require_remote_access():
                return
            executable = find_executable()
            running, pid = process_status()
            everything_executable = find_everything_executable()
            everything_running, everything_pid = everything_process_status()
            self._send_json(
                {
                    "ok": True,
                    "available": executable is not None,
                    "running": running,
                    "pid": pid,
                    "everything_available": everything_executable is not None,
                    "everything_running": everything_running,
                    "everything_pid": everything_pid,
                }
            )
            return
        if path == "/":
            launch_name = parse_qs(request.query).get("launch", [None])[0]
            launch_target = {
                "defect-library": launch_executable,
                "everything": launch_everything,
            }.get(launch_name)
            if launch_target is not None:
                if not self._require_remote_access():
                    return
                self._handle_launch(launch_target)
                return
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path == "/api/remote/launch":
            if not self._require_remote_access():
                return
            try:
                payload = self._read_json_body()
            except ValueError as exc:
                self._send_json({"ok": False, "message": str(exc)}, status=400)
                return
            launch_target = {
                "defect-library": launch_executable,
                "everything": launch_everything,
            }.get(payload.get("target"))
            if launch_target is None:
                self._send_json({"ok": False, "message": "不支持的启动目标。"}, status=400)
                return
            self._handle_launch(launch_target)
            return

        launch_target = {
            "/api/launch-defect-library": launch_executable,
            "/api/launch-everything": launch_everything,
        }.get(path)
        if launch_target is None:
            self._send_json({"ok": False, "message": "接口不存在"}, status=404)
            return
        if REMOTE_MODE and not self._require_remote_access():
            return

        self._handle_launch(launch_target)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string}] {format % args}")


def main() -> None:
    global ALLOWED_ORIGINS, REMOTE_ACCESS_TOKEN, REMOTE_MODE

    parser = argparse.ArgumentParser(description="PCB B/S local integration server")
    parser.add_argument("--host", default=os.environ.get("PCB_BS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PCB_BS_PORT", "8765")))
    parser.add_argument(
        "--remote",
        action="store_true",
        help="enable token-protected remote launch endpoints",
    )
    args = parser.parse_args()

    REMOTE_MODE = args.remote or not _is_loopback_host(args.host)
    REMOTE_ACCESS_TOKEN, token_file = _load_remote_access_token(REMOTE_MODE)
    ALLOWED_ORIGINS = _configured_origins()
    if REMOTE_MODE and not REMOTE_ACCESS_TOKEN:
        raise SystemExit("远程模式需要访问令牌，请设置 PCB_BS_ACCESS_TOKEN 后重试。")

    # Keep requests on the main thread so Windows GUI launch inherits the
    # interactive desktop used by the local server process.
    server = HTTPServer((args.host, args.port), RequestHandler)
    print(f"PCB B/S platform running at http://{args.host}:{args.port}")
    print(f"EXE status: {'found' if find_executable() else 'not found'}")
    if REMOTE_MODE:
        print("Remote launch: enabled")
        print(f"Remote access token: {REMOTE_ACCESS_TOKEN}")
        print(f"Token file: {token_file}")
        print(f"Allowed origins: {', '.join(sorted(ALLOWED_ORIGINS))}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
