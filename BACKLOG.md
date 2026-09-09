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

  **2026-09-09 real validation run — results.** Adi recorded 5 videos of
  the `nails` (top-right) partition depleted on a real, known schedule:
  100% @ 9:30, 75% @ 12:36, 50% @ 14:25, 25% @ 15:57, 0% @ 18:02. Two
  separate results from this:

  1. *The actual production pipeline* (`main.py`, OWL-ViT) — every drawer
     read `part_count = 0` across all 5 videos, same failure mode as the
     2026-09-03 run. Confirms this is a real, repeatable limitation, not
     a one-off. `check_nightly_depletion` correctly found no non-zero
     baseline and stayed quiet rather than alerting on garbage.

  2. *`scripts/edge_density_prototype.py` against the same 5 videos*
     (`nails` drawer, ratio to the 9:30 baseline of 27.17%):
       - 12:36 (75% real) → 74.5% ratio — excellent match.
       - 14:25 (50% real) → 73.0% ratio — badly overestimates remaining.
       - 15:57 (25% real) → 62.9% ratio — badly overestimates remaining.
       - 18:02 (0% real) → 14.5% ratio — right direction, but this frame
         has a confound (next point).

  **New finding: the camera/box physically drifted between recordings.**
  Overlaid the drawn ROI boxes on each frame — by the 18:02 video the
  whole tray had visibly shifted down/right in frame vs. the 9:30
  baseline, so the `nails` ROI box no longer cleanly covers the physical
  compartment at that point (it's mostly over blank background by then;
  the compartment itself is visually confirmed empty in the raw frame,
  independent of the ROI box). The 12:36 and 15:57 frames' boxes still
  looked correctly aligned on visual inspection, so this doesn't explain
  the 50%/25% mismatches above — but it likely explains why the 3
  "control" partitions (not supposed to change) drifted 20–52% over the
  same 5 videos: most likely cumulative small nudges to the box each time
  someone opened the drawer to remove nails, across all 5 handling
  events, not just once before the last video.

  **Reading**: edge density nails the 75% checkpoint but compresses the
  50–25% middle of the range (reads ~70% remaining when the real amount
  is 50% or even 25%) before finally dropping near-empty. Plausible
  explanation: a sparse remaining layer of nails still generates
  substantial edge/glare complexity, so the signal doesn't fall
  proportionally with true remaining amount — the same "no depth
  perception" limitation flagged when this approach was first proposed.
  For the literal use case asked for (alert once a drawer crosses below
  50%), this data suggests it would still fire correctly by end-of-night
  (ratio 0.15x, well under 0.5) — but late, not at the true halfway point,
  since the signal was still reading "fine" (73%) exactly when the real
  amount hit 50%.

  **Next, before trusting this further**: physically fix the camera/box
  mount (tripod, tape, bracket — anything that stops it moving between
  sessions) and rerun the same 100/75/50/25/0% protocol, to separate
  "camera drift" from "edge density intrinsically compresses the middle
  of the range" as explanations for the mismatch — right now both are
  plausibly contributing and this data can't cleanly separate them.

  **2026-09-10 drift-controlled rerun — result: drift wasn't the (whole)
  problem.** Adi taped the box down and re-recorded the same
  100/75/50/25/0% schedule for `nails` (9:05/12:34/14:52/16:54/18:45).
  Verified visually via ROI overlays on all 5 frames that camera position
  held steady this time (a reference object — a "Boom Boom" nasal stick
  sitting on the shelf above the box — lands in nearly identical pixel
  position at 9:05 and 18:45). So this run isolates the signal's real
  behavior from camera drift. Result, `nails` ratio to the 9:05 baseline
  (22.49% edge density):
    - 12:34 (75% real) → 0.97x — barely moved; should have dropped ~25%.
    - 14:52 (50% real) → 0.67x — still far above where 50% real should read.
    - 16:54 (25% real) → 0.67x — identical to the 50% checkpoint; totally
      flat despite a further real 25-point drop.
    - 18:45 (0% real, visually confirmed near-empty in the raw frame) →
      0.49x — right at the 0.5 alert threshold, not near 0.
  So with drift now controlled for, the signal still doesn't track real
  depletion in the 75%→25% range at all, and even true-empty barely grazes
  the alert threshold rather than reading clearly low.

  Tested one concrete hypothesis for the "never approaches 0" part: the
  drawn `nails` ROI (`[504, 695, 826, 1108]`) likely includes a sliver of
  the compartment's own rigid divider walls, which have their own
  reflective edges independent of contents, creating a constant edge
  "floor." Recomputed the same 5 frames with the ROI inset 40px on every
  side (`[544, 735, 786, 1068]`) to exclude the walls: the near-empty
  reading did improve (0.49x → 0.34x at 18:45; 0.67x → 0.52x at 16:54),
  so wall-inclusion is a real contributing factor — but the 12:34
  checkpoint was essentially unchanged (0.97x → 0.97x) and still
  completely fails to register a real 25%-removed state. Divider-wall
  inclusion explains part of the "floor," not the flat non-response
  across the upper half of the range.

  **Where this leaves the technique**: two independent controlled runs
  (2026-09-09 uncontrolled-drift, 2026-09-10 drift-controlled) both show
  the same shape — compressed/flat through the 100%→25% range, only
  moving meaningfully once a partition is nearly empty, and even then
  landing right at rather than clearly past the alert threshold. This is
  no longer explainable by camera drift or lighting alone; it looks like
  a real limitation of raw, unnormalized Canny edge density as a single
  global number for this content. Ideas not yet tried:
    - Normalize each drawer against its sibling drawers *in the same
      frame* (cancels shared lighting/exposure — same-frame comparison
      instead of absolute values across hours). Did a rough check against
      this same dataset; inconclusive because partition `3` had one
      anomalous spike at 14:52 (23.66%, up from a 12.89% baseline) that
      pollutes the normalization — needs a cleaner rerun to evaluate
      properly, ideally one that also checks why `3` spiked.
    - Explicit per-partition calibration against captured "full" and
      "empty" reference shots (ties into the admin-panel idea from
      2026-09-03: let the user capture reference images and compute
      against those directly, rather than a general formula).
    - A different metric entirely (e.g. specular-highlight area from
      the metal's glare, which may scale differently than generic edge
      count).
  This is a real decision point on approach, not just a tuning tweak —
  flagged to Adi rather than picked unilaterally.

  **2026-09-10 (later same day) — redrawn ROIs via the real wizard, not
  just an ad hoc inset.** Adi redrew all 4 partitions with `python main.py
  --setup`, deliberately keeping every box tightly inside the compartment
  walls this time (informed by the 40px-inset test above). Reran edge
  density on both the 09-10 (drift-controlled) and 09-09 (drift-confounded)
  sets with the new ROIs:

  09-10 set, `nails` ratio to 9:05 baseline (30.82%):
    - 12:34 (75% real) → 0.96x
    - 14:52 (50% real) → 0.49x — excellent match
    - 16:54 (25% real) → 0.53x — close to the 50% reading, not 25%
    - 18:45 (0% real) → **0.02x** — essentially perfect, vs. 0.49x with
      the old, wall-including ROI. Confirms wall inclusion was indeed the
      dominant cause of the "never reaches 0" floor.
  Control partitions (`big_nails`, `3`, `4`) also tightened up a lot:
  0.86x/1.05x/0.97x across the full day, down from the 0.70x–1.52x swings
  seen with the old ROI on the same-shape 09-09 data. Applying the new
  ROI retroactively to the old 09-09 footage also smoothed `nails` into a
  monotonic decline (100%→86.6%→83.5%→64.4%→4.3%), though `4` (a control)
  still shows a false 0.49x there — expected, since that's the known
  drift-affected date and a better ROI can't fix footage that was
  actually miscaptured.

  **Important new observation**: overlaid the new ROI on the raw 12:34
  frame and looked at it directly — the `nails` compartment visually
  still looks essentially full, not 25%-depleted. The 14:52 and 16:54
  frames look similarly sparse to *each other* (not clearly 50% vs. 25%
  distinguishable by eye either). So the flat/compressed readings at
  those two checkpoints may not be a signal defect — they may be
  correctly reporting that the real removed amount didn't land precisely
  on the intended 75/50/25 schedule (plausible if removal was eyeballed
  rather than counted/weighed at each step). Open question for Adi:
  were the removed amounts at each checkpoint actually measured, or
  approximate? That determines whether the remaining mismatch is a CV
  problem or a test-execution one.

  **Answered: removal was measured (~25 nails per stage).** So the
  75%/50%/25%/0% schedule was real, not approximate — meaning the
  75%/25% compression is a genuine property of edge density, not a test
  artifact. **However**, per Adi: the actual requirement is only
  full/halfway/critical-empty (100/50/0), not a smooth percentage —
  75%/25% were only ever included as intermediate test stress-points.
  Against the levels that actually matter, the tightened-ROI signal is
  excellent: 1.00x / 0.49x / 0.02x for 100%/50%/0% real. **Verdict: edge
  density (Canny density, tight wall-excluding ROI) is validated as a
  coarse state detector — full vs. halfway vs. empty — which is exactly
  what `min_threshold`/`critical_threshold` alerting needs. It is not a
  reliable continuous percentage gauge (see 75%/25% compression), so
  don't build any "X% remaining" UI on top of it without further work.**

  **Not yet done: wiring this into the actual production pipeline.**
  `scripts/edge_density_prototype.py` is still a standalone diagnostic —
  `main.py`/`InventoryMonitor` still use OWL-ViT counting (which doesn't
  work for this content) for real alerting. Next real step is deciding
  whether/how to replace or supplement the counting-based detection in
  the production monitor with this edge-density approach.

  **Done 2026-09-10: wired into the production pipeline, per-drawer
  selectable, OWL-ViT kept alongside it.** Per Adi: keep both methods
  (some items may count fine with OWL-ViT), and full/getting-low/empty is
  exactly what's needed for the underlying 2-bin kanban use case this
  whole project automates. Implementation:
    - Shared `edge_density()` function extracted to `src/core/edge_density.py`
      (both the prototype script and production monitor now use the exact
      same, already-validated calculation — no duplicated logic).
    - New `detection_method: "owlvit" | "edge_density"` field per drawer
      in `config/config.yaml` (defaults to `"owlvit"` if absent, so old
      configs keep working unchanged).
    - `InventoryMonitor.analyze_frame` (`src/core/monitor.py`) branches
      per drawer: `_analyze_owlvit` is the original count-vs-threshold
      logic, untouched; `_analyze_edge_density` computes edge density in
      that drawer's ROI, compares to a stored `edge_density_full_reference`
      baseline, and classifies OK/LOW/CRITICAL against `low_ratio`
      (default 0.5) / `critical_ratio` (default 0.15) — the same numbers
      validated against real data above.
    - `main.py` only loads the OWL-ViT model at all if at least one
      configured drawer still uses it — verified end-to-end with a
      temporary all-edge_density config: log shows "No owlvit drawers
      configured, skipping model load" and a full video (44 frames)
      processes in ~3 seconds instead of minutes.
    - `python main.py --setup` (`scripts/find_roi.py`) now asks per
      partition which method to use. For `edge_density`, it auto-captures
      the full-state calibration from the frame being drawn on (with an
      explicit on-screen reminder that frame must show the bin full) and
      prompts for `low_ratio`/`critical_ratio` pre-filled with the
      validated defaults.
    - Verified end-to-end against real footage: replaying the known
      100%/50%/0% frames through the real `InventoryMonitor.analyze_frame`
      reproduced the exact validated numbers (100%→OK, 49%→LOW, 2%→
      CRITICAL), and a mixed owlvit+edge_density config correctly ran both
      methods independently in the same frame.
    - **Known limitation, not fixed in this pass**: `src/reports/daily_report.py`
      and the email template render `part_count`/`current_count` as a bare
      number — for edge_density drawers that number is a percentage (e.g.
      "38"), not an item count, and nothing in the report/email currently
      labels it as such. Cosmetic, not incorrect underlying data.
    - **Still open**: config.yaml's actual `nails` drawer hasn't been
      switched to `detection_method: edge_density` yet — that requires
      re-running `python main.py --setup` interactively (needs a human at
      the mouse) to pick it for real, rather than the in-memory test
      configs used to verify the code above.
