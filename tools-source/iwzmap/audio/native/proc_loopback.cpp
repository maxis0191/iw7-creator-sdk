// proc_loopback: record the audio one process tree renders (WASAPI process loopback, Windows 10 2004+).
// Only the target process and its children are captured: other applications on the machine are not.
//
//   proc_loopback.exe --pid <pid> --out <file.wav> [--seconds N] [--stop-file <path>]
//
// Writes 48 kHz stereo 16-bit PCM. The WAV header is rewritten every second, so the file stays valid
// if the recorder is killed. Stops when the target exits, after N seconds, or when the stop file exists.
// A sidecar <file.wav>.json records the start time (UTC, QPC), frames written and silent-buffer counts.
// Build: cl /EHsc /O2 proc_loopback.cpp /link ole32.lib mmdevapi.lib (from a VS x64 prompt).
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <audioclientactivationparams.h>
#include <cstdio>
#include <cstdint>
#include <string>
#include <vector>

#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "mmdevapi.lib")

namespace
{
    const UINT32 kRate = 48000;
    const UINT16 kChannels = 2;
    const UINT16 kBits = 16;

    class completion_handler : public IActivateAudioInterfaceCompletionHandler, public IAgileObject
    {
    public:
        HANDLE done = CreateEventW(nullptr, TRUE, FALSE, nullptr);
        HRESULT activate_result = E_FAIL;
        IAudioClient* client = nullptr;
        LONG refs = 1;

        STDMETHODIMP QueryInterface(REFIID riid, void** out) override
        {
            if (riid == __uuidof(IUnknown) || riid == __uuidof(IActivateAudioInterfaceCompletionHandler))
                *out = static_cast<IActivateAudioInterfaceCompletionHandler*>(this);
            else if (riid == __uuidof(IAgileObject))
                *out = static_cast<IAgileObject*>(this);
            else
            {
                *out = nullptr;
                return E_NOINTERFACE;
            }
            AddRef();
            return S_OK;
        }
        STDMETHODIMP_(ULONG) AddRef() override { return InterlockedIncrement(&refs); }
        STDMETHODIMP_(ULONG) Release() override
        {
            const auto r = InterlockedDecrement(&refs);
            if (!r) delete this;
            return r;
        }
        STDMETHODIMP ActivateCompleted(IActivateAudioInterfaceAsyncOperation* op) override
        {
            IUnknown* unk = nullptr;
            HRESULT hr = op->GetActivateResult(&activate_result, &unk);
            if (SUCCEEDED(hr) && SUCCEEDED(activate_result) && unk)
                activate_result = unk->QueryInterface(IID_PPV_ARGS(&client));
            else if (SUCCEEDED(activate_result))
                activate_result = hr;
            if (unk) unk->Release();
            SetEvent(done);
            return S_OK;
        }
    };

    void write_header(FILE* f, uint32_t data_bytes)
    {
        const uint32_t byte_rate = kRate * kChannels * kBits / 8;
        const uint16_t align = kChannels * kBits / 8;
        const uint32_t riff = 36 + data_bytes, fmt_size = 16;
        const uint16_t pcm = 1;
        fseek(f, 0, SEEK_SET);
        fwrite("RIFF", 1, 4, f); fwrite(&riff, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
        fwrite(&fmt_size, 4, 1, f); fwrite(&pcm, 2, 1, f); fwrite(&kChannels, 2, 1, f);
        fwrite(&kRate, 4, 1, f); fwrite(&byte_rate, 4, 1, f); fwrite(&align, 2, 1, f); fwrite(&kBits, 2, 1, f);
        fwrite("data", 1, 4, f); fwrite(&data_bytes, 4, 1, f);
        fseek(f, 0, SEEK_END);
    }

    bool file_exists(const std::wstring& path)
    {
        return !path.empty() && GetFileAttributesW(path.c_str()) != INVALID_FILE_ATTRIBUTES;
    }
}

int wmain(int argc, wchar_t** argv)
{
    DWORD pid = 0;
    double seconds = 600.0;
    std::wstring out, stop_file;
    for (int i = 1; i + 1 < argc; i += 2)
    {
        const std::wstring k = argv[i];
        if (k == L"--pid") pid = wcstoul(argv[i + 1], nullptr, 10);
        else if (k == L"--out") out = argv[i + 1];
        else if (k == L"--seconds") seconds = _wtof(argv[i + 1]);
        else if (k == L"--stop-file") stop_file = argv[i + 1];
    }
    if (!pid || out.empty())
    {
        fwprintf(stderr, L"usage: proc_loopback --pid <pid> --out <file.wav> [--seconds N] [--stop-file path]\n");
        return 2;
    }
    HANDLE target = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (!target)
    {
        fwprintf(stderr, L"cannot open process %lu\n", pid);
        return 3;
    }
    CoInitializeEx(nullptr, COINIT_MULTITHREADED);

    AUDIOCLIENT_ACTIVATION_PARAMS params{};
    params.ActivationType = AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK;
    params.ProcessLoopbackParams.TargetProcessId = pid;
    params.ProcessLoopbackParams.ProcessLoopbackMode = PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE;
    PROPVARIANT pv{};
    pv.vt = VT_BLOB;
    pv.blob.cbSize = sizeof(params);
    pv.blob.pBlobData = reinterpret_cast<BYTE*>(&params);

    auto* handler = new completion_handler();
    IActivateAudioInterfaceAsyncOperation* op = nullptr;
    HRESULT hr = ActivateAudioInterfaceAsync(VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK, __uuidof(IAudioClient), &pv, handler, &op);
    if (FAILED(hr))
    {
        fwprintf(stderr, L"ActivateAudioInterfaceAsync failed 0x%08lx\n", hr);
        return 4;
    }
    WaitForSingleObject(handler->done, 10000);
    if (FAILED(handler->activate_result) || !handler->client)
    {
        fwprintf(stderr, L"activation failed 0x%08lx\n", handler->activate_result);
        return 5;
    }
    IAudioClient* client = handler->client;

    WAVEFORMATEX wfx{};
    wfx.wFormatTag = WAVE_FORMAT_PCM;
    wfx.nChannels = kChannels;
    wfx.nSamplesPerSec = kRate;
    wfx.wBitsPerSample = kBits;
    wfx.nBlockAlign = kChannels * kBits / 8;
    wfx.nAvgBytesPerSec = kRate * wfx.nBlockAlign;
    HANDLE ready = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    hr = client->Initialize(AUDCLNT_SHAREMODE_SHARED,
                            AUDCLNT_STREAMFLAGS_LOOPBACK | AUDCLNT_STREAMFLAGS_EVENTCALLBACK | AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM,
                            200000, 0, &wfx, nullptr);
    if (FAILED(hr))
    {
        fwprintf(stderr, L"IAudioClient::Initialize failed 0x%08lx\n", hr);
        return 6;
    }
    client->SetEventHandle(ready);
    IAudioCaptureClient* capture = nullptr;
    hr = client->GetService(IID_PPV_ARGS(&capture));
    if (FAILED(hr))
    {
        fwprintf(stderr, L"GetService failed 0x%08lx\n", hr);
        return 7;
    }

    FILE* f = _wfopen(out.c_str(), L"wb+");
    if (!f)
    {
        fwprintf(stderr, L"cannot write %s\n", out.c_str());
        return 8;
    }
    write_header(f, 0);
    FILETIME start_ft{};
    GetSystemTimePreciseAsFileTime(&start_ft);
    LARGE_INTEGER qpc0{}, qpf{};
    QueryPerformanceCounter(&qpc0);
    QueryPerformanceFrequency(&qpf);
    client->Start();

    uint64_t frames = 0, silent_packets = 0, packets = 0, glitches = 0, padded_frames = 0;
    uint32_t data_bytes = 0;
    ULONGLONG last_flush = GetTickCount64(), t0 = last_flush;
    std::vector<BYTE> zeros;
    int exit_reason = 0;  // 0 time, 1 target exited, 2 stop file
    for (;;)
    {
        HANDLE waits[2] = {ready, target};
        const DWORD w = WaitForMultipleObjects(2, waits, FALSE, 500);
        if (w == WAIT_OBJECT_0 + 1) { exit_reason = 1; break; }
        UINT32 next = 0;
        while (SUCCEEDED(capture->GetNextPacketSize(&next)) && next)
        {
            BYTE* data = nullptr;
            UINT32 n = 0;
            DWORD flags = 0;
            UINT64 dev_pos = 0, qpc_pos = 0;  // qpc_pos: 100 ns units
            if (FAILED(capture->GetBuffer(&data, &n, &flags, &dev_pos, &qpc_pos))) break;
            const UINT32 bytes = n * wfx.nBlockAlign;
            // The loopback stream can pause while the target renders nothing: place each packet on the
            // wall clock (its QPC timestamp) and fill the gap with silence, so file time == real time.
            if (qpc_pos)
            {
                const double start_100ns = qpc0.QuadPart * 1e7 / double(qpf.QuadPart);
                const double at = (double(qpc_pos) - start_100ns) * kRate / 1e7;
                if (at > double(frames) + kRate / 50)
                {
                    const uint64_t pad = uint64_t(at) - frames;
                    zeros.assign(size_t(pad) * wfx.nBlockAlign, 0);
                    fwrite(zeros.data(), 1, zeros.size(), f);
                    data_bytes += uint32_t(zeros.size());
                    frames += pad;
                    padded_frames += pad;
                }
            }
            if (flags & AUDCLNT_BUFFERFLAGS_DATA_DISCONTINUITY) glitches++;
            if (flags & AUDCLNT_BUFFERFLAGS_SILENT)
            {
                zeros.assign(bytes, 0);
                fwrite(zeros.data(), 1, bytes, f);
                silent_packets++;
            }
            else
                fwrite(data, 1, bytes, f);
            data_bytes += bytes;
            frames += n;
            packets++;
            capture->ReleaseBuffer(n);
        }
        const ULONGLONG now = GetTickCount64();
        if (now - last_flush >= 1000)
        {
            write_header(f, data_bytes);
            fflush(f);
            last_flush = now;
            if (file_exists(stop_file)) { exit_reason = 2; break; }
        }
        if ((now - t0) / 1000.0 >= seconds) { exit_reason = 0; break; }
    }
    client->Stop();
    write_header(f, data_bytes);
    fclose(f);

    ULARGE_INTEGER u{};
    u.LowPart = start_ft.dwLowDateTime;
    u.HighPart = start_ft.dwHighDateTime;
    const std::wstring side = out + L".json";
    FILE* j = _wfopen(side.c_str(), L"w");
    if (j)
    {
        fprintf(j, "{\"schema\":\"iwz.proc-loopback/1\",\"pid\":%lu,\"rate\":%u,\"channels\":%u,\"bits\":%u,"
                   "\"start_filetime_utc\":%llu,\"start_qpc\":%lld,\"qpc_frequency\":%lld,\"frames\":%llu,"
                   "\"seconds\":%.3f,\"packets\":%llu,\"silent_packets\":%llu,\"discontinuities\":%llu,\"padded_frames\":%llu,\"exit\":\"%s\"}\n",
                pid, kRate, kChannels, kBits, u.QuadPart, qpc0.QuadPart, qpf.QuadPart, frames, frames / double(kRate),
                packets, silent_packets, glitches, padded_frames, exit_reason == 1 ? "target-exited" : exit_reason == 2 ? "stop-file" : "time");
        fclose(j);
    }
    capture->Release();
    client->Release();
    CloseHandle(target);
    printf("frames=%llu seconds=%.2f silent_packets=%llu\n", frames, frames / double(kRate), silent_packets);
    return 0;
}
