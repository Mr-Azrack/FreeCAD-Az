# SPDX-License-Identifier: LGPL-2.1-or-later
"""Session-scoped canvas colors and a presentation-only construction grid."""

import FreeCAD as App
from . import modeling


class Appearance:
    def __init__(self):
        self.params = App.ParamGet("User parameter:BaseApp/Preferences/View")
        self.saved = {name: (kind, value) for kind, name, value in self.params.GetContents()}
        self.values = {
            "Simple": ("Bool", True),
            "Gradient": ("Bool", False),
            "BackgroundColor": ("Unsigned Long", 0xE9ECEFFF),
            "SelectionColor": ("Unsigned Long", 0x398DDFFF),
            "PreselectionColor": ("Unsigned Long", 0x83BAE8FF),
            "EditedEdgeColor": ("Unsigned Long", 0x287AAFFF),
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
            "FullyConstrainedColor": 0x00FF00FF,
            "FullyConstraintElementColor": 0x80CF9EFF,
            "ConstructionColor": 0x0000DCFF,
            "FullyConstraintConstructionElementColor": 0x8FA8FCFF,
        }
        self.grids = []
        self.grid_visible = False
        self.last_view = None

    def activate(self):
        for name, (kind, value) in self.values.items():
            self.write(kind, name, value)

    def write(self, kind, name, value):
        methods = {
            "Bool": "Bool",
            "Unsigned Long": "Unsigned",
            "Int": "Int",
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
        color = coin.SoBaseColor()
        color.rgb = (0.77, 0.80, 0.83)
        style = coin.SoDrawStyle()
        style.lineWidth = 1
        coords = coin.SoCoordinate3()
        # A fixed world plane keeps the grid's millimetre spacing meaningful.
        # It is a scene decoration, never a document object or exportable shape.
        points = []
        for i in range(-20, 21):
            p = i * 10.0
            points.extend([(-200, p, 0), (200, p, 0), (p, -200, 0), (p, 200, 0)])
        coords.point.setValues(0, len(points), points)
        lines = coin.SoLineSet()
        lines.numVertices.setValues(0, 82, [2] * 82)
        for child in (color, style, coords, lines):
            group.addChild(child)
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
        if self.grid_visible or any(v == view for v, _root, _node in self.grids):
            node = self.grid(view)
            node.whichChild = -3 if self.grid_visible and not modeling.in_sketch() else -1
        self.last_view = view

    def toggle_grid(self, checked):
        self.grid_visible = checked
        self.update()

    def fit(self, callback):
        visible = []
        for _view, _root, node in self.grids:
            try:
                visible.append((node, node.whichChild.getValue()))
                node.whichChild = -1
            except RuntimeError:
                pass
        try:
            return callback()
        finally:
            for node, value in visible:
                try:
                    node.whichChild = value
                except RuntimeError:
                    pass

    def deactivate(self):
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
