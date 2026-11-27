"""Asynchronous pooled WAV playback. No input text is stored or transmitted."""
from pathlib import Path
import sys
from PySide6.QtCore import QObject,QUrl,QTimer,Signal
from PySide6.QtMultimedia import QSoundEffect,QMediaDevices
from custom_audio import sound_path

class SoundEngine(QObject):
    birdTriggered=Signal()
    def __init__(self,root,prefs,parent=None):
        super().__init__(parent);self.root=Path(root);self.prefs=dict(prefs);self.pool={};self.last_bird=-1e9
        self.available=sys.platform=='win32' and bool(QMediaDevices.audioOutputs())
        self.configure(prefs)
    def configure(self,prefs):
        changed=any(self.prefs.get(key)!=prefs.get(key) for key in ('sound_pack','custom_sounds'));self.prefs=dict(prefs)
        if changed:
            for voices in self.pool.values():
                for effect in voices:effect.stop();effect.deleteLater()
            self.pool.clear()
        if self.available:
            for filename in ['key_press.wav','space_press.wav','enter_press.wav','backspace_press.wav','modifier_press.wav','mouse_press.wav']:
                self.voices(self.packfile(filename),8 if filename=='key_press.wav' else 3)
            self.voices(self.root/'assets'/'sounds'/'pirb_coo.wav',1)
    def packfile(self,name):return sound_path(self.root,self.prefs,name)
    def preview_slot(self,name):
        volume=self.prefs['mouse_volume' if name=='mouse_press.wav' else 'keyboard_volume']
        self.play_file(self.packfile(name),volume,8 if name=='key_press.wav' else 3)
    def voices(self,path,count=3):
        key=str(path)
        if key not in self.pool:
            effects=[]
            for _ in range(count):
                effect=QSoundEffect(self);effect.setSource(QUrl.fromLocalFile(str(path.resolve())));effects.append(effect)
            self.pool[key]=effects
        return self.pool[key]
    def play_file(self,path,volume,count=3):
        if not self.available or volume<=0 or not Path(path).is_file():return False
        voices=self.voices(path,count);effect=next((v for v in voices if not v.isPlaying()),voices[0])
        if effect.status()!=QSoundEffect.Status.Ready:return False
        effect.setVolume(max(0,min(1,volume/100)));effect.play();return True
    def key(self,vk,force=False):
        if not force and not self.prefs['keyboard_sound']:return
        filename='space_press.wav' if vk==32 else 'enter_press.wav' if vk in (13,108) else 'backspace_press.wav' if vk==8 else 'modifier_press.wav' if vk in (9,91,92,160,161,162,163,164,165) else 'key_press.wav'
        self.play_file(self.packfile(filename),self.prefs['keyboard_volume'],8 if filename=='key_press.wav' else 3)
    def mouse(self,force=False):
        if force or self.prefs['mouse_sound']:self.play_file(self.packfile('mouse_press.wav'),self.prefs['mouse_volume'])
    def bird(self,force=False):
        if force or self.prefs['pirb_sound']:
            self.birdTriggered.emit()
            self.play_file(self.root/'assets'/'sounds'/'pirb_coo.wav',self.prefs['pirb_volume'],1)
    def idle(self,now,seconds):
        if self.prefs['pirb_sound'] and seconds>45 and now-self.last_bird>120:
            self.bird();self.last_bird=now
    def preview(self):
        for n,key in enumerate((65,83,68,32,13)):QTimer.singleShot(n*190,lambda k=key:self.key(k,True))
    def close(self):
        for voices in self.pool.values():
            for effect in voices:effect.stop()
