#!/usr/bin/env python3
"""Build MTL OS1 overlay artifacts over an AOSP base.

This script generates:
- bootanimation.zip
- shutdownanimation.zip
- SystemUI and Launcher overlay directories
- 35 app skeletons under system/app or system/priv-app
- a manifest describing the overlay pack

The goal is to keep the AOSP engine intact while replacing the visible UI layer.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import textwrap
import zipfile
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Pillow is required. Install it with: pip install pillow"
    ) from exc

APP_NAMES = [
    "MTLDialer",
    "MTLContacts",
    "MTLMessages",
    "MTLCamera",
    "MTLGallery",
    "MTLStore",
    "MTLThemes",
    "MTLCleaner",
    "MTLDataSaver",
    "MTLBatteryLab",
    "MShare",
    "MTLAI",
    "MTLSettings",
    "MTLKeyboard",
    "MTLCalculator",
    "MTLClock",
    "MTLFileManager",
    "MTLFMRadio",
    "MTLSoundRecorder",
    "MTLMusic",
    "MTLVideo",
    "MTLNotes",
    "MTLWeather",
    "MTLCalendar",
    "MTLBrowser",
    "MTLEmail",
    "MTLCompass",
    "MTLTorch",
    "MTLBackup",
    "MTLSafety",
    "MTLKidsMode",
    "MTLDownloads",
    "MTLAbout",
]

APP_MANIFEST = {
    "MTLDialer": "com.mtl.dialer",
    "MTLContacts": "com.mtl.contacts",
    "MTLMessages": "com.mtl.messages",
    "MTLCamera": "com.mtl.camera",
    "MTLGallery": "com.mtl.gallery",
    "MTLStore": "com.mtl.store",
    "MTLThemes": "com.mtl.themes",
    "MTLCleaner": "com.mtl.cleaner",
    "MTLDataSaver": "com.mtl.datasaver",
    "MTLBatteryLab": "com.mtl.batterylab",
    "MShare": "com.mtl.mshare",
    "MTLAI": "com.mtl.ai",
    "MTLSettings": "com.mtl.settings",
    "MTLKeyboard": "com.mtl.keyboard",
    "MTLCalculator": "com.mtl.calculator",
    "MTLClock": "com.mtl.clock",
    "MTLFileManager": "com.mtl.filemanager",
    "MTLFMRadio": "com.mtl.fmradio",
    "MTLSoundRecorder": "com.mtl.soundrecorder",
    "MTLMusic": "com.mtl.music",
    "MTLVideo": "com.mtl.video",
    "MTLNotes": "com.mtl.notes",
    "MTLWeather": "com.mtl.weather",
    "MTLCalendar": "com.mtl.calendar",
    "MTLBrowser": "com.mtl.browser",
    "MTLEmail": "com.mtl.email",
    "MTLCompass": "com.mtl.compass",
    "MTLTorch": "com.mtl.torch",
    "MTLBackup": "com.mtl.backup",
    "MTLSafety": "com.mtl.safety",
    "MTLKidsMode": "com.mtl.kidsmode",
    "MTLDownloads": "com.mtl.downloads",
    "MTLAbout": "com.mtl.about",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def make_background(width: int, height: int, dark: tuple[int, int, int], light: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (width, height), dark + (255,))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(0, height, 18):
        alpha = int(16 + (i / height) * 28)
        draw.rectangle((0, i, width, i + 12), fill=(20, 42, 30, alpha))
    img = Image.alpha_composite(img, overlay)
    return img


def draw_growing_seed(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, leaf_color: tuple[int, int, int], accent: tuple[int, int, int]) -> None:
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=leaf_color)
    draw.polygon([
        (cx, cy - radius * 1.9),
        (cx + radius * 0.75, cy),
        (cx, cy + radius * 1.8),
        (cx - radius * 0.75, cy),
    ], fill=accent)
    draw.line((cx, cy - radius * 1.9, cx, cy + radius * 1.8), fill=(255, 255, 255, 120), width=max(2, int(radius * 0.12)))


def generate_frame(width: int, height: int, phase: float, label: str, accent: str) -> Image.Image:
    canvas = make_background(width, height, (10, 47, 31), (230, 213, 184))
    draw = ImageDraw.Draw(canvas)
    cx = width / 2
    cy = height * 0.54
    growth = min(1.0, phase * 1.4)
    radius = max(40, min(width * 0.15, width * 0.2 * growth + 60))
    draw_growing_seed(draw, cx, cy, radius, (10, 47, 31), (255, 107, 53))

    # Ripple ring
    ring = int(220 + (1 - growth) * 600)
    for i in range(8):
        alpha = max(0, int(90 - i * 9))
        r = ring + i * 30
        outline = (230, 213, 184, alpha)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=outline, width=max(2, int((1 - growth) * 12 + 2)))

    # Leaf arcs for flow feel
    for offset in range(-3, 4):
        top_y = height * 0.25 + offset * 16
        draw.arc((cx - width * 0.24, top_y, cx + width * 0.24, top_y + height * 0.26), start=200, end=340, fill=(230, 213, 184, 120), width=3)

    # Text
    text = label
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
    except OSError:
        font = None
    if font is not None:
        bbox = draw.textbbox((0, 0), text, font=font)
        tx = (width - (bbox[2] - bbox[0])) / 2
        ty = height * 0.76
        draw.text((tx, ty), text, font=font, fill=(230, 213, 184, 240))
    return canvas


def build_animation_zip(output_path: Path, label: str, accent: str, fps: int = 30, width: int = 1080, height: int = 1920, frame_count: int = 16) -> None:
    work_dir = output_path.parent / f"{output_path.stem}_frames"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    ensure_dir(work_dir)

    for idx in range(frame_count):
        phase = idx / max(1, frame_count - 1)
        frame = generate_frame(width, height, phase, label, accent)
        frame_path = work_dir / f"part{idx:02d}.png"
        frame.save(frame_path)

    desc_lines = [f"{width} {height} {fps}"]
    for idx in range(frame_count):
        desc_lines.append(f"p 1 0 part{idx:02d}.png")
    (work_dir / "desc.txt").write_text("\n".join(desc_lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(work_dir.iterdir()):
            zf.write(file, arcname=file.name)

    shutil.rmtree(work_dir)


def create_systemui_template(out_dir: Path) -> None:
    ensure_dir(out_dir / "res" / "values")
    (out_dir / "AndroidManifest.xml").write_text(
        textwrap.dedent(
            """\
            <manifest package="com.mtl.systemui" xmlns:android="http://schemas.android.com/apk/res/android">
                <application android:label="MTL SystemUI" android:icon="@android:drawable/sym_def_app_icon" />
            </manifest>
            """
        ),
        encoding="utf-8",
    )
    (out_dir / "res" / "values" / "strings.xml").write_text(
        textwrap.dedent(
            """\
            <resources>
                <string name="app_name">MTL SystemUI</string>
                <string name="lockscreen_title">Welcome 🤗</string>
                <string name="arc_control_title">ARC Control</string>
            </resources>
            """
        ),
        encoding="utf-8",
    )
    (out_dir / "FlowSystemUI.kt").write_text(
        textwrap.dedent(
            """\
            package com.mtl.systemui

            import androidx.compose.foundation.background
            import androidx.compose.foundation.layout.Arrangement
            import androidx.compose.foundation.layout.Box
            import androidx.compose.foundation.layout.Column
            import androidx.compose.foundation.layout.Row
            import androidx.compose.foundation.layout.fillMaxSize
            import androidx.compose.foundation.layout.fillMaxWidth
            import androidx.compose.foundation.layout.height
            import androidx.compose.foundation.layout.padding
            import androidx.compose.foundation.shape.RoundedCornerShape
            import androidx.compose.material3.Text
            import androidx.compose.runtime.Composable
            import androidx.compose.ui.Alignment
            import androidx.compose.ui.Modifier
            import androidx.compose.ui.graphics.Color
            import androidx.compose.ui.text.font.FontWeight
            import androidx.compose.ui.unit.dp
            import androidx.compose.ui.unit.sp

            object MTLTheme {
                val Forest = Color(0xFF0A2F1F)
                val DeepForest = Color(0xFF081A12)
                val Sand = Color(0xFFE6D5B8)
                val Orange = Color(0xFFFF6B35)
            }

            @Composable
            fun MTLFlowLockscreen() {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(MTLTheme.DeepForest)
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "Welcome 🤗",
                            color = MTLTheme.Sand,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.SemiBold
                        )

                        Box(
                            modifier = Modifier
                                .padding(top = 28.dp)
                                .height(120.dp)
                                .fillMaxWidth()
                                .background(color = MTLTheme.Forest, shape = RoundedCornerShape(36.dp))
                                .padding(18.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Row(horizontalArrangement = Arrangement.SpaceEvenly) {
                                ArcAction("Camera")
                                ArcAction("Flash")
                            }
                        }
                    }
                }
            }

            @Composable
            fun MTLFlowStatusBar() {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MTLTheme.Forest)
                        .padding(horizontal = 18.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("9:41", color = MTLTheme.Sand, fontSize = 14.sp)
                    Text("MTL Flow", color = MTLTheme.Orange, fontSize = 14.sp)
                    Text("5G", color = MTLTheme.Sand, fontSize = 14.sp)
                }
            }

            @Composable
            fun MTLArcControlCenter() {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color(0xFF071A13))
                        .padding(20.dp),
                    contentAlignment = Alignment.CenterEnd
                ) {
                    Column(
                        modifier = Modifier
                            .background(MTLTheme.Forest, RoundedCornerShape(28.dp))
                            .padding(18.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("ARC Control", color = MTLTheme.Sand, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                        Text("Brightness", color = MTLTheme.Sand)
                        Text("Volume", color = MTLTheme.Sand)
                        Text("Flash", color = MTLTheme.Orange)
                    }
                }
            }

            @Composable
            private fun ArcAction(label: String) {
                Box(
                    modifier = Modifier
                        .background(Color(0xFF123F2C), RoundedCornerShape(24.dp))
                        .padding(horizontal = 20.dp, vertical = 12.dp)
                ) {
                    Text(label, color = MTLTheme.Sand, fontSize = 15.sp)
                }
            }
            """
        ),
        encoding="utf-8",
    )


def create_launcher_template(out_dir: Path) -> None:
    ensure_dir(out_dir / "res" / "values")
    (out_dir / "AndroidManifest.xml").write_text(
        textwrap.dedent(
            """\
            <manifest package="com.mtl.launcher" xmlns:android="http://schemas.android.com/apk/res/android">
                <application android:label="MTL Launcher" android:icon="@android:drawable/sym_def_app_icon" />
            </manifest>
            """
        ),
        encoding="utf-8",
    )
    (out_dir / "res" / "values" / "strings.xml").write_text(
        textwrap.dedent(
            """\
            <resources>
                <string name="app_name">MTL Launcher</string>
                <string name="dock_phone">Phone</string>
                <string name="dock_message">Chat</string>
                <string name="dock_ai">AI</string>
            </resources>
            """
        ),
        encoding="utf-8",
    )
    (out_dir / "FlowLauncher.kt").write_text(
        textwrap.dedent(
            """\
            package com.mtl.launcher

            import androidx.compose.foundation.background
            import androidx.compose.foundation.layout.Arrangement
            import androidx.compose.foundation.layout.Box
            import androidx.compose.foundation.layout.Column
            import androidx.compose.foundation.layout.Row
            import androidx.compose.foundation.layout.fillMaxSize
            import androidx.compose.foundation.layout.fillMaxWidth
            import androidx.compose.foundation.layout.height
            import androidx.compose.foundation.layout.padding
            import androidx.compose.foundation.shape.RoundedCornerShape
            import androidx.compose.material3.Text
            import androidx.compose.runtime.Composable
            import androidx.compose.ui.Alignment
            import androidx.compose.ui.Modifier
            import androidx.compose.ui.graphics.Color
            import androidx.compose.ui.text.font.FontWeight
            import androidx.compose.ui.unit.dp
            import androidx.compose.ui.unit.sp

            object MTLTheme {
                val Forest = Color(0xFF0A2F1F)
                val DeepForest = Color(0xFF081A12)
                val Sand = Color(0xFFE6D5B8)
                val Orange = Color(0xFFFF6B35)
            }

            @Composable
            fun MTLFlowLauncher() {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(MTLTheme.DeepForest)
                        .padding(18.dp),
                    contentAlignment = Alignment.BottomCenter
                ) {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.SpaceBetween,
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 22.dp),
                            horizontalArrangement = Arrangement.SpaceAround
                        ) {
                            AppBubble("Phone")
                            AppBubble("Chat")
                            AppBubble("Store")
                        }

                        Box(
                            modifier = Modifier
                                .fillMaxWidth(0.86f)
                                .height(78.dp)
                                .background(MTLTheme.Forest, RoundedCornerShape(38.dp))
                                .padding(horizontal = 22.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Row(horizontalArrangement = Arrangement.SpaceEvenly) {
                                DockApp("Cam")
                                DockApp("Msg")
                                DockApp("AI")
                            }
                        }
                    }
                }
            }

            @Composable
            private fun AppBubble(label: String) {
                Box(
                    modifier = Modifier
                        .background(Color(0xFF163D2E), RoundedCornerShape(28.dp))
                        .padding(horizontal = 20.dp, vertical = 18.dp)
                ) {
                    Text(label, color = MTLTheme.Sand, fontSize = 18.sp, fontWeight = FontWeight.Medium)
                }
            }

            @Composable
            private fun DockApp(label: String) {
                Text(label, color = MTLTheme.Sand, fontSize = 16.sp, fontWeight = FontWeight.Medium)
            }
            """
        ),
        encoding="utf-8",
    )


def make_app_files(app_dir: Path, package_name: str, display_name: str) -> None:
    ensure_dir(app_dir / "res" / "values")
    ensure_dir(app_dir / "app" / "src" / "main" / "java" / package_name.replace(".", "/"))

    (app_dir / "AndroidManifest.xml").write_text(
        textwrap.dedent(
            f"""\
            <manifest package="{package_name}" xmlns:android="http://schemas.android.com/apk/res/android">
                <application android:label="{display_name}" android:icon="@android:drawable/sym_def_app_icon">
                    <activity android:name=".MainActivity" android:exported="true">
                        <intent-filter>
                            <action android:name="android.intent.action.MAIN" />
                            <category android:name="android.intent.category.LAUNCHER" />
                        </intent-filter>
                    </activity>
                </application>
            </manifest>
            """
        ),
        encoding="utf-8",
    )

    (app_dir / "res" / "values" / "strings.xml").write_text(
        textwrap.dedent(
            f"""\
            <resources>
                <string name="app_name">{display_name}</string>
            </resources>
            """
        ),
        encoding="utf-8",
    )

    kt_file = app_dir / "app" / "src" / "main" / "java" / package_name.replace(".", "/") / "MainActivity.kt"
    kt_file.parent.mkdir(parents=True, exist_ok=True)
    kt_file.write_text(
        textwrap.dedent(
            f"""\
            package {package_name}

            import android.os.Bundle
            import androidx.activity.ComponentActivity
            import androidx.activity.compose.setContent
            import androidx.compose.foundation.background
            import androidx.compose.foundation.layout.Box
            import androidx.compose.foundation.layout.fillMaxSize
            import androidx.compose.foundation.layout.padding
            import androidx.compose.material3.MaterialTheme
            import androidx.compose.material3.Text
            import androidx.compose.runtime.Composable
            import androidx.compose.ui.Alignment
            import androidx.compose.ui.Modifier
            import androidx.compose.ui.graphics.Color
            import androidx.compose.ui.unit.dp

            class MainActivity : ComponentActivity() {{
                override fun onCreate(savedInstanceState: Bundle?) {{
                    super.onCreate(savedInstanceState)
                    setContent {{
                        MTLFlowTheme {{
                            MTLFlowScreen(title = \"{display_name}\")
                        }}
                    }}
                }}
            }}

            @Composable
            private fun MTLFlowTheme(content: @Composable () -> Unit) {{
                MaterialTheme(
                    colorScheme = MaterialTheme.colorScheme.copy(
                        primary = Color(0xFF0A2F1F),
                        secondary = Color(0xFFFF6B35),
                        surface = Color(0xFFE6D5B8),
                        background = Color(0xFF081A12)
                    ),
                    content = content
                )
            }}

            @Composable
            private fun MTLFlowScreen(title: String) {{
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color(0xFF081A12))
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {{
                    Text(
                        text = title,
                        color = Color(0xFFE6D5B8),
                        style = MaterialTheme.typography.headlineMedium
                    )
                }}
            }}
            """
        ),
        encoding="utf-8",
    )


def build_app_overlay(root_dir: Path) -> None:
    system_app_dir = root_dir / "system" / "app"
    system_priv_dir = root_dir / "system" / "priv-app"
    ensure_dir(system_app_dir)
    ensure_dir(system_priv_dir)

    for app_name in APP_NAMES:
        app_pkg = APP_MANIFEST[app_name]
        target_dir = system_app_dir / app_name
        if app_name in {"MTLSettings", "MTLDialer", "MTLContacts"}:
            target_dir = system_priv_dir / app_name
        make_app_files(target_dir, app_pkg, app_name)

    create_systemui_template(system_priv_dir / "MTLSystemUI")
    create_launcher_template(system_priv_dir / "MTLLauncher")


def write_manifest(root_dir: Path) -> None:
    manifest = {
        "project": "MTL OS1",
        "target": "AOSP overlay / system image",
        "packages": [
            {"name": app_name, "package": APP_MANIFEST[app_name]} for app_name in APP_NAMES
        ],
        "system_ui": "MTLSystemUI",
        "launcher": "MTLLauncher",
        "theme": {
            "deepForestGreen": "#0A2F1F",
            "riverSandBeige": "#E6D5B8",
            "sunsetOrange": "#FF6B35",
            "midnightForest": "#081A12",
        },
        "design_philosophy": [
            "Palm seed icons",
            "Organic leaf curves",
            "Arc control center",
            "Water-flow motion",
        ],
    }
    (root_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def create_system_image_stub(output_root: Path) -> None:
    image_path = output_root / "mtl-system.img"
    with zipfile.ZipFile(image_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted((output_root / "system").rglob("*")):
            if file_path.is_file():
                zf.write(file_path, arcname=str(file_path.relative_to(output_root)))
    return None


def create_mockup_svg(path: Path, title: str, subtitle: str, accent: str) -> None:
    svg = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1080\" height=\"1920\" viewBox=\"0 0 1080 1920\">
      <defs>
        <linearGradient id=\"bg\" x1=\"0\" x2=\"1\" y1=\"0\" y2=\"1\">
          <stop offset=\"0%\" stop-color=\"#081A12\"/>
          <stop offset=\"100%\" stop-color=\"#0A2F1F\"/>
        </linearGradient>
      </defs>
      <rect width=\"1080\" height=\"1920\" fill=\"url(#bg)\"/>
      <path d=\"M 100 1100 C 260 840, 420 980, 540 900 S 930 760, 980 1010 L 980 1450 C 890 1320, 760 1390, 645 1460 S 330 1520, 200 1460 L 100 1100 Z\" fill=\"{accent}\" opacity=\"0.9\"/>
      <path d=\"M 460 760 C 520 620, 590 640, 630 560 C 670 640, 740 650, 800 760 L 630 1100 Z\" fill=\"#E6D5B8\" opacity=\"0.82\"/>
      <circle cx=\"540\" cy=\"860\" r=\"80\" fill=\"#0A2F1F\" opacity=\"0.9\"/>
      <text x=\"540\" y=\"400\" text-anchor=\"middle\" font-size=\"64\" fill=\"#E6D5B8\" font-family=\"sans-serif\">{title}</text>
      <text x=\"540\" y=\"500\" text-anchor=\"middle\" font-size=\"30\" fill=\"#E6D5B8\" opacity=\"0.8\" font-family=\"sans-serif\">{subtitle}</text>
      <circle cx=\"540\" cy=\"1480\" r=\"200\" fill=\"none\" stroke=\"#E6D5B8\" stroke-width=\"4\" opacity=\"0.4\"/>
      <circle cx=\"540\" cy=\"1480\" r=\"150\" fill=\"none\" stroke=\"#FF6B35\" stroke-width=\"4\" opacity=\"0.6\"/>
    </svg>
    """
    path.write_text(svg, encoding="utf-8")


def build_mockups(root_dir: Path) -> None:
    screenshots_dir = root_dir / "docs" / "screenshots"
    ensure_dir(screenshots_dir)
    create_mockup_svg(screenshots_dir / "boot-animation.svg", "MTL Welcome", "leaf grows into river flow", "#FF6B35")
    create_mockup_svg(screenshots_dir / "shutdown-animation.svg", "See you soon", "seed settles into quiet water", "#E6D5B8")
    create_mockup_svg(screenshots_dir / "arc-control-center.svg", "ARC Control", "right-edge palm fronds", "#FF6B35")
    create_mockup_svg(screenshots_dir / "launcher-flow.svg", "Flow Canvas", "floating dock + river widgets", "#E6D5B8")


def build_output(output_dir: Path) -> None:
    ensure_dir(output_dir)
    build_mockups(output_dir.parent)
    media_dir = output_dir / "system" / "media"
    ensure_dir(media_dir)
    build_animation_zip(media_dir / "bootanimation.zip", "Welcome 🤗", "#FF6B35", fps=30, width=1080, height=1920, frame_count=18)
    build_animation_zip(media_dir / "shutdownanimation.zip", "See you soon 😃", "#E6D5B8", fps=30, width=1080, height=1920, frame_count=18)
    build_app_overlay(output_dir)
    write_manifest(output_dir)
    create_system_image_stub(output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the MTL OS1 AOSP overlay pack")
    parser.add_argument("--output", type=Path, default=Path("dist"), help="Output directory for the generated overlay")
    args = parser.parse_args()
    build_output(args.output)
    print(f"MTL overlay generated at {args.output.resolve()}")
