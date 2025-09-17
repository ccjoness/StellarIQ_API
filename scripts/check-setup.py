#!/usr/bin/env python3
"""
Script to check if the development environment is properly set up.
"""

import sys
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
        return False


def check_poetry():
    """Check if Poetry is available"""
    try:
        result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
        else:
            print("❌ Poetry not found")
            return False
    except FileNotFoundError:
        print("❌ Poetry not found")
        return False


def check_dependencies():
    """Check if key dependencies are installed"""
    dependencies = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "redis",
        "httpx",
        "pydantic",
        "alembic",
    ]
    
    missing = []
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing.append(dep)
    
    return len(missing) == 0


def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file not found")
        return False


def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            
            # Check docker-compose
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
                return True
            else:
                print("❌ Docker Compose not found")
                return False
        else:
            print("❌ Docker not found")
            return False
    except FileNotFoundError:
        print("❌ Docker not found")
        return False


def main():
    """Run all checks"""
    print("🔍 Checking StellarIQ Backend development environment...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Poetry", check_poetry),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Docker", check_docker),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append(check_func())
    
    print("\n" + "="*50)
    
    if all(results):
        print("🎉 All checks passed! Your development environment is ready.")
        print("\nNext steps:")
        print("1. Start services: make docker-up")
        print("2. Run migrations: make upgrade")
        print("3. Start server: make run")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nFor help, run: make help")
        sys.exit(1)


if __name__ == "__main__":
    main()
