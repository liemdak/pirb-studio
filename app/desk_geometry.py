"""One plane for the keyboard, tabletop, texture and view bounds."""
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
    points = tabletop_corners()
    return points + [point + QPointF(0, DESK_DEPTH) for point in points]


def tabletop_path():
    path = QPainterPath()
    path.addPolygon(QPolygonF(tabletop_corners()))
    path.closeSubpath()
    return path


def desk_body_path():
    """One swept solid, without overlapping front/right fascia outlines."""
    corners = tabletop_corners()
    offset = QPointF(0, DESK_DEPTH)
    body = tabletop_path()
    body = body.united(QTransform.fromTranslate(0, DESK_DEPTH).map(body))
    for index, a in enumerate(corners):
        b = corners[(index + 1) % len(corners)]
        face = QPainterPath()
        face.addPolygon(QPolygonF([a, b, b + offset, a + offset]))
        face.closeSubpath()
        body = body.united(face)
    return body
