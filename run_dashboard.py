"""Quick startup guide and validation script."""

import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Verify all required packages are available."""
    print("\n" + "=" * 70)
    print("📦 Checking Dependencies")
    print("=" * 70)

    required_packages = {
        "streamlit": "Streamlit dashboard framework",
        "plotly": "Interactive visualizations",
        "pandas": "Data processing",
        "numpy": "Numerical computing",
        "scipy": "Scientific computing",
        "networkx": "Graph algorithms",
    }

    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {package:20} {description}")
        except ImportError:
            print(f"✗ {package:20} {description} [MISSING]")
            missing.append(package)

    return missing


def install_missing(packages):
    """Install missing packages."""
    if not packages:
        return True

    print("\n" + "=" * 70)
    print("⬇️  Installing Missing Packages")
    print("=" * 70)

    for package in packages:
        print(f"\nInstalling {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--quiet"],
            capture_output=True,
        )
        if result.returncode != 0:
            print(f"⚠️  Failed to install {package}")
            print(f"   Manual install: pip install {package}")
            return False
        print(f"✓ {package} installed")

    return True


def run_tests():
    """Run metrics test suite."""
    print("\n" + "=" * 70)
    print("🧪 Running Tests")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, "test_metrics.py"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Tests failed!")
        print(result.stdout)
        print(result.stderr)
        return False


def run_dashboard():
    """Start the Streamlit dashboard."""
    print("\n" + "=" * 70)
    print("🚀 Starting Dashboard")
    print("=" * 70)
    print("\n📍 Dashboard will open at: http://localhost:8501")
    print("   Press Ctrl+C to stop\n")

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "ui/dashboard.py"],
            cwd=Path(__file__).parent,
        )
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard stopped")


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🚀 Smart Delivery Dispatch System - Dashboard Startup  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    # Check dependencies
    missing = check_dependencies()

    if missing:
        print(f"\n⚠️  {len(missing)} package(s) missing")
        print("   Option 1: Install automatically? (recommended)")
        print("   Option 2: Continue with core features only")
        print("   Option 3: Exit")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            if not install_missing(missing):
                print("\n⚠️  Some packages failed to install")
                print("   Dashboard requires: streamlit, plotly")
        elif choice == "3":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Continuing with available packages...")

    # Run tests
    if input("\nRun metrics tests first? (y/n): ").strip().lower() == "y":
        if not run_tests():
            print("\n⚠️  Tests failed. Continue anyway? (y/n): ", end="")
            if input().strip().lower() != "y":
                sys.exit(1)

    # Start dashboard
    if input("\nStart dashboard? (y/n): ").strip().lower() == "y":
        run_dashboard()
    else:
        print("\n✓ You can run 'streamlit run ui/dashboard.py' manually")
        print("  Or: python run_dashboard.py")


if __name__ == "__main__":
    main()
