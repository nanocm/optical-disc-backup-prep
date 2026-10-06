"""Windows GUI for preparing, hashing, and verifying an optical-disc backup."""

from __future__ import annotations

import json
import ctypes
import os
import queue
import subprocess
import threading
import time
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, scrolledtext, ttk

from backup_core import (
    BackupError,
    BackupPlan,
    compose_disc_id,
    create_batch,
    generate_manifest,
    load_existing_disc,
    render_disc_info,
    save_about,
    verify_batch,
)


HERE = Path(__file__).resolve().parent


def enable_windows_dpi_awareness() -> None:
    """Let Tk draw at the monitor's real DPI instead of being bitmap-scaled."""
    if os.name != "nt":
        return
    try:
        set_context = ctypes.windll.user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = ctypes.c_bool
        if set_context(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2
            return
    except (AttributeError, OSError):
        pass
    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


MEDIA_TYPES = {
    0: "未知", 1: "CD-ROM", 2: "CD-R", 3: "CD-RW", 4: "DVD-ROM",
    5: "DVD-RAM", 6: "DVD+R", 7: "DVD+RW", 8: "DVD+R DL",
    9: "DVD-R", 10: "DVD-RW", 11: "DVD-R DL", 12: "通用光盘",
    13: "DVD+RW DL", 14: "HD DVD-ROM", 15: "HD DVD-R",
    16: "HD DVD-RAM", 17: "保留类型", 18: "BD-ROM", 19: "BD-R", 20: "BD-RE",
}


def readable_size(size: int | None) -> str:
    if size is None or size < 0:
        return "未知"
    if size >= 1_000_000_000:
        return f"{size / 1_000_000_000:.2f} GB"
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB"
    return f"{size:,} 字节"


def suggested_media(info: dict) -> str:
    name = MEDIA_TYPES.get(info.get("MediaTypeCode"), "未知")
    sectors = info.get("TotalSectors")
    if not isinstance(sectors, int) or sectors <= 0:
        return name
    gb = sectors * 2048 / 1_000_000_000
    if name.startswith("BD-"):
        size = min((25, 50, 100, 128), key=lambda item: abs(item - gb))
        return f"{name} {size} GB" if abs(size - gb) / size < .15 else name
    if name.startswith("DVD") and not name.endswith("ROM"):
        size = min((4.7, 8.5), key=lambda item: abs(item - gb))
        return f"{name} {size:g} GB" if abs(size - gb) / size < .15 else name
    if name.startswith("CD-") and .5 < gb < .9:
        return f"{name} 700 MB"
    return name


def read_optical_drives(include_media: bool = False, drive_letter: str = "") -> list[dict]:
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
               "Bypass", "-File", str(HERE / "read_disc.ps1")]
    if include_media:
        command.append("-IncludeMedia")
        if drive_letter:
            command.extend(("-DriveLetter", drive_letter))
    result = subprocess.run(
        command, capture_output=True, encoding="utf-8", errors="replace", timeout=35,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False,
    )
    if result.returncode:
        raise BackupError(f"Windows 光驱查询失败：{result.stderr.strip() or result.returncode}")
    try:
        data = json.loads(result.stdout.lstrip("\ufeff"))
    except json.JSONDecodeError as exc:
        raise BackupError(f"无法解析 Windows 光驱信息：{result.stdout[:300]}") from exc
    if data.get("Error"):
        raise BackupError(f"Windows 光驱查询失败：{data['Error']}")
    return data.get("Drives", [])


class BackupGUI(tk.Tk):
    def __init__(self) -> None:
        enable_windows_dpi_awareness()
        super().__init__()
        self.title("光盘备份准备工具")
        display_scale = max(1.0, float(self.tk.call("tk", "scaling")) / (96 / 72))
        self.geometry(f"{round(950 * display_scale)}x{round(760 * display_scale)}")
        self.minsize(round(830 * display_scale), round(680 * display_scale))
        tkfont.nametofont("TkDefaultFont").configure(family="Microsoft YaHei UI", size=9)
        tkfont.nametofont("TkTextFont").configure(family="Microsoft YaHei UI", size=9)
        self.discs: dict[str, dict] = {}
        self.events: queue.Queue = queue.Queue()
        self.busy = False
        self.disc_id_buttons: list[ttk.Button] = []
        self._setting_disc_parts = False
        self.using_existing_disc = False

        self.drive_var = tk.StringVar()
        self.disc_id_var = tk.StringVar()
        self.prefix_var = tk.StringVar(value="ARC")
        self.middle_var = tk.StringVar()
        self.suffix_var = tk.StringVar()
        self.media_var = tk.StringVar()
        self.mid_var = tk.StringVar()
        self.omit_about_var = tk.BooleanVar(value=False)
        self.batch_no_var = tk.StringVar(value="01")
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.title_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.batch_path_var = tk.StringVar()
        self.disc_summary = tk.StringVar(value="启动时只识别光驱；点击“读取光盘”才查询盘片。")
        self.batch_preview = tk.StringVar()
        self.status_var = tk.StringVar(value="等待输入；程序只写本地准备目录，不会刻录。")

        self._build_widgets()
        self._sync_about_controls()
        for variable in (self.prefix_var, self.middle_var, self.suffix_var):
            variable.trace_add("write", lambda *_: self._on_disc_part_changed())
        self._on_disc_part_changed()
        self._update_preview()
        for variable in (self.disc_id_var, self.batch_no_var, self.date_var, self.title_var):
            variable.trace_add("write", lambda *_: self._update_preview())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(80, self._poll_events)
        self.startup_drive_after = self.after(250, self.refresh_drives)

    def _build_widgets(self) -> None:
        body = ttk.Frame(self, padding=14)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(4, weight=1)

        ttk.Label(body, text="光盘备份准备工具", font=("Microsoft YaHei UI", 16, "bold")).grid(
            row=0, column=0, sticky="w")
        ttk.Label(body, text="创建空目录 → 整理 DATA → 可选保存 ABOUT → 生成 SHA-256 → 刻录后读回校验",
                  foreground="#52616b").grid(row=1, column=0, sticky="w", pady=(2, 10))

        disc = ttk.LabelFrame(body, text="1  盘片信息与盘号", padding=10)
        disc.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        disc.columnconfigure(1, weight=1)
        ttk.Label(disc, text="光驱").grid(row=0, column=0, sticky="w")
        self.drive_combo = ttk.Combobox(disc, textvariable=self.drive_var, state="readonly")
        self.drive_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.drive_combo.bind("<<ComboboxSelected>>", lambda _event: self._show_selected_disc())
        self.read_button = ttk.Button(disc, text="读取光盘", command=self.refresh_discs)
        self.read_button.grid(row=0, column=2, sticky="e")
        ttk.Label(disc, textvariable=self.disc_summary, wraplength=800,
                  foreground="#315c6d").grid(row=1, column=0, columnspan=3, sticky="w", pady=(7, 8))

        fields = ttk.Frame(disc)
        fields.grid(row=2, column=0, columnspan=3, sticky="ew")
        fields.columnconfigure(1, weight=1)
        fields.columnconfigure(3, weight=1)
        fields.columnconfigure(5, weight=1)
        ttk.Label(fields, text="盘号").grid(row=0, column=0, sticky="w")
        ttk.Entry(fields, textvariable=self.disc_id_var, state="readonly").grid(
            row=0, column=1, columnspan=3, sticky="ew", padx=(8, 16))
        existing_button = ttk.Button(fields, text="沿用已有盘号…", command=self._use_existing_disc)
        existing_button.grid(row=0, column=4, columnspan=2, sticky="e")
        self.disc_id_buttons.append(existing_button)

        ttk.Label(fields, text="前缀").grid(row=1, column=0, sticky="w", pady=(7, 0))
        ttk.Entry(fields, textvariable=self.prefix_var).grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=(7, 0))
        ttk.Label(fields, text="中段（盘型代码）").grid(row=1, column=2, sticky="w", pady=(7, 0))
        ttk.Entry(fields, textvariable=self.middle_var).grid(row=1, column=3, sticky="ew", padx=(8, 16), pady=(7, 0))
        ttk.Label(fields, text="序号").grid(row=1, column=4, sticky="w", pady=(7, 0))
        ttk.Entry(fields, textvariable=self.suffix_var).grid(row=1, column=5, sticky="ew", pady=(7, 0))

        ttk.Label(fields, text="介质").grid(row=2, column=0, sticky="w", pady=(7, 0))
        ttk.Combobox(fields, textvariable=self.media_var,
                     values=("BD-R 25 GB", "BD-R DL 50 GB", "BD-RE 25 GB",
                             "DVD-R 4.7 GB", "DVD+R 4.7 GB", "DVD-RW 4.7 GB", "CD-R 700 MB"))\
            .grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(7, 0))
        ttk.Label(fields, text="制造商 MID（可选）").grid(row=2, column=2, sticky="w", pady=(7, 0))
        ttk.Entry(fields, textvariable=self.mid_var).grid(row=2, column=3, sticky="ew", padx=(8, 16), pady=(7, 0))
        ttk.Label(fields, text="例：ARC + BDR25 + 001 → ARC_BDR25_001。制造商 MID 可从 ImgBurn 查询。",
                  foreground="#66757e").grid(row=3, column=0, columnspan=6, sticky="w", pady=(6, 0))

        batch = ttk.LabelFrame(body, text="2  文件批次", padding=10)
        batch.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        batch.columnconfigure(1, weight=1)
        batch.columnconfigure(3, weight=1)
        batch.columnconfigure(5, weight=2)
        ttk.Label(batch, text="批次").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(batch, from_=1, to=99, width=5, format="%02.0f", textvariable=self.batch_no_var)\
            .grid(row=0, column=1, sticky="w", padx=(8, 16))
        ttk.Label(batch, text="日期").grid(row=0, column=2, sticky="w")
        ttk.Entry(batch, textvariable=self.date_var, width=14).grid(row=0, column=3, sticky="w", padx=(8, 16))
        ttk.Label(batch, text="主题").grid(row=0, column=4, sticky="w")
        ttk.Entry(batch, textvariable=self.title_var).grid(row=0, column=5, sticky="ew", padx=(8, 0))
        ttk.Label(batch, textvariable=self.batch_preview, foreground="#315c6d",
                  wraplength=800).grid(row=1, column=0, columnspan=6, sticky="w", pady=(7, 8))

        ttk.Label(batch, text="准备目录").grid(row=2, column=0, sticky="w")
        ttk.Entry(batch, textvariable=self.output_var).grid(row=2, column=1, columnspan=4,
                                                             sticky="ew", padx=(8, 8))
        ttk.Button(batch, text="选择…", command=self._choose_output).grid(row=2, column=5, sticky="e")
        ttk.Label(batch, text="当前批次").grid(row=3, column=0, sticky="w", pady=(7, 0))
        ttk.Entry(batch, textvariable=self.batch_path_var).grid(row=3, column=1, columnspan=4,
                                                                 sticky="ew", padx=(8, 8), pady=(7, 0))
        ttk.Button(batch, text="选已有批次…", command=self._choose_existing_batch)\
            .grid(row=3, column=5, sticky="e", pady=(7, 0))
        ttk.Label(batch, text="创建后先打开 DATA 放入文件；SHA256SUMS 初始为空，ABOUT 按下方勾选决定是否创建。",
                  foreground="#66757e").grid(row=4, column=0, columnspan=6, sticky="w", pady=(6, 0))

        about_frame = ttk.LabelFrame(body, text="3  ABOUT.txt：来源、内容和版本说明", padding=10)
        about_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        about_frame.columnconfigure(0, weight=1)
        about_frame.rowconfigure(2, weight=1)
        self.omit_about_check = ttk.Checkbutton(
            about_frame, text="本批次不写 ABOUT.txt", variable=self.omit_about_var,
            command=self._on_about_option_changed)
        self.omit_about_check.grid(row=0, column=0, sticky="w")
        self.import_about_button = ttk.Button(about_frame, text="导入 TXT…", command=self._import_about)
        self.import_about_button.grid(row=0, column=1, sticky="e")
        ttk.Label(about_frame, text="需要说明时在这里填写或导入，再点“保存 ABOUT”；勾选不写后只校验 DATA。",
                  foreground="#66757e").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 5))
        self.about_text = scrolledtext.ScrolledText(about_frame, height=6, wrap="word", undo=True,
                                                   font=("Microsoft YaHei UI", 9))
        self.about_text.grid(row=2, column=0, columnspan=2, sticky="nsew")

        actions = ttk.Frame(body)
        actions.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.action_buttons: list[ttk.Button] = []
        for label, action in (
            ("预览 DISC_INFO", self._preview_disc_info),
            ("创建空批次", self._create_batch),
            ("打开 DATA", self._open_data),
            ("保存 ABOUT", self._save_about),
            ("生成／更新 SHA", self._generate_manifest),
            ("校验目录／光盘", self._verify_batch),
        ):
            button = ttk.Button(actions, text=label, command=action)
            button.pack(side="left", padx=(0, 7))
            self.action_buttons.append(button)
            if label == "保存 ABOUT":
                self.save_about_button = button

        self.progress = ttk.Progressbar(body, mode="determinate", maximum=100)
        self.progress.grid(row=6, column=0, sticky="ew")
        ttk.Label(body, textvariable=self.status_var, wraplength=880).grid(row=7, column=0,
                                                                            sticky="w", pady=(6, 0))

    def _update_preview(self) -> None:
        try:
            number = f"{int(self.batch_no_var.get()):02d}"
        except ValueError:
            number = "??"
        disc = self.disc_id_var.get().strip() or "盘号"
        title = self.title_var.get().strip() or "主题"
        self.batch_preview.set(f"将创建：{disc} / B{number}_{self.date_var.get()}_{title} / DATA")

    def _on_about_option_changed(self) -> None:
        self._sync_about_controls()
        if self.omit_about_var.get():
            self.status_var.set("已选择不写 ABOUT.txt；生成 SHA 时只记录 DATA 中的文件。")

    def _sync_about_controls(self) -> None:
        editable = not self.omit_about_var.get() and not self.busy
        self.about_text.configure(state="normal" if editable else "disabled")
        self.import_about_button.configure(state="normal" if editable else "disabled")
        self.save_about_button.configure(state="normal" if editable else "disabled")

    def _on_disc_part_changed(self) -> None:
        if self._setting_disc_parts:
            return
        self.using_existing_disc = False
        self.batch_path_var.set("")
        self.batch_no_var.set("01")
        try:
            disc_id = compose_disc_id(self.prefix_var.get(), self.middle_var.get(), self.suffix_var.get())
        except BackupError:
            disc_id = ""
        self.disc_id_var.set(disc_id)

    def _choose_output(self) -> None:
        chosen = filedialog.askdirectory(title="选择本地准备目录")
        if chosen:
            self.output_var.set(chosen)

    def _use_existing_disc(self) -> None:
        initial = self.output_var.get().strip() or str(Path.home())
        chosen = filedialog.askdirectory(title="选择含 DISC_INFO.txt 的已有盘号目录", initialdir=initial)
        if not chosen:
            return
        try:
            existing = load_existing_disc(Path(chosen))
        except (BackupError, OSError) as exc:
            messagebox.showerror("无法沿用盘号", str(exc))
            return
        self._setting_disc_parts = True
        try:
            parts = existing.disc_id.split("_")
            self.prefix_var.set(parts[0] if len(parts) == 3 else "")
            self.middle_var.set(parts[1] if len(parts) == 3 else "")
            self.suffix_var.set(parts[2] if len(parts) == 3 else "")
        finally:
            self._setting_disc_parts = False
        self.using_existing_disc = True
        self.output_var.set(str(existing.output_root))
        self.disc_id_var.set(existing.disc_id)
        self.media_var.set(existing.media)
        self.mid_var.set(existing.mid)
        self.batch_no_var.set(f"{existing.next_batch_number:02d}")
        self.batch_path_var.set("")
        self.status_var.set(
            f"已读取 {existing.disc_id}；下一批为 B{existing.next_batch_number:02d}。"
            "请核对盘片可续写及 ABOUT 编辑框的内容。")

    def _choose_existing_batch(self) -> None:
        initial = self.batch_path_var.get() or self.output_var.get() or str(Path.home())
        chosen = filedialog.askdirectory(title="选择现有 Bxx 批次目录", initialdir=initial)
        if not chosen:
            return
        if self.about_text.get("1.0", "end-1c").strip():
            if not messagebox.askyesno("切换批次", "当前编辑框内容会被选定批次的 ABOUT.txt 替换。继续吗？"):
                return
        self.batch_path_var.set(chosen)
        self.about_text.configure(state="normal")
        try:
            content = (Path(chosen) / "ABOUT.txt").read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            content = ""
        self.about_text.delete("1.0", "end")
        self.about_text.insert("1.0", content)
        self.omit_about_var.set(not (Path(chosen) / "ABOUT.txt").is_file())
        self._sync_about_controls()
        self.status_var.set(f"当前批次：{chosen}")

    def _import_about(self) -> None:
        chosen = filedialog.askopenfilename(title="导入 ABOUT.txt",
                                            filetypes=(("文本文件", "*.txt"), ("所有文件", "*.*")))
        if not chosen:
            return
        try:
            content = Path(chosen).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("导入失败", f"请确认文件是 UTF-8 文本：{exc}")
            return
        self.about_text.delete("1.0", "end")
        self.about_text.insert("1.0", content)
        self.status_var.set("ABOUT 内容已导入编辑框；还需要点“保存 ABOUT”。")

    def _selected_disc(self) -> dict | None:
        return self.discs.get(self.drive_var.get())

    def _make_plan(self, require_output: bool = True) -> BackupPlan:
        if require_output and not self.output_var.get().strip():
            raise BackupError("请先选择本地准备目录。")
        media = self.media_var.get().strip()
        disc_id = (self.disc_id_var.get() if self.using_existing_disc else
                   compose_disc_id(self.prefix_var.get(), self.middle_var.get(), self.suffix_var.get()))
        return BackupPlan(
            output_root=Path(self.output_var.get()) if self.output_var.get() else Path.home(),
            disc_id=disc_id, media=media, mid=self.mid_var.get().strip(),
            batch_number=int(self.batch_no_var.get()), batch_date=self.date_var.get().strip(),
            title=self.title_var.get().strip(), omit_about=self.omit_about_var.get(),
        )

    def _current_batch(self) -> Path | None:
        path = self.batch_path_var.get().strip()
        if not path:
            messagebox.showinfo("选择批次", "请先创建空批次，或用“选已有批次…”指定目录。")
            return None
        return Path(path)

    def _start(self, label: str, work, on_done) -> None:
        if self.busy:
            return
        self.busy = True
        self.status_var.set(label)
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self.read_button.configure(state="disabled")
        for button in self.action_buttons:
            button.configure(state="disabled")
        for button in self.disc_id_buttons:
            button.configure(state="disabled")
        self.omit_about_check.configure(state="disabled")
        self._sync_about_controls()

        def progress(done: int, total: int, message: str) -> None:
            now = time.monotonic()
            if now - progress.last >= .12 or done >= total:
                progress.last = now
                self.events.put(("progress", done, total, message))
        progress.last = 0.0

        def runner() -> None:
            try:
                result = work(progress)
            except Exception as exc:
                self.events.put(("error", label, str(exc)))
            else:
                self.events.put(("done", label, result, on_done))

        threading.Thread(target=runner, daemon=True).start()

    def _poll_events(self) -> None:
        for _ in range(100):
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "progress":
                _, done, total, message = event
                if str(self.progress.cget("mode")) != "determinate":
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                self.progress["value"] = min(100, done * 100 / max(1, total))
                self.status_var.set(message)
            elif event[0] == "error":
                _, label, detail = event
                self._finish()
                self.status_var.set(f"{label}失败")
                messagebox.showerror(label, detail)
            elif event[0] == "done":
                _, _label, result, callback = event
                self._finish()
                callback(result)
        self.after(80, self._poll_events)

    def _finish(self) -> None:
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.read_button.configure(state="normal")
        for button in self.action_buttons:
            button.configure(state="normal")
        for button in self.disc_id_buttons:
            button.configure(state="normal")
        self.omit_about_check.configure(state="normal")
        self._sync_about_controls()

    def refresh_drives(self) -> None:
        self._start("识别光驱", lambda _p: read_optical_drives(),
                    lambda drives: self._apply_discs(drives, include_media=False))

    def refresh_discs(self) -> None:
        selected = self._selected_disc() or {}
        drive_letter = str(selected.get("DriveLetter") or "")
        self._start("读取光盘信息",
                    lambda _p: read_optical_drives(include_media=True, drive_letter=drive_letter),
                    lambda drives: self._apply_discs(drives, include_media=True))

    def _apply_discs(self, drives: list[dict], include_media: bool) -> None:
        previous = self.drive_var.get()
        self.discs = {}
        for info in drives:
            label = f"{info.get('DriveLetter') or '?'} · {info.get('Vendor', '')} {info.get('Product', '')} {info.get('Revision', '')}".strip()
            self.discs[label] = info
        labels = list(self.discs)
        self.drive_combo["values"] = labels
        self.drive_var.set(previous if previous in self.discs else (labels[0] if labels else ""))
        self._show_selected_disc()
        if not labels:
            self.status_var.set("没有检测到光驱；仍可手动填写介质并准备目录。")
        elif include_media:
            self.status_var.set("已查询选定光驱中的盘片；读取过程没有写盘。")
        else:
            self.status_var.set(f"检测到 {len(labels)} 台光驱；尚未读取光盘。")

    def _show_selected_disc(self) -> None:
        info = self._selected_disc()
        if not info:
            self.disc_summary.set("未检测到光驱；介质类型可手动填写。")
            return
        if not info.get("MediaQueried"):
            self.disc_summary.set("已识别光驱；尚未读取盘片。介质类型可手动填写。")
            return
        media = suggested_media(info)
        code = info.get("MediaTypeCode")
        total = info.get("TotalSectors")
        free = info.get("FreeSectors")
        parts = [f"当前盘片：{media}（IMAPI 类型 {code if code is not None else '未知'}）"]
        if isinstance(total, int) and total >= 0:
            parts.append(f"报告容量 {readable_size(total * 2048)}")
        if isinstance(free, int) and free >= 0:
            parts.append(f"报告剩余 {readable_size(free * 2048)}")
        if info.get("VolumeLabel"):
            parts.append(f"现有卷标 {info['VolumeLabel']}")
        if info.get("FileSystem"):
            parts.append(f"文件系统 {info['FileSystem']}")
        if info.get("Error"):
            parts.append(f"部分信息不可读：{info['Error']}")
        self.disc_summary.set("；".join(parts) + "。刻录前仍需在刻录软件中确认盘片状态。")
        if not self.media_var.get() and code is not None and media != "未知":
            self.media_var.set(media)

    def _preview_disc_info(self) -> None:
        try:
            plan = self._make_plan(require_output=False)
        except (BackupError, ValueError) as exc:
            messagebox.showerror("输入有误", str(exc))
            return
        window = tk.Toplevel(self)
        window.title("DISC_INFO.txt 预览")
        window.geometry("720x300")
        content = scrolledtext.ScrolledText(window, wrap="word", font=("Consolas", 10), padx=10, pady=10)
        content.pack(fill="both", expand=True)
        content.insert("1.0", render_disc_info(plan))
        content.configure(state="disabled")

    def _create_batch(self) -> None:
        try:
            plan = self._make_plan()
            batch = create_batch(plan)
        except (BackupError, OSError, ValueError) as exc:
            messagebox.showerror("创建失败", str(exc))
            return
        self.batch_path_var.set(str(batch))
        if plan.omit_about:
            self.status_var.set(f"已创建不含 ABOUT 的空批次：{batch}。整理 DATA 后生成 SHA。")
            messagebox.showinfo("空批次已创建", f"已创建 DATA/ 和空 SHA256SUMS.txt，未创建 ABOUT.txt：\n{batch}")
        else:
            self.status_var.set(f"已创建空批次：{batch}。先整理 DATA，再保存 ABOUT 和生成 SHA。")
            messagebox.showinfo("空批次已创建", f"已创建空 ABOUT.txt、SHA256SUMS.txt 和 DATA/：\n{batch}")

    def _open_data(self) -> None:
        batch = self._current_batch()
        if batch is None:
            return
        data = batch / "DATA"
        if not data.is_dir():
            messagebox.showerror("目录不存在", f"找不到 DATA：{data}")
            return
        os.startfile(data)

    def _save_about(self) -> None:
        if self.omit_about_var.get():
            messagebox.showerror("未写入 ABOUT", "当前勾选了“不写 ABOUT.txt”；取消勾选后才可保存。")
            return
        batch = self._current_batch()
        if batch is None:
            return
        content = self.about_text.get("1.0", "end-1c")
        manifest = batch / "SHA256SUMS.txt"
        invalidate = False
        if manifest.is_file() and manifest.stat().st_size:
            invalidate = messagebox.askyesno(
                "使旧清单失效", "现有 SHA256SUMS.txt 已有校验值。\n\n修改 ABOUT 会先清空这份本地清单；之后必须重新生成 SHA。继续吗？")
            if not invalidate:
                return
        try:
            save_about(batch, content, invalidate_manifest=invalidate)
        except (BackupError, OSError) as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        self.status_var.set(f"已保存 ABOUT：{batch / 'ABOUT.txt'}。若 DATA 已整理好，请生成 SHA。")
        messagebox.showinfo("ABOUT 已保存", "已写入当前批次的 ABOUT.txt。")

    def _generate_manifest(self) -> None:
        batch = self._current_batch()
        if batch is None:
            return
        manifest = batch / "SHA256SUMS.txt"
        replace = False
        if manifest.is_file() and manifest.stat().st_size:
            replace = messagebox.askyesno(
                "更新本地校验清单", "SHA256SUMS.txt 已有校验值。\n\n只在这批文件尚未刻录、确实要更新时覆盖。继续吗？")
            if not replace:
                return
        omit_about = self.omit_about_var.get()
        self._start("计算 SHA-256",
                    lambda p: generate_manifest(batch, replace=replace, progress=p, omit_about=omit_about),
                    lambda result: self._manifest_done(result, batch, omit_about))

    def _manifest_done(self, manifest: Path, batch: Path, omit_about: bool) -> None:
        self.status_var.set(f"SHA256SUMS.txt 已生成：{manifest}。刻录前可校验当前目录。")
        scope = "DATA 中的每个文件" if omit_about else "ABOUT 和 DATA 中的每个文件"
        messagebox.showinfo("校验清单已生成", f"已计算 {scope}：\n{manifest}\n\n现在可以校验本地目录，再用刻录软件写盘。")

    def _verify_batch(self) -> None:
        initial = self.batch_path_var.get() or self.output_var.get() or str(Path.home())
        chosen = filedialog.askdirectory(title="选择要校验的 Bxx 目录；可以是本地目录或光盘目录",
                                         initialdir=initial)
        if chosen:
            self._start("逐文件读回校验", lambda p: verify_batch(Path(chosen), p), self._show_verification)

    def _show_verification(self, result) -> None:
        if result.passed:
            text = f"PASS：{result.file_count} 个文件，读回 {readable_size(result.total_bytes)}。"
            self.status_var.set(text)
            messagebox.showinfo("校验通过", text)
        else:
            detail = "\n".join(result.problems[:30])
            if len(result.problems) > 30:
                detail += f"\n另有 {len(result.problems) - 30} 条问题。"
            self.status_var.set(f"校验失败：{len(result.problems)} 条问题。")
            messagebox.showerror("校验失败", detail)

    def _on_close(self) -> None:
        if self.busy and not messagebox.askyesno("任务正在运行", "正在读取或校验。仍要退出吗？"):
            return
        self.destroy()


if __name__ == "__main__":
    BackupGUI().mainloop()
