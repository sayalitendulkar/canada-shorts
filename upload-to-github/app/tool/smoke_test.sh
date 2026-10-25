#!/usr/bin/env bash
# Start-up test: installs the new app on a simulated Android phone, opens it,
# waits, and reports whether it is still running. Any crash lines are copied
# to the run's Summary page. Run from the app/ folder.
set +e
PKG=ca.canadashorts.news
APK=build/app/outputs/flutter-apk/app-release.apk
SUMMARY=${GITHUB_STEP_SUMMARY:-/dev/stdout}

adb install -r "$APK"
adb logcat -c
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1
sleep 30
PID=$(adb shell pidof "$PKG" | tr -d '\r')
adb logcat -d > logcat.txt
CRASH=$(grep -E "FATAL EXCEPTION|AndroidRuntime|E/flutter|E flutter|Fatal signal|Abort message|DEBUG   :" logcat.txt | head -60)

if [ -n "$PID" ] && [ -z "$(grep 'FATAL EXCEPTION' logcat.txt)" ]; then
  echo "## Start-up test: the app opened and kept running for 30 seconds" >> "$SUMMARY"
  if [ -n "$CRASH" ]; then
    { echo "Warnings seen:"; echo '```'; echo "$CRASH"; echo '```'; } >> "$SUMMARY"
  fi
  exit 0
fi

{ echo "## Start-up test: the app CRASHED"; echo '```'; echo "$CRASH"; echo '```'; } >> "$SUMMARY"
echo "$CRASH" | head -15 | while read -r line; do echo "::error::$line"; done
exit 1
