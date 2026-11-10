// SPDX-License-Identifier: LGPL-2.1-or-later
// Conservative GitHub Release discovery. Never install an unsigned/unchecked asset.
using System;
using System.Collections;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

internal sealed class AzAvailablePatch {
    internal string From;
    internal string To;
    internal string Url;
    internal string Sha256;
    internal long Bytes;
}

internal static class AzOnlineUpdates {
    private const string ReleaseApi =
        "https://api.github.com/repos/Mr-Azrack/FreeCAD-Az/releases/latest";
    private const string ReleaseBase =
        "https://github.com/Mr-Azrack/FreeCAD-Az/releases/download/";
    private static readonly Regex VersionPattern =
        new Regex(@"^\d+\.\d+\.\d+$", RegexOptions.CultureInvariant);
    private static readonly Regex HashPattern =
        new Regex(@"^[0-9a-fA-F]{64}$", RegexOptions.CultureInvariant);

    private static string StringValue(IDictionary obj, string key) {
        return obj.Contains(key) && obj[key] != null ? Convert.ToString(obj[key]) : "";
    }
    private static bool Flag(IDictionary obj, string key) {
        return obj.Contains(key) && obj[key] != null && Convert.ToBoolean(obj[key]);
    }
    private static IDictionary Parse(string raw) {
        return new JavaScriptSerializer().DeserializeObject(raw) as IDictionary
            ?? throw new InvalidDataException("Invalid release metadata.");
    }
    internal static string InstalledVersion(string root) {
        string marker = Path.Combine(root, "AZ Native Version.json");
        if (!File.Exists(marker)) throw new FileNotFoundException("Native installed version missing.", marker);
        IDictionary state = Parse(File.ReadAllText(marker));
        if (StringValue(state, "product") != "AzDesignNative")
            throw new InvalidDataException("Not an Az Design Native installation.");
        string version = StringValue(state, "version");
        if (!VersionPattern.IsMatch(version))
            throw new InvalidDataException("Installed version is invalid.");
        return version;
    }
    private static int Compare(string a, string b) {
        var x = a.Split('.');
        var y = b.Split('.');
        for (int i = 0; i < 3; ++i) {
            int c = int.Parse(x[i]).CompareTo(int.Parse(y[i]));
            if (c != 0) return c;
        }
        return 0;
    }
    private static WebClient Client() {
        ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;
        var client = new WebClient();
        client.Headers[HttpRequestHeader.UserAgent] = "DesignNative-Updater/1";
        client.Headers[HttpRequestHeader.Accept] = "application/vnd.github+json";
        return client;
    }
    internal static AzAvailablePatch Find(string installed) {
        if (!VersionPattern.IsMatch(installed)) throw new InvalidDataException("Invalid local version.");
        string raw;
        using (var client = Client()) raw = client.DownloadString(ReleaseApi);
        return Select(raw, installed);
    }
    // Pure metadata-selection routine also used by Windows offline tests.
    internal static AzAvailablePatch Select(string releaseJson, string installed) {
        IDictionary release = Parse(releaseJson);
        if (Flag(release, "draft") || Flag(release, "prerelease"))
            return null;
        var assets = release["assets"] as object[];
        if (assets == null) return null;
        AzAvailablePatch selected = null;
        foreach (object value in assets) {
            IDictionary asset = value as IDictionary;
            if (asset == null) continue;
            string name = StringValue(asset, "name");
            var match = Regex.Match(name,
                @"^AzDesignNative-(\d+\.\d+\.\d+)-to-(\d+\.\d+\.\d+)\.azpatch$",
                RegexOptions.CultureInvariant);
            if (!match.Success || match.Groups[1].Value != installed) continue;
            string to = match.Groups[2].Value;
            if (Compare(to, installed) <= 0) continue;
            string url = StringValue(asset, "browser_download_url");
            string digest = StringValue(asset, "digest");
            string prefix = "sha256:";
            if (!digest.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                continue;
            string sha = digest.Substring(prefix.Length);
            Uri uri;
            if (!HashPattern.IsMatch(sha) || !Uri.TryCreate(url, UriKind.Absolute, out uri) ||
                uri.Scheme != Uri.UriSchemeHttps ||
                !uri.Host.Equals("github.com", StringComparison.OrdinalIgnoreCase) ||
                !url.StartsWith(ReleaseBase, StringComparison.Ordinal))
                continue;
            long bytes = Convert.ToInt64(asset["size"]);
            if (bytes <= 0 || bytes > 2147483648L) continue;
            if (selected == null || Compare(to, selected.To) > 0)
                selected = new AzAvailablePatch { From=installed, To=to, Url=url,
                                                   Sha256=sha.ToLowerInvariant(), Bytes=bytes };
        }
        return selected;
    }
    internal static string DownloadVerified(AzAvailablePatch patch) {
        string folder = Path.Combine(Path.GetTempPath(), "DesignNative-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(folder);
        string destination = Path.Combine(folder, "update.azpatch");
        try {
            using (var client = Client()) client.DownloadFile(patch.Url, destination);
            if (new FileInfo(destination).Length != patch.Bytes)
                throw new InvalidDataException("Patch download length does not match GitHub.");
            using (var stream = File.OpenRead(destination))
            using (var sha = SHA256.Create()) {
                string actual = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
                if (!actual.Equals(patch.Sha256, StringComparison.Ordinal))
                    throw new InvalidDataException("Patch SHA256 failed GitHub release verification.");
            }
            return destination;
        } catch {
            if (File.Exists(destination)) File.Delete(destination);
            try { Directory.Delete(folder); } catch { }
            throw;
        }
    }
}
