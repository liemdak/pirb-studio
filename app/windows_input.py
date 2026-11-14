"""Windows keyboard hook. States and pending press events exist only in memory."""
import ctypes
from ctypes import wintypes

class KeyboardInput:
    def __init__(self):
        self.held=set(); self.presses=[]
        self.user32=ctypes.WinDLL('user32',use_last_error=True)
        kernel32=ctypes.WinDLL('kernel32',use_last_error=True)
        LRESULT=ctypes.c_ssize_t
        HOOKPROC=ctypes.WINFUNCTYPE(LRESULT,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
        class KBD(ctypes.Structure):
            _fields_=[('vkCode',wintypes.DWORD),('scanCode',wintypes.DWORD),('flags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ctypes.c_size_t)]
        self.user32.CallNextHookEx.argtypes=[wintypes.HANDLE,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM]
        self.user32.CallNextHookEx.restype=LRESULT
        self.user32.SetWindowsHookExW.argtypes=[ctypes.c_int,HOOKPROC,wintypes.HINSTANCE,wintypes.DWORD]
        self.user32.SetWindowsHookExW.restype=wintypes.HANDLE
        self.user32.UnhookWindowsHookEx.argtypes=[wintypes.HANDLE]
        kernel32.GetModuleHandleW.argtypes=[wintypes.LPCWSTR]; kernel32.GetModuleHandleW.restype=wintypes.HMODULE
        def callback(code,msg,data):
            if code>=0:
                k=ctypes.cast(data,ctypes.POINTER(KBD)).contents
                vk=k.vkCode
                pad={71:103,72:104,73:105,75:100,76:101,77:102,79:97,80:98,81:99,82:96,83:110}
                if not k.flags&1 and k.scanCode in pad: vk=pad[k.scanCode]
                if vk==13 and k.flags&1: vk=108 # Dedicated internal ID for numpad Enter.
                elif vk==16: vk=161 if k.scanCode==54 else 160
                elif vk==17: vk=163 if k.flags&1 else 162
                elif vk==18: vk=165 if k.flags&1 else 164
                if msg in (0x100,0x104):
                    fresh=vk not in self.held
                    self.held.add(vk)
                    # Only pending visual events; cap to avoid growth during UI stalls.
                    if fresh and len(self.presses)<128: self.presses.append(vk)
                elif msg in (0x101,0x105): self.held.discard(vk)
            return self.user32.CallNextHookEx(None,code,msg,data)
        self.callback=HOOKPROC(callback)
        self.hook=self.user32.SetWindowsHookExW(13,self.callback,kernel32.GetModuleHandleW(None),0)
        if not self.hook: raise ctypes.WinError(ctypes.get_last_error())
    def consume(self):
        presses,self.presses=self.presses,[]
        return set(self.held),presses
    def close(self):
        if self.hook:
            self.user32.UnhookWindowsHookEx(self.hook); self.hook=None
        self.held.clear(); self.presses.clear()
