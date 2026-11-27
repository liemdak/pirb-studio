"""Final-device border and pressed-key regressions, including fractional DPI."""
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from PySide6.QtCore import Qt,QSettings,QCoreApplication,QEvent
from PySide6.QtGui import QImage,QPainter,QPixmap,QColor
from PySide6.QtWidgets import QApplication
import main
from devices import draw_keyboard
from skins import draw_rgb
from desk_geometry import desk_content_path,content_inset
from test_settings import SilentAudio


class RenderEdgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.settings=QSettings(self.temp.name+'/prefs.ini',QSettings.Format.IniFormat)
        with patch.object(main,'QSettings',lambda *_:self.settings),patch.object(main,'SoundEngine',SilentAudio):self.w=main.Companion(True)
        self.w.timer.stop()

    def tearDown(self):
        self.w.save();self.w.close();self.w.deleteLater()
        self.app.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.temp.cleanup()

    def test_pressed_cache_matches_fresh_complete_keyboard_instead_of_old_caps(self):
        for width,angle in ((180,-9),(320,-9),(600,-9),(600,30)):
            self.w.apply_preferences(dict(self.w.prefs,scene_width=width,scene_rotation=angle))
            self.w.prepare_screen_cache()
            for held,glow in (({65},{}),({27,112,113,114,32,13},{}),({k for _,k,_ in main.KEYS},{}),(set(),{65:1,32:1})):
                self.w.held=held;self.w.glow=glow
                actual=self.w.keyboard_screen()
                world=QPixmap(self.w.board_base);p=QPainter(world);p.setRenderHint(QPainter.RenderHint.Antialiasing)
                draw_keyboard(p,self.w.board,main.KEYS,self.w.keyrect,held,glow,draw_case=False);p.end()
                expected=self.w.screen_target();p=QPainter(expected)
                p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                p.setTransform(self.w.scene_mapping());p.setClipPath(desk_content_path(content_inset(p)))
                p.drawPixmap(0,0,world);p.end()
                # Region clipping may round one channel by one least-significant
                # bit; compare premultiplied pixels so transparent RGB is irrelevant.
                actual_image=actual.toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                expected_image=expected.toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                aa=bytes(actual_image.constBits());bb=bytes(expected_image.constBits())
                self.assertLessEqual(max(abs(a-b) for a,b in zip(aa,bb)),1,
                                     f'Raised-key remnants: {width}, {angle}, {held}')
                self.assertEqual(actual.cacheKey(),self.w.keyboard_screen().cacheKey())

    def test_all_four_outer_pixel_boundaries_remain_dark_with_rgb_and_pressed_keys(self):
        self.w.held={27,112,113,114,115,32,13};self.w.glow={}
        for dpr in (1.,1.25,1.5,2.):
            with patch.object(self.w,'devicePixelRatioF',return_value=dpr):
                for width in (180,600):
                    for angle in (-9,30):
                        for mode in ('off','purple','rainbow'):
                            self.w.apply_preferences(dict(self.w.prefs,scene_width=width,scene_rotation=angle,rgb=mode))
                            self.w.prepare_screen_cache();frame=QPixmap(self.w._screen_cache[0]);p=QPainter(frame)
                            if mode=='rainbow':
                                p.setTransform(self.w.scene_mapping());draw_rgb(p,self.w.board,mode,1.0);p.resetTransform()
                            p.drawPixmap(0,0,self.w.keyboard_screen());p.end()
                            image=frame.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                            data=bytes(image.constBits());stride=image.bytesPerLine();ww=image.width();hh=image.height()
                            tops=[None]*ww;bottoms=[None]*ww;boundary=set()
                            for y in range(hh):
                                alpha=data[y*stride+3:y*stride+ww*4:4]
                                xs=[x for x,a in enumerate(alpha) if a>=128]
                                if not xs:continue
                                boundary.update(((xs[0],y),(xs[-1],y)))
                                for x in xs:
                                    if tops[x] is None:tops[x]=y
                                    bottoms[x]=y
                            boundary.update((x,y) for x,y in enumerate(tops) if y is not None)
                            boundary.update((x,y) for x,y in enumerate(bottoms) if y is not None)
                            self.assertGreater(len(boundary),20)
                            for x,y in boundary:
                                offset=y*stride+x*4
                                self.assertLessEqual(max(data[offset:offset+3]),80,
                                    f'Bright edge fragment at {(x,y)}, width={width}, angle={angle}, DPI={dpr}, RGB={mode}')

    def test_white_custom_skin_cannot_produce_bright_border_fragments(self):
        path=self.temp.name+'/white.png'
        image=QImage(64,64,QImage.Format.Format_RGB32);image.fill(QColor('white'));image.save(path)
        self.w.apply_preferences(dict(self.w.prefs,skin='custom',custom_skin=path,brightness=100))
        self.test_all_four_outer_pixel_boundaries_remain_dark_with_rgb_and_pressed_keys()

    def test_monitor_dpi_change_rebuilds_the_final_resolution_cache(self):
        self.w.apply_preferences(dict(self.w.prefs,scene_width=320,scene_rotation=-9))
        with patch.object(self.w,'devicePixelRatioF',return_value=1.):
            self.w.prepare_screen_cache();old=self.w._screen_cache[0].cacheKey()
        with patch.object(self.w,'devicePixelRatioF',return_value=1.5):
            self.w.prepare_screen_cache();new=self.w._screen_cache[0]
            self.assertNotEqual(old,new.cacheKey())
            self.assertEqual(new.width(),math.ceil(self.w.width()*1.5))
            self.assertEqual(new.devicePixelRatio(),1.5)
            self.w.prepare_screen_cache();self.assertEqual(new.cacheKey(),self.w._screen_cache[0].cacheKey())

if __name__=='__main__':unittest.main()
