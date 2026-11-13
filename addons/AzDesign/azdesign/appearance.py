# SPDX-License-Identifier: LGPL-2.1-or-later
"""Session-scoped canvas colors and a presentation-only construction grid."""

import FreeCAD as App
from . import modeling


class Appearance:
    def __init__(self):
        self.params = App.ParamGet("User parameter:BaseApp/Preferences/View")
        self.saved = {
            name: (kind, value) for kind, name, value in (self.params.GetContents() or ())
        }
        self.grid_preferences = App.ParamGet("User parameter:BaseApp/Preferences/Mod/AzDesign")
        self.values = {
            "Simple": ("Bool", True),
            "Gradient": ("Bool", False),
            "BackgroundColor": ("Unsigned Long", 0xE9ECEFFF),
            "SelectionColor": ("Unsigned Long", 0x398DDFFF),
            "PreselectionColor": ("Unsigned Long", 0x83BAE8FF),
            "EditedEdgeColor": ("Unsigned Long", 0x174C74FF),
            "SketchEdgeColor": ("Unsigned Long", 0x174C74FF),
            "SketchVertexColor": ("Unsigned Long", 0x174C74FF),
            "FullyConstrainedColor": ("Unsigned Long", 0x304D60FF),
            "FullyConstraintElementColor": ("Unsigned Long", 0x416B58FF),
            "ConstructionColor": ("Unsigned Long", 0x507FB6FF),
            "FullyConstraintConstructionElementColor": ("Unsigned Long", 0x50729AFF),
        }
        # Sketcher reads an absent preference using its current cached color.
        # Prime its native defaults before removing keys that were absent on
        # entry, otherwise a dark Az edit color can survive into native CAD.
        self.sketch_defaults = {
            "EditedEdgeColor": 0xFFFFFFFF,
            "SketchEdgeColor": 0xFFFFFFFF,
            "SketchVertexColor": 0xFFFFFFFF,
            "FullyConstrainedColor": 0x00FF00FF,
            "FullyConstraintElementColor": 0x80CF9EFF,
            "ConstructionColor": 0x0000DCFF,
            "FullyConstraintConstructionElementColor": 0x8FA8FCFF,
        }
        self.grids = []
        self.grid_visible = self.grid_preferences.GetBool("ShowGrid", True)
        self.sketch_grids = []
        self.last_view = None
        self._fit_generation = 0

    def activate(self):
        for name, (kind, value) in self.values.items():
            self.write(kind, name, value)

    def write(self, kind, name, value):
        methods = {
            "Bool": "Bool",
            "Boolean": "Bool",
            "Unsigned Long": "Unsigned",
            "Int": "Int",
            "Integer": "Int",
            "String": "String",
            "Float": "Float",
        }
        getattr(self.params, "Set" + methods[kind])(name, value)

    def grid(self, view):
        for saved, root, node in self.grids:
            if saved == view:
                return node
        from pivy import coin

        root = view.getSceneGraph()
        node = coin.SoSwitch()
        node.setName("AzWorkspaceGrid")
        group = coin.SoSeparator()
        picking = coin.SoPickStyle()
        picking.style = coin.SoPickStyle.UNPICKABLE
        group.addChild(picking)
        # World-space 10 mm major / 2 mm minor lines remain separate from
        # document geometry, picking and exports.
        # The grid is a reference, not foreground geometry: keep even
        # major lines behind the model's visible edges and sketch cues.
        for major, rgb in ((False, (0.91, 0.92, 0.93)), (True, (0.82, 0.85, 0.88))):
            level = coin.SoSeparator()
            color = coin.SoBaseColor()
            color.rgb = rgb
            style = coin.SoDrawStyle()
            style.lineWidth = 1
            coords = coin.SoCoordinate3()
            points = []
            for i in range(-100, 101):
                if (i % 5 == 0) != major:
                    continue
                p = i * 2.0
                points.extend([(-200, p, 0), (200, p, 0), (p, -200, 0), (p, 200, 0)])
            coords.point.setValues(0, len(points), points)
            lines = coin.SoLineSet()
            lines.numVertices.setValues(0, len(points) // 2, [2] * (len(points) // 2))
            for child in (color, style, coords, lines):
                level.addChild(child)
            group.addChild(level)
        # This decoration is inserted before all model geometry. Clear its
        # bounds before traversal reaches the model so native animated Fit and
        # sketch entry ignore the floor, not only Az's explicit Fit command.
        reset = coin.SoResetTransform()
        reset.whatToReset = coin.SoResetTransform.BBOX
        group.addChild(reset)
        node.addChild(group)
        root.insertChild(node, 0)
        self.grids.append((view, root, node))
        return node

    def update(self):
        doc = modeling.current_document()
        if not doc:
            return
        import FreeCADGui as Gui

        view = Gui.activeDocument().activeView()
        if not hasattr(view, "getSceneGraph"):
            return
        sketch = modeling.in_sketch()
        if sketch and hasattr(sketch.ViewObject, "ShowGrid"):
            provider = sketch.ViewObject
            if not any(saved == provider for saved, _value in self.sketch_grids):
                self.sketch_grids.append((provider, provider.ShowGrid))
            if provider.ShowGrid != self.grid_visible:
                provider.ShowGrid = self.grid_visible
        elif not sketch:
            self.restore_sketch_grids()
        if self.grid_visible or any(v == view for v, _root, _node in self.grids):
            node = self.grid(view)
            node.whichChild = -3 if self.grid_visible and not sketch else -1
        self.last_view = view

    def toggle_grid(self, checked):
        self.grid_visible = checked
        self.grid_preferences.SetBool("ShowGrid", checked)
        self.update()

    def restore_sketch_grids(self):
        for provider, visible in self.sketch_grids:
            try:
                provider.ShowGrid = visible
            except (RuntimeError, ReferenceError):
                pass
        self.sketch_grids = []

    def fit(self, callback):
        # FreeCAD may animate fitAll after returning from the Python call.
        # Restoring the 400 mm decorative grid immediately makes that later
        # camera framing include the grid and leaves a tiny, narrow model.
        # Keep the grid hidden until the camera animation has settled.
        self._fit_generation += 1
        generation = self._fit_generation
        visible = []
        for _view, _root, node in self.grids:
            try:
                visible.append((node, node.whichChild.getValue()))
                node.whichChild = -1
            except (RuntimeError, ReferenceError):
                pass
        def restore():
            if generation != self._fit_generation:
                return  # A newer Home/Fit is still animating.
            for node, _previous in visible:
                try:
                    if any(saved_node is node for _view, _root, saved_node in self.grids):
                        node.whichChild = -3 if self.grid_visible and not modeling.in_sketch() else -1
                except (RuntimeError, ReferenceError):
                    pass
        try:
            result = callback()
        except Exception:
            restore()
            raise
        if visible:
            from .qt import QtCore
            QtCore.QTimer.singleShot(1200, restore)
        return result

    def deactivate(self):
        self.restore_sketch_grids()
        for _view, root, node in self.grids:
            try:
                if root.findChild(node) >= 0:
                    root.removeChild(node)
            except (RuntimeError, ReferenceError):
                pass
        self.grids = []
        removers = {"Bool": "Bool", "Unsigned Long": "Unsigned"}
        for name, (kind, _value) in self.values.items():
            if name in self.saved:
                self.write(self.saved[name][0], name, self.saved[name][1])
            else:
                if name in self.sketch_defaults:
                    self.params.SetUnsigned(name, self.sketch_defaults[name])
                getattr(self.params, "Rem" + removers[kind])(name)
