"""Validated, locally copied PCM sound overrides. No codecs or network needed."""
import hashlib
import os
import tempfile
import wave
from pathlib import Path

from PySide6.QtCore import QStandardPaths

SOUND_SLOTS = (
    ('Phím thường', 'key_press.wav'),
    ('Phím Space', 'space_press.wav'),
    ('Phím Enter', 'enter_press.wav'),
    ('Phím Backspace', 'backspace_press.wav'),
    ('Phím bổ trợ', 'modifier_press.wav'),
    ('Click chuột', 'mouse_press.wav'),
)
SLOT_FILES = frozenset(filename for _, filename in SOUND_SLOTS)
MAX_BYTES = 8 * 1024 * 1024
MAX_SECONDS = 3


def validate_wav(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Hãy chọn âm thanh nhỏ hơn 8 MB.')
    try:
        with wave.open(str(path), 'rb') as sample:
            frames, rate = sample.getnframes(), sample.getframerate()
            channels, width = sample.getnchannels(), sample.getsampwidth()
            if (sample.getcomptype() != 'NONE' or channels not in (1, 2)
                    or width not in (1, 2, 3, 4) or not 8000 <= rate <= 192000
                    or frames <= 0 or frames > rate * MAX_SECONDS):
                raise ValueError('Hãy chọn WAV PCM mono/stereo dài tối đa 3 giây.')
            if len(sample.readframes(frames)) != frames * channels * width:
                raise ValueError('Tệp âm thanh chưa đầy đủ hoặc bị hỏng.')
    except (wave.Error, EOFError) as error:
        raise ValueError('Không đọc được WAV. Hãy chọn WAV PCM hợp lệ.') from error


def import_sound(path, destination=None):
    """Validate the exact copied bytes; identical sounds share an immutable file."""
    with Path(path).open('rb') as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Hãy chọn âm thanh nhỏ hơn 8 MB.')
    folder = (Path(destination) if destination is not None else
              Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / 'custom_sounds')
    folder.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='import-', suffix='.wav', dir=folder)
    temporary = Path(temporary)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(data)
        validate_wav(temporary)
        stem = ''.join(c for c in Path(path).stem if c.isalnum() or c in ' -_').strip()[:48] or 'sound'
        target = folder / (stem + '-' + hashlib.sha256(data).hexdigest() + '.wav')
        temporary.replace(target)
        return str(target)
    finally:
        temporary.unlink(missing_ok=True)


def sound_path(root, prefs, filename):
    if prefs.get('sound_pack') == 'custom':
        overrides = prefs.get('custom_sounds', {})
        choices = [overrides.get(filename)]
        if filename != 'mouse_press.wav':
            choices.append(overrides.get('key_press.wav'))
        for value in choices:
            if isinstance(value, str) and value and Path(value).is_file():
                return Path(value)
        pack = 'thock'
    else:
        pack = prefs.get('sound_pack', 'thock')
    return Path(root) / 'assets' / 'sounds' / pack / filename
