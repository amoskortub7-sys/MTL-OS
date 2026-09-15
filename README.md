# MTL OS1

MTL OS1 is an Android launcher and AOSP overlay project using the Flow visual language.

## Installable launcher APK

The `app` module is a standalone launcher APK. It can be installed on an existing Android phone without replacing the operating system. It declares itself as a Home app, presents the Flow home screen, and opens installed applications from the dock and tiles.

Build it with:

```bash
gradle :app:assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`. Install it with:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Press the Home button and select **MTL Flow** as the launcher. The full OS overlay pipeline remains available through `build.py` and `merge_overlay.py`.
