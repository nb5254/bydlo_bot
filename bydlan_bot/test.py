import os
import sys

print("=" * 50)
print("RAILWAY DEBUG TEST")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")
print("\nEnvironment variables:")
print(f"TG_API_ID: {'✅ SET' if os.getenv('TG_API_ID') else '❌ MISSING'}")
print(f"TG_API_HASH: {'✅ SET' if os.getenv('TG_API_HASH') else '❌ MISSING'}")
print(f"TG_BOT_TOKEN: {'✅ SET' if os.getenv('TG_BOT_TOKEN') else '❌ MISSING'}")
print(f"ANTHROPIC_API_KEY: {'✅ SET' if os.getenv('ANTHROPIC_API_KEY') else '❌ MISSING'}")
print("=" * 50)
print("Test complete. If you see this, Python is working!")
print("=" * 50)
