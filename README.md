# 光盘备份准备工具

这是一个 Windows 桌面程序，用来整理刻录前的文件、生成 SHA-256 清单，并在刻录后读回校验。程序不刻录光盘；`DATA/` 中的文件由你自己安排，它不会移动或修改源文件。

界面为中文。[English overview](README.en.md)

## 运行

需要 Windows、Python 3.11 或更新版本（安装时包含 Tkinter），以及系统自带的 Windows PowerShell 5.1。双击 `run_gui.cmd`，或在项目目录运行：

```powershell
python backup_gui.py
```

不需要安装第三方 Python 包，也不需要管理员权限。启动时程序只识别光驱，不读盘；没有光驱也能准备目录和校验硬盘上的文件。点击“读取光盘”后，程序才会查询所选光驱中的盘片。

## 准备一张新盘

1. 选择硬盘上的准备目录，例如 `D:\Archive-Staging`。填写计划使用的介质，如 `BD-R 25 GB`。如果盘片已放入光驱，可点“读取光盘”核对类型；制造商 MID 仍需从 ImgBurn 等工具手动抄入，也可以留空。
2. 填写盘号的三段：前缀 `ARC`、中段 `BDR25`、序号 `001` 会组成 `ARC_BDR25_001`。中段是自定代码，不是盘片的制造商 MID。序号由你管理，程序不会自动占号或检查其他准备目录。
3. 填写批次号、日期和主题。需要说明文件时保持“本批次不写 ABOUT.txt”未勾选；不需要时勾选。点击“创建空批次”。
4. 点击“打开 DATA”，自行建立子目录并把待备份文件复制进去。如果要写说明，可在界面中填写或导入 UTF-8 文本，再点“保存 ABOUT”。
5. 点击“生成／更新 SHA”，然后用“校验目录／光盘”选择本地的 `B01_...` 目录，先检查准备好的文件。
6. 用刻录软件写盘。光盘根目录应包含 `DISC_INFO.txt` 和 `B01_...`，不要多刻一层 `ARC_BDR25_001`。刻录软件的卷标可以设为盘号。刻录完成后弹出、重插光盘，再用本工具选择光盘上的 `B01_...` 目录读回校验。

未勾选“不写 ABOUT.txt”时，目录如下：

```text
D:\Archive-Staging\ARC_BDR25_001\
├── DISC_INFO.txt
└── B01_2026-10-06_Photos\
    ├── ABOUT.txt
    ├── SHA256SUMS.txt
    └── DATA\
        └── ...自行整理的文件和子目录
```

勾选“不写 ABOUT.txt”后，新批次不会创建该文件。如果已经创建了空的 `ABOUT.txt`，生成清单时勾选此项会移除它；已有内容的 `ABOUT.txt` 不会被自动删除。`SHA256SUMS.txt` 在生成前是空文件，空文件不表示校验通过。

要为同一张盘准备 B02，点击“沿用已有盘号…”，选择包含 `DISC_INFO.txt` 的盘号目录。程序会带回盘号、介质、MID，并填写下一批次号。能否真正把 B02 刻到同一张盘，取决于第一次刻录时选用的文件系统、会话设置和盘片是否仍可续写。详见[数据光盘刻录指南](https://nanocm.github.io/optical-disc-writing-guide/)。

## SHA-256 与读回校验

程序递归遍历 `DATA/`，为每个普通文件计算 SHA-256；有 `ABOUT.txt` 时也计算它。清单每行是 64 位十六进制摘要、两个空格和相对于批次目录的路径：

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  DATA/hello.txt
```

“校验目录／光盘”是只读操作。它会重新读取清单中的文件，检查哈希、缺失文件及多出的文件。可以对硬盘准备目录使用，也可以在刻录后对光盘上的批次目录使用。它不测量盘片的 LDC/BIS、PI 等物理质量。

清单不计算自身，也不包含盘根目录的 `DISC_INFO.txt`。目录本身没有文件哈希，空目录不会写入清单。程序拒绝读取 `DATA/` 中的链接和云盘占位文件。`DISC_INFO.txt` 中的介质与 MID 是准备时记录的信息；尤其是 MID，程序无法自动验证你手填的值。

文件格式与校验范围见 [docs/FORMAT.md](docs/FORMAT.md)。

## 开发

```powershell
python -m unittest discover -s tests -v
```

`backup_core.py` 负责创建目录和校验，`backup_gui.py` 是 Tkinter 界面，`read_disc.ps1` 通过 Windows IMAPI2 只读查询光驱。运行测试不会刻录光盘。

本项目采用 [MIT 许可证](LICENSE)。
