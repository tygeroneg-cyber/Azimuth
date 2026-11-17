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
push = r"""<script>
(function(){
  /* OneSignal se încarcă doar după acordul utilizatorului (sau pentru cei deja abonați, cu permisiunea dată în browser). */
  var SDK = "https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js";
  var base = location.pathname.replace(/[^/]*$/, "");
  var loaded = false, OSref = null, done, ready;
  function flag(){ try { return localStorage.getItem("az-push-consent"); } catch(e) { return null; } }
  function setFlag(v){ try { localStorage.setItem("az-push-consent", v); } catch(e) {} }
  function consented(){
    var f = flag(); if (f === "1") return true; if (f === "0") return false;
    return ("Notification" in window) && Notification.permission === "granted";
  }
  function load(){
    if (loaded) return ready; loaded = true;
    ready = new Promise(function(r){ done = function(v){ if (!v) loaded = false; r(v); }; });
    /* dacă serviciul nu răspunde în 20 de secunde, butonul nu rămâne blocat: următoarea apăsare reîncearcă */
    setTimeout(function(){ if (!OSref) done(null); }, 20000);
    window.OneSignalDeferred = window.OneSignalDeferred || [];
    OneSignalDeferred.push(async function(OS){
      try {
        await OS.init({ appId: "febcbdcd-b552-4489-b331-294900387ad8", safari_web_id: "web.onesignal.auto.47e61a84-7486-476e-83ad-85400aafc6ca", serviceWorkerPath: base.slice(1) + "sw.js", serviceWorkerParam: { scope: base }, notifyButton: { enable: false } });
        OSref = OS; done(OS);
      } catch(e) { done(null); }
      try { window.dispatchEvent(new Event("az-push-ready")); } catch(e) {}
    });
    if (!window.__azOSsdk) { window.__azOSsdk = true; var s = document.createElement("script"); s.src = SDK; s.defer = true; s.onerror = function(){ window.__azOSsdk = false; done(null); }; document.head.appendChild(s); }
    return ready;
  }
  if (consented()) load();
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
    needsConsent: function(){ return flag() !== "1"; },
    toggle: async function(agreed){
      var st = this.state(); if (st === "na" || st === "ios" || st === "blocked") return;
      if (st === "on") { var O = await ready; if (O) await O.User.PushSubscription.optOut(); setFlag("0"); return; }
      if (agreed !== true && flag() !== "1") return;
      setFlag("1");
      /* permisiunea se cere imediat, în aceeași apăsare (iPhone și Samsung o refuză dacă vine după o încărcare) */
      var perm = Notification.permission;
      if (perm === "default") { try { perm = await Notification.requestPermission(); } catch(e) { perm = Notification.permission; } }
      if (perm !== "granted") { try { window.dispatchEvent(new Event("az-push-ready")); } catch(e) {} return; }
      var OS = await load(); if (!OS) return;
      await OS.User.PushSubscription.optIn();
      try { window.dispatchEvent(new Event("az-push-ready")); } catch(e) {}
    }
  };
})();
</script>
</body>"""
s=s.replace('<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("sw.js").catch(function(){});}</script>\n</body>', push, 1)
assert "OneSignalSDK.page.js" in s

# Content Security Policy (meta): only our own files, the inline scripts listed by hash, and OneSignal.
import re, hashlib, base64
hashes = []
for m in re.finditer(r"<script>(.*?)</script>", s, re.S):
    hashes.append("'sha256-" + base64.b64encode(hashlib.sha256(m.group(1).encode("utf-8")).digest()).decode() + "'")
csp = ("default-src 'self'; script-src 'self' " + " ".join(hashes) + " https://cdn.onesignal.com https://onesignal.com https://*.onesignal.com; "
       "style-src 'self' 'unsafe-inline' https://cdn.onesignal.com https://onesignal.com; img-src 'self' data: https:; "
       "font-src 'self' https://cdn.onesignal.com https://onesignal.com; connect-src 'self' https://onesignal.com https://*.onesignal.com; "
       "frame-src https://onesignal.com https://*.onesignal.com; worker-src 'self'; manifest-src 'self'; media-src 'none'; "
       "object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests")
s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="' + csp + '">', 1)
open(os.path.join(ROOT,"index.html"),"w",encoding="utf-8").write(s)
print("index.html built")
