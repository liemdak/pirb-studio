"""Continuous chest and wing geometry. One filled outline prevents shoulder seams."""
import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainterPath, QColor, QPen, QLinearGradient, QRadialGradient,QPixmap,QPainter,QBrush

LEFT_ROOT=QPointF(446,316)
RIGHT_ROOT=QPointF(641,342)

def wing_path(root, contact):
    delta=contact-root
    length=max(1.,math.hypot(delta.x(),delta.y()))
    along=delta/length
    normal=QPointF(-along.y(),along.x())
    tip=contact-along*24
    d=tip-root
    path=QPainterPath(root+normal*38)
    path.cubicTo(root+d*.28+normal*39,tip-d*.16+normal*25,tip+normal*24)
    path.quadTo(tip+along*32+normal*21,tip+along*23+normal*8)
    path.quadTo(tip+along*36,tip+along*23-normal*8)
    path.quadTo(tip+along*32-normal*21,tip-normal*24)
    path.cubicTo(tip-d*.16-normal*25,root+d*.28-normal*39,root-normal*38)
    path.closeSubpath()
    return path

def chest_path():
    path=QPainterPath()
    path.moveTo(440,276)
    path.cubicTo(477,250,590,255,648,295)
    path.cubicTo(683,320,696,373,672,400)
    path.cubicTo(635,435,480,425,435,392)
    path.cubicTo(408,372,407,311,440,276)
    path.closeSubpath()
    return path

def silhouette(mouse_contact,key_contact):
    return chest_path().united(wing_path(LEFT_ROOT,mouse_contact)).united(wing_path(RIGHT_ROOT,key_contact))

_BODY_BRUSH=None
def body_brush():
    global _BODY_BRUSH
    if _BODY_BRUSH is not None:return _BODY_BRUSH
    texture=QPixmap(1800,1125);texture.setDevicePixelRatio(1.5);texture.fill(Qt.GlobalColor.transparent);p=QPainter(texture);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    gradient=QLinearGradient(415,270,610,470)
    for stop,color in [(0,'#c7ccdf'),(.28,'#b2bad3'),(.65,'#929fbf'),(1,'#697a9f')]:gradient.setColorAt(stop,QColor(color))
    p.fillRect(QRectF(0,0,1200,750),gradient)
    sheen=QRadialGradient(QPointF(491,301),230);sheen.setColorAt(0,QColor(242,245,255,75));sheen.setColorAt(.65,QColor(227,233,255,15));sheen.setColorAt(1,QColor(213,225,255,0));p.fillRect(QRectF(0,0,1200,750),sheen)
    bib=QPainterPath(QPointF(436,289));bib.cubicTo(QPointF(480,276),QPointF(610,294),QPointF(659,320));bib.lineTo(658,345)
    for x,y in [(630,358),(597,367),(563,370),(529,365),(495,356),(465,344)]:bib.quadTo(QPointF(x+15,y+13),QPointF(x,y))
    bib.closeSubpath()
    light=QLinearGradient(450,285,600,380);light.setColorAt(0,QColor('#e0e3ed'));light.setColorAt(.65,QColor('#c6cde0'));light.setColorAt(1,QColor('#aebbd4'));p.fillPath(bib,light)
    p.end();_BODY_BRUSH=QBrush(texture);return _BODY_BRUSH

def draw_rig(p,mouse_contact,key_contact):
    shape=silhouette(mouse_contact,key_contact)
    # Soft contact shadow and one continuous outline keep the shoulders coherent.
    p.save();p.translate(0,6);p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(20,16,35,34));p.drawPath(shape);p.restore()
    p.setPen(QPen(QColor('#44334f'),3.1,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin));p.setBrush(body_brush());p.drawPath(shape)
    p.save();p.setClipPath(shape)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for root,contact in [(LEFT_ROOT,mouse_contact),(RIGHT_ROOT,key_contact)]:
        delta=contact-root
        for t in (.44,.60,.76):
            at=root+delta*t
            path=QPainterPath(at+QPointF(-12,-1));path.quadTo(at+QPointF(0,8),at+QPointF(11,1))
            p.setPen(QPen(QColor(81,101,142,95),1.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawPath(path)
            p.save();p.translate(0,-1);p.setPen(QPen(QColor(235,241,255,80),.9));p.drawPath(path);p.restore()
    p.setPen(QPen(QColor(246,247,255,58),1.3));p.drawPath(shape)
    p.restore()
