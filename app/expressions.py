"""Beak, cheek and emote animation. The head and torso stay positionally stable."""
import math
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QPainterPath,QColor,QPen,QLinearGradient

class Expressions:
    def __init__(self):
        self.event='calm';self.until=-1.;self.last_click=-10.;self.demo_until=-1.;self.demo_start=0.;self.mouth=0.;self.kind='calm';self.smile=0.;self.focus=0.;self.sleep=0.;self.emote=0.;self.wink=0.;self.yawn=0.;self.emote_kind='happy';self.hits=[]
    def key(self,now):
        self.hits=[t for t in self.hits if now-t<.8]+[now]
        self.event='excited' if len(self.hits)>=5 else 'focused';self.until=now+.7
    def click(self,now,button=1):
        self.event='wink' if button==2 else ('surprised' if now-self.last_click<.35 else 'happy')
        self.last_click=now;self.until=now+.85
    def coo(self,now):
        self.event='chirp';self.until=now+1.6
    def demo(self,now):
        self.demo_start=now;self.demo_until=now+6.
    def tick(self,now,dt,idle,mode='auto'):
        if now<self.demo_until:
            kind=('happy','focused','surprised','chirp','yawn','sleepy')[min(5,int(now-self.demo_start))]
        elif mode!='auto':kind=mode
        elif now<self.until:kind=self.event
        elif idle>18:
            kind='yawn' if (idle-18)%28<1.8 else 'sleepy'
        elif idle>8:kind='thinking'
        else:kind='calm'
        self.kind=kind
        if kind in ('happy','chirp','excited','surprised','wink'):self.emote_kind=kind
        target={'calm':0.,'focused':.15,'happy':.62,'surprised':.96,'sleepy':.05,'thinking':0.,'wink':.35,'excited':.75}.get(kind,0.)
        if kind=='chirp':target=.45+.35*(.5+.5*math.sin(now*15))
        if kind=='yawn':target=.90
        blend=1-math.exp(-max(0,dt)*13)
        self.mouth+=(target-self.mouth)*blend
        for name,desired in [('smile',1. if kind in ('happy','chirp','wink','excited') else 0.),('focus',1. if kind=='focused' else 0.),('sleep',1. if kind in ('sleepy','yawn') else 0.),('emote',1. if kind in ('happy','chirp','excited','surprised','wink') else 0.),('wink',1. if kind=='wink' else 0.),('yawn',1. if kind=='yawn' else 0.)]:setattr(self,name,getattr(self,name)+(desired-getattr(self,name))*blend)

def draw_expression(p,state,now):
    # A complete beak layer covers the old still beak, so the mouth has one outline.
    beak=QPainterPath(QPointF(79,190))
    beak.cubicTo(88,181,99,184,109,175)
    beak.cubicTo(123,165,131,158,144,158)
    beak.cubicTo(161,159,174,175,179,189)
    beak.cubicTo(182,198,187,198,195,202)
    beak.quadTo(204,208,195,215)
    beak.cubicTo(180,226,162,234,144,238)
    beak.cubicTo(121,244,102,232,91,216)
    beak.quadTo(85,207,82,200)
    beak.quadTo(75,197,79,190)
    gradient=QLinearGradient(105,179,174,249);gradient.setColorAt(0,QColor('#ffd18a'));gradient.setColorAt(.6,QColor('#ff9b49'));gradient.setColorAt(1,QColor('#ed8844'))
    p.setBrush(gradient);p.setPen(QPen(QColor('#573847'),3.4,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin));p.drawPath(beak)
    p.save();p.setClipPath(beak);shine=QPainterPath(QPointF(96,190));shine.cubicTo(119,173,136,170,148,175);p.setPen(QPen(QColor(255,244,201,120),2.2,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(shine);p.restore()
    gap=state.mouth*20
    mouth=QPainterPath(QPointF(89,200));mouth.cubicTo(102,218,111,216,124,211);mouth.cubicTo(147,203,171,202,194,209)
    if gap<.6:
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor('#6a3d40'),2.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawPath(mouth)
    else:
        mouth.cubicTo(176,210+gap*.9,127,219+gap*.8,89,200);mouth.closeSubpath()
        if state.kind in ('yawn','surprised'):
            mouth=QPainterPath();mouth.addEllipse(QRectF(128,211-gap*.2,34,6+gap))
        p.setPen(QPen(QColor('#663947'),1.5));p.setBrush(QColor('#563143'));p.drawPath(mouth)
        if gap>7:
            p.save();p.setClipPath(mouth);p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#dc8c96'));p.drawEllipse(QRectF(133,219+gap*.28,35,9));p.restore()
    if state.smile>.02 or state.kind=='surprised':
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(244,151,165,int(105*max(state.smile,.3 if state.kind=='surprised' else 0))))
        p.drawEllipse(QRectF(42,222,28,13));p.drawEllipse(QRectF(261,244,27,13))
    if state.focus>.03:
        p.setPen(QPen(QColor(88,66,91,int(255*state.focus)),2.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(38,133),QPointF(61,139));p.drawLine(QPointF(245,171),QPointF(272,167))
    if state.emote>.02 and state.emote_kind in ('happy','chirp','excited','wink'):
        p.save();p.setOpacity(state.emote)
        p.setPen(QPen(QColor('#f5da80'),2));p.setBrush(QColor('#f9e7aa'))
        for x,y,size in ((319,124,8),(336,147,5)):
            star=QPainterPath(QPointF(x,y-size));star.lineTo(x+size*.3,y-size*.3);star.lineTo(x+size,y);star.lineTo(x+size*.3,y+size*.3);star.lineTo(x,y+size);star.lineTo(x-size*.3,y+size*.3);star.lineTo(x-size,y);star.lineTo(x-size*.3,y-size*.3);star.closeSubpath();p.drawPath(star)
        p.restore()
    if state.kind in ('thinking','surprised','chirp'):
        p.setPen(QColor('#f4d885'));font=p.font();font.setPixelSize(26);font.setBold(True);p.setFont(font)
        p.drawText(QRectF(313,77,36,40),Qt.AlignmentFlag.AlignCenter,{'thinking':'?','surprised':'!','chirp':'♪'}[state.kind])
    if state.kind=='sleepy':
        p.setPen(QColor('#d5c0ef'));font=p.font();font.setPixelSize(19);font.setBold(True);p.setFont(font);p.drawText(QPointF(315,110),'z');font.setPixelSize(13);p.setFont(font);p.drawText(QPointF(338,92),'z')
