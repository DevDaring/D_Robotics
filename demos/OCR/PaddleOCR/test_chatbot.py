#!/usr/bin/env python3
"""
Test Chatbot - Standalone Gemini 2.5 Flash Test Script

This script demonstrates a simple chatbot using Google Gemini 2.5 Flash model.
Takes dummy input and returns AI-generated responses.

Target Platform: RDK x5 Kit (Ubuntu 22.04 ARM64)
Image: rdk-x5-ubuntu22-preinstalled-desktop-3.3.3-arm64.img.xz

============================================================
INSTALLATION INSTRUCTIONS FOR RDK X5 (Ubuntu 22 ARM64)
============================================================

Step 1: Update system packages
    sudo apt update && sudo apt upgrade -y

Step 2: Install Python and pip (if not already installed)
    sudo apt install -y python3 python3-pip python3-venv

Step 3: Install required Python package
    pip3 install google-generativeai

Step 4: (Optional) If SSL certificate errors occur
    pip3 install certifi
    export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")

Step 5: Run the script
    python3 test_chatbot.py

============================================================
MINIMUM REQUIREMENTS
============================================================
- Python 3.8 or higher
- google-generativeai >= 0.3.0
- Internet connection for API calls
- Valid Gemini API key

============================================================
"""

import os
import sys

# ============================================================
# CONFIGURATION - Gemini API Credentials
# ============================================================
# GCP Project: hackathon-472817
# Account: koushikdeb2009@gmail.com
#
# To get your API key:
# 1. Go to: https://aistudio.google.com/app/apikey
# 2. Create API key for project: hackathon-472817
# 3. Replace the placeholder below with your actual API key

GEMINI_API_KEY = "Secret"  # <-- Replace with your actual API key
MODEL_NAME = "gemini-2.5-flash-lite-preview-09-2025"  # Gemini 2.5 Flash model

# ============================================================
# DUMMY TEST INPUTS
# ============================================================
DUMMY_INPUTS = [
    "Hello! What is your name?",
    "Explain quantum computing in simple terms for a 10-year-old.",
    "Write a short poem about artificial intelligence.",
    "What are the top 3 benefits of renewable energy?",
    "Tell me a fun fact about the human brain.",
]


def setup_gemini():
    """
    Initialize the Gemini API client.
    
    Returns:
        Configured GenerativeModel instance or None on error
    """
    try:
        import google.generativeai as genai
        
        # Configure API key
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Create model instance
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        
        print(f"[SETUP] ✅ Gemini API configured successfully")
        print(f"[SETUP] Model: {MODEL_NAME}")
        return model
        
    except ImportError:
        print("[SETUP] ❌ Error: google-generativeai not installed")
        print("[SETUP] Run: pip3 install google-generativeai")
        return None
    except Exception as e:
        print(f"[SETUP] ❌ Error: {e}")
        return None


def chat_with_gemini(model, user_input: str) -> str:
    """
    Send a message to Gemini and get a response.
    
    Args:
        model: Configured GenerativeModel instance
        user_input: User's message/question
        
    Returns:
        AI response text or error message
    """
    try:
        # Generate response
        response = model.generate_content(user_input)
        
        # Extract text from response
        if response and response.text:
            return response.text
        else:
            return "(No response generated)"
            
    except Exception as e:
        return f"Error: {e}"


def run_dummy_tests(model):
    """
    Run all dummy test inputs and display results.
    
    Args:
        model: Configured GenerativeModel instance
    """
    print("\n" + "=" * 60)
    print("🧪 RUNNING DUMMY TESTS")
    print("=" * 60)
    
    for i, user_input in enumerate(DUMMY_INPUTS, 1):
        print(f"\n{'─' * 60}")
        print(f"📝 TEST {i}/{len(DUMMY_INPUTS)}")
        print(f"{'─' * 60}")
        print(f"\n👤 USER INPUT:")
        print(f"   {user_input}")
        
        print(f"\n🤖 GEMINI RESPONSE:")
        response = chat_with_gemini(model, user_input)
        
        # Format response with indentation
        for line in response.split('\n'):
            print(f"   {line}")
        
        print()


def interactive_mode(model):
    """
    Run interactive chat mode where user can type questions.
    
    Args:
        model: Configured GenerativeModel instance
    """
    print("\n" + "=" * 60)
    print("💬 INTERACTIVE CHAT MODE")
    print("=" * 60)
    print("Type your questions below. Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            print("\n🤖 Gemini: ", end="")
            response = chat_with_gemini(model, user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def main():
    """Main function to run the chatbot test."""
    print("=" * 60)
    print("🤖 Gemini 2.5 Flash Chatbot Test")
    print("=" * 60)
    print(f"\nPlatform: RDK x5 Kit (Ubuntu 22 ARM64)")
    print(f"Model: {MODEL_NAME}")
    print(f"Project: hackathon-472817")
    print("-" * 60)
    
    # Check if API key is set
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("\n⚠️  WARNING: API key not configured!")
        print("   Please edit this file and replace 'YOUR_GEMINI_API_KEY_HERE'")
        print("   with your actual Gemini API key from:")
        print("   https://aistudio.google.com/app/apikey")
        print("\n   Make sure to select project: hackathon-472817")
        return
    
    # Setup Gemini
    print("\n[INIT] Initializing Gemini API...")
    model = setup_gemini()
    
    if not model:
        print("\n❌ Failed to initialize Gemini. Exiting.")
        return
    
    # Run dummy tests first
    run_dummy_tests(model)
    
    # Ask if user wants interactive mode
    print("\n" + "=" * 60)
    print("📊 DUMMY TESTS COMPLETED")
    print("=" * 60)
    
    try:
        choice = input("\n🔄 Enter interactive chat mode? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            interactive_mode(model)
    except (KeyboardInterrupt, EOFError):
        pass
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
