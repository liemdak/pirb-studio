"""Windows portable entry with local DLL paths and visible startup diagnostics."""
import os,sys,runpy,traceback
from pathlib import Path

_runtime_dll_handles=[]
def main():
    internal=Path(sys.executable).resolve().parent
    package=internal/'Lib/site-packages/PySide6'
    if sys.platform=='win32':
        for folder in (internal,package,internal/'Lib/site-packages/shiboken6'):_runtime_dll_handles.append(os.add_dll_directory(str(folder)))
        os.environ['PATH']=str(package)+os.pathsep+os.environ.get('PATH','')
        os.environ['QT_PLUGIN_PATH']=str(package/'plugins');os.environ['QT_QPA_PLATFORM_PLUGIN_PATH']=str(package/'plugins/platforms')
    entry=Path(__file__).with_name('main.py');sys.argv=[str(entry),*sys.argv[1:]]
    try:runpy.run_path(str(entry),run_name='__main__')
    except SystemExit:raise
    except BaseException:
        details=traceback.format_exc();message='Không thể mở PIRB.'
        try:
            folder=Path(os.environ.get('LOCALAPPDATA',str(internal)))/'PIRBDesktop';folder.mkdir(parents=True,exist_ok=True)
            file=folder/'startup-error.log';file.write_text(details,encoding='utf-8');message+='\nChi tiết lỗi: '+str(file)
        except OSError:message+='\n'+details[-900:]
        if sys.platform=='win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,message,'Pirb Desk',0x10)
        else:print(details,file=sys.stderr)
        raise SystemExit(1)
if __name__=='__main__':main()
