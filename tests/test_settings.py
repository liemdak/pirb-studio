"""User-facing language/persistence and scene regression tests (offscreen Qt)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from PySide6.QtCore import QObject, Signal, QSettings, QRect, QPointF
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QTabWidget, QLabel, QPushButton, QCheckBox
import main
import preferences
import settings_dialog
import view
import rig
from i18n import EN


class SilentAudio(QObject):
    birdTriggered = Signal()
    available = False
    def __init__(self, *args): super().__init__()
    def configure(self, *args): pass
    def close(self): pass
    def preview(self, *args): pass
    def mouse(self, *args): pass
    def bird(self, *args): pass


class FakeKeyboard:
    def consume(self): return set(), []
    def close(self): pass


class SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = QSettings(str(Path(self.temp.name) / 'prefs.ini'), QSettings.Format.IniFormat)
        self.patches = [patch.object(main, 'QSettings', lambda *_: self.settings),
                        patch.object(main, 'SoundEngine', SilentAudio)]
        if sys.platform == 'win32':
            import windows_input
            self.patches.append(patch.object(windows_input, 'KeyboardInput', FakeKeyboard))
        for p in self.patches: p.start()
        self.w = main.Companion(True)
        self.w.timer.stop()
        self.w.show_settings()
        self.d = self.w.settings_dialog
        self.d.preview_timer.stop()
        self.app.processEvents()

    def tearDown(self):
        self.w.save()
        self.d.close()
        self.w.close()
        self.d.deleteLater()
        self.w.deleteLater()
        self.app.processEvents()
        for p in reversed(self.patches): p.stop()
        self.settings.sync()
        self.temp.cleanup()

    def language(self, language):
        self.d.language.setCurrentIndex(self.d.language.findData(language))
        self.app.processEvents()

    def test_round_trip_preserves_all_values(self):
        self.d.scene_preset(320, -9, 'bottom_right')
        self.d.controls['keyboard_volume'].setValue(43)
        self.d.rgb.setCurrentIndex(self.d.rgb.findData('rainbow'))
        before = dict(self.w.prefs)
        for language, expected in [('en', 'Position & size'), ('vi', 'Vị trí & kích thước'), ('en', 'Position & size')]:
            self.language(language)
            self.assertEqual(self.d.findChild(QTabWidget).tabText(0), expected)
            self.assertEqual({k: v for k, v in self.w.prefs.items() if k != 'language'},
                             {k: v for k, v in before.items() if k != 'language'})
        self.settings.sync()
        loaded = preferences.load_preferences(self.settings)
        self.assertEqual(loaded, self.w.prefs)
        other = settings_dialog.SettingsDialog(self.w)
        self.assertEqual(other.language.currentData(), 'en')
        self.assertEqual(other.findChild(QTabWidget).tabText(2), 'Sound')
        other.preview_timer.stop(); other.close(); other.deleteLater()

    def test_full_catalog_and_menu(self):
        self.language('en')
        self.assertEqual(self.w.tray.contextMenu().actions()[0].text(), 'Appearance & sound…')
        menu=self.w.menu()
        self.assertEqual(menu.actions()[-1].text(), 'Exit')
        for widget in self.d.findChildren(QLabel) + self.d.findChildren(QPushButton) + self.d.findChildren(QCheckBox):
            source = widget.property('source_text')
            if source and any(ord(c) > 255 for c in source) and source != 'Ngôn ngữ / Language':
                self.assertIn(source, EN, source)
                self.assertEqual(widget.text(), EN[source])
        self.assertEqual(self.d.controls['bird_tilt'].accessibleName(), 'PIRB tilt')

    def test_dynamic_custom_image_and_controls_after_switch(self):
        self.language('en')
        image = Path(self.temp.name) / 'desk.png'
        q = QImage(32, 32, QImage.Format.Format_RGB32); q.fill(0xff998877); q.save(str(image))
        with patch.object(settings_dialog.QFileDialog, 'getOpenFileName', return_value=(str(image), '')), \
             patch.object(settings_dialog, 'import_skin', return_value=str(image)):
            self.d.choose_image()
        self.assertEqual(self.d.skin.currentText(), 'Your image')
        self.assertEqual(self.w.prefs['skin'], 'custom')
        self.language('vi'); self.assertEqual(self.d.skin.currentText(), 'Ảnh của bạn')
        self.language('en'); self.assertEqual(self.d.skin.currentText(), 'Your image')
        self.d.controls['scene_rotation'].setValue(41)
        self.assertEqual(self.w.prefs['scene_rotation'], 41)
        check = self.d.controls['mouse_sound']; check.setChecked(not check.isChecked())
        self.assertEqual(self.w.prefs['mouse_sound'], check.isChecked())

    def test_layouts_fit_both_languages(self):
        for language in ('vi', 'en'):
            self.language(language)
            for size in ((740, 850), (660, 620)):
                self.d.resize(*size)
                tabs = self.d.findChild(QTabWidget)
                for index in range(tabs.count()):
                    tabs.setCurrentIndex(index); self.app.processEvents(); self.d.update_preview()
                    self.assertEqual(tabs.widget(index).horizontalScrollBar().maximum(), 0)
                    self.assertFalse(self.d.grab().isNull())

    def test_scene_and_wing_contact_regression(self):
        for screen in (QRect(0, 0, 1920, 1080), QRect(-1280, 0, 1280, 720), QRect(0, 0, 800, 600)):
            for angle in range(-180, 181, 15):
                for width in (180, 240, 600, 1200):
                    transform, ww, hh, _ = view.view_geometry(angle, width, screen, self.w.visual_outline())
                    self.assertTrue(transform.isInvertible())
                    self.assertLessEqual(ww, screen.width() - 14)
                    self.assertLessEqual(hh, screen.height() - 14)
                    for point in self.w.visual_outline():
                        p = transform.map(point)
                        self.assertTrue(0 <= p.x() <= ww and 0 <= p.y() <= hh)
        for tilt in (-18, 0, 18):
            self.w.apply_preferences(dict(self.w.prefs, bird_tilt=tilt))
            pose = self.w.character_transform(); inverse, _ = pose.inverted()
            for _, _, rect in main.KEYS:
                key = self.w.keypoint(rect); mouse = QPointF(255, 387)
                shape = rig.silhouette(inverse.map(mouse), inverse.map(key))
                self.assertEqual(len(shape.toFillPolygons()), 1)
                self.assertLess((pose.map(inverse.map(key)) - key).manhattanLength(), 1e-7)

    def test_old_preferences_migrate_and_bad_language_falls_back(self):
        self.settings.setValue('preferences', json.dumps({'scene_width': 355, 'keyboard_volume': 48}))
        loaded = preferences.load_preferences(self.settings)
        self.assertEqual((loaded['language'], loaded['scene_width'], loaded['keyboard_volume']), ('vi', 355, 48))
        self.settings.setValue('preferences', json.dumps({'language': 'unsupported'}))
        self.assertEqual(preferences.load_preferences(self.settings)['language'], 'vi')


if __name__ == '__main__':
    unittest.main()
