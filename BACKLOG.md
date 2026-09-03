# Backlog

## Bugs

- ~~A video recorded in a different physical camera orientation silently
  gets wrong ROI results, with no error.~~ **Fixed 2026-09-03.** Discovered
  when `partition_1_20260903_172845.MOV` turned out to be landscape
  (1920x1080) while the other two test videos were portrait (1080x1920),
  and nothing checked a video's frame size against the size the drawer
  ROIs were drawn at. Fix: `scripts/find_roi.py` now writes
  `video.roi_frame_size: [w, h]` into `config/config.yaml` when it saves
  partitions, and `process_video_file` in `main.py` compares each video's
  actual frame size against it before doing any detection work, skipping
  (and logging an error + marking the DB record `success=False`) on a
  mismatch instead of silently analyzing a misaligned frame. Still true
  operationally: keep the camera in a fixed orientation across recording
  sessions — the guard skips mismatches, it doesn't fix them.

- **`app.py`'s Streamlit uploader always saves videos with a `.mp4`
  extension, even for `.mov` uploads.** `format_video_filename` (line 47)
  hardcodes `.mp4` regardless of the uploaded file's actual type — the
  file picker accepts `mp4/avi/mov/mkv` (line 148), but a `.mov` upload
  gets written to disk as `..._<timestamp>.mp4` containing MOV-encoded
  bytes. Likely still plays/decodes fine (ffmpeg sniffs the container
  rather than trusting the extension), but the extension is wrong and
  could confuse other tooling. Fix: derive the saved extension from
  `uploaded_file.name`'s suffix instead of hardcoding `.mp4`.

- **`part_type` isn't used to filter detections per drawer.**
  `InventoryMonitor._filter_detections_in_roi` (`src/core/monitor.py:63`)
  only checks whether a detection's bounding box overlaps a drawer's ROI —
  it never checks the detection's label against that drawer's `part_type`.
  So if two partitions are physically close enough that a detection from
  one drawer's contents lands inside a neighboring drawer's ROI (e.g. a
  coin detected inside the screws partition box), it gets counted there
  too, regardless of `part_type`. Fix: filter `detections` in
  `_filter_detections_in_roi` (or before calling it) to only those whose
  `label` matches `drawer_config['part_type']`.

## Investigate

- **OWL-ViT (google/owlvit-base-patch32) doesn't reliably count dense piles
  of small nails.** Tested 2026-09-03 against a real "drawer open" frame
  from `partition_1_20260903_212818.MOV` (visibly 100+ nails per
  partition): with the configured query `"nails"`, top detection
  confidence was ~1.2% — far below the 10% `confidence_threshold`. Trying
  singular phrasing (`"a nail"`) raised the top confidence to ~6.5%, still
  below threshold; even lowering the threshold to 3% with that phrasing
  only produced 11 boxes on a frame with hundreds of visible nails. This
  isn't a threshold-tuning fix — the model just doesn't resolve individual
  objects in a dense, cluttered pile of small near-identical items. As a
  direct result, every drawer read `count=0` for the whole
  `2026-09-03 --process-all` test run, which trivially tripped every
  CRITICAL alert (0 < critical_threshold) and left the new
  end-of-night depletion check (`check_nightly_depletion` in `main.py`)
  with no valid non-zero baseline to compare against.
  Options to explore: a counting-specific model/approach (e.g. classical
  CV blob/contour counting, which tends to work better for dense small
  parts than zero-shot detection), or a differently-fine-tuned detector.
  Simple prompt/threshold tuning alone did not get this to a usable place.

- **Edge-density prototype (`scripts/edge_density_prototype.py`) looks
  promising as a depletion signal, needs more validation.** Built and run
  2026-09-03 as an alternative to per-object counting: since pile *depth*
  (not just covered area) is what actually indicates depletion, and plain
  area/coverage thresholding can't tell a thin single layer from a deep
  pile, this measures Canny edge density per ROI instead — a deep tangled
  pile of overlapping metal parts has far more edges/glare per pixel than
  a thin layer, even at similar coverage. Visually verified the edges
  track the actual nail piles, not background/lighting noise (see overlay
  from that session). On the one valid same-orientation comparison
  available (video1 15:29 → video3 21:28, both visibly still full),
  ratios came back 0.82x–1.02x across all 4 drawers — correctly did not
  false-alarm on stable inventory. Not yet validated against an actual
  depletion event (no same-orientation before/after pair with real
  depletion existed in this test set — see the orientation-mismatch bug
  above).

  **Important caveat from that same result**: 0% real change already
  produced a 0.82x–1.02x spread — i.e. ~±18% noise floor with nothing
  actually removed. That's the main open risk: moderate depletion (roughly
  20–30%) may not be distinguishable from noise. A pass/fail threshold
  check alone won't tell us this — need actual correlation data.

  **Validation protocol to close this out** (agreed with Adi 2026-09-03):
  one drawer taken through several controlled checkpoints, same locked
  camera orientation throughout (now enforced by the `roi_frame_size`
  guard), with the *real* removed amount logged at each step (counted or
  weighed, not eyeballed):
    1. Baseline: full.
    2. ~10–20% removed — the case most likely to be lost in the ~18%
       noise floor above; if this can't be distinguished, the signal
       isn't sensitive enough for early-warning alerts.
    3. ~50% removed.
    4. ~75%+ / near-empty removed — check the signal doesn't do something
       strange once the tray floor becomes visible (different texture/
       reflectivity than a pile of parts).
  Reuse the existing video1↔video3 pair (both full, same orientation) as
  the established 0%-change noise-floor reference — no need to redo that
  leg. Compare the resulting edge-density ratios against the logged real
  fractions to see whether the relationship is usable, not just whether a
  single 50% threshold happens to trip correctly.
