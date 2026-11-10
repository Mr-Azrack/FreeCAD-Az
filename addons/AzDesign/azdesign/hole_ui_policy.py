# SPDX-License-Identifier: LGPL-2.1-or-later
"""Conservative UI rules for fast Hole previews without surprise helices."""


def can_live_preview(spec, *, enabled, has_sketch, original_modeled=False, previously_modeled=False):
    """Only a complete, non-helical Hole may auto-recompute.

    A feature that started or was just previewed with geometric threads needs
    a deliberate, consented manual preview even when its checkbox is now off.
    """
    if not enabled or not has_sketch:
        return False
    if spec.model_thread or original_modeled or previously_modeled:
        return False
    if spec.thread_type != "None" and not spec.thread_size:
        return False
    try:
        spec.validate()
    except ValueError:
        return False
    return True
