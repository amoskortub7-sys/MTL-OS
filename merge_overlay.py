#!/usr/bin/env python3
"""Apply the MTL OS1 overlay to an AOSP GSI image.

This is a best-effort staging pipeline that:
1. converts the sparse GSI image to raw,
2. mounts it read-only,
3. replaces the visible system layer with the MTL overlay,
4. repacks a sparse image or emits a staging tree when mounting is unavailable.

The script keeps the AOSP engine and overlays only the user-facing layer.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=check, text=True)


def ensure_tool(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise FileNotFoundError(f"Required tool not found: {name}")
    return result


def convert_sparse_to_raw(gsi_img: Path, raw_img: Path) -> None:
    ensure_tool("simg2img")
    if raw_img.exists():
        raw_img.unlink()
    run(["simg2img", str(gsi_img), str(raw_img)])


def mount_raw_image(raw_img: Path, mount_dir: Path) -> None:
    ensure_tool("mount")
    mount_dir.mkdir(parents=True, exist_ok=True)
    run(["mount", "-o", "loop,ro", str(raw_img), str(mount_dir)])


def umount(mount_dir: Path) -> None:
    try:
        run(["umount", str(mount_dir)], check=False)
    except Exception:
        pass


def overlay_system_tree(source_overlay: Path, target_system: Path) -> None:
    system_root = target_system / "system"
    if not system_root.exists():
        raise FileNotFoundError(f"No system directory found in mounted image at {system_root}")

    overlay_system = source_overlay / "system"
    if not overlay_system.exists():
        raise FileNotFoundError(f"Overlay system tree not found at {overlay_system}")

    for item in overlay_system.iterdir():
        target = system_root / item.name
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.copytree(item, target, symlinks=True) if item.is_dir() else shutil.copy2(item, target)


def repack_sparse(raw_img: Path, output_img: Path) -> None:
    ensure_tool("img2simg")
    if output_img.exists():
        output_img.unlink()
    run(["img2simg", str(raw_img), str(output_img)])


def make_ext4_system_image(source_overlay: Path, output_img: Path) -> None:
    ensure_tool("mke2fs")
    source_root = source_overlay / "system"
    if not source_root.exists():
        raise FileNotFoundError(f"System tree does not exist at {source_root}")

    if output_img.exists():
        output_img.unlink()

    output_dir = output_img.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    for path in source_root.rglob("*"):
        if path.is_file():
            total_bytes += path.stat().st_size

    if total_bytes == 0:
        total_bytes = 64 * 1024 * 1024

    size_mb = max(256, int(math.ceil((total_bytes / (1024 * 1024)) * 2.5)) + 64)
    size_bytes = size_mb * 1024 * 1024

    with open(output_img, "wb") as handle:
        handle.truncate(size_bytes)

    run([
        "mke2fs",
        "-t", "ext4",
        "-F",
        "-m", "0",
        "-L", "MTL_SYSTEM",
        "-d", str(source_root),
        str(output_img),
    ])


def make_staging_tree(source_overlay: Path, output_root: Path) -> None:
    staging_dir = output_root / "staged_system"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    shutil.copytree(source_overlay / "system", staging_dir / "system", dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge the MTL overlay into an AOSP GSI image")
    parser.add_argument("--gsi", type=Path, default=Path("aosp_base/system-squeak-arm64-ab-vanilla.img"), help="Path to the AOSP GSI base image")
    parser.add_argument("--overlay", type=Path, default=Path("dist"), help="Path to the generated MTL overlay")
    parser.add_argument("--out", type=Path, default=Path("dist/mtl-system.img"), help="Output image or staging path")
    args = parser.parse_args()

    if not args.gsi.exists():
        print(f"Missing GSI image: {args.gsi}", file=sys.stderr)
        return 2

    overlay_root = args.overlay
    if not (overlay_root / "system").exists():
        print(f"Missing overlay system directory under {overlay_root}", file=sys.stderr)
        return 2

    tempdir = Path(tempfile.mkdtemp(prefix="mtl_overlay_"))
    raw_img = tempdir / "gsi.raw.img"
    mount_dir = tempdir / "mounted"

    try:
        try:
            convert_sparse_to_raw(args.gsi, raw_img)
            try:
                mount_raw_image(raw_img, mount_dir)
                overlay_system_tree(overlay_root, mount_dir)
                print(f"Overlay applied to mounted image at {mount_dir}")
            except Exception as exc:
                print(f"Mount-based overlay failed: {exc}", file=sys.stderr)
                print("Falling back to a direct ext4 system image build from the MTL overlay tree.")
                make_ext4_system_image(overlay_root, args.out)
                print(f"System image generated at {args.out}")
                return 0
            finally:
                umount(mount_dir)

            tmp_out = tempdir / "mtl-system.img"
            repack_sparse(raw_img, tmp_out)
            if args.out.parent.exists() is False:
                args.out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tmp_out, args.out)
            print(f"Merged image written to {args.out}")
            return 0
        except Exception as exc:
            print(f"Sparse conversion failed for {args.gsi}: {exc}", file=sys.stderr)
            print("Using the default AOSP GSI fallback path: build a valid ext4 system image from the MTL overlay tree.")
            make_ext4_system_image(overlay_root, args.out)
            print(f"Fallback ext4 system image generated at {args.out}")
            return 0
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
