# GameFrame V5 — verified screenshot delivery

V5 adds actual **fresh JPEG presence verification** to the V4 three-shot native capture runner. The V4 client binary and native V2 cgame DLL that the user already compiled work unchanged: **no native rebuild necessary**.

## Exact code structure

- `gameframe/ioquake3_capture_verify.py`: `snapshot_screenshot_dir` snapshots JPEG name/mtime/size; `find_new_files` compares the folder; `match_capture_files` maps only exact requested capture stems or numeric-suffixed variants; `wait_for_capture` polls for bounded time; `stage_verified_capture` copies to safe deterministic output without overwriting.
- `gameframe/ioquake3_v4_production.py`: captures screenshot snapshot before each shot, runs V3 camera take, queues screenshot, waits for a matching file, stages image, annotates shot and overall verification.
- `gameframe/ioquake3_v4_production_cli.py`: V5 opt-in flags `--screenshot-dir`, `--output-dir`, `--capture-timeout`; saves manifest with per-shot actual file paths.
- `tests/test_ioquake3_capture_verify.py`: test fresh/stale matching, missing captures, organized copy and overwrite refusal.
- `docs/examples/quake_v4_film.json`: unchanged three-shot 24-second cinematic film.

## Windows validation

Leave your V4-patched ioquake3 running with the same known V2 native DLL, `sv_pure 0`, `vm_cgame 0`, and q3dm1 loaded. Then open a second PowerShell:

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
python -m gameframe.ioquake3_v4_production_cli docs/examples/quake_v4_film.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --run --capture --screenshot-dir "D:\AI\Game Frame\ioq3-v2-home\baseq3\screenshots" --output-dir "output\arena_film_24s" --manifest "output\arena_film_24s\manifest.json"
```

Expected (subject to local verification): 3 shots, 195 camera commands queued, 3 capture requests; `capture_files_verified: true` only if all three *new* expected JPEGs appear and are copied successfully. If one is missing, false; per-shot manifest shows which.

```powershell
Get-ChildItem "output\arena_film_24s"
Get-Content "output\arena_film_24s\manifest.json"
```

Expected final layout:

```
output/arena_film_24s/
  manifest.json
  01_establishing_pan.jpg
  02_compression_telephoto.jpg
  03_return_wide.jpg
```

## Safety / caveats

- Verification is based on on-disk JPEG metadata and requested file names, **not** image content, render-state feedback or frame-accurate capture timing.
- Existing output JPEG names are never overwritten; for retakes use a **new --output-dir** per run.
- The native engine might choose numeric-suffixed names. Matching accepts exact names or numeric suffixes only; it never assigns a random screenshot merely because it was recently modified.
- `--screenshot-dir` and `--output-dir` must be passed together, alongside `--run --capture`.
- When capture verification flags are absent, V4 behavior is unchanged.
- The manifest includes each shot's source/output file locations and a per-shot verification flag; no movie is exported.
