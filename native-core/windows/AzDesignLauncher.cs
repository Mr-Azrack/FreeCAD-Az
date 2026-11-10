// SPDX-License-Identifier: LGPL-2.1-or-later
// Az Design Native Windows GUI launcher. Compiled as WindowsApplication:
// users can launch from Start Menu/desktop without a cmd window.
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("Az Design Native")]
[assembly: AssemblyProduct("Az Design Native")]
[assembly: AssemblyCompany("Az Design")]
[assembly: AssemblyVersion("0.5.2.0")]

static class AzDesignLauncher
{
    [STAThread]
    static void Main(string[] args)
    {
        try
        {
            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
            string executable = Path.Combine(root, "bin", "FreeCAD.exe");
            string pluginPath = Path.Combine(root, "bin", "platforms");
            if (!File.Exists(executable) || !File.Exists(Path.Combine(pluginPath, "qwindows.dll")))
                throw new FileNotFoundException(
                    "Az Design's compiled FreeCAD or Qt platform plugin is missing. Please repair this installation.");

            string profile = Path.Combine(Environment.GetFolderPath(
                Environment.SpecialFolder.LocalApplicationData), "AzDesign", "Native-1.1");
            Directory.CreateDirectory(profile);
            Directory.CreateDirectory(Path.Combine(profile, "Data"));

            ProcessStartInfo psi = new ProcessStartInfo(executable);
            psi.WorkingDirectory = Path.Combine(root, "bin");
            psi.UseShellExecute = false;
            // Only ordinary launches default to Design Home. File arguments
            // retain their stored workbench routing and specialized contexts.
            if (args.Length == 0)
                psi.EnvironmentVariables["AZ_DESIGN_NATIVE_HOME"] = "1";
            psi.EnvironmentVariables["FREECAD_USER_HOME"] = profile;
            psi.EnvironmentVariables["FREECAD_USER_DATA"] = Path.Combine(profile, "Data");
            psi.EnvironmentVariables["QT_PLUGIN_PATH"] = Path.Combine(root, "bin");
            psi.EnvironmentVariables["QT_QPA_PLATFORM_PLUGIN_PATH"] = pluginPath;
            psi.EnvironmentVariables["PATH"] = Path.Combine(root, "bin") + ";" +
                (Environment.GetEnvironmentVariable("PATH") ?? "");
            psi.Arguments = "--user-cfg " + Quote(Path.Combine(profile, "user.cfg")) +
                            " --system-cfg " + Quote(Path.Combine(profile, "system.cfg"));
            foreach (string arg in args)
                psi.Arguments += " " + Quote(arg);
            Process.Start(psi);
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Az Design Native – Launch error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }
}
