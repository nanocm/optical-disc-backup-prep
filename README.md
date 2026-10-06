# 光盘备份准备工具

[English](README.en.md) · [下载 Windows 版](https://github.com/nanocm/optical-disc-backup-prep/releases/latest)

在刻录前建立盘号和批次目录，给文件生成 SHA-256 清单；刻录后，从光盘读回文件并校验。程序不会执行刻录，也不会替你移动源文件。界面右上角的 **语言/language** 可以在中文和英文之间切换。

## 下载与运行

从 [Releases](https://github.com/nanocm/optical-disc-backup-prep/releases/latest) 下载 `OpticalDiscBackupPrep-…-windows-x64.exe`，直接运行。这个版本自带 Python 和所需的文件，不必安装 Python。下载页同时提供 `SHA256SUMS.txt`，可核对 EXE 的 SHA-256。

运行源码需要 Windows、Python 3.11 或更新版本（含 Tkinter），以及 Windows PowerShell 5.1。下载仓库后双击 `run_gui.cmd`，或在项目目录运行：

```powershell
python backup_gui.py
```

启动时只列出光驱，不读取盘片。没有光驱也能准备目录和校验硬盘文件。只有点击“读取光盘”时，程序才查询选定光驱中的介质。

## 准备一张盘

1. 在硬盘上选一个已有的准备目录。填写介质类型，并输入盘号的前缀、中段和序号。例如 `ARC`、`BDR25`、`001` 组成 `ARC_BDR25_001`。中段是自定的盘型代码，不是制造商 MID。
2. 如需记录 MID，从 ImgBurn 等工具核对后手动填写；不确定就留空。程序读取的盘片信息不能自动验证 MID。
3. 填写批次号、日期和主题；也可以勾选“手动输入完整批次名”，直接填写 `B03_2026-10-06_Photos`。手动模式要求 `B01_YYYY-MM-DD_Title` 格式，批次号为 01–99。需要 `ABOUT.txt` 时保持“不写 ABOUT.txt”未勾选；不需要时勾选。点击“创建空批次”。
4. 点击“打开 DATA”，自行建立子目录并复制文件。需要说明时，可在界面中编写或导入 UTF-8 文本，然后点击“保存 ABOUT”。
5. 文件整理完毕后点击“生成／更新 SHA”。再点“校验目录／光盘”，选择硬盘上的 `B01_…` 目录做一次校验。
6. 用刻录软件写盘。把盘号目录**里面**的内容放到光盘根目录，设置卷标（可用盘号），检查容量和刻录设置。完成后弹出、重插光盘，选择光盘上的 `B01_…` 目录再校验一次。

未勾选“不写 ABOUT.txt”时，准备目录如下。`SHA256SUMS.txt` 刚创建时是空的；必须在放入数据后生成清单。

```text
D:\Archive-Staging\ARC_BDR25_001\
├── DISC_INFO.txt
└── B01_2026-10-06_Photos\
    ├── ABOUT.txt
    ├── SHA256SUMS.txt
    └── DATA\
        └── …自行整理的文件和子目录
```

不写 ABOUT 时，批次目录中没有 `ABOUT.txt`。如果先创建了空文件，生成清单时勾选“不写 ABOUT.txt”会移除这个空文件；已有内容的 ABOUT 不会被自动删除。

为同一盘准备下一批时，点击“沿用已有盘号…”，选择含 `DISC_INFO.txt` 的盘号目录。程序会带回盘号、介质和 MID，并填写下一批次号。**准备出 B02 不表示光盘一定可续写。**续写能力取决于介质、第一次刻录的会话设置和盘片状态。操作细节见[数据光盘刻录指南](https://nanocm.github.io/optical-disc-writing-guide/)。

## 清单记录了什么

程序递归计算 `DATA/` 内每个普通文件的 SHA-256；有 `ABOUT.txt` 时，也计算它。清单每行由小写十六进制摘要、两个空格和相对于批次目录的路径组成：

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  DATA/hello.txt
```

“校验目录／光盘”会重新读取文件，报告哈希不符、缺失文件和多出的文件。它不测量 LDC/BIS、PI 等盘片物理错误率，也不检查空目录。`SHA256SUMS.txt` 不记录自身或盘根目录的 `DISC_INFO.txt`；建议把这两个文件另存一份到硬盘索引，以便日后核对盘号和介质记录。程序拒绝 `DATA/` 中的链接和云盘占位文件。

格式细节见[目录与校验格式](docs/FORMAT.md)。

## 开发与打包

程序只使用 Python 标准库。`backup_core.py` 处理目录与校验，`backup_gui.py` 是 Tkinter 界面，`read_disc.ps1` 通过 Windows IMAPI2 查询光驱。运行测试：

```powershell
python -m unittest discover -s tests -v
```

EXE 的构建步骤见[构建说明](docs/BUILD.md)。项目采用 [MIT 许可证](LICENSE)。
