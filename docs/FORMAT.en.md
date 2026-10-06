# Folder and checksum format

Each disc-ID folder holds the content intended for one disc. You can assemble a batch name from its number, date, and title or enter the full name directly. Both use `B01_YYYY-MM-DD_Title`, with numbers from 01 to 99. Preparing B02 in the same folder does not guarantee that the physical disc can be appended; the burning method and disc state determine that.

```text
ARC_BDR25_001/
├── DISC_INFO.txt
├── B01_2026-10-06_Photos/
│   ├── ABOUT.txt             # optional
│   ├── SHA256SUMS.txt
│   └── DATA/
└── B02_2026-10-20_Documents/
    ├── SHA256SUMS.txt
    └── DATA/
```

`DISC_INFO.txt` is UTF-8 text. It records the disc ID, intended media type, creation date, folder convention, checksum algorithm, and suggested volume label. The `MID:` line is included only when entered manually. The app does not rewrite this file when adding a batch to an existing disc-ID folder. The optical drive and Windows-reported capacity are shown only in the app, not saved here.

Each batch has its own UTF-8 `SHA256SUMS.txt`. Every line has a lowercase 64-character SHA-256 digest, **two spaces**, and a path relative to the batch folder. Paths use `/` separators:

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  DATA/hello.txt
```

The app hashes every regular file under `DATA/` recursively. If `ABOUT.txt` exists, it is included too. An omitted ABOUT must be selected explicitly in the interface. Empty folders, `SHA256SUMS.txt`, and `DISC_INFO.txt` at the disc root are outside the manifest.

Verification checks the manifest's format, hashes listed files again, and reports missing or unexpected files. It rejects symbolic links, Windows reparse points, and cloud-only placeholders under `DATA/`. A passing result means the selected batch matches its manifest. Keep separate copies of `DISC_INFO.txt` and the manifest in a hard-drive index if you want an independent record of the disc ID, media, and MID. The app does not measure physical disc error rates.

If `DISC_INFO.txt` on a burned disc contains an error, correct your local record and note the value on the disc. Adding a session to a write-once disc solely to change one metadata line can make earlier files invisible in Windows if the old directory tree is not imported correctly.
