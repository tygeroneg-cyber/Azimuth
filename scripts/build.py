#!/usr/bin/env python3
"""Builds index.html (the GitHub Pages app) from src/template.html.

Usage, from the repository root:  python3 scripts/build.py

Steps:
1. Inserts the flag images (src/flags.json) in place of __FLAGS__.
2. Adds the install tags (manifest, icons) and the OneSignal push setup.
3. Checks that the main script still parses (needs node; skipped if node is missing).
"""
import os, json, shutil, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
flags = open(os.path.join(ROOT, "src", "flags.json"), encoding="utf-8").read().replace("</", "<\\/")
assert "__FLAGS__" in t, "template is missing the __FLAGS__ placeholder"
s = t.replace("__FLAGS__", flags, 1)

# syntax check of the main script (the second <script> block)
if shutil.which("node"):
    main = s.split("<script>")[2].split("</script>")[0]
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(main); tmp = f.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode != 0:
        raise SystemExit("Script error in template:\n" + r.stderr)

s=s.replace("<title>Azimuth</title>",'<title>Azimuth</title>\n<link rel="manifest" href="manifest.json">\n<link rel="icon" type="image/png" href="icons/icon-192.png">\n<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n<meta name="mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-capable" content="yes">',1)
s=s.replace("</body>",'<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("sw.js").catch(function(){});}</script>\n</body>',1)
push = r"""<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
<script>
(function(){
  var base = location.pathname.replace(/[^/]*$/, "");
  window.OneSignalDeferred = window.OneSignalDeferred || [];
  var ready = new Promise(function(res){
    OneSignalDeferred.push(async function(OS){
      try {
        await OS.init({ appId: "febcbdcd-b552-4489-b331-294900387ad8", safari_web_id: "web.onesignal.auto.47e61a84-7486-476e-83ad-85400aafc6ca", serviceWorkerPath: base.slice(1) + "sw.js", serviceWorkerParam: { scope: base }, notifyButton: { enable: false } });
        res(OS);
      } catch(e) { res(null); }
    });
  });
  var OSref = null; ready.then(function(o){ OSref = o; });
  window.AZ_PUSH = {
    state: function(){
      if (!("Notification" in window) || !("serviceWorker" in navigator) || !("PushManager" in window)) {
        var ios = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
        var standalone = navigator.standalone === true || (window.matchMedia && matchMedia("(display-mode: standalone)").matches);
        return (ios && !standalone) ? "ios" : "na";
      }
      if (Notification.permission === "denied") return "blocked";
      try { if (OSref && OSref.User.PushSubscription.optedIn) return "on"; } catch(e) {}
      return "off";
    },
    toggle: async function(){
      var st = this.state(); if (st === "na" || st === "ios" || st === "blocked") return;
      var OS = await ready; if (!OS) return;
      var sub = OS.User.PushSubscription;
      if (sub.optedIn) { await sub.optOut(); return; }
      if (!OS.Notifications.permission) await OS.Notifications.requestPermission();
      await sub.optIn();
    }
  };
})();
</script>
</body>"""
s=s.replace('<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("sw.js").catch(function(){});}</script>\n</body>', push, 1)
assert "OneSignalSDK.page.js" in s
open(os.path.join(ROOT,"index.html"),"w",encoding="utf-8").write(s)
print("index.html built")
