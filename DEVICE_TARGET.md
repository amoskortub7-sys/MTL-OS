# MTL OS1 Device Target

This project is aligned to the following custom OEM prototype specification:

- Model: MTL-OG1
- Device type: Custom OEM prototype, not a retail Xiaomi/POCO device
- Chipset: MediaTek Dimensity 7400 Ultra 5G
- CPU architecture: arm64-v8a
- RAM: 12GB
- Storage: 512GB UFS 3.1
- Battery: 6500mAh
- Biometrics: In-display optical fingerprint scanner
- Display: Curved AMOLED, single 50MP front punch-hole at top-right
- Rear camera: 50MP main + 50MP telephoto + 8MP ultra-wide + LED flash
- Main camera sensor: Sony LYT-700C, 1/1.56 inch, 7P glass, f/1.8, OIS
- Video: 4K @ 30fps with EIS
- Protection: IP54 splash and dust resistance
- Bootloader: Unlocked factory engineering build
- Flash method: fastboot unlock enabled by default

## Base platform

- Firmware base: Stock Android 16 AOSP GSI (aosp_arm64-ab)
- Vendor package: MediaTek BSP driver package
- Build strategy: Keep the AOSP engine and replace the user-visible layer with the MTL Flow UI

## Important note

This is the correct custom OEM target profile for the MTL OS1 prototype. The project is still not a completed flashable phone ROM until the exact OEM board support package, device tree, BSP vendor files, kernel, and signed images are integrated for the MTL-OG1 engineering unit.

The current repo is therefore a realistic AOSP overlay build target for this exact hardware and prototype platform, not a finished retail-device installer.
