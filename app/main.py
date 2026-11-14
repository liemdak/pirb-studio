"""PIRB Studio: local transient input; no recording or networking."""
import sys, math, time, ctypes, random, json
from collections import OrderedDict
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSettings, QStandardPaths, QLockFile
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QPixmap, QIcon, QCursor, QTransform, QPolygonF, QLinearGradient, QRadialGradient, QRegion
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon, QMessageBox
from keyboard_geometry import KEYS
from devices import draw_keyboard, draw_mouse
from rig import draw_rig,chest_path
from preferences import load_preferences
from skins import desk_surface,draw_rgb,EDGE
from sound_engine import SoundEngine
from expressions import Expressions,draw_expression
from view import view_geometry,corner_position
from effects import Effects
from i18n import translate
from version import VERSION
CANVAS_H=720
ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))

def mix(a,b,t): return a+(b-a)*t

def blink(t, start, duration=.22):
    phase=(t-start)/duration
    return math.sin(math.pi*phase)**.6 if 0 < phase < 1 else 0.

class Companion(QWidget):
    def __init__(self,demo=False):
        super().__init__(); self.demo=demo; self.settings=QSettings('PIRBCompanion','Desktop')
        if not self.settings.contains('preferences'):
            previous=QSettings('PIRBCompanion','Desktop05')
            for key in ('preferences','width','x','y'):
                if previous.contains(key):self.settings.setValue(key,previous.value(key))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.Tool|Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.root=ROOT;self.prefs=load_preferences(self.settings);self.desk_cache=None;self.settings_dialog=None
        self.audio=SoundEngine(ROOT,self.prefs,self)
        self._view_transform=QTransform();self._render_scale=1.;self._scene_center=None;self._mouse_cache={};self.effects=Effects()
        self.move(int(self.settings.value('x',60)),int(self.settings.value('y',80)))
        self.head=QPixmap(str(ROOT/'assets/head_hd.png'));self.head.setDevicePixelRatio(3);self.body=self.head
        if self.head.isNull() or self.body.isNull(): raise RuntimeError('Missing PIRB assets. Extract the entire ZIP before starting.')
        self.rig=json.loads((ROOT/'assets/rig.json').read_text())
        self.held=set(); self.glow={}; self.buttons=set(); self.drag=None; self.locked=False; self.paused=False; self.clickthrough=False
        self.t0=time.monotonic(); self.last_activity=self.t0; self.blink_at=self.t0+2.4
        self.expression=Expressions();self.audio.birdTriggered.connect(lambda:self.expression.coo(time.monotonic()))
        self.eye_close=0.; self.gaze=QPointF(); self.lift=-12.; self.mouse_press=0.
        self.board=QTransform(-.94,-.16,.43,-.78,865,611)
        self.board_base=None;self.board_idle=None;self._screen_cache=None
        self.target=QPointF(650,467); self.tip=QPointF(self.target); self.tap_at=-100.
        self.mousepos=QPointF(245,420); self.frame_time=self.t0
        self.user32=ctypes.windll.user32 if sys.platform=='win32' else None
        if self.user32:
            self.user32.GetAsyncKeyState.argtypes=[ctypes.c_int]; self.user32.GetAsyncKeyState.restype=ctypes.c_short
        elif not demo: raise RuntimeError('This app runs on Windows. Use --demo on other systems.')
        self.keyboard=None
        if self.user32:
            from windows_input import KeyboardInput
            self.keyboard=KeyboardInput()
        self.tray=QSystemTrayIcon(QIcon(self.head),self); self.tray.setToolTip('PIRB Studio '+VERSION); self.tray.setContextMenu(self.menu()); self.tray.show()
        self.update_view_layout()
        self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(16)
    def menu(self):
        tr=lambda text:translate(text,self.prefs.get('language','vi'))
        m=QMenu()
        m.addAction(tr('Giao diện & âm thanh…'),self.show_settings)
        m.addSeparator()
        m.addAction(tr('Tạm dừng / tiếp tục'),self.pause); m.addAction(tr('Khóa / mở vị trí'),self.lock)
        m.addAction(tr('Bấm xuyên / tương tác'),self.toggle_through)
        for size in (240,360,600,800):m.addAction(tr('Cỡ cảnh {size}px').format(size=size),lambda checked=False,s=size:self.set_view(scene_width=s))
        m.addAction(tr('Canh bàn ngang mép màn hình'),lambda:self.set_view(scene_rotation=-9))
        m.addAction(tr('Về góc xoay 0°'),lambda:self.set_view(scene_rotation=0))
        m.addAction(tr('Hiện / ẩn'),lambda:self.setVisible(not self.isVisible()))
        m.addAction(tr('Thoát'),QApplication.instance().quit); return m
    def show_settings(self):
        from settings_dialog import SettingsDialog
        if self.settings_dialog is not None:self.settings_dialog.close();self.settings_dialog.deleteLater()
        self.settings_dialog=SettingsDialog(self)
        self.settings_dialog.show();self.settings_dialog.raise_();self.settings_dialog.activateWindow()
    def apply_preferences(self,prefs):
        old=self.prefs
        if any(old.get(k)!=prefs.get(k) for k in ('skin','custom_skin','brightness','zoom','pan_x','pan_y','skin_rotation')):self.desk_cache=None;self._screen_cache=None
        if old['rgb']!=prefs['rgb']:self.board_base=None;self.board_idle=None;self._screen_cache=None
        view_changed=any(old.get(k)!=prefs.get(k) for k in ('scene_width','scene_rotation','dock','bird_scale','bird_tilt','bird_x','bird_y'))
        self.prefs=dict(prefs)
        if old.get('language')!=prefs.get('language'):
            previous=self.tray.contextMenu();self.tray.setContextMenu(self.menu())
            if previous:previous.deleteLater()
        if view_changed:
            pose_only=not any(old.get(k)!=prefs.get(k) for k in ('scene_width','scene_rotation','dock'))
            self.update_view_layout(QPointF(600,570) if pose_only else None)
        self.settings.setValue('preferences',json.dumps(self.prefs,ensure_ascii=False))
        if any(old[k]!=prefs[k] for k in ('sound_pack','keyboard_sound','mouse_sound','pirb_sound','keyboard_volume','mouse_volume','pirb_volume')):self.audio.configure(self.prefs)
        self.update()
    def set_view(self,**values):
        prefs=dict(self.prefs);prefs.update(values);self.apply_preferences(prefs)
    def visual_outline(self):
        points=[point+QPointF(0,70) for point in EDGE];pose=self.character_transform()
        for rect in (QRectF(365,18,365,303),chest_path().boundingRect()):
            points.extend(pose.map(point)+QPointF(0,70) for point in (rect.topLeft(),rect.topRight(),rect.bottomRight(),rect.bottomLeft()))
        return QPolygonF(points)
    def update_view_layout(self,anchor=None):
        self._screen_cache=None
        screen=QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen();available=screen.availableGeometry()
        old_anchor=QPointF(self.pos())+self._view_transform.map(anchor) if anchor is not None else None
        self._view_transform,width,height,self._render_scale=view_geometry(self.prefs['scene_rotation'],self.prefs['scene_width'],available,self.visual_outline())
        if self._scene_center is None:self._scene_center=QPointF(self.x()+width/2,self.y()+height/2)
        self.resize(width,height)
        if self.prefs['dock']!='free':
            self.move(corner_position(available,(width,height),self.prefs['dock']));self._scene_center=QPointF(self.x()+width/2,self.y()+height/2)
        else:
            if old_anchor is not None:self._scene_center=old_anchor-self._view_transform.map(anchor)+QPointF(width/2,height/2)
            wanted_x=round(self._scene_center.x()-width/2);wanted_y=round(self._scene_center.y()-height/2)
            x=max(available.left(),min(available.right()-width+1,wanted_x));y=max(available.top(),min(available.bottom()-height+1,wanted_y))
            self.move(x,y)
            if x!=wanted_x:self._scene_center.setX(x+width/2)
            if y!=wanted_y:self._scene_center.setY(y+height/2)
    def wheelEvent(self,e):
        step=1 if e.angleDelta().y()>0 else -1
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_view(scene_width=max(180,min(1200,self.prefs['scene_width']+step*20)));e.accept()
        elif e.modifiers() & Qt.KeyboardModifier.AltModifier:
            self.set_view(scene_rotation=max(-180,min(180,self.prefs['scene_rotation']+step*2)));e.accept()
        else:e.ignore()
    def pause(self):
        self.paused=not self.paused; self.held.clear(); self.buttons.clear(); self.glow.clear()
    def lock(self): self.locked=not self.locked
    def toggle_through(self):
        self.clickthrough=not self.clickthrough
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput,self.clickthrough); self.show()
    def keyrect(self,r): return QRectF(r.x()*24,r.y()*28,r.width()*24-2.6,r.height()*28-2.6)
    def keypoint(self,r): return self.board.map(self.keyrect(r).center())+QPointF(0,-20)
    def tick(self):
        now=time.monotonic(); dt=min(.08,now-self.frame_time); self.frame_time=now; held=set(); buttons=set(); gaze=QPointF(); presses=[]
        if self.keyboard:
            state,presses=self.keyboard.consume()
        if self.demo and not self.paused:
            elapsed=now-self.t0
            if elapsed%10 < 7: held={ord('CHATGPT'[int(elapsed*7)%7])} if elapsed%(1/7)<.09 else set()
            else: buttons={1} if elapsed%.6<.18 else set()
            gaze=QPointF(math.sin(elapsed*.8),math.cos(elapsed*.6)*.5)
        elif self.user32 and not self.paused:
            held=state
            buttons={b for b in (1,2,4) if self.user32.GetAsyncKeyState(b)&0x8000}
            rect=QApplication.primaryScreen().virtualGeometry(); pos=QCursor.pos()
            gaze=QPointF(max(-1,min(1,(pos.x()-rect.center().x())/(rect.width()/2))),max(-1,min(1,(pos.y()-rect.center().y())/(rect.height()/2))))
        new=(held-self.held)|set(presses) if not self.paused else set()
        if new or buttons or (gaze-self.gaze).manhattanLength()>.02:self.last_activity=now
        # Preserve event order: the wing reaches the last physical key received.
        ordered=presses if presses and not self.paused else sorted(new)
        for vk in new: self.glow[vk]=now+.18
        for vk in ordered:
            for label,code,r in KEYS:
                if vk==code:
                    self.target=self.keypoint(r); self.tap_at=now; break
        if ordered:
            self.expression.key(now)
            for vk in ordered:
                for _,code,r in KEYS:
                    if code==vk:self.effects.key(self.keypoint(r),now);break
        if buttons-self.buttons:
            self.expression.click(now,2 if 2 in buttons-self.buttons else 1);self.effects.click(self.mousepos,now)
        if not self.paused and not self.demo:
            for vk in ordered:self.audio.key(vk)
            if buttons-self.buttons:self.audio.mouse()
            self.audio.idle(now,now-self.last_activity)
        self.held=held; self.buttons=buttons; self.glow={k:v for k,v in self.glow.items() if v>now}
        self.gaze=mix(self.gaze,gaze,1-math.exp(-dt*11))
        self.mousepos=QPointF(245+self.gaze.x()*27+self.gaze.y()*9,420+self.gaze.x()*5+self.gaze.y()*15)
        if now-self.last_activity>2: self.target=self.keypoint(KEYS[45][2])
        # Time-based smoothing gives the same response at different refresh rates.
        self.tip=mix(self.tip,self.target,1-math.exp(-dt*32))
        self.eye_close=blink(now,self.blink_at)
        if now>self.blink_at+.24: self.blink_at=now+random.uniform(2.3,5.3)
        idle=now-self.last_activity>12
        if idle and self.prefs['expression']=='auto': self.eye_close=max(self.eye_close,.35+.08*math.sin(now))
        self.lift=mix(self.lift,5. if held else -12.,1-math.exp(-dt*28))
        self.mouse_press=mix(self.mouse_press,3. if buttons else 0.,1-math.exp(-dt*30))
        self.expression.tick(now,dt,now-self.last_activity,self.prefs['expression'])
        self.eye_close=max(self.eye_close,self.expression.sleep*.45,self.expression.yawn*.86)
        self.eye_close=max(self.eye_close,self.expression.smile*.12)
        self.update()
    def eye(self,p,box,close,color):
        x,y,w,h=box;r=QRectF(x,y,w,h)
        # Erase the entire baked eye, including its old contour, before blinking.
        patch=QLinearGradient(x,y,x+w,y+h)
        patch.setColorAt(0,QColor('#9499b4' if x<100 else '#929bb8'));patch.setColorAt(1,QColor('#a1aac4'))
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(patch);p.drawEllipse(r.adjusted(-6,-6,6,6))
        closed=close
        if x>100:closed=max(closed,self.expression.wink*.99)
        center=r.center();height=max(2.2,h*(1-closed)**1.1);visible=QRectF(x,center.y()-height/2,w,height)
        if closed>.95:
            path=QPainterPath(QPointF(x+2,center.y()));path.quadTo(QPointF(center.x(),center.y()+5),QPointF(x+w-2,center.y()-1))
            p.setPen(QPen(QColor('#3f344f'),2.4,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path);return
        shadow=visible.translated(0,2);p.setBrush(QColor(50,42,68,32));p.drawEllipse(shadow)
        white=QLinearGradient(visible.topLeft(),visible.bottomRight());white.setColorAt(0,QColor('#fffef6'));white.setColorAt(1,QColor('#e2e4ed'))
        p.setBrush(white);p.setPen(QPen(QColor('#4d3b58'),1.8));p.drawEllipse(visible)
        p.save();clip=QPainterPath();clip.addEllipse(visible);p.setClipPath(clip)
        cx=center.x()+self.gaze.x()*w*.11;cy=center.y()+self.gaze.y()*h*.08
        iris=QRadialGradient(QPointF(cx-w*.1,cy-h*.15),w*.47);iris.setColorAt(0,QColor('#ffcf77'));iris.setColorAt(.6,QColor('#e8983f'));iris.setColorAt(1,QColor('#9d592d'))
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(iris);p.drawEllipse(QRectF(cx-w*.31,cy-h*.39,w*.62,h*.78))
        p.setBrush(QColor('#292431'));p.drawEllipse(QRectF(cx-w*.15,cy-h*.29,w*.30,h*.58))
        p.setBrush(QColor('#fffef9'));p.drawEllipse(QRectF(cx-w*.18,cy-h*.28,w*.18,h*.17));p.setBrush(QColor(255,255,255,170));p.drawEllipse(QRectF(cx+w*.08,cy+h*.12,w*.07,h*.07))
        p.restore();p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(255,255,255,95),.8));p.drawArc(visible.adjusted(1,1,-1,-1),5*16,165*16)
    def ensure_board_cache(self):
        if self.board_base is None:
            self.board_base=QPixmap(2000,1300);self.board_base.setDevicePixelRatio(2);self.board_base.fill(Qt.GlobalColor.transparent)
            cache=QPainter(self.board_base);cache.setRenderHint(QPainter.RenderHint.Antialiasing)
            draw_keyboard(cache,self.board,KEYS,self.keyrect,set(),{},draw_caps=False,backlight=self.prefs['rgb']!='off');cache.end()
            self.board_idle=QPixmap(self.board_base)
            cache=QPainter(self.board_idle);cache.setRenderHint(QPainter.RenderHint.Antialiasing)
            draw_keyboard(cache,self.board,KEYS,self.keyrect,set(),{},draw_case=False);cache.end()
    def scene_mapping(self):
        mapping=QTransform(self._view_transform);mapping.translate(0,70);return mapping
    def prepare_screen_cache(self):
        if self._screen_cache is not None:return
        self.ensure_board_cache()
        if self.desk_cache is None:self.desk_cache=desk_surface(ROOT,self.prefs)
        result=[];dpr=self.devicePixelRatioF()
        for index,source in enumerate((self.desk_cache,self.board_idle,self.board_base)):
            target=QPixmap(math.ceil(self.width()*dpr),math.ceil(self.height()*dpr));target.setDevicePixelRatio(dpr);target.fill(Qt.GlobalColor.transparent)
            cache=QPainter(target);cache.setRenderHint(QPainter.RenderHint.Antialiasing);cache.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);cache.setTransform(self.scene_mapping());cache.drawPixmap(0,0,source)
            if index==0 and self.prefs['rgb']=='purple':draw_rgb(cache,self.board,'purple',0)
            cache.end();result.append(target)
        self._screen_cache=result;self._keyboard_state_cache=OrderedDict()
    def keyboard_screen(self):
        state=tuple(sorted(self.held|set(self.glow)))
        if not state:return self._screen_cache[1]
        if state in self._keyboard_state_cache:
            self._keyboard_state_cache.move_to_end(state);return self._keyboard_state_cache[state]
        frame=QPixmap(self._screen_cache[1]);cache=QPainter(frame);cache.setRenderHint(QPainter.RenderHint.Antialiasing);cache.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);self.keyboard_active(cache);cache.end()
        self._keyboard_state_cache[state]=frame
        budget=max(2,min(8,24*1024*1024//max(1,frame.width()*frame.height()*4)))
        while len(self._keyboard_state_cache)>budget:self._keyboard_state_cache.popitem(last=False)
        return frame
    def keyboard_active(self,p):
        active=self.held|set(self.glow)
        if not active:return
        region=QRegion()
        for _,vk,r in KEYS:
            if vk in active:region=region.united(QRegion(self.board.mapRect(self.keyrect(r)).adjusted(-3,-23,3,3).toAlignedRect()))
        screen_region=self.scene_mapping().map(region)
        # Restore the already-transformed plate and redraw only clipped neighbours.
        p.save();p.setClipRegion(screen_region);p.drawPixmap(0,0,self._screen_cache[2]);p.setTransform(self.scene_mapping())
        draw_keyboard(p,self.board,KEYS,self.keyrect,self.held,self.glow,draw_case=False,clip_region=region)
        p.restore()
    def draw_mouse_cached(self,p):
        state=tuple(sorted(self.buttons & {1,2}))
        if state not in self._mouse_cache:
            pixmap=QPixmap(360,360);pixmap.setDevicePixelRatio(2);pixmap.fill(Qt.GlobalColor.transparent)
            cache=QPainter(pixmap);cache.setRenderHint(QPainter.RenderHint.Antialiasing);cache.translate(90,90);draw_mouse(cache,QPointF(),set(state));cache.end();self._mouse_cache[state]=pixmap
        p.drawPixmap(self.mousepos-QPointF(90,90),self._mouse_cache[state])
    def character_transform(self):
        def build(dx=0,dy=0):
            pose=QTransform();pose.translate(550+self.prefs['bird_x']+dx,420+self.prefs['bird_y']+dy)
            pose.rotate(self.prefs['bird_tilt']);pose.scale(self.prefs['bird_scale']/100,self.prefs['bird_scale']/100);pose.translate(-550,-420)
            return pose
        pose=build();head=pose.mapRect(QRectF(365,18,365,303))
        dx=max(0,10-head.left())-max(0,head.right()-990)
        dy=max(0,-60-head.top())
        return build(dx,dy)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.prepare_screen_cache()
        p.drawPixmap(0,0,self._screen_cache[0])
        p.save();p.setTransform(self.scene_mapping());
        if self.prefs['rgb']=='rainbow':draw_rgb(p,self.board,'rainbow',time.monotonic()-self.t0)
        p.restore()
        p.drawPixmap(0,0,self.keyboard_screen())
        p.setTransform(self.scene_mapping())
        self.draw_mouse_cached(p)
        self.effects.draw(p,time.monotonic(),self.prefs['effects'],'base')
        # Enlarge the connected rig about its chest, keeping both device contacts fixed.
        pose=self.character_transform();inverse,ok=pose.inverted()
        mouse_contact=self.mousepos+QPointF(10,-33+self.mouse_press);key_contact=self.tip+QPointF(0,self.lift)
        p.save();p.setTransform(pose,True)
        draw_rig(p,inverse.map(mouse_contact),inverse.map(key_contact))
        p.save();p.translate(365,18)
        # Follow the feathered head edge so the old torso crop cannot form a seam.
        head_clip=QPainterPath(QPointF(0,0));head_clip.lineTo(365,0);head_clip.lineTo(365,242)
        head_clip.cubicTo(338,255,312,271,285,282)
        head_clip.cubicTo(259,298,222,306,180,302)
        head_clip.cubicTo(135,298,91,286,60,272)
        head_clip.cubicTo(35,257,13,245,0,235);head_clip.closeSubpath()
        p.setClipPath(head_clip)
        p.drawPixmap(0,0,self.head)
        for r in self.rig['eyes']:self.eye(p,r,self.eye_close,self.rig['skin'])
        draw_expression(p,self.expression,time.monotonic())
        p.restore()
        p.restore()
        self.effects.draw(p,time.monotonic(),self.prefs['effects'],'spark')
        p.end()
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.RightButton: self.menu().exec(e.globalPosition().toPoint())
        elif e.button()==Qt.MouseButton.LeftButton and not self.locked:
            self.prefs['dock']='free';self.drag=e.globalPosition().toPoint()-self.pos()
    def mouseMoveEvent(self,e):
        if self.drag is not None: self.move(e.globalPosition().toPoint()-self.drag)
    def mouseReleaseEvent(self,e):
        self.drag=None;self._scene_center=QPointF(self.x()+self.width()/2,self.y()+self.height()/2);self.settings.setValue('preferences',json.dumps(self.prefs,ensure_ascii=False))
    def save(self):
        if self.settings_dialog:self.settings_dialog.close()
        self.audio.close()
        if self.keyboard: self.keyboard.close()
        for k,v in [('width',self.width()),('x',self.x()),('y',self.y())]: self.settings.setValue(k,v)
        self.settings.sync()
        self.tray.hide()

if __name__=='__main__':
    app=QApplication(sys.argv);app.setOrganizationName("PIRBCommunity");app.setApplicationName("PIRBDesktop");app.setApplicationVersion(VERSION); app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(str(ROOT/'assets/head_hd.png')))
    instance_dir=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation));instance_dir.mkdir(parents=True,exist_ok=True)
    instance_lock=QLockFile(str(instance_dir/'pirb-instance.lock'))
    if not instance_lock.tryLock(0):
        prefs=load_preferences(QSettings('PIRBCompanion','Desktop'))
        QMessageBox.information(None,'PIRB',translate('PIRB đang chạy. Hãy mở menu biểu tượng PIRB cạnh đồng hồ.',prefs['language']));sys.exit(0)
    app.aboutToQuit.connect(instance_lock.unlock)
    w=Companion('--demo' in sys.argv or '--snapshot' in sys.argv); app.aboutToQuit.connect(w.save); w.show()
    if '--snapshot' in sys.argv:
        def snapshot(): w.grab().save(str(ROOT/'preview.png')); app.quit()
        QTimer.singleShot(500,snapshot)
    sys.exit(app.exec())
