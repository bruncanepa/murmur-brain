#!/usr/bin/env python3
"""
Multi-platform build script for Murmur Brain
Builds executables for macOS, Windows, and Linux
"""

import sys
import os
import shutil
import subprocess
import argparse
import platform
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


class BuildSystem:
    """Main build orchestration system"""

    def __init__(self):
        self.root_dir = Path(__file__).parent.absolute()
        self.build_dir = self.root_dir / 'build'
        self.dist_dir = self.root_dir / 'dist'
        self.server_dir = self.root_dir / 'server'
        self.scripts_dir = self.root_dir / 'scripts'
        self.platform = platform.system()

    def print_step(self, message):
        """Print a build step message"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {message}{Colors.END}")

    def print_success(self, message):
        """Print a success message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")

    def print_error(self, message):
        """Print an error message"""
        print(f"{Colors.RED}✗ {message}{Colors.END}", file=sys.stderr)

    def print_warning(self, message):
        """Print a warning message"""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

    def run_command(self, command, cwd=None, shell=False):
        """Run a shell command and return success status"""
        try:
            if isinstance(command, str) and not shell:
                command = command.split()

            result = subprocess.run(
                command,
                cwd=cwd or self.root_dir,
                check=True,
                shell=shell,
                capture_output=False
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.print_error(f"Command failed with exit code {e.returncode}")
            return False
        except FileNotFoundError:
            self.print_error(f"Command not found: {command[0] if isinstance(command, list) else command}")
            return False

    def clean_build(self):
        """Clean previous build artifacts"""
        self.print_step("Cleaning previous build artifacts...")

        dirs_to_clean = [
            self.build_dir,
            self.root_dir / 'dist_pyinstaller',
            self.root_dir / '__pycache__',
            self.server_dir / '__pycache__',
        ]

        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.print_success(f"Removed {dir_path.name}/")

        # Clean .pyc files
        for pyc_file in self.root_dir.rglob('*.pyc'):
            pyc_file.unlink()

        self.print_success("Build artifacts cleaned")

    def check_dependencies(self):
        """Check if required dependencies are installed"""
        self.print_step("Checking dependencies...")

        dependencies = {
            'node': 'Node.js is required for frontend build',
            'pnpm': 'pnpm is required (npm install -g pnpm)',
            'python3': 'Python 3 is required',
            'pip3': 'pip3 is required for Python packages'
        }

        missing = []
        for cmd, message in dependencies.items():
            if not shutil.which(cmd):
                self.print_error(f"{cmd} not found: {message}")
                missing.append(cmd)
            else:
                self.print_success(f"{cmd} found")

        if missing:
            self.print_error(f"Missing dependencies: {', '.join(missing)}")
            return False

        # Check PyInstaller
        try:
            import PyInstaller
            self.print_success("PyInstaller found")
        except ImportError:
            self.print_error("PyInstaller not found. Install: pip3 install pyinstaller")
            return False

        return True

    def build_frontend(self):
        """Build the React frontend"""
        self.print_step("Building frontend with Vite...")

        # Install dependencies
        if not (self.root_dir / 'node_modules').exists():
            self.print_step("Installing frontend dependencies...")
            if not self.run_command(['pnpm', 'install']):
                return False
            self.print_success("Frontend dependencies installed")

        # Build
        if not self.run_command(['pnpm', 'build']):
            self.print_error("Frontend build failed")
            return False

        if not self.dist_dir.exists():
            self.print_error("Frontend build did not produce dist/ folder")
            return False

        self.print_success("Frontend built successfully")
        return True

    def install_python_deps(self):
        """Install Python dependencies"""
        self.print_step("Installing Python dependencies...")

        requirements = self.server_dir / 'requirements.txt'
        if not requirements.exists():
            self.print_error("requirements.txt not found")
            return False

        if not self.run_command(['pip3', 'install', '-r', str(requirements)]):
            self.print_error("Failed to install Python dependencies")
            return False

        # Install PyInstaller if not present
        if not self.run_command(['pip3', 'install', 'pyinstaller']):
            self.print_warning("PyInstaller installation failed, may already be installed")

        self.print_success("Python dependencies installed")
        return True

    def build_executable(self):
        """Build executable with PyInstaller"""
        self.print_step(f"Building executable for {self.platform}...")

        spec_file = self.root_dir / 'murmur-brain.spec'
        if not spec_file.exists():
            self.print_error("murmur-brain.spec not found")
            return False

        # Run PyInstaller
        if not self.run_command(['pyinstaller', '--clean', '-y', str(spec_file)]):
            self.print_error("PyInstaller build failed")
            return False

        self.print_success(f"Executable built for {self.platform}")
        return True

    def package_macos(self):
        """Package macOS .app and create .dmg"""
        self.print_step("Packaging for macOS...")

        app_path = self.root_dir / 'dist' / 'Murmur-Brain.app'
        if not app_path.exists():
            self.print_error(f"Application bundle not found at {app_path}")
            return False

        # Create build/macos directory
        macos_build_dir = self.build_dir / 'macos'
        macos_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy .app bundle
        dest_app = macos_build_dir / 'Murmur-Brain.app'
        if dest_app.exists():
            shutil.rmtree(dest_app)
        shutil.copytree(app_path, dest_app)
        self.print_success(f"Copied .app bundle to {macos_build_dir}")

        # TODO: Create .dmg (requires create-dmg or similar tool)
        self.print_warning("DMG creation not yet implemented")
        self.print_warning("Install create-dmg: brew install create-dmg")

        return True

    def package_windows(self):
        """Package Windows executable and create installer"""
        self.print_step("Packaging for Windows...")

        exe_path = self.root_dir / 'dist' / 'Murmur-Brain.exe'
        if not exe_path.exists():
            self.print_error(f"Executable not found at {exe_path}")
            return False

        # Create build/windows directory
        windows_build_dir = self.build_dir / 'windows'
        windows_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy executable
        dest_exe = windows_build_dir / 'Murmur-Brain.exe'
        shutil.copy(exe_path, dest_exe)
        self.print_success(f"Copied executable to {windows_build_dir}")

        # TODO: Create installer with NSIS
        self.print_warning("Installer creation not yet implemented")
        self.print_warning("Install NSIS for creating installers")

        return True

    def package_linux(self):
        """Package Linux executable and create AppImage"""
        self.print_step("Packaging for Linux...")

        app_dir = self.root_dir / 'dist' / 'Murmur-Brain'
        if not app_dir.exists():
            self.print_error(f"Application directory not found at {app_dir}")
            return False

        # Create build/linux directory
        linux_build_dir = self.build_dir / 'linux'
        linux_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy application directory
        dest_dir = linux_build_dir / 'Murmur-Brain'
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(app_dir, dest_dir)
        self.print_success(f"Copied application to {linux_build_dir}")

        # TODO: Create AppImage
        self.print_warning("AppImage creation not yet implemented")
        self.print_warning("Install appimagetool for creating AppImages")

        return True

    def build_for_platform(self, target_platform=None):
        """Build for specific platform"""
        target = target_platform or self.platform

        # Build frontend and backend (common steps)
        if not self.build_frontend():
            return False

        if not self.install_python_deps():
            return False

        if not self.build_executable():
            return False

        # Platform-specific packaging
        if target == 'Darwin':  # macOS
            return self.package_macos()
        elif target == 'Windows':
            return self.package_windows()
        elif target.startswith('Linux'):
            return self.package_linux()
        else:
            self.print_error(f"Unsupported platform: {target}")
            return False

    def build_all(self):
        """Build for all platforms"""
        self.print_step("Building for all platforms...")

        platforms = ['Darwin', 'Windows', 'Linux']
        results = {}

        for platform_name in platforms:
            self.print_step(f"\n{'='*60}")
            self.print_step(f"Building for {platform_name}")
            self.print_step(f"{'='*60}")

            if platform_name == self.platform or platform_name.startswith(self.platform):
                results[platform_name] = self.build_for_platform(platform_name)
            else:
                self.print_warning(f"Cross-compilation for {platform_name} not supported")
                self.print_warning("Build on native platform or use CI/CD")
                results[platform_name] = False

        # Summary
        self.print_step("\n" + "="*60)
        self.print_step("Build Summary")
        self.print_step("="*60)
        for platform_name, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            color = Colors.GREEN if success else Colors.RED
            print(f"{color}{platform_name:20} {status}{Colors.END}")

        return all(results.values())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Build Murmur Brain for multiple platforms')
    parser.add_argument('--all', action='store_true', help='Build for all platforms')
    parser.add_argument('--macos', action='store_true', help='Build for macOS')
    parser.add_argument('--windows', action='store_true', help='Build for Windows')
    parser.add_argument('--linux', action='store_true', help='Build for Linux')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts')
    parser.add_argument('--check', action='store_true', help='Check dependencies only')

    args = parser.parse_args()
    builder = BuildSystem()

    # Print header
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Murmur Brain Build System{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

    # Clean if requested
    if args.clean:
        builder.clean_build()
        return 0

    # Check dependencies
    if not builder.check_dependencies():
        return 1

    if args.check:
        return 0

    # Determine what to build
    if args.all:
        success = builder.build_all()
    elif args.macos:
        success = builder.build_for_platform('Darwin')
    elif args.windows:
        success = builder.build_for_platform('Windows')
    elif args.linux:
        success = builder.build_for_platform('Linux')
    else:
        # Default: build for current platform
        builder.print_step(f"Building for current platform: {builder.platform}")
        success = builder.build_for_platform()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
