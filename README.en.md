# Optical disc backup prep

This Windows desktop app prepares files for an optical-disc backup and checks them after burning. It creates a disc folder, an optional `ABOUT.txt`, and a SHA-256 manifest. You arrange the files under `DATA/` and burn the prepared content with separate software. The app never writes to an optical drive or changes your source files.

The interface and [full instructions](README.md) are in Chinese.

## Run

Install Python 3.11 or later with Tkinter on Windows. Windows PowerShell 5.1 is also required for drive detection. No third-party Python packages or administrator rights are needed.

Double-click `run_gui.cmd`, or run:

```powershell
python backup_gui.py
```

At startup the app identifies available drives without reading a disc. Disc information is queried only when you click **读取光盘** (Read disc). You can prepare and hash files without a connected drive; enter the intended media type manually.

## Workflow

1. Choose a staging directory on a hard drive. Enter a disc ID in three parts, such as `ARC`, `BDR25`, and `001`, which produces `ARC_BDR25_001`. Enter the intended media type. The manufacturer's MID is optional and must be checked separately.
2. Enter a batch number, date, and title. Select **本批次不写 ABOUT.txt** if this batch should have no description file. Create the batch.
3. Copy your files into `DATA/`. Save `ABOUT.txt` if you chose to include it, then generate `SHA256SUMS.txt`.
4. Verify the staging batch. Burn the contents of the disc-ID folder so that `DISC_INFO.txt` and the `B01_...` directory are at the disc root.
5. Eject and reinsert the disc. Select its `B01_...` directory in the app and verify again.

The manifest covers every regular file under `DATA/` recursively and `ABOUT.txt` when present. Empty folders, `DISC_INFO.txt`, and the manifest itself are outside its scope. Verification compares file hashes and detects missing or unexpected files. It does not measure the disc's physical error rates. See [the format reference](docs/FORMAT.md) for details.

Run the tests with `python -m unittest discover -s tests -v`. Licensed under [MIT](LICENSE).
