#!/bin/bash
# Linux-specific build and packaging script
# Creates AppImage for portable Linux distribution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/linux"
APP_NAME="Murmur-Brain"

echo "=================================================="
echo "Linux Build and Packaging Script"
echo "=================================================="

cd "$PROJECT_ROOT"

# Step 1: Run main build
echo ""
echo "▶ Running main build process..."
python3 build-all.py --linux

if [ $? -ne 0 ]; then
    echo "✗ Build failed"
    exit 1
fi

# Step 2: Create AppDir structure
echo ""
echo "▶ Creating AppDir structure..."

APPDIR="$BUILD_DIR/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy application files
cp -r "$BUILD_DIR/$APP_NAME"/* "$APPDIR/usr/bin/"

# Create desktop entry
cat > "$APPDIR/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Local Brain
Comment=Local RAG Application with Ollama
Exec=$APP_NAME
Icon=$APP_NAME
Categories=Utility;Development;
Terminal=false
EOF

# Copy icon (if exists)
if [ -f "$PROJECT_ROOT/resources/icon.png" ]; then
    cp "$PROJECT_ROOT/resources/icon.png" \
        "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"
fi

# Create AppRun script
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin"
exec "./Murmur-Brain" "$@"
EOF

chmod +x "$APPDIR/AppRun"

echo "✓ AppDir structure created"

# Step 3: Create AppImage (if appimagetool is available)
echo ""
echo "▶ Creating AppImage..."

if command -v appimagetool &> /dev/null; then
    APPIMAGE_PATH="$BUILD_DIR/$APP_NAME-x86_64.AppImage"

    # Remove old AppImage if exists
    rm -f "$APPIMAGE_PATH"

    # Create AppImage
    appimagetool "$APPDIR" "$APPIMAGE_PATH"

    if [ -f "$APPIMAGE_PATH" ]; then
        chmod +x "$APPIMAGE_PATH"
        echo "✓ AppImage created: $APPIMAGE_PATH"
    else
        echo "✗ AppImage creation failed"
    fi
else
    echo "⚠ appimagetool not found"
    echo "  Download from: https://github.com/AppImage/AppImageKit/releases"
    echo "  Install: chmod +x appimagetool-*.AppImage && sudo mv appimagetool-*.AppImage /usr/local/bin/appimagetool"
    echo "  Skipping AppImage creation"
fi

# Step 4: Create .deb package (optional)
echo ""
echo "▶ Checking for .deb package creation..."

if command -v dpkg-deb &> /dev/null; then
    echo "▶ Creating .deb package..."

    DEB_DIR="$BUILD_DIR/deb"
    rm -rf "$DEB_DIR"
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/usr/local/bin"
    mkdir -p "$DEB_DIR/usr/share/applications"

    # Copy files
    cp -r "$BUILD_DIR/$APP_NAME" "$DEB_DIR/usr/local/bin/"
    cp "$APPDIR/usr/share/applications/$APP_NAME.desktop" \
        "$DEB_DIR/usr/share/applications/"

    # Create control file
    cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: murmur-brain
Version: 2.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Local Brain <contact@example.com>
Description: Local RAG Application with Ollama
 A local RAG (Retrieval-Augmented Generation) application
 that works with Ollama for AI-powered document processing.
EOF

    # Build .deb
    dpkg-deb --build "$DEB_DIR" "$BUILD_DIR/${APP_NAME}_2.0.0_amd64.deb"

    echo "✓ .deb package created"
else
    echo "⚠ dpkg-deb not found, skipping .deb creation"
fi

# Summary
echo ""
echo "=================================================="
echo "Build Complete!"
echo "=================================================="
echo "Output location: $BUILD_DIR"
echo ""
ls -lh "$BUILD_DIR" | grep -E "\.(AppImage|deb)$" || echo "No packages created"
echo ""
