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
from PySide6.QtGui import QPainterPath,QPolygonF,QTransform
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

    def test_table_shell_is_continuous_and_side_vectors_match_after_rotation(self):
        body=desk.desk_body_path()
        self.assertEqual(len(body.toFillPolygons()),1)
        a,b,c,d=desk.tabletop_corners()
        for start,end in ((d,c),(c,b)):
            self.assertTrue(body.contains((start+end)/2+QPointF(0,desk.DESK_DEPTH/2)))
        for angle in range(-180,181,15):
            transform=QTransform();transform.rotate(angle)
            aa,bb,cc,dd=[transform.map(p) for p in (a,b,c,d)]
            self.assertLess(((dd-aa)-(cc-bb)).manhattanLength(),1e-7)
        self.assertLessEqual(body.boundingRect().height(),desk.tabletop_path().boundingRect().height()+desk.DESK_DEPTH+.001)

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
