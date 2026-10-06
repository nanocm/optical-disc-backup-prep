# 构建 Windows EXE / Build the Windows EXE

在 Windows x64 的 PowerShell 中，从仓库根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_release.ps1
```

构建脚本生成图标，用 PyInstaller 打包 GUI、`read_disc.ps1` 和图标，最后把 EXE 及其 SHA-256 清单放进 `release/`。运行 EXE 不需要 Python。`build/`、`dist/` 和 `release/` 是本地构建产物，不提交到 Git。

On Windows x64, run the commands above from the repository root in PowerShell. The script generates the icon, bundles the GUI and `read_disc.ps1` with PyInstaller, and writes the EXE plus a SHA-256 checksum to `release/`. The resulting EXE runs without a Python installation. Build outputs remain local and are excluded from Git.

提交或发布前先运行测试 / Run the tests before committing or publishing:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
