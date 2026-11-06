// IW7 client diagnostics, injected into an owned private test client:
//  - engine error journal: hooks Com_Error (iw7_ship 0x140B8D830), appends "code caller message" to the
//    file named by IW7_ERROR_JOURNAL, then forwards the error unchanged;
//  - optional GPU frame capture: IW7_RDOC_DLL (renderdoc.dll, loaded right after injection, before the
//    D3D device exists), IW7_RDOC_OUT (capture path template), IW7_RDOC_CAPTURE_MS (delay after injection).
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <intrin.h>
#include "MinHook.h"
#include <dbghelp.h>
#include <stdbool.h>
#include "renderdoc_app.h"

typedef void (*com_error_t)(int code, const char* fmt, ...);
static com_error_t original;
static char journal[MAX_PATH];

static void append(const char* line)
{
    HANDLE f = CreateFileA(journal, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    DWORD w; WriteFile(f, line, (DWORD)strlen(line), &w, NULL); CloseHandle(f);
}

static void hooked(int code, const char* fmt, ...)
{
    char message[4096], line[4400];
    va_list a; va_start(a, fmt); _vsnprintf_s(message, sizeof(message), _TRUNCATE, fmt ? fmt : "", a); va_end(a);
    _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] Com_Error code=%d caller=%p message=%s\r\n", GetTickCount64(), code, _ReturnAddress(), message);
    append(line);
    original(code, "%s", message);
}

static DWORD WINAPI install(LPVOID unused)
{
    char line[256];
    Sleep(6000); // the game image is unpacked and iw7-mod has installed its own hooks by then
    MH_STATUS s = MH_Initialize();
    if (s == MH_OK || s == MH_ERROR_ALREADY_INITIALIZED) s = MH_CreateHook((LPVOID)0x140B8D830, (LPVOID)hooked, (LPVOID*)&original);
    if (s == MH_OK) s = MH_EnableHook((LPVOID)0x140B8D830);
    _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] journal installed status=%d\r\n", GetTickCount64(), (int)s);
    append(line);
    return 0;
}

static DWORD WINAPI rdoc_capture(LPVOID unused)
{
    char path[MAX_PATH], out[MAX_PATH], ms[32], line[512];
    if (!GetEnvironmentVariableA("IW7_RDOC_DLL", path, sizeof(path))) return 0;
    HMODULE m = LoadLibraryA(path);
    _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] renderdoc loaded=%d\r\n", GetTickCount64(), m != NULL);
    append(line);
    if (!m) return 0;
    DWORD delay = GetEnvironmentVariableA("IW7_RDOC_CAPTURE_MS", ms, sizeof(ms)) ? (DWORD)atoi(ms) : 40000;
    Sleep(delay);
    pRENDERDOC_GetAPI get = (pRENDERDOC_GetAPI)GetProcAddress(m, "RENDERDOC_GetAPI");
    RENDERDOC_API_1_1_2* api = NULL;
    if (!get || !get(eRENDERDOC_API_Version_1_1_2, (void**)&api) || !api) { append("renderdoc api unavailable\r\n"); return 0; }
    if (GetEnvironmentVariableA("IW7_RDOC_OUT", out, sizeof(out))) api->SetCaptureFilePathTemplate(out);
    api->TriggerCapture();
    Sleep(5000);
    _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] renderdoc captures=%u\r\n", GetTickCount64(), api->GetNumCaptures());
    append(line);
    return 0;
}

// optional diagnostic dvar override for the owned test client: IW7_DVAR_FORCE="name=int;name=int"
// (re-applied once per second for IW7_DVAR_FORCE_SECONDS, default 240, so map loads cannot reset it)
typedef void* (*dvar_find_t)(const char* name);
typedef void (*dvar_set_int_t)(void* dvar, int value);
static DWORD WINAPI dvar_force(LPVOID unused)
{
    char spec[1024], secs[32], line[512];
    if (!GetEnvironmentVariableA("IW7_DVAR_FORCE", spec, sizeof(spec))) return 0;
    int seconds = GetEnvironmentVariableA("IW7_DVAR_FORCE_SECONDS", secs, sizeof(secs)) ? atoi(secs) : 240;
    dvar_find_t find = (dvar_find_t)0x140CEA460;
    dvar_set_int_t set_int = (dvar_set_int_t)0x140CED3D0;
    char delay[32];
    if (GetEnvironmentVariableA("IW7_DVAR_FORCE_EARLY", delay, sizeof(delay)))
    {
        // set the first listed dvar the moment it is registered (before the renderer starts using it)
        char name[256]; lstrcpynA(name, spec, sizeof(name));
        char* eq = strchr(name, '='); if (!eq) return 0; *eq = 0;
        const int value = atoi(eq + 1);
        Sleep(1000);
        for (int i = 0; i < 12000; i++)
        {
            void* d = NULL;
            __try { d = find(name); } __except (EXCEPTION_EXECUTE_HANDLER) { d = NULL; }
            if (d)
            {
                *(int*)((unsigned char*)d + 16) = value;
                _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] dvar early %s=%d after %d polls\r\n", GetTickCount64(), name, value, i);
                append(line);
                break;
            }
            Sleep(5);
        }
        Sleep(2000);
    }
    else
        Sleep(GetEnvironmentVariableA("IW7_DVAR_FORCE_DELAY_MS", delay, sizeof(delay)) ? (DWORD)atoi(delay) : 8000);
    for (int t = 0; t < seconds; t++)
    {
        char copy[1024]; lstrcpynA(copy, spec, sizeof(copy));
        char* ctx = NULL;
        for (char* item = strtok_s(copy, ";", &ctx); item; item = strtok_s(NULL, ";", &ctx))
        {
            char* eq = strchr(item, '=');
            if (!eq) continue;
            *eq = 0;
            void* d = find(item);
            if (d && eq[1] != '?') { set_int(d, atoi(eq + 1)); *(int*)((unsigned char*)d + 16) = atoi(eq + 1); } // enums ignore Dvar_SetInt
            if (t == 0 || t == seconds - 1)
            {
                const unsigned char* b = (const unsigned char*)d;
                _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] dvar force %s=%s found=%d flags=%08x type=%u current=%d\r\n",
                    GetTickCount64(), item, eq + 1, d != NULL, d ? *(const unsigned int*)(b + 4) : 0, d ? b[9] : 0, d ? *(const int*)(b + 16) : 0);
                append(line);
            }
        }
        Sleep(1000);
    }
    return 0;
}

// first-chance access violations inside the game image (first 8), with registers: crash sites the
// iw7-mod handler cannot dump (fast-fail after a fault, early faults) still leave a trace
static volatile LONG veh_count;
static LONG CALLBACK veh(PEXCEPTION_POINTERS e)
{
    if (e->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION) return EXCEPTION_CONTINUE_SEARCH;
    ULONG_PTR ip = (ULONG_PTR)e->ExceptionRecord->ExceptionAddress;
    if (ip < 0x140000000ull || ip > 0x150000000ull) return EXCEPTION_CONTINUE_SEARCH;
    if (InterlockedIncrement(&veh_count) > 40) return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT* c = e->ContextRecord; char line[1024];
    _snprintf_s(line, sizeof(line), _TRUNCATE,
        "[%llu] AV ip=%p op=%llu addr=%p rax=%llx rbx=%llx rcx=%llx rdx=%llx rsi=%llx rdi=%llx rbp=%llx rsp=%llx r8=%llx r9=%llx r10=%llx r11=%llx r12=%llx r13=%llx r14=%llx r15=%llx ret=%llx\r\n",
        GetTickCount64(), (void*)ip, (unsigned long long)e->ExceptionRecord->ExceptionInformation[0], (void*)e->ExceptionRecord->ExceptionInformation[1],
        c->Rax, c->Rbx, c->Rcx, c->Rdx, c->Rsi, c->Rdi, c->Rbp, c->Rsp, c->R8, c->R9, c->R10, c->R11, c->R12, c->R13, c->R14, c->R15,
        *(unsigned long long*)c->Rsp);
    append(line);
    // first fault only: full-memory dump next to the journal (IW7_FAULT_DUMP=1)
    char want[8];
    static volatile LONG dumped;
    if (GetEnvironmentVariableA("IW7_FAULT_DUMP", want, sizeof(want)) && InterlockedExchange(&dumped, 1) == 0)
    {
        char path[MAX_PATH + 8];
        _snprintf_s(path, sizeof(path), _TRUNCATE, "%s.dmp", journal);
        HANDLE f = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (f != INVALID_HANDLE_VALUE)
        {
            MINIDUMP_EXCEPTION_INFORMATION mei = {GetCurrentThreadId(), e, FALSE};
            MiniDumpWriteDump(GetCurrentProcess(), GetCurrentProcessId(), f,
                (MINIDUMP_TYPE)(MiniDumpWithFullMemory | MiniDumpWithHandleData | MiniDumpWithThreadInfo), &mei, NULL, NULL);
            CloseHandle(f);
            append("full dump written\r\n");
        }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

// client connection state (clientUIActives[0] at 0x142246C30): logged on every change
static DWORD WINAPI client_state(LPVOID unused)
{
    char line[256]; int last[4] = {-1, -1, -1, -1};
    Sleep(3000);
    for (int t = 0; t < 4000; t++)
    {
        const unsigned char* c = (const unsigned char*)0x142246C30;
        int now[4] = {c[0], *(const int*)(c + 4), *(const int*)(c + 8), c[33]};
        if (memcmp(now, last, sizeof(now)))
        {
            _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] client active=%d keyCatchers=%x connState=%d cgameInit=%d\r\n", GetTickCount64(), now[0], now[1], now[2], now[3]);
            append(line);
            memcpy(last, now, sizeof(now));
        }
        Sleep(50);
    }
    return 0;
}

// LuaFile assets (LUI scripts) of the loaded zones: written to IW7_LUA_DUMP/<sanitized name> on "@luadump"
typedef struct { const char* name; int len; char strippingType; const char* buffer; } lua_file_t;
typedef char (*db_enum_t)(int type, void (*cb)(void* header, void* data), const void* data);
static int lua_dumped;
static void lua_dump_one(void* header, void* data)
{
    char dir[MAX_PATH], path[MAX_PATH * 2], name[MAX_PATH];
    lua_file_t* lua = (lua_file_t*)header;
    if (!lua || !lua->name || !lua->buffer || lua->len <= 0) return;
    if (!GetEnvironmentVariableA("IW7_LUA_DUMP", dir, sizeof(dir))) return;
    int i = 0;
    for (const char* c = lua->name; *c && i < MAX_PATH - 1; c++) name[i++] = (*c == '/' || *c == '\\' || *c == ':') ? '_' : *c;
    name[i] = 0;
    _snprintf_s(path, sizeof(path), _TRUNCATE, "%s\\%s", dir, name);
    HANDLE f = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, 0, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    DWORD w;
    WriteFile(f, lua->buffer, (DWORD)lua->len, &w, NULL);
    CloseHandle(f);
    lua_dumped++;
}
static void lua_dump(void)
{
    char dir[MAX_PATH], line[300];
    if (!GetEnvironmentVariableA("IW7_LUA_DUMP", dir, sizeof(dir))) return;
    CreateDirectoryA(dir, NULL);
    lua_dumped = 0;
    ((db_enum_t)0x140A76CE0)(59, lua_dump_one, NULL);
    _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] luadump files=%d\r\n", GetTickCount64(), lua_dumped);
    append(line);
}

// timed console commands (frontend scenarios without GSC): IW7_TIMED_CMDS="<ms after injection>:<command>|..."
typedef void (*cbuf_add_text_t)(int local_client, const char* text);
static DWORD WINAPI timed_cmds(LPVOID unused)
{
    char spec[2048], line[600];
    if (!GetEnvironmentVariableA("IW7_TIMED_CMDS", spec, sizeof(spec))) return 0;
    cbuf_add_text_t add = (cbuf_add_text_t)0x140B7C290;
    ULONGLONG start = GetTickCount64();
    char* ctx = NULL;
    for (char* item = strtok_s(spec, "|", &ctx); item; item = strtok_s(NULL, "|", &ctx))
    {
        char* colon = strchr(item, ':');
        if (!colon) continue;
        *colon = 0;
        ULONGLONG at = start + (ULONGLONG)_atoi64(item);
        while (GetTickCount64() < at) Sleep(50);
        if (!strcmp(colon + 1, "@luadump")) { lua_dump(); continue; }
        char cmd[512];
        _snprintf_s(cmd, sizeof(cmd), _TRUNCATE, "%s\n", colon + 1);
        add(0, cmd);
        _snprintf_s(line, sizeof(line), _TRUNCATE, "[%llu] cmd %s\r\n", GetTickCount64(), colon + 1);
        append(line);
    }
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID r)
{
    if (reason == DLL_PROCESS_ATTACH)
    {
        DisableThreadLibraryCalls(h);
        AddVectoredExceptionHandler(1, veh);
        if (!GetEnvironmentVariableA("IW7_ERROR_JOURNAL", journal, sizeof(journal)))
            lstrcpyA(journal, "iw7-error-journal.log");
        CloseHandle(CreateThread(NULL, 0, rdoc_capture, NULL, 0, NULL));
        CloseHandle(CreateThread(NULL, 0, install, NULL, 0, NULL));
        CloseHandle(CreateThread(NULL, 0, dvar_force, NULL, 0, NULL));
        CloseHandle(CreateThread(NULL, 0, client_state, NULL, 0, NULL));
        CloseHandle(CreateThread(NULL, 0, timed_cmds, NULL, 0, NULL));
    }
    return TRUE;
}
