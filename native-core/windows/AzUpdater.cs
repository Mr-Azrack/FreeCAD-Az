// SPDX-License-Identifier: LGPL-2.1-or-later
// Small native GUI wrapper for Az Design Native patch packages.
// Runs the independent PowerShell apply process AFTER this GUI exits.
using System;
using System.Diagnostics;
using System.Drawing;
using System.ComponentModel;
using System.IO;
using System.Text.RegularExpressions;
using System.Windows.Forms;

static class AzNativeUpdater
{
    static string root;
    static Form window;
    static Label versionLabel;

    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
        window = new Form();
        window.Text = "Design Native – Update";
        window.AutoScaleMode = AutoScaleMode.Font;
        window.Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 10.5f, FontStyle.Regular);
        window.ClientSize = new Size(560, 318);
        window.FormBorderStyle = FormBorderStyle.FixedDialog;
        window.StartPosition = FormStartPosition.CenterScreen;
        window.MaximizeBox = false;
        window.MinimizeBox = false;

        Label heading = new Label();
        heading.Text = "Design Native updater";
        heading.Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 15, FontStyle.Bold);
        heading.Location = new Point(20, 18);
        heading.Size = new Size(520, 34);
        window.Controls.Add(heading);

        versionLabel = new Label();
        versionLabel.Text = VersionText();
        versionLabel.Location = new Point(20, 64);
        versionLabel.Size = new Size(520, 28);
        window.Controls.Add(versionLabel);

        Label help = new Label();
        help.Text = "Check approved GitHub releases for a small verified patch. Save and close Design before installing. Manual patch and rollback remain available.";
        help.Location = new Point(20, 105);
        help.Size = new Size(520, 68);
        window.Controls.Add(help);

        Button check = new Button();
        check.Text = "Check for Updates";
        check.Location = new Point(20, 188);
        check.Size = new Size(520, 46);
        check.Click += (sender, e) => CheckOnline(check);
        window.Controls.Add(check);

        Button apply = new Button();
        apply.Text = "Install patch ZIP...";
        apply.Location = new Point(20, 256);
        apply.Size = new Size(166, 43);
        apply.Click += (s, e) => ChoosePatch();
        window.Controls.Add(apply);

        Button rollback = new Button();
        rollback.Text = "Roll back update";
        rollback.Location = new Point(197, 256);
        rollback.Size = new Size(166, 43);
        rollback.Click += (s, e) => Rollback();
        window.Controls.Add(rollback);

        Button close = new Button();
        close.Text = "Close";
        close.Location = new Point(375, 256);
        close.Size = new Size(165, 43);
        close.Click += (s, e) => window.Close();
        window.Controls.Add(close);

        Application.Run(window);
    }

    static string VersionText()
    {
        string marker = Path.Combine(root, "AZ Native Version.json");
        if (!File.Exists(marker)) return "This app is missing its installed version marker.";
        Match match = Regex.Match(File.ReadAllText(marker), "\"version\"\\s*:\\s*\"([^\"]+)\"");
        return match.Success ? "Installed version: " + match.Groups[1].Value :
            "Could not read installed version.";
    }

    static bool NativeRunning()
    {
        string binary = Path.Combine(root, "bin", "FreeCAD.exe");
        foreach (Process process in Process.GetProcessesByName("FreeCAD")) {
            try {
                if (String.Equals(process.MainModule.FileName, binary,
                                  StringComparison.OrdinalIgnoreCase))
                    return true;
            } catch { /* Do not interfere with unrelated protected processes. */ }
            finally { process.Dispose(); }
        }
        return false;
    }

    static bool Confirm()
    {
        if (NativeRunning()) {
            MessageBox.Show(window,
                "Save your documents, then CLOSE the Design application window. " +
                "Leave this updater open. Click OK after Design has closed.",
                "Close Design to update", MessageBoxButtons.OK, MessageBoxIcon.Information);
            if (NativeRunning()) {
                MessageBox.Show(window,
                    "Design is still running. Nothing was changed. Close it and try again.",
                    "Update not started", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
        }
        return MessageBox.Show(window,
            "Install the verified patch? A rollback backup will be kept.",
            "Design Update", MessageBoxButtons.YesNo,
            MessageBoxIcon.Question) == DialogResult.Yes;
    }

    static void CheckOnline(Button button)
    {
        button.Enabled = false;
        button.Text = "Checking GitHub...";
        var worker = new BackgroundWorker();
        worker.DoWork += (s, e) =>
        {
            string installed = AzOnlineUpdates.InstalledVersion(root);
            var available = AzOnlineUpdates.Find(installed);
            if (available == null) { e.Result = null; return; }
            e.Result = available;
        };
        worker.RunWorkerCompleted += (s, e) =>
        {
            button.Enabled = true;
            button.Text = "Check for Updates";
            if (e.Error != null) {
                MessageBox.Show(window, "Unable to check for a verified release: " + e.Error.Message,
                    "Design Update", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            var patch = e.Result as AzAvailablePatch;
            if (patch == null) {
                MessageBox.Show(window, "No compatible verified patch is published for this installed version.",
                    "Design Update", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            if (MessageBox.Show(window,
                "Verified patch: " + patch.From + " to " + patch.To +
                "\nSize: " + (patch.Bytes / 1024) + " KB" +
                "\n\nDownload this GitHub release patch? Your documents will not be modified. " +
                "You must save and close Design before applying it.",
                "Design Update", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
                return;
            button.Enabled = false;
            button.Text = "Downloading...";
            var download = new BackgroundWorker();
            download.DoWork += (sender, args) => args.Result = AzOnlineUpdates.DownloadVerified(patch);
            download.RunWorkerCompleted += (sender, args) =>
            {
                button.Enabled = true;
                button.Text = "Check for Updates";
                if (args.Error != null) {
                    MessageBox.Show(window, "Update download was refused: " + args.Error.Message,
                        "Design Update", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }
                if (Confirm()) LaunchInstaller(args.Result as string, false);
            };
            download.RunWorkerAsync();
        };
        worker.RunWorkerAsync();
    }

    static void ChoosePatch()
    {
        if (!Confirm()) return;
        OpenFileDialog dialog = new OpenFileDialog();
        dialog.Title = "Select official Az Design Native patch";
        dialog.Filter = "Az Design patch ZIP (*.azpatch;*.zip)|*.azpatch;*.zip|All files|*.*";
        dialog.CheckFileExists = true;
        if (dialog.ShowDialog(window) != DialogResult.OK) return;
        LaunchInstaller(dialog.FileName, false);
    }

    static void Rollback()
    {
        if (!Confirm()) return;
        string record = Path.Combine(Environment.GetFolderPath(
            Environment.SpecialFolder.LocalApplicationData), "AzDesign", "Updates", "last_success.json");
        if (!File.Exists(record))
        {
            MessageBox.Show(window, "No previous update backup was found.", "Az Design Native");
            return;
        }
        if (MessageBox.Show(window, "Restore the previous installed version using the last saved backup?",
            "Az Design Native", MessageBoxButtons.YesNo,
            MessageBoxIcon.Question) == DialogResult.Yes)
            LaunchInstaller(null, true);
    }

    static void LaunchInstaller(string patch, bool rollback)
    {
        try
        {
            string source = Path.Combine(root, "ApplyAzPatch.ps1");
            if (!File.Exists(source)) throw new FileNotFoundException("Az update engine is missing", source);
            string temp = Path.Combine(Path.GetTempPath(), "AzNativeUpdate-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temp);
            string script = Path.Combine(temp, "ApplyAzPatch.ps1");
            File.Copy(source, script);
            ProcessStartInfo info = new ProcessStartInfo("powershell.exe");
            info.UseShellExecute = false;
            info.CreateNoWindow = true;
            info.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -STA -File " +
                Q(script) + " -InstallDir " + Q(root) +
                (rollback ? " -RollbackLatest" : " -PatchZip " + Q(patch));
            Process.Start(info);
            // The child updater runs independently so it can replace
            // application files after this process completely exits.
            window.Close();
        }
        catch (Exception ex)
        {
            MessageBox.Show(window, ex.Message, "Az Design Native",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    static string Q(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }
}
