# SVG Layer Exporter — Setup & Usage Guide

## What This Does

Takes a multi-page Inkscape SVG (like your Kallax inserts file) and exports
every layer from every page as its own individual SVG file, cropped tightly
to the content. Ready to import one at a time into Easel or any other CNC
software.

**Given:** `IKEA KALLAX INSERTS - 6MM.svg`

**Produces:**
```
IKEA_KALLAX_INSERTS_-_6MM/
├── PAGE_27/
│   ├── PAGE_27_path1-3.svg
│   ├── PAGE_27_path2-14.svg
│   └── ...
├── PAGE_26/
│   ├── PAGE_26_path1-07.svg
│   └── ...
└── ...
```

---

## One-Time Setup

### 1. Make sure Python is installed
Open PowerShell and run:
```powershell
python --version
```
You need Python 3.7 or higher.

### 2. Install the one dependency
```powershell
pip install lxml
```
`lxml` is the XML parsing library. Everything else is Python standard library.

If pip complains, try:
```powershell
python -m pip install lxml
```

### 3. Save the script somewhere permanent
Suggested location: `C:\Scripts\svg_layer_exporter.py`

---

## Running It

### Option A — Drag and drop (easiest)
1. Open PowerShell
2. Type: `python C:\Scripts\svg_layer_exporter.py ` (with a space at the end)
3. Drag your SVG file from Explorer onto the PowerShell window
4. The path gets pasted automatically
5. Hit Enter

### Option B — Prompted input
1. Open PowerShell
2. Run: `python C:\Scripts\svg_layer_exporter.py`
3. When prompted, paste or type the full path to your SVG
4. Hit Enter

### Option C — Direct path argument
```powershell
python C:\Scripts\svg_layer_exporter.py "C:\Projects\IKEA KALLAX INSERTS - 6MM.svg"
```

---

## What Happens

The script will print its progress as it runs, creating an output folder
next to your SVG file, named after it, with one subfolder per page and
one SVG per layer inside.

---

## Name Sanitization Rules

Spaces → hyphens. Special characters → hyphens. Multiple hyphens → one hyphen.

---

## Troubleshooting

### "No module named lxml"
Run: `pip install lxml` then try again.

### "No layers found in this SVG"
The SVG might not have the standard Inkscape layer structure.
Open in Inkscape and check that your layers show up in the
Layers and Objects panel with the layer icon (not just groups).

### Files export but look empty
The script uses a coordinate-based bbox approach. Open the exported
SVG in Inkscape to verify it looks correct first.

### Some layers say "SKIP (no content)"
Could be a text layer, an empty layer, or a layer with only embedded
images. The script skips these rather than exporting blank files.

---

## Pro Tips

- **Run it on a copy first** if you're nervous — the script never modifies
  your original SVG, it only reads it.
- **Safe to re-run** — overwrites existing exports cleanly.
