"""Visible text for the Chinese and English desktop interface.

Chinese is the source language of the existing file format and core module.
Only display text is translated; filenames and saved metadata stay stable.
"""

from __future__ import annotations


EN: dict[str, str] = {
    "光盘备份准备工具": "Optical Disc Backup Prep",
    "创建空目录 → 整理 DATA → 可选保存 ABOUT → 生成 SHA-256 → 刻录后读回校验":
        "Create a batch · Add files · Save notes · Hash · Verify after burning",
    "1  盘片信息与盘号": "1  Disc and identifier",
    "光驱": "Optical drive",
    "读取光盘": "Read disc",
    "盘号": "Disc ID",
    "沿用已有盘号…": "Use existing disc ID…",
    "前缀": "Prefix",
    "中段（盘型代码）": "Media code",
    "序号": "Number",
    "介质": "Media",
    "制造商 MID（可选）": "Manufacturer MID (optional)",
    "例：ARC + BDR25 + 001 → ARC_BDR25_001。制造商 MID 可从 ImgBurn 查询。":
        "Example: ARC + BDR25 + 001 → ARC_BDR25_001. Find the manufacturer's MID in ImgBurn.",
    "2  文件批次": "2  Batch",
    "批次": "Batch",
    "日期": "Date",
    "主题": "Title",
    "准备目录": "Staging folder",
    "选择…": "Browse…",
    "当前批次": "Current batch",
    "手动输入完整批次名（B01_YYYY-MM-DD_Title）":
        "Enter full batch name (B01_YYYY-MM-DD_Title)",
    "选已有批次…": "Open existing batch…",
    "创建后先打开 DATA 放入文件；SHA256SUMS 初始为空，ABOUT 按下方勾选决定是否创建。":
        "After creating the batch, put files in DATA/. The checksum file starts empty; ABOUT.txt is optional.",
    "3  ABOUT.txt：来源、内容和版本说明": "3  ABOUT.txt: source and notes",
    "本批次不写 ABOUT.txt": "Omit ABOUT.txt for this batch",
    "导入 TXT…": "Import TXT…",
    "需要说明时在这里填写或导入，再点“保存 ABOUT”；勾选不写后只校验 DATA。":
        "Write or import notes here, then save. If omitted, the manifest covers DATA/ only.",
    "预览 DISC_INFO": "Preview DISC_INFO",
    "创建空批次": "Create batch",
    "打开 DATA": "Open DATA",
    "保存 ABOUT": "Save ABOUT",
    "生成／更新 SHA": "Generate SHA-256",
    "校验目录／光盘": "Verify folder/disc",
    "启动时只识别光驱；点击“读取光盘”才查询盘片。":
        "Drive detection does not read media. Select Read disc to query the inserted disc.",
    "等待输入；程序只写本地准备目录，不会刻录。":
        "Ready. This app prepares local files; it does not burn discs.",
    "将创建：{disc} / B{number}_{date}_{title} / DATA":
        "New batch: {disc} / B{number}_{date}_{title} / DATA",
    "将创建：{disc} / {name} / DATA": "New batch: {disc} / {name} / DATA",
    "已选择不写 ABOUT.txt；生成 SHA 时只记录 DATA 中的文件。":
        "ABOUT.txt omitted. The manifest will cover files in DATA/ only.",
    "选择本地准备目录": "Choose a local staging folder",
    "选择含 DISC_INFO.txt 的已有盘号目录": "Choose a disc-ID folder containing DISC_INFO.txt",
    "无法沿用盘号": "Cannot use disc ID",
    "已读取 {disc_id}；下一批为 B{number:02d}。请核对盘片可续写及 ABOUT 编辑框的内容。":
        "Loaded {disc_id}; the next batch is B{number:02d}. Check that the disc can be appended and review the ABOUT editor.",
    "选择现有 Bxx 批次目录": "Choose an existing Bxx batch folder",
    "切换批次": "Switch batch",
    "当前编辑框内容会被选定批次的 ABOUT.txt 替换。继续吗？":
        "The selected batch's ABOUT.txt will replace the text in the editor. Continue?",
    "当前批次：{path}": "Current batch: {path}",
    "导入 ABOUT.txt": "Import ABOUT.txt",
    "文本文件": "Text files",
    "所有文件": "All files",
    "导入失败": "Import failed",
    "请确认文件是 UTF-8 文本：{detail}": "Make sure the file is UTF-8 text: {detail}",
    "ABOUT 内容已导入编辑框；还需要点“保存 ABOUT”。":
        "Notes imported into the editor. Select Save ABOUT to write them to the batch.",
    "请先选择本地准备目录。": "Choose a local staging folder first.",
    "选择批次": "Select a batch",
    "请先创建空批次，或用“选已有批次…”指定目录。":
        "Create a batch first, or select an existing batch folder.",
    "{label}失败": "{label} failed",
    "识别光驱": "Detect drives",
    "读取光盘信息": "Read disc information",
    "没有检测到光驱；仍可手动填写介质并准备目录。":
        "No optical drive found. You can still enter the media type and prepare files.",
    "已查询选定光驱中的盘片；读取过程没有写盘。":
        "Disc information read. No data was written to the disc.",
    "检测到 {count} 台光驱；尚未读取光盘。":
        "Found {count} optical drive(s). The disc has not been read.",
    "未检测到光驱；介质类型可手动填写。":
        "No optical drive found. Enter the media type manually.",
    "已识别光驱；尚未读取盘片。介质类型可手动填写。":
        "Drive detected; disc not yet read. Enter the media type manually if needed.",
    "当前盘片：{media}（IMAPI 类型 {code}）": "Inserted disc: {media} (IMAPI type {code})",
    "报告容量 {size}": "Reported capacity {size}",
    "报告剩余 {size}": "Reported free space {size}",
    "现有卷标 {label}": "Volume label {label}",
    "文件系统 {name}": "File system {name}",
    "部分信息不可读：{detail}": "Some details could not be read: {detail}",
    "刻录前仍需在刻录软件中确认盘片状态。":
        "Confirm the disc's writable state in your burning software before writing.",
    "输入有误": "Invalid input",
    "DISC_INFO.txt 预览": "DISC_INFO.txt preview",
    "创建失败": "Could not create batch",
    "已创建不含 ABOUT 的空批次：{path}。整理 DATA 后生成 SHA。":
        "Created {path} without ABOUT.txt. Add files to DATA/, then generate the manifest.",
    "已创建 DATA/ 和空 SHA256SUMS.txt，未创建 ABOUT.txt：\n{path}":
        "Created DATA/ and an empty SHA256SUMS.txt. ABOUT.txt was omitted:\n{path}",
    "空批次已创建": "Batch created",
    "已创建空批次：{path}。先整理 DATA，再保存 ABOUT 和生成 SHA。":
        "Created {path}. Add files to DATA/, save ABOUT.txt, then generate the manifest.",
    "已创建空 ABOUT.txt、SHA256SUMS.txt 和 DATA/：\n{path}":
        "Created empty ABOUT.txt and SHA256SUMS.txt, plus DATA/:\n{path}",
    "目录不存在": "Folder not found",
    "找不到 DATA：{path}": "DATA/ was not found: {path}",
    "未写入 ABOUT": "ABOUT.txt not saved",
    "当前勾选了“不写 ABOUT.txt”；取消勾选后才可保存。":
        "ABOUT.txt is set to be omitted. Clear that option before saving it.",
    "使旧清单失效": "Clear old manifest",
    "现有 SHA256SUMS.txt 已有校验值。\n\n修改 ABOUT 会先清空这份本地清单；之后必须重新生成 SHA。继续吗？":
        "SHA256SUMS.txt already contains hashes. Saving ABOUT.txt will clear the local manifest; you must regenerate it. Continue?",
    "保存失败": "Save failed",
    "已保存 ABOUT：{path}。若 DATA 已整理好，请生成 SHA。":
        "Saved ABOUT.txt to {path}. Generate the manifest when DATA/ is ready.",
    "ABOUT 已保存": "ABOUT.txt saved",
    "已写入当前批次的 ABOUT.txt。": "ABOUT.txt was saved in the current batch.",
    "更新本地校验清单": "Replace local manifest",
    "SHA256SUMS.txt 已有校验值。\n\n只在这批文件尚未刻录、确实要更新时覆盖。继续吗？":
        "SHA256SUMS.txt already contains hashes. Replace it only if this batch has not been burned and you intend to update it. Continue?",
    "计算 SHA-256": "Calculate SHA-256",
    "SHA256SUMS.txt 已生成：{path}。刻录前可校验当前目录。":
        "Generated {path}. You can verify the staging folder before burning.",
    "DATA 中的每个文件": "every file in DATA/",
    "ABOUT 和 DATA 中的每个文件": "ABOUT.txt and every file in DATA/",
    "校验清单已生成": "Manifest generated",
    "已计算 {scope}：\n{path}\n\n现在可以校验本地目录，再用刻录软件写盘。":
        "Hashed {scope}:\n{path}\n\nVerify the staging folder, then burn it with separate software.",
    "选择要校验的 Bxx 目录；可以是本地目录或光盘目录":
        "Choose a Bxx batch folder on your computer or disc",
    "逐文件读回校验": "Read and verify files",
    "PASS：{count} 个文件，读回 {size}。": "PASS: {count} file(s), {size} read.",
    "校验通过": "Verification passed",
    "另有 {count} 条问题。": "{count} more issue(s).",
    "校验失败：{count} 条问题。": "Verification failed: {count} issue(s).",
    "校验失败": "Verification failed",
    "任务正在运行": "Task in progress",
    "正在读取或校验。仍要退出吗？": "A read or verification task is running. Exit anyway?",
    "未知": "Unknown",
    "通用光盘": "Generic optical disc",
    "保留类型": "Reserved type",
    "{size:,} 字节": "{size:,} bytes",
}

# Core messages stay in Chinese for compatibility with callers. The GUI
# translates them at its boundary, including path-specific diagnostics.
CORE_EXACT: dict[str, str] = {
    "批次目录名须为 B01_YYYY-MM-DD_Title，例如 B03_2026-10-06_Photos。":
        "Enter a batch folder name such as B03_2026-10-06_Photos (B01_YYYY-MM-DD_Title).",
    "盘号须由 1–32 个字母、数字、下划线或连字符组成，首字须为字母或数字。":
        "The disc ID must be 1–32 letters, digits, underscores or hyphens, starting with a letter or digit.",
    "请填写介质类型，例如 BD-R 25 GB。": "Enter a media type, such as BD-R 25 GB.",
    "MID 不能包含换行符。": "MID cannot contain a line break.",
    "批次编号须在 01–99 之间。": "Batch number must be between 01 and 99.",
    "批次日期须为有效的 YYYY-MM-DD。": "Enter a valid date in YYYY-MM-DD format.",
    "请填写 1–48 字的主题，末尾不能是空格或句点。":
        "Enter a title of 1–48 characters that does not end with a space or period.",
    "主题包含 Windows 文件名不允许的字符。": "The title contains characters Windows does not allow in filenames.",
    "准备目录不能位于光盘上。请选硬盘目录。": "Choose a staging folder on a hard drive, not on an optical disc.",
    "请选择存在的本地准备目录。": "Choose an existing local staging folder.",
    "准备目录不能是指向其他位置的链接或云盘占位目录。":
        "The staging folder cannot be a link or cloud-only placeholder.",
    "盘号前缀只能包含英文字母和数字，例如 ARC。": "The disc-ID prefix must use letters and digits only, such as ARC.",
    "盘号中段只能包含英文字母和数字，例如 BDR25。": "The media code must use letters and digits only, such as BDR25.",
    "盘号序号须为 1–8 位数字，例如 001。": "The number must have 1–8 digits, such as 001.",
    "组合后的盘号超过 32 个字符，请缩短前缀或中段。": "The disc ID exceeds 32 characters. Shorten the prefix or media code.",
    "请选择硬盘上已有的盘号目录。": "Choose an existing disc-ID folder on a hard drive.",
    "所选目录没有普通的 DISC_INFO.txt。": "The folder has no regular DISC_INFO.txt file.",
    "DISC_INFO.txt 中的盘号或介质与目录不符。": "The disc ID or media in DISC_INFO.txt does not match the folder.",
    "该盘已有 B99，不能再增加批次。": "This disc already has B99; no more batches can be added.",
    "已有盘号目录是链接或指向光驱，不能继续写入。":
        "The existing disc-ID folder is a link or points to an optical drive.",
    "已有 DISC_INFO.txt 的盘号与当前输入不符。": "The disc ID differs from the existing DISC_INFO.txt.",
    "已有 DISC_INFO.txt 的介质类型与当前输入不符。": "The media type differs from the existing DISC_INFO.txt.",
    "已有 DISC_INFO.txt 的 MID 与当前输入不符。": "The MID differs from the existing DISC_INFO.txt.",
    "程序不会修改光盘。请选择硬盘上的备份准备目录。":
        "This app cannot change a disc. Choose the staging folder on a hard drive.",
    "批次目录是链接或云盘占位目录，不能写入。": "The batch folder is a link or cloud-only placeholder.",
    "批次目录指向光驱，程序不会写入光盘。": "The batch folder points to an optical drive; the app will not write to it.",
    "批次目录须包含 DATA/ 和 SHA256SUMS.txt。": "The batch folder must contain DATA/ and SHA256SUMS.txt.",
    "ABOUT.txt 必须是普通文件，或不创建。": "ABOUT.txt must be a regular file or be absent.",
    "批次目录包含链接或云盘占位文件，请使用真实的本地文件。":
        "The batch contains a link or cloud-only placeholder. Use local files.",
    "请先填写 ABOUT 内容。": "Enter text for ABOUT.txt first.",
    "SHA256SUMS.txt 已有内容。先确认使旧清单失效，再更新 ABOUT。":
        "SHA256SUMS.txt is not empty. Confirm that the old manifest should be cleared before updating ABOUT.txt.",
    "DATA 文件夹不存在，或是链接／云盘占位目录。":
        "DATA/ is missing, is a link, or is a cloud-only placeholder.",
    "DATA 还是空的。请先把文件放进去。": "DATA/ is empty. Add files first.",
    "ABOUT.txt 已有内容；不能在“不写 ABOUT”模式下略过它。":
        "ABOUT.txt contains text and cannot be omitted. Clear the omit option or remove the notes yourself.",
    "ABOUT.txt 缺失或为空。请填写内容，或勾选“不写 ABOUT.txt”。":
        "ABOUT.txt is missing or empty. Add notes or select Omit ABOUT.txt.",
    "SHA256SUMS.txt 已有内容。需要更新时请明确确认覆盖本地清单。":
        "SHA256SUMS.txt already contains hashes. Confirm replacement before updating it.",
    "所选目录须包含 SHA256SUMS.txt 和 DATA 文件夹。":
        "The selected folder must contain SHA256SUMS.txt and DATA/.",
    "批次目录中存在链接，无法安全校验。": "The batch folder contains a link and cannot be verified safely.",
    "SHA256SUMS.txt 为空，尚未生成校验清单。": "SHA256SUMS.txt is empty. Generate the manifest first.",
    "ABOUT.txt 仍为空": "ABOUT.txt is still empty",
    "ABOUT.txt 不是普通文件": "ABOUT.txt is not a regular file",
    "校验完成": "Verification complete",
    "SHA256SUMS.txt 已更新": "SHA256SUMS.txt updated",
}

CORE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("无法读取已有盘号目录：", "Could not read the disc-ID folder: "),
    ("已有盘号目录却没有普通的 DISC_INFO.txt：", "The disc-ID folder has no regular DISC_INFO.txt: "),
    ("该批次目录已存在，不会覆盖：", "The batch folder already exists and will not be overwritten: "),
    ("无法读取 SHA256SUMS.txt：", "Could not read SHA256SUMS.txt: "),
    ("无法读取 ", "Could not read "),
    ("DATA 中有链接或云盘占位文件：", "DATA/ contains a link or cloud-only placeholder: "),
    ("DATA 中有大小写冲突的路径：", "DATA/ contains paths that differ only by case: "),
    ("DATA 中有非普通文件：", "DATA/ contains a non-regular file: "),
    ("SHA256SUMS.txt 有重复路径：", "SHA256SUMS.txt contains a duplicate path: "),
    ("清单所列文件缺失：", "Missing file listed in manifest: "),
    ("目录中有清单未列的文件：", "File not listed in manifest: "),
    ("批次根目录有未纳入清单的项目：", "Unexpected item in batch root: "),
    ("哈希不符：", "Hash mismatch: "),
    ("读取失败：", "Read failed: "),
    ("计算：", "Hashing: "),
    ("校验：", "Verifying: "),
    ("计算 ABOUT.txt", "Hashing ABOUT.txt"),
    ("Windows 光驱查询失败：", "Windows drive query failed: "),
    ("无法解析 Windows 光驱信息：", "Could not parse Windows drive information: "),
)


def tr(source: str, language: str = "zh", **values: object) -> str:
    template = EN.get(source, source) if language == "en" else source
    return template.format(**values) if values else template


def localize_core(message: str, language: str = "zh") -> str:
    if language != "en":
        return message
    if message in CORE_EXACT:
        return CORE_EXACT[message]
    if message.startswith("SHA256SUMS.txt 第 ") and " 行格式或路径无效。" in message:
        number = message.removeprefix("SHA256SUMS.txt 第 ").split(" 行", 1)[0]
        return f"SHA256SUMS.txt line {number} has an invalid format or path."
    for prefix, replacement in CORE_PREFIXES:
        if message.startswith(prefix):
            return replacement + message[len(prefix):]
    return message
