// doctor.exe - the Doctor's command line on Windows (1.6.6). DevosMapDoctor.exe is a window program: it has no console
// of its own, so a terminal would not wait for it nor show what it prints. This small console program runs it with
// --cli and the rest of the command line, hands it this console (stdin, stdout, stderr), waits, and returns its exit
// code. Ctrl+C stops it. It looks for DevosMapDoctor.exe in its own folder.
//
// Built by build.py with the zig from pip: python -m ziglang cc -target x86_64-windows-gnu -municode -O2 -s
#include <windows.h>
#include <wchar.h>

static PROCESS_INFORMATION child;

static BOOL WINAPI on_ctrl(DWORD kind) {
    (void)kind;
    if (child.hProcess) TerminateProcess(child.hProcess, 130);
    return TRUE;
}

static void say(const wchar_t *text) {
    DWORD n;
    HANDLE err = GetStdHandle(STD_ERROR_HANDLE);
    if (!WriteConsoleW(err, text, (DWORD)wcslen(text), &n, NULL)) {
        char buf[1024];
        int len = WideCharToMultiByte(CP_UTF8, 0, text, -1, buf, sizeof buf, NULL, NULL);
        if (len > 1) WriteFile(err, buf, (DWORD)(len - 1), &n, NULL);
    }
}

int wmain(void) {
    static wchar_t exe[32768], line[32768 + 64];
    DWORD n = GetModuleFileNameW(NULL, exe, 32768);
    if (!n || n >= 32768) return 2;
    wchar_t *slash = wcsrchr(exe, L'\\');
    if (!slash) return 2;
    wcscpy(slash + 1, L"DevosMapDoctor.exe");
    if (GetFileAttributesW(exe) == INVALID_FILE_ATTRIBUTES) {
        say(L"doctor: DevosMapDoctor.exe is not in the folder of doctor.exe\n");
        return 2;
    }
    // the arguments as they came: the command line after the program's own name (quoted or not)
    const wchar_t *rest = GetCommandLineW();
    if (*rest == L'"') {
        rest++;
        while (*rest && *rest != L'"') rest++;
        if (*rest) rest++;
    } else {
        while (*rest && *rest != L' ' && *rest != L'\t') rest++;
    }
    while (*rest == L' ' || *rest == L'\t') rest++;
    if (wcslen(exe) + wcslen(rest) + 16 >= sizeof line / sizeof line[0]) return 2;
    wcscpy(line, L"\"");
    wcscat(line, exe);
    wcscat(line, L"\" --cli ");
    wcscat(line, rest);

    STARTUPINFOW si;
    ZeroMemory(&si, sizeof si);
    si.cb = sizeof si;
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    SetConsoleCtrlHandler(on_ctrl, TRUE);
    if (!CreateProcessW(exe, line, NULL, NULL, TRUE, 0, NULL, NULL, &si, &child)) {
        say(L"doctor: DevosMapDoctor.exe did not start\n");
        return 2;
    }
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(child.hProcess, &code);
    CloseHandle(child.hThread);
    CloseHandle(child.hProcess);
    return (int)code;
}
