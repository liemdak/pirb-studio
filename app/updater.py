"""Opt-in install after a version prompt; anonymous public GitHub release checks."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlsplit

from PySide6.QtCore import QObject, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QWidget
from i18n import translate
from version import VERSION

REPOSITORY = 'liemdak/pirb-studio'
API_URL = 'https://api.github.com/repos/' + REPOSITORY + '/releases?per_page=30'
RELEASE_ROOT = 'https://github.com/' + REPOSITORY + '/releases/'
CHECK_INTERVAL = 6 * 60 * 60
MAX_INSTALLER_SIZE = 200 * 1024 * 1024
VERSION_PATTERN = re.compile(r'^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$')


def version_key(value):
    match = VERSION_PATTERN.fullmatch(str(value))
    if not match:
        raise ValueError('Unsupported version')
    major, minor, patch, prerelease = match.groups()
    parts = tuple((0, int(p)) if p.isdigit() else (1, p) for p in (prerelease or '').split('.'))
    return int(major), int(minor), int(patch), int(prerelease is None), parts


def asset_url(url, tag, filename):
    expected = RELEASE_ROOT + 'download/' + quote(tag, safe='') + '/' + quote(filename, safe='')
    return isinstance(url, str) and url == expected and urlsplit(url).scheme == 'https'


@dataclass(frozen=True)
class Release:
    version: str
    tag: str
    page: str
    notes: str
    filename: str
    download: str
    checksum: str
    size: int
    digest: str = ''


def newest_release(rows, current=VERSION, include_prereleases=True):
    if not isinstance(rows, list):
        raise ValueError('Invalid release response')
    candidates = []
    for row in rows:
        if not isinstance(row, dict) or row.get('draft') or (row.get('prerelease') and not include_prereleases):
            continue
        tag = row.get('tag_name', '')
        try:
            key = version_key(tag)
        except (TypeError, ValueError):
            continue
        if key <= version_key(current) or (not include_prereleases and key[3] == 0):
            continue
        version = tag.removeprefix('v')
        filename = f'PIRB_Studio_{version}_Windows_x64_Setup.exe'
        assets = {a.get('name'): a for a in row.get('assets', []) if isinstance(a, dict) and a.get('state') == 'uploaded'}
        installer, checksum = assets.get(filename, {}), assets.get('SHA256SUMS.txt', {})
        size = installer.get('size', 0)
        if not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= MAX_INSTALLER_SIZE:
            continue
        if not asset_url(installer.get('browser_download_url'), tag, filename) or not asset_url(checksum.get('browser_download_url'), tag, 'SHA256SUMS.txt'):
            continue
        page = RELEASE_ROOT + 'tag/' + quote(tag, safe='')
        if row.get('html_url') != page:
            continue
        digest = installer.get('digest') or ''
        if digest and not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest):
            continue
        candidates.append((key, Release(version, tag, page, str(row.get('body') or '')[:10000], filename,
                                        installer['browser_download_url'], checksum['browser_download_url'], size,
                                        digest.removeprefix('sha256:').lower())))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def checksum_for(data, filename):
    matches = []
    for line in data.decode('utf-8-sig').splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', line.strip())
        if match and match[2] == filename:
            matches.append(match[1].lower())
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous checksum')
    return matches[0]


def verify_installer(path, release, checksum):
    if release.digest and release.digest != checksum:
        raise ValueError('Release digest mismatch')
    if path.stat().st_size != release.size:
        raise ValueError('Incomplete installer')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise ValueError('Invalid Windows executable')
        stream.seek(0)
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != checksum:
        raise ValueError('Installer checksum mismatch')


class UpdateController(QObject):
    statusChanged = Signal()

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.network = QNetworkAccessManager(self)
        self.status = 'Chưa kiểm tra cập nhật.'
        self.status_values = {}
        self.available = None
        self._reply = None
        self._prompt = None
        self._dialogs = []
        self._progress = None
        self._temp = None
        self._closing = False
        self._cancelled = False
        self._launched = False
        self._notified = set()
        self.timer = QTimer(self)
        self.timer.setInterval(CHECK_INTERVAL * 1000)
        self.timer.timeout.connect(self.check)

    @property
    def busy(self):
        return self._reply is not None or self._prompt is not None or self._progress is not None

    def tr(self, source):
        return translate(source, self.owner.prefs.get('language', 'vi'))

    def set_status(self, source, **values):
        self.status, self.status_values = source, values
        self.statusChanged.emit()

    def start(self):
        self.timer.start()
        QTimer.singleShot(4000, self.check)

    def _get(self, url, limit, success, failure, destination=None):
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent', ('PIRB-Studio/' + VERSION).encode())
        request.setRawHeader(b'Accept', b'application/vnd.github+json' if url.startswith('https://api.github.com/') else b'application/octet-stream')
        request.setTransferTimeout(20000)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy.value)
        reply = self.network.get(request)
        self._reply = reply
        self.statusChanged.emit()
        state = {'data': bytearray(), 'size': 0, 'error': None}
        try:
            stream = destination.open('wb') if destination else None
        except OSError:
            self._reply = None; reply.abort(); reply.deleteLater(); failure(); return
        deadline = QTimer(reply); deadline.setSingleShot(True)
        deadline.timeout.connect(reply.abort); deadline.start(300000 if destination else 30000)

        def read():
            data = bytes(reply.readAll())
            state['size'] += len(data)
            if state['size'] > limit:
                state['error'] = 'size'; reply.abort(); return
            try:
                if stream:
                    stream.write(data)
                    if self._progress:
                        self._progress.setRange(0, 100)
                        self._progress.setValue(min(99, state['size'] * 100 // max(1, limit)))
                else:
                    state['data'].extend(data)
            except OSError:
                state['error'] = 'disk'; reply.abort()

        def finished():
            deadline.stop()
            if reply.isOpen(): read()
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            failed = state['error'] or reply.error() != QNetworkReply.NetworkError.NoError or status != 200
            if stream:
                try: stream.close()
                except OSError: failed = True
            if self._reply is reply: self._reply = None
            reply.deleteLater()
            if self._closing or self._cancelled or failed:
                if destination: destination.unlink(missing_ok=True)
                if not self._closing: failure()
                return
            success(destination if destination else bytes(state['data']))

        reply.readyRead.connect(read); reply.finished.connect(finished)

    def check(self, manual=False):
        if self._closing or self.busy:
            return
        if not manual:
            if not self.owner.prefs.get('check_updates', True): return
            try: last = float(self.owner.settings.value('updater/last_check', 0))
            except (TypeError, ValueError): last = 0
            if 0 <= time.time() - last < CHECK_INTERVAL: return
        self.owner.settings.setValue('updater/last_check', time.time())
        self.set_status('Đang kiểm tra cập nhật…')
        self._get(API_URL, 2 * 1024 * 1024,
                  lambda data: self._checked(data, manual), lambda: self._failed(manual))

    def _checked(self, data, manual):
        try:
            self.available = newest_release(json.loads(data), VERSION, self.owner.prefs.get('include_prereleases', True))
        except (ValueError, TypeError, UnicodeError):
            self._failed(manual); return
        if not self.available:
            self.set_status('Bạn đang dùng phiên bản mới nhất.')
            if manual: self._notice('Bạn đang dùng phiên bản mới nhất.')
            return
        self.set_status('Có bản mới: {version}', version=self.available.version)
        version = self.available.version
        if not manual and version in self._notified: return
        self._notified.add(version)
        self._offer(self.available)

    def _failed(self, manual):
        self.set_status('Chưa kiểm tra được. Hãy kiểm tra kết nối mạng và thử lại.')
        if manual: self._notice(self.status)

    def _notice(self, source):
        box = QMessageBox(QMessageBox.Icon.Information, 'PIRB Studio', self.tr(source))
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self._dialogs.append(box)
        box.finished.connect(lambda _: self._release_dialog(box)); box.open()

    def _release_dialog(self, box):
        if box in self._dialogs: self._dialogs.remove(box)
        box.deleteLater()

    def _offer(self, release):
        box = QMessageBox(QMessageBox.Icon.Information, self.tr('Có bản cập nhật mới'),
                          self.tr('PIRB {new} đã có sẵn. Bạn đang dùng {current}.\n\nBạn có muốn tải và cài bản cập nhật không?').format(new=release.version, current=VERSION))
        box.setTextFormat(Qt.TextFormat.PlainText)
        if release.notes: box.setDetailedText(release.notes)
        box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        yes = box.addButton(self.tr('Cập nhật ngay'), QMessageBox.ButtonRole.AcceptRole)
        later = box.addButton(self.tr('Để sau'), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(later)
        self._prompt = box; self.statusChanged.emit()

        def answered(_):
            accepted = box.clickedButton() is yes
            self._prompt = None; box.deleteLater(); self.statusChanged.emit()
            if accepted and not self._closing: self.download(release)

        box.finished.connect(answered); box.open()

    def download(self, release):
        if self._closing or self._reply: return
        if sys.platform != 'win32':
            QDesktopServices.openUrl(QUrl(release.page)); return
        self._cancelled = False
        self._progress = QProgressDialog(self.tr('Đang tải bản cập nhật…'), self.tr('Hủy'), 0, 100,
                                         self.owner if isinstance(self.owner, QWidget) else None)
        self._progress.setValue(0)
        self._progress.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._progress.setWindowTitle('PIRB Studio'); self._progress.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self._progress.setAutoClose(False); self._progress.canceled.connect(self.cancel)
        self._progress.show(); self.set_status('Đang tải bản cập nhật…')

        def got_checksum(data):
            try:
                checksum = checksum_for(data, release.filename)
                if release.digest and release.digest != checksum: raise ValueError('Digest mismatch')
                self._temp = Path(tempfile.mkdtemp(prefix='PIRB-update-'))
                dest = self._temp / release.filename
            except (ValueError, OSError, UnicodeError):
                self._download_failed(); return
            self._get(release.download, release.size,
                      lambda path: self._install(path, release, checksum), self._download_failed, dest)

        self._get(release.checksum, 64 * 1024, got_checksum, self._download_failed)

    def _finish_progress(self):
        if self._progress:
            progress, self._progress = self._progress, None
            progress.canceled.disconnect(self.cancel)
            progress.close()

    def _install(self, path, release, checksum):
        try:
            verify_installer(path, release, checksum)
            # No shell and no elevation: run only after the user's update choice.
            subprocess.Popen([str(path)], cwd=str(path.parent))
        except (OSError, ValueError):
            self._download_failed(); return
        self._launched = True
        self._finish_progress()
        self.set_status('Đang mở trình cài đặt…')
        QTimer.singleShot(0, QApplication.instance().quit)

    def cancel(self):
        self._cancelled = True
        if self._reply: self._reply.abort()
        self._finish_progress()
        self.set_status('Đã hủy cập nhật. Bạn vẫn đang dùng bản hiện tại.')

    def _download_failed(self):
        self._finish_progress()
        if self._temp and not self._launched:
            shutil.rmtree(self._temp, ignore_errors=True); self._temp = None
        if not self._cancelled:
            self.set_status('Không tải hoặc xác minh được bộ cài. Chưa thay đổi ứng dụng.')
            self._notice(self.status)
        else:
            self.set_status('Đã hủy cập nhật. Bạn vẫn đang dùng bản hiện tại.')

    def close(self):
        self._closing = True; self.timer.stop()
        if self._reply: self._reply.abort()
        if self._prompt: self._prompt.close()
        for box in list(self._dialogs): box.close()
        self._finish_progress()
        if self._temp and not self._launched: shutil.rmtree(self._temp, ignore_errors=True)
