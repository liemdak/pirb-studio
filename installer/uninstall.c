#define UNICODE
#define _UNICODE
#define COBJMACROS
#include <windows.h>
#include <shlobj.h>
#include <objbase.h>
DWORD _tls_index=0;
static wchar_t root[32768],exe[32768],self[32768],tmp[32768],copy[32768],command[32768],linkfile[32768],linktarget[32768];
static const wchar_t *title=L"Pirb Desk · Uninstall / Gỡ cài đặt";
static const GUID CLSID_Link={0x00021401,0,0,{0xc0,0,0,0,0,0,0,0x46}};
static const GUID IID_Link={0x000214f9,0,0,{0xc0,0,0,0,0,0,0,0x46}};
static const GUID IID_File={0x0000010b,0,0,{0xc0,0,0,0,0,0,0,0x46}};
static void fail(const wchar_t *s){MessageBoxW(NULL,s,title,MB_OK|MB_ICONERROR);ExitProcess(1);}
static BOOL remove_tree(const wchar_t *path){
 WIN32_FIND_DATAW data;BOOL ok=TRUE;
 if(lstrlenW(path)>31000)return FALSE;
 wchar_t *pattern=HeapAlloc(GetProcessHeap(),0,65536*2);if(!pattern)return FALSE;wchar_t *child=pattern+32768;
 lstrcpyW(pattern,path);lstrcatW(pattern,L"\\*");HANDLE search=FindFirstFileW(pattern,&data);
 if(search!=INVALID_HANDLE_VALUE){do{
  if(!lstrcmpW(data.cFileName,L".")||!lstrcmpW(data.cFileName,L".."))continue;
  lstrcpyW(child,path);lstrcatW(child,L"\\");lstrcatW(child,data.cFileName);
  if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
   if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT){if(!RemoveDirectoryW(child))ok=FALSE;}
   else if(!remove_tree(child))ok=FALSE;
  }else if(!DeleteFileW(child))ok=FALSE;
 }while(FindNextFileW(search,&data));FindClose(search);}
 BOOL removed=RemoveDirectoryW(path);HeapFree(GetProcessHeap(),0,pattern);return removed&&ok;
}
static void remove_shortcut(int folder){
 if(FAILED(SHGetFolderPathW(NULL,folder,NULL,SHGFP_TYPE_CURRENT,linkfile)))return;
 lstrcatW(linkfile,L"\\Pirb Desk.lnk");IShellLinkW *link=NULL;IPersistFile *file=NULL;
 if(SUCCEEDED(CoCreateInstance(&CLSID_Link,NULL,CLSCTX_INPROC_SERVER,&IID_Link,(void**)&link))){
  if(SUCCEEDED(IShellLinkW_QueryInterface(link,&IID_File,(void**)&file))){
   if(SUCCEEDED(IPersistFile_Load(file,linkfile,STGM_READ))&&SUCCEEDED(IShellLinkW_GetPath(link,linktarget,32768,NULL,SLGP_RAWPATH))&&!lstrcmpiW(linktarget,exe))DeleteFileW(linkfile);
   IPersistFile_Release(file);
  }IShellLinkW_Release(link);
 }
}
void pirb_uninstall_start(void){
 DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",root,32768);if(!n||n>31000)fail(L"Cannot locate the install folder / Không tìm thấy thư mục cài.");
 lstrcatW(root,L"\\Programs\\PIRBStudio\\0.10.0\\PirbDesk");lstrcpyW(exe,root);lstrcatW(exe,L"\\PirbDesk.exe");
 GetModuleFileNameW(NULL,self,32768);lstrcpyW(command,root);lstrcatW(command,L"\\Uninstall.exe");
 if(!lstrcmpiW(self,command)){
  if(MessageBoxW(NULL,L"Remove Pirb Desk 0.10.0? Your preferences and custom images will be kept.\n\nGỡ Pirb Desk 0.10.0? Tùy chọn và ảnh riêng được giữ lại.\nHãy thoát PIRB trước / Please exit PIRB first.",title,MB_YESNO|MB_ICONQUESTION)!=IDYES)ExitProcess(0);
  HANDLE check=CreateFileW(exe,GENERIC_WRITE,0,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
  if(check==INVALID_HANDLE_VALUE)fail(L"Exit PIRB and try again / Hãy thoát hẳn PIRB rồi thử lại.");CloseHandle(check);
  GetTempPathW(32768,tmp);if(!GetTempFileNameW(tmp,L"pru",0,copy))fail(L"Cannot create temporary file / Không tạo được tệp tạm.");
  if(!CopyFileW(self,copy,FALSE)){DeleteFileW(copy);fail(L"Cannot start uninstaller / Không khởi động được trình gỡ.");}
  lstrcpyW(command,L"\"");lstrcatW(command,copy);lstrcatW(command,L"\" --remove");STARTUPINFOW si={0};PROCESS_INFORMATION pi={0};si.cb=sizeof(si);
  if(!CreateProcessW(copy,command,NULL,NULL,FALSE,0,NULL,tmp,&si,&pi)){DeleteFileW(copy);fail(L"Cannot start uninstaller / Không khởi động được trình gỡ.");}
  CloseHandle(pi.hThread);CloseHandle(pi.hProcess);ExitProcess(0);
 }
 // The temporary worker only accepts this exact per-user versioned destination.
 BOOL worker=FALSE;const wchar_t *arg=GetCommandLineW();while(*arg){if(!lstrcmpW(arg,L"--remove")){worker=TRUE;break;}arg++;}if(!worker)ExitProcess(1);
 Sleep(600);BOOL removed=FALSE;
 for(int i=0;i<8&&!removed;i++){removed=remove_tree(root);if(!removed)Sleep(200);}
 if(!removed)fail(L"Some files could not be removed. Exit PIRB and remove the 0.10.0 folder manually.\nMột số tệp chưa được gỡ. Hãy thoát PIRB rồi xóa thư mục 0.10.0.");
 CoInitializeEx(NULL,COINIT_APARTMENTTHREADED);remove_shortcut(CSIDL_DESKTOPDIRECTORY);remove_shortcut(CSIDL_PROGRAMS);CoUninitialize();
 HKEY key;const wchar_t *reg=L"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PIRBStudio";wchar_t version[64];DWORD bytes=sizeof(version);
 if(RegOpenKeyExW(HKEY_CURRENT_USER,reg,0,KEY_QUERY_VALUE,&key)==ERROR_SUCCESS){
  BOOL current=RegQueryValueExW(key,L"DisplayVersion",NULL,NULL,(BYTE*)version,&bytes)==ERROR_SUCCESS&&!lstrcmpW(version,L"0.10.0");RegCloseKey(key);if(current)RegDeleteKeyW(HKEY_CURRENT_USER,reg);
 }
 MessageBoxW(NULL,L"Pirb Desk 0.10.0 removed. Preferences kept.\nĐã gỡ Pirb Desk 0.10.0. Tùy chọn được giữ lại.",title,MB_OK|MB_ICONINFORMATION);ExitProcess(0);
}
