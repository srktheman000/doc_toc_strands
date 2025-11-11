"""Simple test of the strands-agents implementation."""

import os
os.environ["GEMINI_API_KEY"] = "AIzaSyCHOi7lTvC3qxcHTAkQiaVdsyN_lwFeydw"

from src.gemini_agent import GeminiAgent

try:
    print("=== Testing GeminiAgent Initialization ===")
    agent = GeminiAgent()
    print("[OK] Agent initialized successfully!")

    print("\n=== Testing Calculator Tool ===")
    response = agent.send_message("What is 2+2?")
    print(f"Response: {response}")

    print("\n=== Test Complete ===")
    print("All tests passed!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
