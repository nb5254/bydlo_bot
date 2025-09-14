import os
import sys
import traceback
import time

print("=== STARTING COMPREHENSIVE DEBUG ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Check environment variables first
print("\n=== CHECKING ENVIRONMENT VARIABLES ===")
required_vars = ["TG_API_ID", "TG_API_HASH", "TG_BOT_TOKEN", "ANTHROPIC_API_KEY"]
all_vars_present = True

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: SET (length: {len(value)})")
    else:
        print(f"❌ {var}: NOT SET")
        all_vars_present = False

if not all_vars_present:
    print("❌ CRITICAL: Missing environment variables!")
    print("Bot cannot start without all 4 environment variables.")
    sys.exit(1)

# Test basic imports
print("\n=== TESTING BASIC IMPORTS ===")

basic_imports = [
    "asyncio", "typing", "os", "sys",
    "cachetools", "structlog", "pyrogram", "anthropic", "pydantic"
]

for module in basic_imports:
    try:
        __import__(module)
        print(f"✅ {module}")
    except Exception as e:
        print(f"❌ {module}: {e}")

# Test custom module imports
print("\n=== TESTING CUSTOM MODULE IMPORTS ===")

try:
    print("Testing: import db")
    import db
    print("✅ db imported")
except Exception as e:
    print(f"❌ db failed: {e}")
    traceback.print_exc()

try:
    print("Testing: import db.kv")
    import db.kv
    print("✅ db.kv imported")
except Exception as e:
    print(f"❌ db.kv failed: {e}")
    traceback.print_exc()

try:
    print("Testing: import realm")
    import realm
    print("✅ realm imported")
except Exception as e:
    print(f"❌ realm failed: {e}")
    traceback.print_exc()

try:
    print("Testing: import realm.anthropic")
    import realm.anthropic
    print("✅ realm.anthropic imported")
except Exception as e:
    print(f"❌ realm.anthropic failed: {e}")
    traceback.print_exc()

try:
    print("Testing: import realm.anthropic.api")
    import realm.anthropic.api
    print("✅ realm.anthropic.api imported")
except Exception as e:
    print(f"❌ realm.anthropic.api failed: {e}")
    traceback.print_exc()

try:
    print("Testing: import bydlan")
    import bydlan
    print("✅ bydlan imported")
except Exception as e:
    print(f"❌ bydlan failed: {e}")
    traceback.print_exc()

# Test API initialization
print("\n=== TESTING API INITIALIZATION ===")

try:
    print("Testing Anthropic API initialization...")
    import realm.anthropic.api as anthropic_api
    import asyncio
    
    async def test_api():
        try:
            await anthropic_api.init()
            print("✅ Anthropic API initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Anthropic API initialization failed: {e}")
            traceback.print_exc()
            return False
    
    api_success = asyncio.run(test_api())
    
except Exception as e:
    print(f"❌ API test setup failed: {e}")
    traceback.print_exc()
    api_success = False

# Test bot initialization if API works
if api_success:
    print("\n=== TESTING BOT INITIALIZATION ===")
    try:
        print("Testing bot initialization...")
        import bydlan
        
        async def test_bot():
            try:
                await bydlan.init()
                print("✅ Bot initialized successfully")
                print("✅ ALL TESTS PASSED - Bot should be working!")
                return True
            except Exception as e:
                print(f"❌ Bot initialization failed: {e}")
                traceback.print_exc()
                return False
        
        bot_success = asyncio.run(test_bot())
        
        if bot_success:
            print("\n🎉 SUCCESS: Bot is ready to run!")
            print("Keeping bot alive...")
            
            # Keep the bot running
            while True:
                print("Bot is running... (will print every 60 seconds)")
                time.sleep(60)
                
    except Exception as e:
        print(f"❌ Bot test setup failed: {e}")
        traceback.print_exc()

print("\n=== DEBUG COMPLETE ===")
print("If you see this, check the errors above.")

# Keep running for Railway to see the logs
while True:
    print("Debug complete - check logs above for errors")
    time.sleep(60)
