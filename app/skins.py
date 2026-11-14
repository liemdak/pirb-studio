"""Cached desk image projected to the existing tabletop, with crop controls."""
from PySide6.QtCore import Qt,QPointF,QRectF
from PySide6.QtGui import QPixmap,QPainter,QPolygonF,QColor,QTransform,QPainterPath,QLinearGradient,QPen
from preferences import load_image

EDGE=[QPointF(0,294),QPointF(1000,454),QPointF(1000,650),QPointF(0,490)]

def skin_path(root,prefs):
    if prefs['skin']=='none':return None
    if prefs['skin']=='custom':return prefs['custom_skin'] or None
    return root/'assets'/'backgrounds'/(prefs['skin']+'.jpg')

def source_crop(width,height,prefs):
    ratio=1000/600
    cropw=min(width,height*ratio)*100/prefs['zoom'];croph=cropw/ratio
    cx=(width-cropw)*(prefs['pan_x']+100)/200
    cy=(height-croph)*(prefs['pan_y']+100)/200
    return QRectF(cx,cy,cropw,croph)

def desk_surface(root,prefs):
    layer=QPixmap(1000,650);layer.fill(Qt.GlobalColor.transparent)
    p=QPainter(layer);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    shape=QPainterPath();shape.addPolygon(QPolygonF(EDGE));p.setClipPath(shape)
    gradient=QLinearGradient(0,294,700,650);gradient.setColorAt(0,QColor('#403448'));gradient.setColorAt(1,QColor('#282333'))
    p.fillPath(shape,gradient)
    path=skin_path(root,prefs)
    if path:
        try:
            image=load_image(path)
            image=image.transformed(QTransform().rotate(prefs['skin_rotation']),Qt.TransformationMode.SmoothTransformation)
            p.save();p.setTransform(QTransform(1,.16,0,196/600,0,294),True)
            p.drawPixmap(QRectF(0,0,1000,600),image,source_crop(image.width(),image.height(),prefs));p.restore()
            p.fillPath(shape,QColor(19,13,31,round(255*(1-prefs['brightness']/100))))
        except (OSError,ValueError):pass
    p.setClipping(False);p.setPen(QPen(QColor('#96819e'),2));p.drawLine(EDGE[0],EDGE[1])
    p.setPen(QPen(QColor('#18151f'),7));p.drawLine(EDGE[2],EDGE[3]);p.end()
    return layer

def draw_rgb(p,board,mode,elapsed):
    if mode=='off':return
    p.save();p.setTransform(board,True)
    r=QRectF(-13,-13,23*24+26,6.4*28+26)
    for spread,alpha in [(8,12),(5,25),(2,70)]:
        gradient=QLinearGradient(r.topLeft(),r.topRight())
        if mode=='purple':colors=['#b481ff','#a267ed','#c392ff']
        else:colors=[QColor.fromHsvF((elapsed*.035+i/3)%1,.55,.95).name() for i in range(3)]
        for i,color in enumerate(colors):
            c=QColor(color);c.setAlpha(alpha);gradient.setColorAt(i/2,c)
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(gradient);p.drawRoundedRect(r.adjusted(-spread,-spread,spread,spread),10,10)
    p.restore()
