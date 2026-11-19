package com.keyzone.video;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONObject;

final class UpdateCheck {
    private static final String PORTAL = "https://keyzone-6laz.onrender.com/";
    private static final Pattern VERSION = Pattern.compile("(\\d+)\\.(\\d+)\\.(\\d+)(?:-beta\\.(\\d+))?");

    static boolean newer(String candidate, String installed) {
        Matcher a = VERSION.matcher(candidate), b = VERSION.matcher(installed);
        if (!a.matches() || !b.matches()) return false;
        for (int i = 1; i <= 4; i++) {
            String left = a.group(i), right = b.group(i);
            if (left == null || right == null) return left == null && right != null;
            int diff = new java.math.BigInteger(left).compareTo(new java.math.BigInteger(right));
            if (diff != 0) return diff > 0;
        }
        return false;
    }

    static void onLaunch(Activity activity) {
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                String installed = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0).versionName;
                connection = (HttpURLConnection)new URL(PORTAL + "release-android.json").openConnection();
                connection.setConnectTimeout(6000);
                connection.setReadTimeout(6000);
                connection.setInstanceFollowRedirects(false);
                if (connection.getResponseCode() != 200) return;
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                try (InputStream in = connection.getInputStream()) {
                    byte[] chunk = new byte[4096];
                    int count;
                    while ((count = in.read(chunk)) != -1) {
                        if (bytes.size() + count > 65536) return;
                        bytes.write(chunk, 0, count);
                    }
                }
                String latest = new JSONObject(bytes.toString("UTF-8")).getString("version");
                if (newer(latest, installed)) activity.runOnUiThread(() -> {
                    if (activity.isFinishing() || activity.isDestroyed()) return;
                    new AlertDialog.Builder(activity).setTitle("Có bản cập nhật KeyZone")
                        .setMessage("Phiên bản " + latest + " đã sẵn sàng.")
                        .setNegativeButton("Để sau", null)
                        .setPositiveButton("Mở trang tải", (dialog, which) -> {
                            Intent link = new Intent(Intent.ACTION_VIEW, Uri.parse(PORTAL + "#android-download-button"));
                            if (link.resolveActivity(activity.getPackageManager()) != null) activity.startActivity(link);
                            else try { activity.startActivity(link); } catch (android.content.ActivityNotFoundException ignored) {}
                        }).show();
                });
            } catch (Exception ignored) {
                // Updates are optional. The studio stays available when the portal is offline.
            } finally { if (connection != null) connection.disconnect(); }
        }, "keyzone-update").start();
    }
}
