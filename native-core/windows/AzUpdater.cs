// SPDX-License-Identifier: LGPL-2.1-or-later
// Small native GUI wrapper for Az Design Native patch packages.
// Runs the independent PowerShell apply process AFTER this GUI exits.
using System;
using System.Diagnostics;
using System.Drawing;
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
        window.Text = "Az Design Native – Update";
        window.ClientSize = new Size(470, 230);
        window.FormBorderStyle = FormBorderStyle.FixedDialog;
        window.StartPosition = FormStartPosition.CenterScreen;
        window.MaximizeBox = false;
        window.MinimizeBox = false;

        Label heading = new Label();
        heading.Text = "Az Design Native updater";
        heading.Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 13, FontStyle.Bold);
        heading.Location = new Point(20, 18);
        heading.Size = new Size(420, 30);
        window.Controls.Add(heading);

        versionLabel = new Label();
        versionLabel.Text = VersionText();
        versionLabel.Location = new Point(20, 55);
        versionLabel.Size = new Size(420, 26);
        window.Controls.Add(versionLabel);

        Label help = new Label();
        help.Text = "Install a small .azpatch ZIP from our GitHub builds, or roll back the last update. Close Az Design before updating.";
        help.Location = new Point(20, 85);
        help.Size = new Size(420, 54);
        window.Controls.Add(help);

        Button apply = new Button();
        apply.Text = "Install patch ZIP...";
        apply.Location = new Point(20, 153);
        apply.Size = new Size(145, 37);
        apply.Click += (s, e) => ChoosePatch();
        window.Controls.Add(apply);

        Button rollback = new Button();
        rollback.Text = "Roll back update";
        rollback.Location = new Point(179, 153);
        rollback.Size = new Size(145, 37);
        rollback.Click += (s, e) => Rollback();
        window.Controls.Add(rollback);

        Button close = new Button();
        close.Text = "Close";
        close.Location = new Point(338, 153);
        close.Size = new Size(112, 37);
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

    static bool Confirm()
    {
        return MessageBox.Show(window, "Close all Az Design Native windows and save your documents before applying an update. Continue?",
            "Az Design Native", MessageBoxButtons.YesNo,
            MessageBoxIcon.Warning) == DialogResult.Yes;
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
