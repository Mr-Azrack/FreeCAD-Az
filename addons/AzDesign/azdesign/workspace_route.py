# SPDX-License-Identifier: LGPL-2.1-or-later
"""Workspace routing for Design without disturbing the Home screen.

FreeCAD itself stores a workbench association in saved native documents and
restores it when those documents activate. Do not override that association.
Only genuinely new, unsaved modeling documents default into Design.
"""
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore

DESIGN = "AzDesignWorkbench"
# A new design from Home/ordinary modeling defaults to Design. A new
# document created by a specialized context (CAM, Mesh, etc.) stays there.
GENERIC = frozenset({
    "", "NoneWorkbench", "StartWorkbench", "PartDesignWorkbench",
    "PartWorkbench", DESIGN,
})
_router = None


def route_new_document(doc_name):
    """Delayed GUI check: opened FCStd documents must retain their workbench."""
    try:
        doc = App.getDocument(doc_name)
        if doc is None or getattr(doc, "FileName", ""):
            return
        active_gui = Gui.activeDocument()
        if active_gui is None or active_gui.Document != doc:
            return
        if getattr(active_gui, "getInEdit", lambda: None)():
            return
        if Gui.Control.activeDialog():
            return
        wb = Gui.activeWorkbench()
        name = wb.name() if wb else ""
        if name not in GENERIC or name == DESIGN:
            return
        Gui.activateWorkbench(DESIGN)
    except (RuntimeError, ReferenceError):
        # The document could have closed while a GUI event was pending.
        return


class _DocumentRouter:
    def slotCreatedDocument(self, doc):
        # Creation fires during file reopening too. Check the resulting
        # FileName after the Qt event loop has processed restore/import.
        name = doc.Name
        QtCore.QTimer.singleShot(250, lambda: route_new_document(name))


def install():
    global _router
    if _router is None:
        _router = _DocumentRouter()
        App.addDocumentObserver(_router)
    return _router
