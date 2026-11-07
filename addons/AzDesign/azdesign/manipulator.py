# SPDX-License-Identifier: LGPL-2.1-or-later
"""Native Coin draggers: viewport motion stays in model millimetres."""

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
from . import features
from .qt import QtCore


def arrow(size, active=False):
    root = coin.SoSeparator()
    color = coin.SoBaseColor()
    color.rgb = (1.0, 0.58, 0.20) if active else (0.20, 0.55, 0.90)
    root.addChild(color)
    # Only the visual arrow is scaled. Scaling its dragger would also scale
    # pointer motion, breaking the relationship between distance and geometry.
    rotate = coin.SoRotation()
    rotate.rotation.setValue(coin.SbRotation(coin.SbVec3f(0, 1, 0), coin.SbVec3f(1, 0, 0)))
    root.addChild(rotate)
    shaft = coin.SoCylinder()
    shaft.radius = size * 0.12
    shaft.height = size
    root.addChild(shaft)
    shift = coin.SoTranslation()
    shift.translation = (0, size * 0.65, 0)
    root.addChild(shift)
    head = coin.SoCone()
    head.bottomRadius = size * 0.35
    head.height = size * 0.65
    root.addChild(head)
    return root


class ExtrudeHandles:
    def __init__(self, task):
        self.task = task
        self.scene = Gui.activeDocument().activeView().getSceneGraph()
        self.root = coin.SoSeparator()
        self.scene.addChild(self.root)
        self.handles = []
        self.dragging = False
        self.removed = False
        self.states = []
        self.timer = QtCore.QTimer(task.form)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    def hide(self):
        if not self.dragging:
            self.root.removeAllChildren()
            self.handles = []
            self.states = []

    def poll(self):
        # Some shipped Pivy builds crash inside remove*Callback even for a
        # standalone dragger. Read native dragger fields from Qt instead of
        # registering Python callbacks with Coin. Coin still owns the actual
        # pointer interaction; the timer only transfers its model-space value.
        for index, (dragger, start, motion, finish) in enumerate(list(self.handles)):
            active = bool(dragger.isActive.getValue())
            previous, position = self.states[index]
            current = float(dragger.translation.getValue()[0])
            self.states[index] = (active, current)
            if active and not previous:
                start()
            if current != position:
                motion()
            if not active and (previous or current != position):
                finish()

    def update(self):
        if self.dragging or self.removed:
            return
        self.hide()
        task = self.task
        if task.picking or task.extent.currentText() != "Distance" or not task.valid:
            return
        spec = task.spec()
        profile = features.source_shape(
            spec["source"], descriptors=spec["regions"], whole=spec["whole"]
        )
        face = profile.Faces[0]
        normal = face.normalAt(0, 0)
        origin = face.CenterOfMass + normal * features.numeric(
            spec["offset"], context=spec["source"][0], signed=True, zero=True
        )
        if spec["reversed"]:
            normal = -normal
        if spec["operation"] == "Cut":
            normal = -normal
        size = max(1.5, min(8.0, profile.BoundBox.DiagonalLength * 0.12))
        length = features.numeric(spec["distance"], context=spec["source"][0], signed=True)
        symmetric = spec["direction"] == "Symmetric"
        self._add(
            origin,
            normal,
            length / 2 if symmetric else length,
            size,
            task.distance,
            2 if symmetric else 1,
        )
        if spec["direction"] == "Two sides":
            length2 = features.numeric(spec["distance2"], context=spec["source"][0])
            self._add(origin, -normal, length2, size, task.distance2, 1)

    def _add(self, origin, normal, distance, size, field, factor):
        group = coin.SoSeparator()
        transform = coin.SoTransform()
        transform.translation = tuple(origin)
        transform.rotation.setValue(
            coin.SbRotation(coin.SbVec3f(1, 0, 0), coin.SbVec3f(*tuple(normal)))
        )
        group.addChild(transform)
        dragger = coin.SoTranslate1Dragger()
        dragger.setPart("translator", arrow(size))
        dragger.setPart("translatorActive", arrow(size, True))
        dragger.setPart("feedback", coin.SoSeparator())
        dragger.setPart("feedbackActive", coin.SoSeparator())
        dragger.translation = (distance, 0, 0)

        def start(*_):
            self.dragging = True

        def motion(*_):
            value = dragger.translation.getValue()[0] * factor
            field.setText("{:.4f} mm".format(value))

        def finish(*_):
            motion()

            # Coin is still traversing this dragger during its finish callback.
            # Rebuilding/removing it there can free the current native node.
            def complete():
                self.dragging = False
                if not self.task.closed:
                    self.task.preview()

            QtCore.QTimer.singleShot(0, complete)

        group.addChild(dragger)
        self.root.addChild(group)
        # Keep callback closures alive for the exact lifetime of their dragger.
        self.handles.append((dragger, start, motion, finish))
        self.states.append((False, float(distance)))

    def remove(self):
        if not self.removed:
            self.timer.stop()
            self.scene.removeChild(self.root)
            self.handles = []
            self.states = []
            self.removed = True
