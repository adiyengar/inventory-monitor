"""
Edge-density: a pile-depth proxy for dense small parts (nails, screws, etc.)
that OWL-ViT can't reliably count individually.

A deep tangled pile of overlapping metal parts has far more edges/glare per
pixel than a thin single layer, even when both cover roughly the same visible
area — so Canny edge density tracks pile depth better than raw pixel coverage
would. Validated 2026-09-10 against a real, measured 100%/50%/0% depletion:
with a tightly-inset ROI (excluding compartment divider walls), ratios came
back 1.00x/0.49x/0.02x — reliable as a coarse full/low/empty state detector,
not a smooth percentage gauge. See BACKLOG.md for the full validation history.
"""
import cv2
import numpy as np


def edge_density(gray_roi):
    """Fraction of pixels in a grayscale ROI crop that are Canny edges."""
    edges = cv2.Canny(gray_roi, 50, 150)
    return float(np.count_nonzero(edges)) / edges.size
