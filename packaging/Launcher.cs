using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Drawing;

class Launcher : Form {
    Label status = new Label();
    Launcher() {
        Text = "KeyZone Video Studio"; Width = 440; Height = 170;
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        StartPosition = FormStartPosition.CenterScreen; FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false; MinimizeBox = false; BackColor = Color.FromArgb(18, 19, 30);
        status.Text = "Đang mở KeyZone Video Studio…"; status.ForeColor = Color.White;
        status.Font = new Font("Segoe UI", 12); status.AutoSize = false; status.Dock = DockStyle.Fill;
        status.TextAlign = ContentAlignment.MiddleCenter; Controls.Add(status);
        Shown += async (s, e) => await StartApp();
    }
    static async Task<string> AvailableUpdate() {
        try {
            var request = (System.Net.HttpWebRequest)System.Net.WebRequest.Create("https://keyzone-6laz.onrender.com/release-windows.json");
            request.AllowAutoRedirect = false;
            var read = Task.Run(() => {
                request.Timeout = 6000;
                request.ReadWriteTimeout = 6000;
                using (var response = request.GetResponse())
                using (var reader = new StreamReader(response.GetResponseStream())) {
                    var json = new System.Web.Script.Serialization.JavaScriptSerializer();
                    var release = json.Deserialize<System.Collections.Generic.Dictionary<string, object>>(reader.ReadToEnd());
                    var local = json.Deserialize<System.Collections.Generic.Dictionary<string, object>>(File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "release.json")));
                    Version latest, installed;
                    if (Version.TryParse((string)release["version"], out latest) && Version.TryParse((string)local["version"], out installed) && latest > installed) return latest.ToString();
                    return null;
                }
            });
            return await read;
        } catch { return null; }
    }
    async Task StartApp() {
        try {
            var update = AvailableUpdate();
            string root = AppDomain.CurrentDomain.BaseDirectory;
            ProcessStartInfo info = new ProcessStartInfo(Path.Combine(root, "runtime", "node", "node.exe"), "\"" + Path.Combine(root, "launcher.mjs") + "\"");
            info.WorkingDirectory = root; info.UseShellExecute = false; info.CreateNoWindow = true;
            info.RedirectStandardOutput = true; info.RedirectStandardError = true;
            using (Process process = Process.Start(info)) {
                Task<string> output = process.StandardOutput.ReadToEndAsync();
                Task<string> errors = process.StandardError.ReadToEndAsync();
                await Task.Run(() => process.WaitForExit());
                string result = await output; string detail = await errors;
                if (process.ExitCode != 0) throw new Exception(result + "\n" + detail);
            }
            string latest = await update;
            if (latest != null && MessageBox.Show(this, "KeyZone " + latest + " đã sẵn sàng. Mở trang tải để cập nhật ngay? Chọn No để sau.", "Cập nhật KeyZone", MessageBoxButtons.YesNo, MessageBoxIcon.Information) == DialogResult.Yes)
                Process.Start(new ProcessStartInfo("https://keyzone-6laz.onrender.com/#download-button") { UseShellExecute = true });
            Close();
        } catch (Exception error) {
            MessageBox.Show(error.Message, "Chưa mở được KeyZone", MessageBoxButtons.OK, MessageBoxIcon.Warning); Close();
        }
    }
    [STAThread] static void Main() { Application.EnableVisualStyles(); Application.Run(new Launcher()); }
}
