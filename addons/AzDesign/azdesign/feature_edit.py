# SPDX-License-Identifier: LGPL-2.1-or-later
"""Single Az edit route for the timeline, Browser and canvas actions.

Always edit the original FreeCAD object. Native features keep their own task
panels; Az-owned Extrude/Hole keep transactional parameter panels.
"""


def edit(obj):
    import FreeCADGui as Gui
    from . import modeling
    from .features import DesignError

    if obj is None:
        raise DesignError("Select a feature or sketch to edit.")
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current modeling task first.")
    doc = obj.Document
    gui_doc = Gui.getDocument(doc.Name)
    if gui_doc is None:
        raise DesignError("The selected feature's document is not open.")
    if obj.isDerivedFrom("Sketcher::SketchObject"):
        return modeling.edit_sketch(obj)
    if getattr(obj, "AzType", "") == "AzExtrude":
        from .tasks import edit_feature
        return edit_feature(obj)
    if obj.isDerivedFrom("PartDesign::Hole"):
        from .hole import edit_feature
        return edit_feature(obj)
    if obj.isDerivedFrom("PartDesign::LinearPattern"):
        # Editing a Design pattern never opens the native FreeCAD task pane.
        from .solid_pattern import show
        return show(editing=obj)
    if obj.isDerivedFrom("PartDesign::Fillet"):
        from .edge_treatments_canvas import show
        return show("Fillet", editing=obj)
    if obj.isDerivedFrom("PartDesign::Chamfer"):
        from .edge_treatments_canvas import show
        return show("Chamfer", editing=obj)
    if obj.isDerivedFrom("PartDesign::Body"):
        view = gui_doc.activeView()
        if view is not None:
            view.setActiveObject("pdbody", obj)
        return obj
    if obj.isDerivedFrom("PartDesign::Feature"):
        return gui_doc.setEdit(obj.Name)
    raise DesignError("This object has no feature editor; use Native Properties.")
