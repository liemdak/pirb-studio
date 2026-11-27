#define UNICODE
#define _UNICODE
#include <windows.h>
/* Small native GUI launcher: only Windows system APIs, no extra C runtime. */
static wchar_t root[32768],runtime[32768],entry[32768],command[32768],error[1024];
DWORD _tls_index=0;
static STARTUPINFOW startup;
static PROCESS_INFORMATION process;
void pirb_start(void) {
 DWORD n=GetModuleFileNameW(NULL,root,32768);
 if(!n||n>32000)ExitProcess(1);
 while(n&&root[n]!=L'\\')n--;
 if(!n)ExitProcess(1);root[n]=0;
 lstrcpyW(runtime,root);lstrcatW(runtime,L"\\_internal\\pirb-runtime.exe");
 lstrcpyW(entry,root);lstrcatW(entry,L"\\_internal\\app\\launch.py");
 if(GetFileAttributesW(runtime)==INVALID_FILE_ATTRIBUTES||GetFileAttributesW(entry)==INVALID_FILE_ATTRIBUTES){MessageBoxW(NULL,L"Hãy giải nén TOÀN BỘ gói PIRB, giữ nguyên thư mục _internal cạnh PirbDesk.exe.",L"PIRB · Chưa đủ tệp",MB_OK|MB_ICONINFORMATION);ExitProcess(1);}
 wchar_t *args=GetCommandLineW();
 if(*args==L'"'){args++;while(*args&&*args!=L'"')args++;if(*args)args++;}
 else while(*args&&*args>L' ')args++;
 while(*args==L' ')args++;
 if(lstrlenW(runtime)+lstrlenW(entry)+lstrlenW(args)+8>=32768)ExitProcess(1);
 lstrcpyW(command,L"\"");lstrcatW(command,runtime);lstrcatW(command,L"\" \"");lstrcatW(command,entry);lstrcatW(command,L"\" ");lstrcatW(command,args);
 startup.cb=sizeof(startup);
 if(!CreateProcessW(runtime,command,NULL,NULL,FALSE,0,NULL,root,&startup,&process)){
  wsprintfW(error,L"Không mở được PIRB. Mã Windows: %lu.\nHãy kiểm tra bạn đã giải nén toàn bộ thư mục.",GetLastError());MessageBoxW(NULL,error,L"PIRB",MB_OK|MB_ICONERROR);ExitProcess(1);}
 CloseHandle(process.hThread);WaitForSingleObject(process.hProcess,INFINITE);DWORD code=0;GetExitCodeProcess(process.hProcess,&code);CloseHandle(process.hProcess);ExitProcess(code);
}
