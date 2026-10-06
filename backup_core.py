"""Create and verify local folders for optical-disc backups.

No function in this module writes to an optical drive. The user arranges DATA/.
The program creates the outer layout and later hashes DATA/ and optional ABOUT.txt.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import re
import stat
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable


CHUNK_SIZE = 1024 * 1024
DISC_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}\Z")
DISC_SEGMENT_RE = re.compile(r"[A-Za-z0-9]+\Z")
DISC_SUFFIX_RE = re.compile(r"[0-9]{1,8}\Z")
BATCH_NUMBER_RE = re.compile(r"B(\d{2})_", re.IGNORECASE)
HASH_LINE_RE = re.compile(r"([0-9a-f]{64})  (.+)\Z")
INVALID_TITLE_CHARS = set('<>:"/\\|?*')
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
Progress = Callable[[int, int, str], None]


class BackupError(Exception):
    """An input or integrity problem that can be shown directly in the GUI."""


@dataclass(frozen=True)
class BackupPlan:
    output_root: Path
    disc_id: str
    media: str
    mid: str
    batch_number: int
    batch_date: str
    title: str
    omit_about: bool = False

    @property
    def batch_name(self) -> str:
        return f"B{self.batch_number:02d}_{self.batch_date}_{self.title.strip()}"

    @property
    def disc_dir(self) -> Path:
        return self.output_root / self.disc_id

    @property
    def batch_dir(self) -> Path:
        return self.disc_dir / self.batch_name


@dataclass(frozen=True)
class DataFile:
    relative: Path
    size: int


@dataclass(frozen=True)
class VerificationResult:
    file_count: int
    total_bytes: int
    problems: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class ExistingDisc:
    output_root: Path
    disc_id: str
    media: str
    mid: str
    next_batch_number: int


def _is_reparse(path: Path) -> bool:
    info = os.stat(path, follow_symlinks=False)
    return bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT) or path.is_symlink()


def _is_optical_path(path: Path) -> bool:
    if os.name != "nt":
        return False
    root = path.anchor or path.absolute().anchor
    get_drive_type = ctypes.windll.kernel32.GetDriveTypeW
    get_drive_type.argtypes = [ctypes.c_wchar_p]
    get_drive_type.restype = ctypes.c_uint
    return bool(root) and get_drive_type(root) == 5


def validate_plan(plan: BackupPlan) -> None:
    if not DISC_ID_RE.fullmatch(plan.disc_id):
        raise BackupError("盘号须由 1–32 个字母、数字、下划线或连字符组成，首字须为字母或数字。")
    if not plan.media.strip() or any(char in plan.media for char in "\r\n"):
        raise BackupError("请填写介质类型，例如 BD-R 25 GB。")
    if any(char in plan.mid for char in "\r\n"):
        raise BackupError("MID 不能包含换行符。")
    if not 1 <= plan.batch_number <= 99:
        raise BackupError("批次编号须在 01–99 之间。")
    try:
        date.fromisoformat(plan.batch_date)
    except ValueError as exc:
        raise BackupError("批次日期须为有效的 YYYY-MM-DD。") from exc
    title = plan.title.strip()
    if not title or len(title) > 48 or title.endswith((".", " ")):
        raise BackupError("请填写 1–48 字的主题，末尾不能是空格或句点。")
    if any(char in INVALID_TITLE_CHARS or ord(char) < 32 for char in title):
        raise BackupError("主题包含 Windows 文件名不允许的字符。")
    if _is_optical_path(plan.output_root):
        raise BackupError("准备目录不能位于光盘上。请选硬盘目录。")
    if not plan.output_root.is_dir():
        raise BackupError("请选择存在的本地准备目录。")
    if _is_reparse(plan.output_root) or _is_optical_path(plan.output_root.resolve()):
        raise BackupError("准备目录不能是指向其他位置的链接或云盘占位目录。")


def render_disc_info(plan: BackupPlan) -> str:
    lines = [
        f"DiscID: {plan.disc_id}",
        f"Media: {plan.media.strip()}",
        f"Created: {date.today().isoformat()}",
        "DirectoryConvention: Bnn_YYYY-MM-DD_Title/DATA/, SHA256SUMS.txt; ABOUT.txt optional",
        "Checksum: SHA-256; hex digest, two spaces, path relative to batch folder",
        f"VolumeLabelToSetWhenBurning: {plan.disc_id}",
    ]
    if plan.mid.strip():
        lines.append(f"MID: {plan.mid.strip()}")
    return "\n".join(lines) + "\n"


def _read_disc_info(path: Path) -> dict[str, str]:
    info: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.partition(": ")
        if separator:
            info[key] = value
    return info


def compose_disc_id(prefix: str, middle: str, suffix: str) -> str:
    """Build a user-chosen disc ID; keep leading zeros in its numeric suffix."""
    prefix, middle, suffix = prefix.strip(), middle.strip(), suffix.strip()
    if not DISC_SEGMENT_RE.fullmatch(prefix):
        raise BackupError("盘号前缀只能包含英文字母和数字，例如 ARC。")
    if not DISC_SEGMENT_RE.fullmatch(middle):
        raise BackupError("盘号中段只能包含英文字母和数字，例如 BDR25。")
    if not DISC_SUFFIX_RE.fullmatch(suffix):
        raise BackupError("盘号序号须为 1–8 位数字，例如 001。")
    disc_id = f"{prefix.upper()}_{middle.upper()}_{suffix}"
    if not DISC_ID_RE.fullmatch(disc_id):
        raise BackupError("组合后的盘号超过 32 个字符，请缩短前缀或中段。")
    return disc_id


def load_existing_disc(disc_dir: Path) -> ExistingDisc:
    """Read a prepared disc folder and find its next unused batch number."""
    if not disc_dir.is_dir() or _is_reparse(disc_dir) or _is_optical_path(disc_dir):
        raise BackupError("请选择硬盘上已有的盘号目录。")
    info_path = disc_dir / "DISC_INFO.txt"
    if not info_path.is_file() or _is_reparse(info_path):
        raise BackupError("所选目录没有普通的 DISC_INFO.txt。")
    try:
        info = _read_disc_info(info_path)
        entries = tuple(disc_dir.iterdir())
    except (OSError, UnicodeError) as exc:
        raise BackupError(f"无法读取已有盘号目录：{exc}") from exc
    disc_id = info.get("DiscID", "")
    media = info.get("Media", "")
    if disc_id != disc_dir.name or not DISC_ID_RE.fullmatch(disc_id) or not media.strip():
        raise BackupError("DISC_INFO.txt 中的盘号或介质与目录不符。")
    highest = 0
    for item in entries:
        match = BATCH_NUMBER_RE.match(item.name)
        if match:
            highest = max(highest, int(match.group(1)))
    if highest >= 99:
        raise BackupError("该盘已有 B99，不能再增加批次。")
    return ExistingDisc(disc_dir.parent, disc_id, media, info.get("MID", ""), highest + 1)


def _ensure_disc_dir(plan: BackupPlan) -> Path:
    disc_dir = plan.disc_dir
    info_path = disc_dir / "DISC_INFO.txt"
    if disc_dir.exists():
        if _is_reparse(disc_dir) or _is_optical_path(disc_dir.resolve()):
            raise BackupError("已有盘号目录是链接或指向光驱，不能继续写入。")
        if not info_path.is_file() or _is_reparse(info_path):
            raise BackupError(f"已有盘号目录却没有普通的 DISC_INFO.txt：{disc_dir}")
        existing = _read_disc_info(info_path)
        if existing.get("DiscID") != plan.disc_id:
            raise BackupError("已有 DISC_INFO.txt 的盘号与当前输入不符。")
        if existing.get("Media") != plan.media.strip():
            raise BackupError("已有 DISC_INFO.txt 的介质类型与当前输入不符。")
        if plan.mid.strip() and existing.get("MID", "") != plan.mid.strip():
            raise BackupError("已有 DISC_INFO.txt 的 MID 与当前输入不符。")
    else:
        disc_dir.mkdir(exist_ok=False)
        with info_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_disc_info(plan))
    return disc_dir


def create_batch(plan: BackupPlan) -> Path:
    """Create the requested empty files and DATA directory; never overwrite."""
    validate_plan(plan)
    final = plan.batch_dir
    if final.exists():
        raise BackupError(f"该批次目录已存在，不会覆盖：{final}")
    _ensure_disc_dir(plan)
    final.mkdir(exist_ok=False)
    (final / "DATA").mkdir()
    if not plan.omit_about:
        (final / "ABOUT.txt").open("x", encoding="utf-8").close()
    (final / "SHA256SUMS.txt").open("x", encoding="utf-8").close()
    return final


def _require_local_batch(batch_dir: Path) -> tuple[Path, Path, Path]:
    if _is_optical_path(batch_dir):
        raise BackupError("程序不会修改光盘。请选择硬盘上的备份准备目录。")
    if _is_reparse(batch_dir):
        raise BackupError("批次目录是链接或云盘占位目录，不能写入。")
    batch_dir = batch_dir.resolve()
    if _is_optical_path(batch_dir):
        raise BackupError("批次目录指向光驱，程序不会写入光盘。")
    data = batch_dir / "DATA"
    about = batch_dir / "ABOUT.txt"
    manifest = batch_dir / "SHA256SUMS.txt"
    if not data.is_dir() or not manifest.is_file():
        raise BackupError("批次目录须包含 DATA/ 和 SHA256SUMS.txt。")
    if (about.exists() or about.is_symlink()) and not about.is_file():
        raise BackupError("ABOUT.txt 必须是普通文件，或不创建。")
    paths = (batch_dir, data, manifest) + ((about,) if about.exists() or about.is_symlink() else ())
    if any(_is_reparse(item) for item in paths):
        raise BackupError("批次目录包含链接或云盘占位文件，请使用真实的本地文件。")
    return data, about, manifest


def save_about(batch_dir: Path, content: str, invalidate_manifest: bool = False) -> Path:
    """Save editor text. Changing a hashed ABOUT requires clearing the old manifest."""
    if not content.strip():
        raise BackupError("请先填写 ABOUT 内容。")
    _, about, manifest = _require_local_batch(batch_dir)
    if manifest.stat().st_size:
        if not invalidate_manifest:
            raise BackupError("SHA256SUMS.txt 已有内容。先确认使旧清单失效，再更新 ABOUT。")
        manifest.write_text("", encoding="utf-8")
    temporary = about.with_name(f"ABOUT.txt.tmp-{uuid.uuid4().hex[:8]}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content.rstrip() + "\n")
        os.replace(temporary, about)
    finally:
        if temporary.exists():
            temporary.unlink()
    return about


def scan_data(data: Path) -> tuple[DataFile, ...]:
    if not data.is_dir() or _is_reparse(data):
        raise BackupError("DATA 文件夹不存在，或是链接／云盘占位目录。")
    files: list[DataFile] = []
    seen: set[str] = set()

    def visit(folder: Path, relative_folder: Path) -> None:
        try:
            with os.scandir(folder) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.casefold())
        except OSError as exc:
            raise BackupError(f"无法读取 {folder}：{exc}") from exc
        for entry in entries:
            path = Path(entry.path)
            relative = relative_folder / entry.name
            if _is_reparse(path):
                raise BackupError(f"DATA 中有链接或云盘占位文件：{path}")
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                visit(path, relative)
            elif stat.S_ISREG(info.st_mode):
                key = relative.as_posix().casefold()
                if key in seen:
                    raise BackupError(f"DATA 中有大小写冲突的路径：{relative}")
                seen.add(key)
                files.append(DataFile(relative, info.st_size))
            else:
                raise BackupError(f"DATA 中有非普通文件：{path}")

    visit(data, Path())
    if not files:
        raise BackupError("DATA 还是空的。请先把文件放进去。")
    return tuple(files)


def _hash_file(path: Path, tick: Callable[[int], None] | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(CHUNK_SIZE):
            digest.update(block)
            if tick:
                tick(len(block))
    return digest.hexdigest()


def generate_manifest(batch_dir: Path, replace: bool = False,
                      progress: Progress | None = None, omit_about: bool = False) -> Path:
    """Hash DATA and, unless explicitly omitted, a nonempty ABOUT.txt."""
    data, about, manifest = _require_local_batch(batch_dir)
    if omit_about:
        if about.is_file() and about.stat().st_size:
            raise BackupError("ABOUT.txt 已有内容；不能在“不写 ABOUT”模式下略过它。")
    elif not about.is_file() or not about.stat().st_size:
        raise BackupError("ABOUT.txt 缺失或为空。请填写内容，或勾选“不写 ABOUT.txt”。")
    previous_manifest = manifest.stat().st_size > 0
    if previous_manifest and not replace:
        raise BackupError("SHA256SUMS.txt 已有内容。需要更新时请明确确认覆盖本地清单。")
    files = scan_data(data)
    if omit_about and about.is_file():
        about.unlink()
    total = max(1, (0 if omit_about else about.stat().st_size) + sum(item.size for item in files))
    completed = 0

    def tick(amount: int, label: str) -> None:
        nonlocal completed
        completed += amount
        if progress:
            progress(min(completed, total), total, label)

    lines = []
    if not omit_about:
        lines.append(f"{_hash_file(about, lambda n: tick(n, '计算 ABOUT.txt'))}  ABOUT.txt")
    for item in files:
        path = data / item.relative
        digest = _hash_file(path, lambda n, rel=item.relative: tick(n, f"计算：{rel}"))
        lines.append(f"{digest}  DATA/{item.relative.as_posix()}")
    temporary = manifest.with_name(f"SHA256SUMS.txt.tmp-{uuid.uuid4().hex[:8]}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(sorted(lines, key=lambda line: line.split("  ", 1)[1].casefold())) + "\n")
        os.replace(temporary, manifest)
    finally:
        if temporary.exists():
            temporary.unlink()
    if progress:
        progress(total, total, "SHA256SUMS.txt 已更新")
    return manifest


def _valid_manifest_path(path: str) -> bool:
    if path == "ABOUT.txt":
        return True
    if not path.startswith("DATA/") or "\\" in path or ":" in path:
        return False
    parts = path.split("/")
    return len(parts) >= 2 and all(part not in ("", ".", "..") for part in parts)


def verify_batch(batch_dir: Path, progress: Progress | None = None) -> VerificationResult:
    """Read only. Works on a local batch or on a batch already burned to disc."""
    batch_dir = batch_dir.resolve()
    manifest = batch_dir / "SHA256SUMS.txt"
    data = batch_dir / "DATA"
    about = batch_dir / "ABOUT.txt"
    if not manifest.is_file() or not data.is_dir():
        raise BackupError("所选目录须包含 SHA256SUMS.txt 和 DATA 文件夹。")
    if any(_is_reparse(item) for item in (batch_dir, data, manifest)):
        raise BackupError("批次目录中存在链接，无法安全校验。")
    try:
        lines = manifest.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise BackupError(f"无法读取 SHA256SUMS.txt：{exc}") from exc
    if not lines:
        raise BackupError("SHA256SUMS.txt 为空，尚未生成校验清单。")

    expected: dict[str, str] = {}
    seen: set[str] = set()
    for number, line in enumerate(lines, 1):
        match = HASH_LINE_RE.fullmatch(line)
        if not match or not _valid_manifest_path(match.group(2)):
            raise BackupError(f"SHA256SUMS.txt 第 {number} 行格式或路径无效。")
        name = match.group(2)
        if name.casefold() in seen:
            raise BackupError(f"SHA256SUMS.txt 有重复路径：{name}")
        seen.add(name.casefold())
        expected[name] = match.group(1)

    problems: list[str] = []
    actual: dict[str, Path] = {}
    if about.is_file() and not _is_reparse(about):
        actual["ABOUT.txt"] = about
        if about.stat().st_size == 0:
            problems.append("ABOUT.txt 仍为空")
    elif about.exists() or about.is_symlink():
        problems.append("ABOUT.txt 不是普通文件")
    try:
        for item in scan_data(data):
            actual[f"DATA/{item.relative.as_posix()}"] = data / item.relative
    except BackupError as exc:
        problems.append(str(exc))
    expected_keys = set(expected)
    actual_keys = set(actual)
    problems.extend(f"清单所列文件缺失：{path}" for path in sorted(expected_keys - actual_keys))
    problems.extend(f"目录中有清单未列的文件：{path}" for path in sorted(actual_keys - expected_keys))
    for item in batch_dir.iterdir():
        if item.name not in {"ABOUT.txt", "DATA", "SHA256SUMS.txt"}:
            problems.append(f"批次根目录有未纳入清单的项目：{item.name}")

    paths = sorted(expected_keys & actual_keys)
    total_bytes = sum(actual[path].stat().st_size for path in paths)
    completed = 0
    for path in paths:
        try:
            digest = hashlib.sha256()
            with actual[path].open("rb") as stream:
                while block := stream.read(CHUNK_SIZE):
                    digest.update(block)
                    completed += len(block)
                    if progress:
                        progress(completed, max(1, total_bytes), f"校验：{path}")
            if digest.hexdigest() != expected[path]:
                problems.append(f"哈希不符：{path}")
        except OSError as exc:
            problems.append(f"读取失败：{path}（{exc}）")
    if progress:
        progress(max(1, total_bytes), max(1, total_bytes), "校验完成")
    return VerificationResult(len(paths), total_bytes, tuple(problems))
