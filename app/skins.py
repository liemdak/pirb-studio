"""Cached tabletop skins on the same plane as the keyboard."""
from PySide6.QtCore import Qt,QPointF,QRectF
from PySide6.QtGui import QPixmap,QPainter,QPolygonF,QColor,QTransform,QPainterPath,QLinearGradient,QPen,QRadialGradient,QFont
from preferences import load_image
from desk_geometry import tabletop_corners,texture_projection,tabletop_path,desk_body_path,front_fascia_path,DESK_DEPTH,desk_content_path,content_inset

EDGE=tabletop_corners()
_CLASSIC=None

def classic_surface():
    global _CLASSIC
    if _CLASSIC is not None:return _CLASSIC
    image=QPixmap(2000,1200);image.fill(Qt.GlobalColor.transparent)
    p=QPainter(image);p.scale(2,2);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    gradient=QLinearGradient(0,0,1000,600)
    for stop,color in ((0,'#241b3b'),(.45,'#35234e'),(1,'#171426')):gradient.setColorAt(stop,QColor(color))
    p.fillRect(QRectF(0,0,1000,600),gradient)
    glow=QRadialGradient(QPointF(570,230),570);glow.setColorAt(0,QColor(132,81,190,48));glow.setColorAt(1,QColor(132,81,190,0));p.fillRect(QRectF(0,0,1000,600),glow)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(5):
        curve=QPainterPath(QPointF(330+i*32,600));curve.cubicTo(490+i*32,350,690+i*28,480,1010,80+i*36)
        p.setPen(QPen(QColor(194,160,238,12+i*2),2));p.drawPath(curve)
    # Keep detail on the back edge; the front stays plain at small sizes.
    p.setPen(QPen(QColor(204,179,118,75),2))
    for y,sign in ((30,1),):
        for x in range(30,965,36):
            motif=QPainterPath(QPointF(x,y));motif.lineTo(x+26,y);motif.lineTo(x+26,y+sign*18);motif.lineTo(x+8,y+sign*18);motif.lineTo(x+8,y+sign*7);motif.lineTo(x+18,y+sign*7);p.drawPath(motif)
    # Text is intentional community decoration, not a redrawn official logo.
    p.setPen(QColor('#d4c3ee'));font=QFont('Segoe UI',30,QFont.Weight.Bold);font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,4);p.setFont(font)
    p.drawText(QPointF(60,507),'PYTH')
    p.setPen(QColor('#9e87b6'));font.setPixelSize(12);font.setBold(False);font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,2);p.setFont(font);p.drawText(QPointF(63,530),'COMMUNITY DESK')
    p.end();_CLASSIC=image;return image

def skin_path(root,prefs):
    if prefs['skin'] in ('none','pyth_classic'):return None
    if prefs['skin']=='custom':return prefs['custom_skin'] or None
    return root/'assets'/'backgrounds'/(prefs['skin']+'.jpg')

def source_crop(width,height,prefs):
    ratio=1000/600
    cropw=min(width,height*ratio)*100/prefs['zoom'];croph=cropw/ratio
    cx=(width-cropw)*(prefs['pan_x']+100)/200
    cy=(height-croph)*(prefs['pan_y']+100)/200
    return QRectF(cx,cy,cropw,croph)

def prepare_desk_material(root,prefs):
    path=skin_path(root,prefs)
    image=classic_surface() if prefs['skin']=='pyth_classic' else None
    if path:
        try:image=load_image(path)
        except (OSError,ValueError):pass
    if image is None:return None,None
    angle=0 if prefs['skin']=='pyth_classic' else prefs['skin_rotation']
    image=image.transformed(QTransform().rotate(angle),Qt.TransformationMode.SmoothTransformation)
    return image,source_crop(image.width(),image.height(),prefs)


def paint_desk(p,prefs,material):
    # Rasterize the outside edge ONCE at the final device size. Only dark matte
    # material can reach it; texture, bevel, RGB and device shadows stay inset.
    shape=desk_body_path()
    p.save();p.fillPath(shape,QColor('#261e33'))
    p.setClipPath(desk_content_path(content_inset(p)),Qt.ClipOperation.IntersectClip)
    gradient=QLinearGradient(200,300,850,620);gradient.setColorAt(0,QColor('#403448'));gradient.setColorAt(1,QColor('#282333'));p.fillPath(shape,gradient)
    image,crop=material
    if image is not None:
        p.save();p.setTransform(texture_projection(),True)
        p.drawPixmap(QRectF(0,0,1000,600),image,crop);p.restore()
        p.fillPath(shape,QColor(19,13,31,round(255*(1-prefs['brightness']/100))))
    front_left=EDGE[3]
    material_gradient=QLinearGradient(front_left,front_left+QPointF(0,-DESK_DEPTH))
    material_gradient.setColorAt(0,QColor('#30253d'));material_gradient.setColorAt(1,QColor('#483554'))
    p.fillPath(front_fascia_path(),material_gradient)
    p.restore()


def desk_surface(root,prefs):
    # Compatibility/export helper; the live window uses paint_desk directly.
    layer=QPixmap(2200,1360);layer.setDevicePixelRatio(2);layer.fill(Qt.GlobalColor.transparent)
    p=QPainter(layer);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    paint_desk(p,prefs,prepare_desk_material(root,prefs));p.end();return layer

def draw_rgb(p,board,mode,elapsed):
    if mode=='off':return
    p.save();p.setClipPath(desk_content_path(content_inset(p)),Qt.ClipOperation.IntersectClip);p.setTransform(board,True)
    r=QRectF(-13,-13,23*24+26,6.4*28+26)
    for spread,alpha in [(8,12),(5,25),(2,70)]:
        gradient=QLinearGradient(r.topLeft(),r.topRight())
        if mode=='purple':colors=['#b481ff','#a267ed','#c392ff']
        else:colors=[QColor.fromHsvF((elapsed*.035+i/3)%1,.55,.95).name() for i in range(3)]
        for i,color in enumerate(colors):
            c=QColor(color);c.setAlpha(alpha);gradient.setColorAt(i/2,c)
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(gradient);p.drawRoundedRect(r.adjusted(-spread,-spread,spread,spread),10,10)
    p.restore()
