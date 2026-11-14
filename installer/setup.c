#define UNICODE
#define _UNICODE
#define COBJMACROS
#include <windows.h>
#include <shlobj.h>
#include <objbase.h>
DWORD _tls_index=0;
static wchar_t self[32768],base[32768],destination[32768],appdir[32768],exe[32768],temp[32768],zipfile[32768],tar[32768],command[32768],linkfile[32768],error[2048];
static unsigned char buffer[65536];
static STARTUPINFOW startup;static PROCESS_INFORMATION process;
static const GUID PIRB_CLSID_ShellLink={0x00021401,0,0,{0xc0,0,0,0,0,0,0,0x46}};
static const GUID PIRB_IID_IShellLinkW={0x000214f9,0,0,{0xc0,0,0,0,0,0,0,0x46}};
static const GUID PIRB_IID_IPersistFile={0x0000010b,0,0,{0xc0,0,0,0,0,0,0,0x46}};
static void fail(const wchar_t *message){MessageBoxW(NULL,message,L"PIRB Studio · Cài đặt",MB_OK|MB_ICONERROR);ExitProcess(1);}
static void folder(wchar_t *path){if(!CreateDirectoryW(path,NULL)&&GetLastError()!=ERROR_ALREADY_EXISTS)fail(L"Không tạo được thư mục cài đặt trong tài khoản hiện tại.");}
static void register_uninstall(void){
 HKEY key;const wchar_t *path=L"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PIRBStudio";
 if(RegCreateKeyExW(HKEY_CURRENT_USER,path,0,NULL,0,KEY_SET_VALUE,NULL,&key,NULL)!=ERROR_SUCCESS)return;
 const wchar_t *name=L"PIRB Studio 0.8.1",*version=L"0.8.1",*publisher=L"PIRB Studio Community";
 RegSetValueExW(key,L"DisplayName",0,REG_SZ,(const BYTE*)name,(lstrlenW(name)+1)*2);
 RegSetValueExW(key,L"DisplayVersion",0,REG_SZ,(const BYTE*)version,(lstrlenW(version)+1)*2);
 RegSetValueExW(key,L"Publisher",0,REG_SZ,(const BYTE*)publisher,(lstrlenW(publisher)+1)*2);
 RegSetValueExW(key,L"InstallLocation",0,REG_SZ,(const BYTE*)appdir,(lstrlenW(appdir)+1)*2);
 RegSetValueExW(key,L"DisplayIcon",0,REG_SZ,(const BYTE*)exe,(lstrlenW(exe)+1)*2);
 lstrcpyW(command,L"\"");lstrcatW(command,appdir);lstrcatW(command,L"\\Uninstall.exe\"");
 RegSetValueExW(key,L"UninstallString",0,REG_SZ,(const BYTE*)command,(lstrlenW(command)+1)*2);
 DWORD one=1;RegSetValueExW(key,L"NoModify",0,REG_DWORD,(const BYTE*)&one,4);RegSetValueExW(key,L"NoRepair",0,REG_DWORD,(const BYTE*)&one,4);RegCloseKey(key);
}
static void shortcut(int csidl){
 if(FAILED(SHGetFolderPathW(NULL,csidl,NULL,SHGFP_TYPE_CURRENT,linkfile)))return;
 lstrcatW(linkfile,L"\\PIRB Studio.lnk");IShellLinkW *link=NULL;IPersistFile *persist=NULL;
 if(SUCCEEDED(CoCreateInstance(&PIRB_CLSID_ShellLink,NULL,CLSCTX_INPROC_SERVER,&PIRB_IID_IShellLinkW,(void**)&link))){
  IShellLinkW_SetPath(link,exe);IShellLinkW_SetWorkingDirectory(link,appdir);IShellLinkW_SetIconLocation(link,exe,0);IShellLinkW_SetDescription(link,L"PIRB Studio · Desktop companion");
  if(SUCCEEDED(IShellLinkW_QueryInterface(link,&PIRB_IID_IPersistFile,(void**)&persist))){IPersistFile_Save(persist,linkfile,TRUE);IPersistFile_Release(persist);}IShellLinkW_Release(link);
 }
}
void pirb_setup_start(void){
 if(MessageBoxW(NULL,L"Cài PIRB Studio 0.8 cho tài khoản hiện tại?\n\nWindows 10 (1809+) / 11, 64-bit. Không cần cài Python.\nWindows 10 (1809+) / 11 x64. Python is bundled.\nSẽ tạo biểu tượng Desktop và Start Menu.\nHãy thoát PIRB đang chạy trước khi tiếp tục.",L"PIRB Studio · Cài đặt",MB_YESNO|MB_ICONINFORMATION)!=IDYES)ExitProcess(0);
 DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",base,32768);if(!n||n>31000)fail(L"Không tìm thấy thư mục dữ liệu tài khoản.");
 lstrcpyW(destination,base);lstrcatW(destination,L"\\Programs");folder(destination);lstrcatW(destination,L"\\PIRBStudio");folder(destination);lstrcatW(destination,L"\\0.8.1");folder(destination);
 lstrcpyW(appdir,destination);lstrcatW(appdir,L"\\PIRB");lstrcpyW(exe,appdir);lstrcatW(exe,L"\\PIRB.exe");
 if(GetFileAttributesW(exe)!=INVALID_FILE_ATTRIBUTES){HANDLE check=CreateFileW(exe,GENERIC_WRITE,0,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);if(check==INVALID_HANDLE_VALUE)fail(L"PIRB đang chạy. Hãy thoát bằng Exit ở biểu tượng cạnh đồng hồ rồi mở Setup lại.");CloseHandle(check);}
 GetModuleFileNameW(NULL,self,32768);HANDLE source=CreateFileW(self,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);if(source==INVALID_HANDLE_VALUE)fail(L"Không đọc được file Setup.");
 LARGE_INTEGER length,position;GetFileSizeEx(source,&length);position.QuadPart=length.QuadPart-16;SetFilePointerEx(source,position,NULL,FILE_BEGIN);
 struct{char magic[8];ULONGLONG size;}footer;DWORD got=0;ReadFile(source,&footer,16,&got,NULL);if(got!=16)fail(L"File Setup chưa tải đầy đủ. Hãy tải lại.");
 const char *magic="PIRBZIP1";for(int i=0;i<8;i++)if(footer.magic[i]!=magic[i])fail(L"File Setup chưa tải đầy đủ. Hãy tải lại.");
 if(got!=16||footer.size==0||footer.size>(ULONGLONG)length.QuadPart-16)fail(L"Gói cài đặt không hợp lệ.");
 GetTempPathW(32768,temp);if(!GetTempFileNameW(temp,L"prb",0,zipfile))fail(L"Không tạo được tệp tạm để cài đặt.");
 HANDLE output=CreateFileW(zipfile,GENERIC_WRITE,0,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_TEMPORARY,NULL);if(output==INVALID_HANDLE_VALUE)fail(L"Không ghi được tệp tạm.");
 position.QuadPart=length.QuadPart-16-footer.size;SetFilePointerEx(source,position,NULL,FILE_BEGIN);ULONGLONG remaining=footer.size;
 HWND progress=CreateWindowExW(WS_EX_TOPMOST,L"STATIC",L"Đang cài PIRB Studio… vui lòng chờ.",WS_OVERLAPPED|WS_CAPTION|WS_VISIBLE,200,200,460,90,NULL,NULL,GetModuleHandleW(NULL),NULL);UpdateWindow(progress);
 while(remaining){DWORD chunk=remaining>sizeof(buffer)?sizeof(buffer):(DWORD)remaining;DWORD written=0;if(!ReadFile(source,buffer,chunk,&got,NULL)||got!=chunk||!WriteFile(output,buffer,chunk,&written,NULL)||written!=chunk)fail(L"Không chép được gói cài đặt. Hãy tải lại Setup.");remaining-=chunk;}
 CloseHandle(source);CloseHandle(output);GetSystemDirectoryW(tar,32768);lstrcatW(tar,L"\\tar.exe");if(GetFileAttributesW(tar)==INVALID_FILE_ATTRIBUTES)fail(L"Phiên bản Windows này thiếu công cụ giải nén tar.exe. Hãy dùng bản portable.");
 if(lstrlenW(tar)+lstrlenW(zipfile)+lstrlenW(destination)+30>=32768)fail(L"Đường dẫn cài đặt quá dài.");
 lstrcpyW(command,L"\"");lstrcatW(command,tar);lstrcatW(command,L"\" -xf \"");lstrcatW(command,zipfile);lstrcatW(command,L"\" -C \"");lstrcatW(command,destination);lstrcatW(command,L"\"");startup.cb=sizeof(startup);
 if(!CreateProcessW(tar,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,destination,&startup,&process))fail(L"Không khởi động được công cụ giải nén của Windows.");CloseHandle(process.hThread);
 MSG message;for(;;){DWORD status=MsgWaitForMultipleObjects(1,&process.hProcess,FALSE,100,QS_ALLINPUT);if(status==WAIT_OBJECT_0)break;if(status==WAIT_FAILED)fail(L"Không theo dõi được tiến trình cài đặt.");while(PeekMessageW(&message,NULL,0,0,PM_REMOVE)){TranslateMessage(&message);DispatchMessageW(&message);}}
 DWORD code=1;GetExitCodeProcess(process.hProcess,&code);CloseHandle(process.hProcess);DeleteFileW(zipfile);DestroyWindow(progress);
 if(code||GetFileAttributesW(exe)==INVALID_FILE_ATTRIBUTES)fail(L"Giải nén ứng dụng chưa thành công. Hãy kiểm tra dung lượng đĩa rồi mở Setup lại.");
 CoInitializeEx(NULL,COINIT_APARTMENTTHREADED);shortcut(CSIDL_DESKTOPDIRECTORY);shortcut(CSIDL_PROGRAMS);CoUninitialize();register_uninstall();
 if(MessageBoxW(NULL,L"Đã cài PIRB Studio.\nBạn có thể mở từ biểu tượng PIRB Studio trên Desktop hoặc Start Menu.\n\nMở PIRB ngay bây giờ?",L"PIRB Studio",MB_YESNO|MB_ICONINFORMATION)==IDYES){
  lstrcpyW(command,L"\"");lstrcatW(command,exe);lstrcatW(command,L"\"");STARTUPINFOW info;PROCESS_INFORMATION child;for(unsigned int i=0;i<sizeof(info);i++)((unsigned char*)&info)[i]=0;info.cb=sizeof(info);
  if(CreateProcessW(exe,command,NULL,NULL,FALSE,0,NULL,appdir,&info,&child)){CloseHandle(child.hThread);CloseHandle(child.hProcess);}
 }
 ExitProcess(0);
}
