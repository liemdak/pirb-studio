"""Whole-scene rotation and continuous sizing, independent of character posing."""
import math
from PySide6.QtCore import QRectF,QPointF
from PySide6.QtGui import QTransform,QPolygonF

CANVAS=QRectF(-18,-18,1036,756)

def view_geometry(angle,width,available=None,content=None):
    rotation=QTransform();rotation.rotate(angle)
    if content is None:content=QPolygonF([QPointF(0,364),QPointF(1000,524),QPointF(1000,720),QPointF(0,560),QPointF(320,10),QPointF(800,10),QPointF(800,440),QPointF(320,440)])
    bounds=rotation.map(content).boundingRect().adjusted(-14,-14,14,14);scale=width/1000
    if available is not None:
        scale=min(scale,max(1,available.width()-16)/bounds.width(),max(1,available.height()-16)/bounds.height())
    transform=QTransform();transform.scale(scale,scale);transform.translate(-bounds.left(),-bounds.top());transform.rotate(angle)
    return transform,math.ceil(bounds.width()*scale),math.ceil(bounds.height()*scale),scale

def corner_position(available,size,dock):
    w,h=size
    right=dock.endswith('right');bottom=dock.startswith('bottom')
    return QPointF(available.right()-w-10 if right else available.left()+10,available.bottom()-h-10 if bottom else available.top()+10).toPoint()
