"""Shaded, extruded desktop devices projected onto a common desk plane."""
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QPen,QPolygonF,QLinearGradient,QRadialGradient,QPainterPath,QTransform

def poly(p,points,color,outline=None):
    p.setPen(Qt.PenStyle.NoPen if outline is None else QPen(QColor(outline),1))
    p.setBrush(QColor(color));p.drawPolygon(QPolygonF(points))

def rounded(p,r,colors,radius=3,pen=None):
    g=QLinearGradient(r.topLeft(),r.bottomRight())
    g.setColorAt(0,QColor(colors[0]));g.setColorAt(1,QColor(colors[1]))
    p.setBrush(g);p.setPen(Qt.PenStyle.NoPen if pen is None else QPen(QColor(pen),.8));p.drawRoundedRect(r,radius,radius)

def draw_keyboard(p,board,keys,keyrect,held,glow,draw_case=True,draw_caps=True,clip_region=None,backlight=False):
    def at(x,y,z=0): return board.map(QPointF(x,y))+QPointF(0,-z)
    if draw_case:
        outer=QRectF(-13,-13,23*24+26,6.4*28+26)
        corners=[outer.topLeft(),outer.topRight(),outer.bottomRight(),outer.bottomLeft()]
        # Soft contact shadow directly below the base.
        for spread,alpha in [(6,14),(3,20),(1,32)]:
            p.save();p.translate(0,4+spread*.5);p.setTransform(board,True)
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(5,3,15,alpha));p.drawRoundedRect(outer.adjusted(-spread,-spread,spread,spread),10,10);p.restore()
        # The aluminum case has vertical walls and a recessed upper plate.
        for i,col in [(0,'#221e32'),(1,'#40354f'),(2,'#332840'),(3,'#242032')]:
            a,b=corners[i],corners[(i+1)%4]
            poly(p,[at(a.x(),a.y(),0),at(b.x(),b.y(),0),at(b.x(),b.y(),11),at(a.x(),a.y(),11)],col)
        p.save();p.translate(0,-11);p.setTransform(board,True)
        rounded(p,outer,('#9a86aa','#53475f'),8,'#252033')
        rounded(p,outer.adjusted(4,4,-4,-4),('#55366c','#413363') if backlight else ('#3d354a','#50405e'),6,'#b5a1c2')
        if backlight:
            p.setPen(QPen(QColor(199,139,255,130),1.7))
            for row in range(7):p.drawLine(QPointF(2,row*28+1),QPointF(550,row*28+1))
        p.restore()
    if not draw_caps: return
    # Far rows first: nearer keycaps can correctly cover their rear neighbours.
    sorted_keys=sorted(keys,key=lambda k:board.map(keyrect(k[2]).center()).y())
    for label,vk,r in sorted_keys:
        footprint=keyrect(r)
        if clip_region is not None and not clip_region.intersects(board.mapRect(footprint).adjusted(-6,-27,6,5).toAlignedRect()):continue
        active=vk in held or vk in glow
        bottom=12;top=15 if active else 20
        cap=footprint.adjusted(2.0,2.0,-2.0,-2.0)
        accent=label in ('Esc','Enter','Space')
        dark=label.startswith('F') or label in ('Ctrl','Alt','Win','Menu')
        colors=('#fff3c0','#d8b65b') if accent else (('#9d86bb','#78608e') if dark else ('#f7f4fa','#c5bed1'))
        if active:colors=('#f6fff3','#b4ddbd')
        low=[footprint.topLeft(),footprint.topRight(),footprint.bottomRight(),footprint.bottomLeft()]
        high=[cap.topLeft(),cap.topRight(),cap.bottomRight(),cap.bottomLeft()]
        for i,color in [(0,'#71677f'),(1,'#898094'),(2,'#a79daf'),(3,'#675e73')]:
            if active:color='#7da58b'
            a,b=low[i],low[(i+1)%4];c,d=high[(i+1)%4],high[i]
            poly(p,[at(a.x(),a.y(),bottom),at(b.x(),b.y(),bottom),at(c.x(),c.y(),top),at(d.x(),d.y(),top)],color)
        p.save();p.translate(0,-top);p.setTransform(board,True)
        rounded(p,cap,colors,2.5,'#5e526d')
        inset=cap.adjusted(1,1,-1,-1)
        p.setPen(QPen(QColor(255,255,255,130),.7));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(inset,2,2)
        p.setPen(QColor('#fcf7ff' if dark and not active else '#413747'))
        font=p.font();font.setPixelSize(7 if len(label)>3 else 9);p.setFont(font);p.drawText(cap,Qt.AlignmentFlag.AlignCenter,label)
        p.restore()
    # Three indicator lights sit in the navigation strip.
    for i,c in enumerate(('#9addb3','#c2a1e3','#eac778')):
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(c));p.drawEllipse(at(19*24+i*15,.22*28,14),2,1.2)

def draw_mouse(p,pos,buttons):
    # The plane matches the keyboard, while the dome rises above it.
    plane=QTransform(-.94,-.16,.43,-.78,pos.x(),pos.y())
    def layer(z):
        p.save();p.translate(0,-z);p.setTransform(plane,True)
    layer(0)
    for grow,alpha in [(9,12),(5,18),(2,32)]:
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(0,0,0,alpha));p.drawEllipse(QRectF(-42-grow,-57-grow,84+grow*2,119+grow*2))
    p.restore()
    # Base, side wall, accent seam, then the raised shell.
    for height,r,colors in [(2,QRectF(-41,-56,82,116),('#201e2d','#36313e')),(7,QRectF(-40,-57,80,113),('#66596e','#2f2a3d')),(9,QRectF(-39,-57,78,111),('#b29cc8','#6e5c83'))]:
        layer(height);rounded(p,r,colors,32,'#292334');p.restore()
    layer(15)
    shell=QPainterPath();shell.moveTo(-34,-36);shell.cubicTo(-37,-62,33,-66,36,-37);shell.cubicTo(43,7,34,48,0,48);shell.cubicTo(-34,48,-41,5,-34,-36);shell.closeSubpath()
    grad=QRadialGradient(QPointF(-14,-1),72);grad.setColorAt(0,QColor('#e7e0ee'));grad.setColorAt(.55,QColor('#b8aac9'));grad.setColorAt(1,QColor('#695977'))
    p.setBrush(grad);p.setPen(QPen(QColor('#53435e'),1.4));p.drawPath(shell)
    # Separate sculpted left/right buttons and depression for each click.
    for button,x in [(1,-33),(2,3)]:
        down=button in buttons
        rect=QRectF(x,-49+(2 if down else 0),30,38)
        rounded(p,rect,('#d5bbef','#88629e') if down else ('#e8e2ef','#b1a0c2'),10,'#746181')
        p.setPen(QPen(QColor(255,255,255,150),1));p.drawLine(QPointF(x+6,-43),QPointF(x+22,-43))
    rounded(p,QRectF(-3,-40,6,22),('#403445','#18151f'),2)
    p.setPen(QPen(QColor('#c3afd5'),1))
    for y in range(-37,-20,4):p.drawLine(QPointF(-2,y),QPointF(2,y))
    # A subtle curved specular streak makes the palm shell read as a dome.
    path=QPainterPath(QPointF(-24,0));path.cubicTo(QPointF(-25,22),QPointF(-12,36),QPointF(0,37))
    p.setPen(QPen(QColor(255,255,255,105),2.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawPath(path)
    p.restore()
