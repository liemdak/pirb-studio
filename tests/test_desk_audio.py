"""Tabletop projection and custom-sound import/routing regressions."""
import json
import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from PySide6.QtCore import QPointF,QSettings
from PySide6.QtGui import QPainterPath,QPolygonF,QTransform,QPainterPathStroker,QPainter,QImage
from PySide6.QtWidgets import QApplication
import custom_audio as audio
import desk_geometry as desk
import preferences
import skins


def make_wav(path,seconds=.05,channels=1):
    with wave.open(str(path),'wb') as sound:
        sound.setnchannels(channels);sound.setsampwidth(2);sound.setframerate(44100)
        sound.writeframes(b'\0\0'*int(seconds*44100)*channels)
    return path


class DeskAndAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_table_and_keyboard_have_shared_axes_and_texture_corners(self):
        projection=desk.texture_projection();back_left,back_right,front_right,front_left=desk.tabletop_corners()
        for source,target in zip((QPointF(0,0),QPointF(1000,0),QPointF(1000,600),QPointF(0,600)),(back_left,back_right,front_right,front_left)):
            self.assertLess((projection.map(source)-target).manhattanLength(),1e-8)
        board=desk.keyboard_projection();inverse,_=board.inverted()
        for point in desk.tabletop_corners():self.assertTrue(desk.DESK_RECT.adjusted(-.001,-.001,.001,.001).contains(inverse.map(point)))
        # Seen from the back towards the front, both planes run down and left.
        self.assertLess(front_left.x(),back_left.x());self.assertGreater(front_left.y(),back_left.y())
        shape=QPainterPath();shape.addPolygon(QPolygonF(desk.tabletop_corners()))
        self.assertTrue(shape.contains(QPointF(245,420)))

    def test_whole_outer_body_has_four_corners_and_both_opposite_pairs_match(self):
        body=desk.desk_body_path();polygon=body.toFillPolygon()
        self.assertEqual(len({(round(p.x(),7),round(p.y(),7)) for p in polygon}),4)
        self.assertEqual(len(desk.desk_outline()),4)
        self.assertEqual(body.boundingRect(),desk.tabletop_path().boundingRect())
        self.assertLess(desk.front_fascia_path().subtracted(body).boundingRect().width(),1e-6)
        for angle in range(-180,181,15):
            for scale in (.18,.32,.6,1.2):
                transform=QTransform();transform.rotate(angle);transform.scale(scale,scale)
                a,b,c,d=[transform.map(p) for p in desk.desk_outline()]
                self.assertLess(((b-a)-(c-d)).manhattanLength(),1e-7)
                self.assertLess(((d-a)-(c-b)).manhattanLength(),1e-7)

    def test_actual_table_and_rgb_pixels_stay_inside_the_four_corner_outline(self):
        root=Path(__file__).resolve().parents[1]/'app'
        stroke=QPainterPathStroker();stroke.setWidth(1.5)
        shape=desk.desk_body_path();allowed=shape.united(stroke.createStroke(shape))
        for mode in ('off','purple','rainbow'):
            layer=skins.desk_surface(root,dict(preferences.DEFAULTS))
            painter=QPainter(layer);skins.draw_rgb(painter,desk.keyboard_projection(),mode,1.0);painter.end()
            image=layer.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            data=bytes(image.constBits());stride=image.bytesPerLine();dpr=layer.devicePixelRatio()
            for y in range(image.height()):
                alpha=data[y*stride+3:y*stride+image.width()*4:4]
                painted=[x for x,value in enumerate(alpha) if value>32]
                if not painted:continue
                for x in (painted[0],painted[-1]):
                    self.assertTrue(allowed.contains(QPointF((x+.5)/dpr,(y+.5)/dpr)),
                                    f'{mode}: visible pixel outside outline at {(x,y)}')

    def test_surface_is_not_clipped_and_old_images_still_render(self):
        root=Path(__file__).resolve().parents[1]/'app'
        for skin in ('pyth_classic','fuji_sakura','none'):
            image=skins.desk_surface(root,dict(preferences.DEFAULTS,skin=skin))
            for corner in desk.desk_outline():
                self.assertTrue(0<=corner.x()<image.width()/image.devicePixelRatio())
                self.assertTrue(0<=corner.y()<image.height()/image.devicePixelRatio())
            self.assertFalse(image.isNull())

    def test_import_copies_valid_sound_and_survives_source_removal(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);source=make_wav(folder/'my click.wav');expected=source.read_bytes()
            copied=Path(audio.import_sound(source,folder/'app-data'))
            self.assertEqual(copied.read_bytes(),expected)
            self.assertEqual(audio.import_sound(source,folder/'app-data'),str(copied))
            source.unlink();audio.validate_wav(copied)

    def test_invalid_long_large_and_truncated_sounds_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            invalid=folder/'fake.wav';invalid.write_bytes(b'not an audio file')
            long=make_wav(folder/'long.wav',3.1)
            truncated=make_wav(folder/'truncated.wav');truncated.write_bytes(truncated.read_bytes()[:-20])
            large=folder/'large.wav';large.write_bytes(b'\0'*(audio.MAX_BYTES+1))
            for sample in (invalid,long,truncated,large):
                with self.subTest(sample=sample.name),self.assertRaises(ValueError):audio.import_sound(sample,folder/'stored')
            self.assertFalse(list((folder/'stored').glob('*.wav')))

    def test_custom_key_fallback_does_not_override_unassigned_mouse(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);key=make_wav(root/'key.wav');space=make_wav(root/'space.wav')
            prefs=dict(preferences.DEFAULTS,sound_pack='custom',custom_sounds={'key_press.wav':str(key),'space_press.wav':str(space)})
            self.assertEqual(audio.sound_path(root,prefs,'space_press.wav'),space)
            self.assertEqual(audio.sound_path(root,prefs,'enter_press.wav'),key)
            self.assertEqual(audio.sound_path(root,prefs,'mouse_press.wav'),root/'assets/sounds/thock/mouse_press.wav')
            space.unlink();self.assertEqual(audio.sound_path(root,prefs,'space_press.wav'),key)
            prefs['sound_pack']='clicky';self.assertEqual(audio.sound_path(root,prefs,'key_press.wav'),root/'assets/sounds/clicky/key_press.wav')

    def test_old_visual_choices_and_custom_sounds_persist_without_namespace_change(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=QSettings(str(Path(temp)/'prefs.ini'),QSettings.Format.IniFormat)
            old={'skin':'fuji_sakura','skin_rotation':180,'bird_tilt':7,'keyboard_volume':31,'language':'en'}
            settings.setValue('preferences',json.dumps(old));loaded=preferences.load_preferences(settings)
            for key,value in old.items():self.assertEqual(loaded[key],value)
            loaded.update(sound_pack='custom',custom_sounds={'key_press.wav':'/local/key.wav','unknown':'/bad.wav'})
            settings.setValue('preferences',json.dumps(loaded));loaded=preferences.load_preferences(settings)
            self.assertEqual(loaded['custom_sounds'],{'key_press.wav':'/local/key.wav'})
            settings.setValue('preferences',json.dumps({'custom_sounds':False,'skin':'missing'}))
            loaded=preferences.load_preferences(settings);self.assertEqual(loaded['custom_sounds'],{});self.assertEqual(loaded['skin'],'pyth_classic')

if __name__=='__main__':unittest.main()
