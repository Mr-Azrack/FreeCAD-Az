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

            // Only this Design Native profile is changed. The ordinary
            // FreeCAD installation and its preferences remain untouched.
            // Set this before launching FreeCAD: InitGui.py runs too late
            // to prevent the *first* FreeCAD splash from appearing.
            try {
                PrepareNoSplash(Path.Combine(profile, "user.cfg"));
            } catch (Exception) {
                // Splash is cosmetic: never prevent modeling because a user
                // preference file is locked, malformed or unavailable.
            }

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

    private static System.Xml.XmlElement EnsureGroup(
        System.Xml.XmlDocument document, System.Xml.XmlElement parent, string name)
    {
        foreach (System.Xml.XmlNode node in parent.ChildNodes)
        {
            System.Xml.XmlElement child = node as System.Xml.XmlElement;
            if (child != null && child.Name == "FCParamGroup"
                && child.GetAttribute("Name") == name)
                return child;
        }
        System.Xml.XmlElement added = document.CreateElement("FCParamGroup");
        added.SetAttribute("Name", name);
        parent.AppendChild(added);
        return added;
    }

    internal static void PrepareNoSplash(string filename)
    {
        System.Xml.XmlDocument document = new System.Xml.XmlDocument();
        if (File.Exists(filename))
            document.Load(filename);
        else
            document.LoadXml("<FCParameters><FCParamGroup Name=\"Root\"/></FCParameters>");
        System.Xml.XmlElement top = document.DocumentElement;
        if (top == null || top.Name != "FCParameters")
            throw new InvalidDataException("Unexpected FreeCAD preferences document.");
        System.Xml.XmlElement group = EnsureGroup(document, top, "Root");
        group = EnsureGroup(document, group, "BaseApp");
        group = EnsureGroup(document, group, "Preferences");
        group = EnsureGroup(document, group, "General");
        System.Xml.XmlElement splasher = null;
        foreach (System.Xml.XmlNode node in group.ChildNodes)
        {
            System.Xml.XmlElement child = node as System.Xml.XmlElement;
            if (child != null && child.Name == "FCBool"
                && child.GetAttribute("Name") == "ShowSplasher")
            {
                splasher = child;
                break;
            }
        }
        if (splasher != null && splasher.GetAttribute("Value") == "0")
            return;
        if (splasher == null)
        {
            splasher = document.CreateElement("FCBool");
            splasher.SetAttribute("Name", "ShowSplasher");
            group.AppendChild(splasher);
        }
        splasher.SetAttribute("Value", "0");
        string staged = filename + ".az-tmp-" + Guid.NewGuid().ToString("N");
        try
        {
            document.Save(staged);
            if (File.Exists(filename))
                File.Replace(staged, filename, filename + ".az-backup", true);
            else
                File.Move(staged, filename);
        }
        finally
        {
            if (File.Exists(staged))
                File.Delete(staged);
        }
    }

    static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }
}
