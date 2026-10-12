using System;
using System.IO;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

// Up to three fixed immutable assets, one bounded worker, no filesystem routing or child process.
public sealed class IW7HudHttp : IDisposable
{
    public const string Route = "/mods/paris_lab_hud/mod.ff";
    public const string ModelRoute = "/mods/paris_model_probe/mod.ff";
    public const string BeaconRoute = "/mods/sdk_beacon/mod.ff";
    public const string SelfContainedBeaconRoute = "/mods/sdk_beacon_self_contained/mod.ff";
    public const string SoundRoute = "/mods/sdk_original_sound_v1/mod.ff";
    public const string SoundLoadedRoute = "/mods/sdk_original_sound_v1/mod.sabl";
    public const string SoundStreamedRoute = "/mods/sdk_original_sound_v1/mod.sabs";
    // Legacy properties identify the primary FF; the journal identifies every completed asset GET.
    public string AssetRoute { get; private set; }
    private readonly Asset[] assets;
    private readonly string journal;
    private readonly TcpListener listener;
    private readonly Thread worker;
    private readonly object sync = new object();
    private TcpClient active;
    private volatile bool stopping;
    private int gets;
    public string SHA256 { get; private set; }
    public string BaseUrl { get; private set; }
    public string Error { get; private set; }
    public bool Stopped { get { return !worker.IsAlive; } }
    public int CompletedGets { get { return Volatile.Read(ref gets); } }

    public IW7HudHttp(byte[] bytes, string expectedHash, string logPath)
        : this(bytes, expectedHash, logPath, Route) { }

    public IW7HudHttp(byte[] bytes, string expectedHash, string logPath, string route)
        : this(LegacyAsset(bytes, expectedHash, route), logPath) { }

    public IW7HudHttp(byte[] ff, string ffHash, byte[] sabl, string sablHash,
        byte[] sabs, string sabsHash, string logPath)
        : this(new[] {
            new Asset(ff, ffHash, SoundRoute, 1600),
            new Asset(sabl, sablHash, SoundLoadedRoute, 128 * 1024),
            new Asset(sabs, sabsHash, SoundStreamedRoute, 4096)
        }, logPath) { }

    private sealed class Asset
    {
        public readonly string Route;
        public readonly byte[] Payload;
        public readonly string SHA256;

        public Asset(byte[] bytes, string expectedHash, string route, int maximum)
        {
            if (bytes == null || bytes.Length == 0 || bytes.Length > maximum)
                throw new ArgumentException("Laboratory HTTP payload exceeds its route-specific bound.");
            Payload = (byte[])bytes.Clone();
            using (var hash = System.Security.Cryptography.SHA256.Create())
                SHA256 = BitConverter.ToString(hash.ComputeHash(Payload)).Replace("-", "");
            if (!String.Equals(SHA256, expectedHash, StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("HUD HTTP payload hash mismatch.");
            Route = route;
        }
    }

    private static Asset[] LegacyAsset(byte[] bytes, string expectedHash, string route)
    {
        // Preserve the historical one-asset whitelist, including its route-specific bounds.
        if (route != Route && route != ModelRoute && route != BeaconRoute && route != SelfContainedBeaconRoute)
            throw new ArgumentException("Unreviewed laboratory asset route.");
        int maximum = route == BeaconRoute || route == SelfContainedBeaconRoute ? 1024 * 1024 : 1600;
        return new[] { new Asset(bytes, expectedHash, route, maximum) };
    }

    private IW7HudHttp(Asset[] approvedAssets, string logPath)
    {
        // Every clone/hash/bound check completes before journal creation or listening.
        assets = approvedAssets;
        AssetRoute = assets[0].Route;
        SHA256 = assets[0].SHA256;
        journal = Path.GetFullPath(logPath);
        // Never append evidence from an earlier run.
        using (new FileStream(journal, FileMode.CreateNew, FileAccess.Write, FileShare.Read)) { }
        listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start(4);
        BaseUrl = "http://127.0.0.1:" + ((IPEndPoint)listener.LocalEndpoint).Port;
        worker = new Thread(Run) { IsBackground = true, Name = "IW7HudHttp" };
        try { worker.Start(); } catch { listener.Stop(); throw; }
    }

    private void Run()
    {
        try
        {
            int attempts = 0;
            while (!stopping && attempts++ < 64)
            {
                TcpClient client = listener.AcceptTcpClient();
                lock (sync) { if (stopping) { client.Dispose(); break; } active = client; }
                try { Serve(client); }
                catch (IOException) { /* bounded incomplete request/disconnected recipient */ }
                catch (SocketException) { }
                finally { lock (sync) { active = null; } client.Dispose(); }
            }
            if (!stopping) Error = "HTTP request budget exhausted.";
        }
        catch (Exception e) { if (!stopping) Error = e.GetType().Name + ": " + e.Message; }
        finally { listener.Stop(); }
    }

    private void Serve(TcpClient client)
    {
        client.ReceiveTimeout = 2000; client.SendTimeout = 2000;
        NetworkStream stream = client.GetStream();
        Stopwatch timeout = Stopwatch.StartNew();
        byte[] header = new byte[4096]; int length = 0;
        while (length < header.Length)
        {
            if (timeout.ElapsedMilliseconds >= 2000) return;
            int b = stream.ReadByte(); if (b < 0) return;
            header[length++] = (byte)b;
            if (length >= 4 && header[length-4] == 13 && header[length-3] == 10 &&
                header[length-2] == 13 && header[length-1] == 10) break;
        }
        if (length < 4 || header[length-4] != 13 || header[length-3] != 10 ||
            header[length-2] != 13 || header[length-1] != 10) return;
        string first = Encoding.ASCII.GetString(header, 0, length).Split(new[] {"\r\n"}, StringSplitOptions.None)[0];
        Asset selected = null;
        foreach (Asset asset in assets)
        {
            if (first == "GET " + asset.Route + " HTTP/1.1" || first == "GET " + asset.Route + " HTTP/1.0")
            { selected = asset; break; }
        }
        bool allowed = selected != null;
        byte[] response = Encoding.ASCII.GetBytes(allowed ?
            "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: " + selected.Payload.Length + "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" :
            "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
        stream.Write(response, 0, response.Length);
        if (!allowed) return;
        stream.Write(selected.Payload, 0, selected.Payload.Length); stream.Flush();
        string row = "{\"utc\":\"" + DateTime.UtcNow.ToString("o") + "\",\"method\":\"GET\",\"path\":\"" + selected.Route +
            "\",\"bytes\":" + selected.Payload.Length + ",\"sha256\":\"" + selected.SHA256 + "\"}\n";
        try { File.AppendAllText(journal, row, new UTF8Encoding(false)); }
        catch (IOException e) { Error = "HTTP journal failed: " + e.Message; return; }
        Interlocked.Increment(ref gets);
    }

    public void Dispose()
    {
        stopping = true; listener.Stop();
        lock (sync) { if (active != null) active.Dispose(); }
        if (!worker.Join(5000)) throw new IOException("HUD HTTP worker closure unconfirmed; retain reservation.");
    }
}
