#!/bin/bash
# macOS-specific build and packaging script
# Creates .app bundle and .dmg installer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/macos"
APP_NAME="Murmur-Brain"

echo "=================================================="
echo "macOS Build and Packaging Script"
echo "=================================================="

cd "$PROJECT_ROOT"

# Step 1: Run main build
echo ""
echo "▶ Running main build process..."
python3 build-all.py --macos

if [ $? -ne 0 ]; then
    echo "✗ Build failed"
    exit 1
fi

# Step 2: Code signing (if certificates are configured)
echo ""
echo "▶ Checking for code signing..."

# Check if CODESIGN_IDENTITY environment variable is set
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "▶ Code signing with identity: $CODESIGN_IDENTITY"

    APP_PATH="$BUILD_DIR/$APP_NAME.app"

    # Sign the app bundle
    codesign --force --deep --sign "$CODESIGN_IDENTITY" \
        --options runtime \
        --entitlements "$PROJECT_ROOT/scripts/entitlements.plist" \
        "$APP_PATH"

    # Verify signature
    codesign --verify --verbose "$APP_PATH"

    echo "✓ Code signing completed"
else
    echo "⚠ CODESIGN_IDENTITY not set, skipping code signing"
    echo "  To enable signing, set: export CODESIGN_IDENTITY=\"Developer ID Application: Your Name\""
fi

# Step 3: Create DMG installer (requires create-dmg)
echo ""
echo "▶ Creating DMG installer..."

if command -v create-dmg &> /dev/null; then
    DMG_PATH="$BUILD_DIR/$APP_NAME.dmg"

    # Remove old DMG if exists
    rm -f "$DMG_PATH"

    # Create DMG
    create-dmg \
        --volname "$APP_NAME" \
        --volicon "$PROJECT_ROOT/resources/icon.icns" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 200 190 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 600 185 \
        "$DMG_PATH" \
        "$BUILD_DIR" \
        || echo "⚠ DMG creation failed (non-fatal)"

    if [ -f "$DMG_PATH" ]; then
        echo "✓ DMG created: $DMG_PATH"
    fi
else
    echo "⚠ create-dmg not found. Install with: brew install create-dmg"
    echo "  Skipping DMG creation"
fi

# Step 4: Notarization (if configured)
echo ""
echo "▶ Checking for notarization..."

if [ -n "$APPLE_ID" ] && [ -n "$APPLE_ID_PASSWORD" ] && [ -n "$TEAM_ID" ]; then
    echo "▶ Notarizing app..."

    DMG_PATH="$BUILD_DIR/$APP_NAME.dmg"

    if [ -f "$DMG_PATH" ]; then
        # Submit for notarization
        xcrun notarytool submit "$DMG_PATH" \
            --apple-id "$APPLE_ID" \
            --password "$APPLE_ID_PASSWORD" \
            --team-id "$TEAM_ID" \
            --wait

        # Staple the ticket
        xcrun stapler staple "$DMG_PATH"

        echo "✓ Notarization completed"
    else
        echo "⚠ DMG not found, skipping notarization"
    fi
else
    echo "⚠ Notarization credentials not set, skipping"
    echo "  Required environment variables:"
    echo "    - APPLE_ID"
    echo "    - APPLE_ID_PASSWORD (app-specific password)"
    echo "    - TEAM_ID"
fi

# Summary
echo ""
echo "=================================================="
echo "Build Complete!"
echo "=================================================="
echo "Output location: $BUILD_DIR"
echo ""
ls -lh "$BUILD_DIR"
echo ""
