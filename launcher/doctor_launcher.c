// doctor.exe: runs DevosMapDoctor.exe --cli in this console and returns its exit code.
#include <windows.h>
#include <wchar.h>

static PROCESS_INFORMATION child;
static HANDLE job;

static BOOL WINAPI on_ctrl(DWORD kind) {
    (void)kind;
    if (job) {
        struct { JOBOBJECT_BASIC_PROCESS_ID_LIST head; ULONG_PTR more[255]; } list;
        ZeroMemory(&list, sizeof list);
        if (QueryInformationJobObject(job, JobObjectBasicProcessIdList, &list, sizeof list, NULL)) {
            for (DWORD i = 0; i < list.head.NumberOfProcessIdsInList; i++) {
                DWORD pid = (DWORD)list.head.ProcessIdList[i];
                if (pid == child.dwProcessId) continue;
                HANDLE h = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
                if (h) {
                    TerminateProcess(h, 130);
                    CloseHandle(h);
                }
            }
        }
        if (WaitForSingleObject(child.hProcess, 5000) != WAIT_OBJECT_0) TerminateJobObject(job, 130);
    } else if (child.hProcess) {
        TerminateProcess(child.hProcess, 130);
    }
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
    job = CreateJobObjectW(NULL, NULL);
    if (job) {
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits;
        ZeroMemory(&limits, sizeof limits);
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof limits)) {
            CloseHandle(job);
            job = NULL;
        }
    }
    SetConsoleCtrlHandler(on_ctrl, TRUE);
    if (!CreateProcessW(exe, line, NULL, NULL, TRUE, job ? CREATE_SUSPENDED : 0, NULL, NULL, &si, &child)) {
        say(L"doctor: DevosMapDoctor.exe did not start\n");
        return 2;
    }
    if (job && !AssignProcessToJobObject(job, child.hProcess)) {
        CloseHandle(job);
        job = NULL;
        ResumeThread(child.hThread);
    } else if (job) {
        ResumeThread(child.hThread);
    }
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(child.hProcess, &code);
    CloseHandle(child.hThread);
    CloseHandle(child.hProcess);
    return (int)code;
}
