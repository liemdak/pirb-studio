"""Release selection, consent, integrity and asynchronous network regressions."""
import hashlib
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from PySide6.QtCore import QObject, QSettings, QEventLoop, QTimer, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QWidget
import preferences
import updater


def release_row(version='0.99.0', payload=b'MZ-test-installer', prerelease=False):
    tag='v'+version
    name=f'PIRB_Studio_{version}_Windows_x64_Setup.exe'
    return {'tag_name':tag,'draft':False,'prerelease':prerelease,'html_url':updater.RELEASE_ROOT+'tag/'+tag,
            'body':'Test release notes', 'assets':[
                {'name':name,'state':'uploaded','size':len(payload),'digest':'sha256:'+hashlib.sha256(payload).hexdigest(),
                 'browser_download_url':updater.RELEASE_ROOT+'download/'+tag+'/'+name},
                {'name':'SHA256SUMS.txt','state':'uploaded','size':100,
                 'browser_download_url':updater.RELEASE_ROOT+'download/'+tag+'/SHA256SUMS.txt'}]}


class UpdaterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.owner=QWidget();self.owner.prefs=dict(preferences.DEFAULTS)
        self.owner.settings=QSettings(str(Path(self.temp.name)/'settings.ini'),QSettings.Format.IniFormat)
        self.controller=updater.UpdateController(self.owner)
        self.notices=[];self.controller._notice=self.notices.append

    def tearDown(self):
        self.controller.close();self.controller.deleteLater();self.app.processEvents()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.temp.cleanup()

    def test_numeric_semver_and_prerelease_order(self):
        self.assertGreater(updater.version_key('v0.10.0'),updater.version_key('0.9.9'))
        self.assertGreater(updater.version_key('1.0.0'),updater.version_key('1.0.0-rc.10'))
        self.assertGreater(updater.version_key('1.0.0-rc.10'),updater.version_key('1.0.0-rc.2'))
        for value in ('latest','0.8','../v0.9.0','https://example.com/1.0.0'):
            with self.assertRaises(ValueError):updater.version_key(value)

    def test_pick_newest_complete_release_and_filter_channels(self):
        self.assertEqual(updater.newest_release([release_row('0.10.0'),release_row('0.9.0')],'0.8.2').version,'0.10.0')
        self.assertIsNone(updater.newest_release([release_row('0.8.2')],'0.8.2'))
        self.assertIsNone(updater.newest_release([release_row('0.99.0',prerelease=True)],'0.8.2',False))
        self.assertIsNone(updater.newest_release([release_row('0.99.0-rc.1')],'0.8.2',False))
        for change in ('draft','missing','wrong_host','wrong_repo','incomplete','too_big'):
            row=release_row()
            if change=='draft':row['draft']=True
            elif change=='missing':row['assets'].pop()
            elif change=='wrong_host':row['assets'][0]['browser_download_url']='https://evil.example/setup.exe'
            elif change=='wrong_repo':row['assets'][0]['browser_download_url']=row['assets'][0]['browser_download_url'].replace('liemdak/','another/')
            elif change=='incomplete':row['assets'][0]['state']='new'
            else:row['assets'][0]['size']=updater.MAX_INSTALLER_SIZE+1
            self.assertIsNone(updater.newest_release([row],'0.8.2'),change)

    def test_checksum_missing_duplicate_and_tampered_installer(self):
        data=b'MZ-test-installer';row=release_row(payload=data);release=updater.newest_release([row],'0.1.0')
        digest=hashlib.sha256(data).hexdigest();line=(digest+'  '+release.filename+'\n').encode()
        self.assertEqual(updater.checksum_for(line,release.filename),digest)
        for checksums in (b'',line+line):
            with self.assertRaises(ValueError):updater.checksum_for(checksums,release.filename)
        path=Path(self.temp.name)/'setup.exe';path.write_bytes(data)
        updater.verify_installer(path,release,digest)
        path.write_bytes(b'MZ-modified-data!')
        with self.assertRaises(ValueError):updater.verify_installer(path,release,digest)
        with self.assertRaises(ValueError):updater.verify_installer(path,release,'0'*64)

    def test_auto_opt_out_interval_offline_and_manual_override(self):
        calls=[]
        def get(url,limit,success,failure,destination=None):calls.append(url);failure()
        self.controller._get=get
        self.owner.prefs['check_updates']=False;self.controller.check();self.assertEqual(calls,[])
        self.controller.check(manual=True);self.assertEqual(len(calls),1);self.assertEqual(len(self.notices),1)
        self.owner.prefs['check_updates']=True;self.controller.check();self.assertEqual(len(calls),1)
        self.controller.check(manual=True);self.assertEqual(len(calls),2)

    def test_prompt_never_downloads_before_acceptance(self):
        release=updater.newest_release([release_row()],'0.1.0')
        with patch.object(self.controller,'download') as download:
            self.controller._offer(release);self.app.processEvents();download.assert_not_called()
            self.controller._prompt.buttons()[1].click();self.app.processEvents();download.assert_not_called()
            self.controller._offer(release);self.app.processEvents();self.controller._prompt.buttons()[0].click()
            self.app.processEvents();download.assert_called_once_with(release)

    def test_detection_notifies_once_per_version_but_manual_can_repeat(self):
        data=json.dumps([release_row()]).encode()
        with patch.object(self.controller,'_offer') as offer:
            self.controller._checked(data,False);self.controller._checked(data,False)
            self.assertEqual(offer.call_count,1)
            self.controller._checked(data,True);self.assertEqual(offer.call_count,2)

    def test_download_verifies_before_launch_and_cancelling_never_launches(self):
        payload=b'MZ-test-installer';release=updater.newest_release([release_row(payload=payload)],'0.1.0')
        checksums=(hashlib.sha256(payload).hexdigest()+'  '+release.filename+'\n').encode()
        def get(url,limit,success,failure,destination=None):
            if destination:destination.write_bytes(payload);success(destination)
            else:success(checksums)
        self.controller._get=get
        with patch.object(updater.sys,'platform','win32'),patch.object(updater.subprocess,'Popen') as launch,patch.object(updater.QTimer,'singleShot'):
            self.controller.download(release);launch.assert_called_once()
            self.assertTrue(self.controller._launched)
        # A corrupt body must never reach process creation.
        self.controller._launched=False
        def corrupt(url,limit,success,failure,destination=None):
            if destination:destination.write_bytes(b'MZ-broken');success(destination)
            else:success(checksums)
        self.controller._get=corrupt
        with patch.object(updater.sys,'platform','win32'),patch.object(updater.subprocess,'Popen') as launch:
            self.controller.download(release);launch.assert_not_called()
        self.assertTrue(self.notices)
        self.controller._get=lambda *a,**k:None
        with patch.object(updater.sys,'platform','win32'),patch.object(updater.subprocess,'Popen') as launch:
            self.controller.download(release);self.controller.cancel();launch.assert_not_called()
            self.assertIsNone(self.controller._progress)

    def test_network_reader_success_error_and_size_limit(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/redirect':
                    self.send_response(302);self.send_header('Location','/asset');self.send_header('Content-Length','0');self.end_headers();return
                data=b'[{"example":true}]'
                self.send_response(200 if self.path!='/fail' else 503)
                self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for route,limit,expected in [('/',100,True),('/redirect',100,True),('/',2,False),('/fail',100,False)]:
                loop=QEventLoop();result=[]
                body=[]
                def ok(data):result.append(True);body.append(data);loop.quit()
                def fail():result.append(False);loop.quit()
                self.controller._get(f'http://127.0.0.1:{server.server_port}'+route,limit,ok,fail)
                timeout=QTimer();timeout.setSingleShot(True);timeout.timeout.connect(loop.quit);timeout.start(5000)
                loop.exec();timeout.stop()
                self.assertEqual(result,[expected]);self.assertIsNone(self.controller._reply)
                if expected:self.assertEqual(body,[b'[{"example":true}]'])
        finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
