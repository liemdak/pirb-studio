"""Short-lived contact lighting and restrained feather-like sparkles."""
import math
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QPen,QRadialGradient,QPainterPath

class Effects:
    def __init__(self):self.events=[];self.keys=[]
    def key(self,point,now):
        self.events.append(('key',QPointF(point),now));self.keys=[t for t in self.keys if now-t<.7]+[now]
        if len(self.keys)>=4:self.events.append(('spark',QPointF(point),now))
        self.events=self.events[-36:]
    def click(self,point,now):self.events=(self.events+[('click',QPointF(point),now)])[-36:]
    def draw(self,p,now,level,layer='all'):
        self.events=[e for e in self.events if now-e[2]<.85]
        if level=='off':return
        strength=.65 if level=='soft' else 1.
        for kind,point,born in self.events:
            if layer=='base' and kind=='spark':continue
            if layer=='spark' and kind!='spark':continue
            age=now-born
            if age<0:continue
            life=.85 if kind=='spark' else .5
            t=min(1,age/life);alpha=(1-t)**2
            if kind in ('key','click'):
                radius=(17+26*t) if kind=='key' else (24+34*t)
                center=point+QPointF(0,8 if kind=='key' else 0)
                glow=QRadialGradient(center,radius);glow.setColorAt(0,QColor(190,147,255,int(85*alpha*strength)));glow.setColorAt(1,QColor(151,106,245,0))
                p.setBrush(glow);p.setPen(Qt.PenStyle.NoPen);p.drawEllipse(center,radius,radius*.48)
                p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(223,200,255,int(130*alpha*strength)),1.4));p.drawEllipse(center,radius*.72,radius*.34)
                if level=='vivid':
                    p.setPen(QPen(QColor(235,201,133,int(110*alpha)),1.1));p.drawEllipse(center,radius*.96,radius*.45)
                    for i in range(3):
                        angle=i*math.tau/3+t*.9
                        tip=center+QPointF(math.cos(angle)*radius,math.sin(angle)*radius*.48)
                        tail=tip-QPointF(math.cos(angle)*5*(1-t),math.sin(angle)*3*(1-t))
                        p.setPen(QPen(QColor(239,216,168,int(170*alpha)),1.5));p.drawLine(tail,tip)
            else:
                for i in range(2 if level=='soft' else 4):
                    x=point.x()+(i-1)*13*(1+t);y=point.y()-t*(35+i*7)
                    size=2.5*(1-t);p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(238,215,255,int(170*alpha*strength)))
                    path=QPainterPath(QPointF(x,y-size*2));path.lineTo(x+size,y);path.lineTo(x,y+size*2);path.lineTo(x-size,y);path.closeSubpath();p.drawPath(path)
