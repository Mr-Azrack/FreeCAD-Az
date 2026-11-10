// SPDX-License-Identifier: LGPL-2.1-or-later
// Offline GitHub metadata contract tests; no network or Windows Forms needed.
using System;
using System.IO;

static class OnlineUpdateTests {
    static void Assert(bool value, string message) {
        if (!value) throw new Exception(message);
    }
    static string Asset(string from, string to, string digest,
                        string url = null, bool prerelease = false) {
        string name = "AzDesignNative-" + from + "-to-" + to + ".azpatch";
        string href = url ?? ("https://github.com/Mr-Azrack/FreeCAD-Az/releases/download/v" +
            to + "/" + name);
        return "{\"draft\":false,\"prerelease\":" + (prerelease ? "true" : "false") +
            ",\"assets\":[{\"name\":\"" + name + "\",\"browser_download_url\":\"" +
            href + "\",\"digest\":\"" + digest + "\",\"size\":12345}]}";
    }
    public static void Main() {
        string hash = "sha256:" + new string('a', 64);
        var good = AzOnlineUpdates.Select(Asset("0.5.2", "0.5.3", hash), "0.5.2");
        Assert(good != null && good.To == "0.5.3" && good.Bytes == 12345,
            "Verified release patch was not selected");
        Assert(AzOnlineUpdates.Select(Asset("0.5.2", "0.5.3", hash), "0.5.1") == null,
            "Wrong baseline was accepted");
        Assert(AzOnlineUpdates.Select(Asset("0.5.2", "0.5.1", hash), "0.5.2") == null,
            "Downgrade was accepted");
        Assert(AzOnlineUpdates.Select(Asset("0.5.2", "0.5.3", hash, null, true), "0.5.2") == null,
            "Prerelease was accepted");
        Assert(AzOnlineUpdates.Select(Asset("0.5.2", "0.5.3", ""), "0.5.2") == null,
            "Missing GitHub digest was accepted");
        Assert(AzOnlineUpdates.Select(Asset("0.5.2", "0.5.3", "sha256:bad"), "0.5.2") == null,
            "Bad digest was accepted");
        Assert(AzOnlineUpdates.Select(
            Asset("0.5.2", "0.5.3", hash, "https://example.com/evil.azpatch"),
            "0.5.2") == null, "Untrusted download host was accepted");
        Console.WriteLine("PASS: verified GitHub update selection and rejected unsafe releases");
    }
}
