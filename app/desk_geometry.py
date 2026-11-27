"""One four-corner silhouette for every visible tabletop layer."""
import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QTransform, QPainterPath, QPolygonF


def keyboard_projection():
    return QTransform(-.94, -.16, .43, -.78, 865, 611)


# Board units. Include the mouse to the left of the keyboard in screen space.
DESK_RECT = QRectF(-45, -20, 855, 255)
TEXTURE_RECT = QRectF(0, 0, 1000, 600)
DESK_DEPTH = 6


def tabletop_corners():
    board = keyboard_projection()
    r = DESK_RECT
    # Back-left, back-right, front-right, front-left as seen by the viewer.
    return [board.map(p) for p in (
        r.bottomRight(), r.bottomLeft(), r.topLeft(), r.topRight())]


def texture_projection():
    back_left, back_right, _, front_left = tabletop_corners()
    horizontal = (back_right - back_left) / TEXTURE_RECT.width()
    depth = (front_left - back_left) / TEXTURE_RECT.height()
    return QTransform(horizontal.x(), horizontal.y(), depth.x(), depth.y(),
                      back_left.x(), back_left.y())


def desk_outline():
    return tabletop_corners()


def tabletop_path():
    path = QPainterPath()
    path.addPolygon(QPolygonF(tabletop_corners()))
    path.closeSubpath()
    return path


def desk_body_path():
    """The complete outer body is the same four-corner parallelogram."""
    return tabletop_path()


def front_fascia_path():
    """Shade a narrow band INSIDE the outline, along the shared depth axis."""
    back_left, _, front_right, front_left = tabletop_corners()
    direction = back_left - front_left
    length = math.hypot(direction.x(), direction.y())
    inset = direction * min(0.1, DESK_DEPTH / max(1.0, length))
    path = QPainterPath()
    path.addPolygon(QPolygonF([
        front_left, front_right, front_right + inset, front_left + inset]))
    path.closeSubpath()
    return path
