"""Finish the Android project after `flutter create` (run from the app/ folder).

- app name, internet permission, AdMob app ID, link opening (https, mailto)
- app ID (permanent once on Google Play!) and minimum Android version
- app icon
Safe to run more than once.
"""
import os
import re
import shutil
import sys

APP_NAME = os.getenv("APP_NAME", "Canada Shorts")
APP_ID = os.getenv("APP_ID", "ca.canadashorts.news")
# AdMob app ID: only added when ads are switched on (set ADMOB_APP_ID in the workflow).
ADMOB_APP_ID = os.getenv("ADMOB_APP_ID", "")

manifest_path = "android/app/src/main/AndroidManifest.xml"
m = open(manifest_path, encoding="utf-8").read()

m = re.sub(r'android:label="[^"]*"', f'android:label="{APP_NAME}"', m, count=1)

if "android.permission.INTERNET" not in m:
    m = m.replace("<application", '<uses-permission android:name="android.permission.INTERNET"/>\n    <application', 1)

if ADMOB_APP_ID and "com.google.android.gms.ads.APPLICATION_ID" not in m:
    meta = (f'\n        <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID"'
            f' android:value="{ADMOB_APP_ID}"/>')
    m = re.sub(r"(<application[^>]*>)", r"\1" + meta, m, count=1)

# Use the older, widely compatible graphics engine (avoids start-up crashes on
# some older Samsung / Mali phones).
if "EnableImpeller" not in m:
    m = re.sub(r"(<application[^>]*>)",
               r'\1\n        <meta-data android:name="io.flutter.embedding.android.EnableImpeller" android:value="false"/>',
               m, count=1)

extra_queries = """
        <intent>
            <action android:name="android.intent.action.VIEW" />
            <data android:scheme="https" />
        </intent>
        <intent>
            <action android:name="android.intent.action.SENDTO" />
            <data android:scheme="mailto" />
        </intent>"""
if 'android:scheme="mailto"' not in m:
    if "<queries>" in m:
        m = m.replace("<queries>", "<queries>" + extra_queries, 1)
    else:
        m = m.replace("</manifest>", f"    <queries>{extra_queries}\n    </queries>\n</manifest>", 1)

open(manifest_path, "w", encoding="utf-8").write(m)

# App ID and minimum Android version (Kotlin or Groovy build file).
for gradle in ("android/app/build.gradle.kts", "android/app/build.gradle"):
    if not os.path.exists(gradle):
        continue
    g = open(gradle, encoding="utf-8").read()
    kts = gradle.endswith(".kts")
    if kts:
        g = re.sub(r'applicationId\s*=\s*"[^"]*"', f'applicationId = "{APP_ID}"', g)
        g = re.sub(r"minSdk\s*=\s*flutter\.minSdkVersion", "minSdk = maxOf(flutter.minSdkVersion, 23)", g)
    else:
        g = re.sub(r'applicationId\s+"[^"]*"', f'applicationId "{APP_ID}"', g)
        g = re.sub(r"minSdkVersion\s+flutter\.minSdkVersion", "minSdkVersion Math.max(flutter.minSdkVersion, 23)", g)
    open(gradle, "w", encoding="utf-8").write(g)
    print("patched", gradle)

# Icons.
for density in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
    src = f"assets/icon/mipmap-{density}/ic_launcher.png"
    dst_dir = f"android/app/src/main/res/mipmap-{density}"
    if os.path.exists(src) and os.path.isdir(dst_dir):
        shutil.copyfile(src, os.path.join(dst_dir, "ic_launcher.png"))

print("Android project ready:", APP_NAME, APP_ID)
sys.exit(0)
