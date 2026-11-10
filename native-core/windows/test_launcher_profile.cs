// SPDX-License-Identifier: LGPL-2.1-or-later
// Windows-only native launcher preference regression. Compiled with
// AzDesignLauncher.cs and explicit /main:TestNativeLauncherProfile.
using System;
using System.IO;
using System.Xml;

static class TestNativeLauncherProfile
{
    static XmlElement Find(XmlElement parent, string kind, string name)
    {
        foreach (XmlNode item in parent.ChildNodes)
        {
            XmlElement child = item as XmlElement;
            if (child != null && child.Name == kind && child.GetAttribute("Name") == name)
                return child;
        }
        throw new Exception("Missing " + kind + ": " + name);
    }

    static void Assert(bool ok, string message)
    {
        if (!ok) throw new Exception(message);
    }

    public static int Main()
    {
        string directory = Path.Combine(Path.GetTempPath(), "AzNativeProfileTest-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        string path = Path.Combine(directory, "user.cfg");
        try
        {
            // First-launch profile starts empty. Splash must already be
            // disabled before FreeCAD.exe gets launched.
            AzDesignLauncher.PrepareNoSplash(path);
            XmlDocument xml = new XmlDocument();
            xml.Load(path);
            XmlElement root = Find(xml.DocumentElement, "FCParamGroup", "Root");
            XmlElement baseApp = Find(root, "FCParamGroup", "BaseApp");
            XmlElement prefs = Find(baseApp, "FCParamGroup", "Preferences");
            XmlElement general = Find(prefs, "FCParamGroup", "General");
            Assert(Find(general, "FCBool", "ShowSplasher").GetAttribute("Value") == "0", "New profile still shows splash");
            // Preserve unrelated native profile preferences (no destructive reset).
            XmlElement custom = xml.CreateElement("FCText");
            custom.SetAttribute("Name", "CustomTestSetting");
            custom.InnerText = "keep-me";
            general.AppendChild(custom);
            Find(general, "FCBool", "ShowSplasher").SetAttribute("Value", "1");
            xml.Save(path);
            AzDesignLauncher.PrepareNoSplash(path);
            xml.Load(path);
            general = Find(Find(Find(Find(xml.DocumentElement, "FCParamGroup", "Root"),
                "FCParamGroup", "BaseApp"), "FCParamGroup", "Preferences"), "FCParamGroup", "General");
            Assert(Find(general, "FCBool", "ShowSplasher").GetAttribute("Value") == "0", "Splash wasn't disabled");
            Assert(Find(general, "FCText", "CustomTestSetting").InnerText == "keep-me", "Existing preference was lost");
            Assert(File.Exists(path + ".az-backup"), "Changed profile missing atomic backup");
            string identical = File.ReadAllText(path);
            AzDesignLauncher.PrepareNoSplash(path);
            Assert(File.ReadAllText(path) == identical, "Unchanged profile was unnecessarily rewritten");

            // Invalid configuration must not be overwritten; caller catches
            // the cosmetic failure and launches the CAD application anyway.
            File.WriteAllText(path, "<broken>");
            bool raised = false;
            try { AzDesignLauncher.PrepareNoSplash(path); } catch (XmlException) { raised = true; }
            Assert(raised, "Malformed profile wasn't rejected safely");
            Assert(File.ReadAllText(path) == "<broken>", "Malformed original was overwritten");
            Console.WriteLine("PASS: native-only first-launch splash config and preference safety");
            return 0;
        }
        finally
        {
            Directory.Delete(directory, true);
        }
    }
}
