# Optical Disc Backup Prep

[中文](README.md) · [Download for Windows](https://github.com/nanocm/optical-disc-backup-prep/releases/latest)

This desktop app creates a disc ID and batch folder before burning, writes a SHA-256 manifest, and reads files back for verification after burning. It does not burn discs or move your source files. Use the **语言/language** selector in the upper-right corner to switch between Chinese and English.

## Download and run

Download `OpticalDiscBackupPrep-…-windows-x64.exe` from [Releases](https://github.com/nanocm/optical-disc-backup-prep/releases/latest) and run it directly. Python is bundled. A `SHA256SUMS.txt` file is available alongside the EXE so you can check the download's SHA-256.

To run from source, use Windows with Python 3.11 or later (including Tkinter) and Windows PowerShell 5.1. Double-click `run_gui.cmd`, or run this command in the project folder:

```powershell
python backup_gui.py
```

At startup the app lists drives without reading media. You can prepare folders and verify files without a drive. Disc details are queried only when you select **Read disc**.

## Prepare a disc

1. Choose an existing staging folder on a hard drive. Enter the intended media type and the three parts of a disc ID. For example, `ARC`, `BDR25`, and `001` become `ARC_BDR25_001`. The middle part is your media code, not the manufacturer's MID.
2. If you want to record the MID, check it in ImgBurn or another disc tool and enter it manually. Leave it blank if uncertain; this app cannot verify the MID automatically.
3. Enter a batch number, date, and title. You can also select **Enter full batch name** and type a name such as `B03_2026-10-06_Photos` directly. The format is `B01_YYYY-MM-DD_Title`, with a batch number from 01 to 99. Leave **Omit ABOUT.txt for this batch** unchecked if you need notes. Select **Create batch**.
4. Select **Open DATA** and copy your files into `DATA/`, arranging subfolders as you like. Write or import UTF-8 notes and select **Save ABOUT** if this batch includes `ABOUT.txt`.
5. Select **Generate SHA-256** after the files are in place. Then select **Verify folder/disc** and choose the `B01_…` folder on your hard drive.
6. Burn the **contents** of the disc-ID folder with separate software, placing `DISC_INFO.txt` and `B01_…` at the disc root. Set a volume label if wanted, and check capacity and burning settings. Eject and reinsert the disc, then verify its `B01_…` folder in the app.

The bottom panel recommends a file system for the selected media. Select **Choose by use…** for the full guide. After generating SHA-256, the app also checks the current batch's `DATA/` for individual files of 2 GiB or more. This is a conservative alert, not a universal ISO 9660 hard limit. The app only advises; it does not set the burning software's file system.

| Use | Recommendation | Check |
| --- | --- | --- |
| Standard data CD | ISO 9660 + Joliet | Test filenames and file reading on older devices. |
| DVD / BD file backup | UDF; data BDs commonly use UDF 2.50, while DVDs should use a UDF revision supported by the target system | Do not use only ISO 9660 / Joliet for large files. Inspect the image first; reinsert and verify after burning. |
| Older computer, car stereo, or player | Follow the device manual; for small files, try ISO 9660 + Joliet or an ISO / UDF bridge disc | Test a disc in the target device. It must support the media, file system, and file format. |
| Directly add, delete, or revise files | DVD-RW, DVD+RW, or BD-RE with Windows Live UDF | Try a small file to confirm it writes immediately. New versions on write-once discs do not reclaim old sectors. |
| Existing ISO or system boot image | Use the burning software's Write image mode | The image already defines its file system and boot layout; adding it as an ordinary data file will not make a boot disc. |
| DVD-Video / BD-Video | Use authoring software; DVD-Video normally uses UDF 1.02 + ISO 9660, BD-Video UDF 2.50 | The directory and video formats must also meet the relevant specification. |
| Append another session later | Keep the disc appendable and import the old session in burning software | A file system alone does not guarantee appending. Reinsert and check both old and new files. |

For an ISO 9660 + Joliet + UDF hybrid image, mount it in Windows and check that the drive's properties show UDF. If they show CDFS, that read does not verify the UDF view. Copy and hash-check a large file, then eject, reinsert, and verify the burned disc as well.

With ABOUT enabled, the staging folder looks like this:

```text
D:\Archive-Staging\ARC_BDR25_001\
├── DISC_INFO.txt
└── B01_2026-10-06_Photos\
    ├── ABOUT.txt
    ├── SHA256SUMS.txt
    └── DATA\
        └── …your files and folders
```

`SHA256SUMS.txt` starts empty. Generate it after adding files. If you omit ABOUT, the file is absent. Selecting the omit option when generating the manifest removes an empty ABOUT file, but never removes one containing notes.

To prepare another batch for the same disc, choose **Use existing disc ID…** and select the folder containing `DISC_INFO.txt`. The app restores the disc ID, media type, and MID, then fills in the next batch number. Whether you can actually burn B02 onto the disc depends on its media and session state. See the [optical-disc writing guide](https://nanocm.github.io/optical-disc-writing-guide/) for burning details (Chinese).

## Manifest and verification

The app hashes every regular file under `DATA/` recursively, plus `ABOUT.txt` when present. Each UTF-8 manifest line contains a lowercase SHA-256 digest, two spaces, and a path relative to the batch folder:

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  DATA/hello.txt
```

Verification reads the listed files again and reports changed, missing, or unexpected files. It does not measure the disc's physical error rates or record empty folders. The manifest excludes itself and `DISC_INFO.txt` at the disc root. Keep separate copies of both files in a hard-drive index if you want to preserve the disc ID and media record for later checking. Links and cloud-only placeholders under `DATA/` are rejected.

See the [format reference](docs/FORMAT.en.md) for details.

## Development and packaging

The app has no third-party runtime dependencies. `backup_core.py` handles folders and checksums; `backup_gui.py` provides the Tkinter interface; `read_disc.ps1` queries optical drives through Windows IMAPI2.

```powershell
python -m unittest discover -s tests -v
```

See the [build instructions](docs/BUILD.md) to make a Windows EXE. Licensed under [MIT](LICENSE).
