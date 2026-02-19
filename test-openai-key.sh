#!/bin/bash

echo "Testing OpenAI API Key..."
echo ""

# Test with gpt-4o-mini (cheaper model)
docker exec rift-backend-1 python3 << 'EOF'
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print("")

client = OpenAI(api_key=api_key)

# Test 1: Try gpt-4o-mini
print("Test 1: Trying gpt-4o-mini...")
try:
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': 'Say "API works!"'}],
        max_tokens=10
    )
    print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
except Exception as e:
    error = str(e)
    if '429' in error or 'quota' in error.lower():
        print(f"❌ QUOTA EXCEEDED - This API key has no credits")
        print(f"   Go to: https://platform.openai.com/account/billing")
    elif '401' in error or 'authentication' in error.lower():
        print(f"❌ INVALID KEY - This API key is not valid")
    else:
        print(f"❌ ERROR: {error[:200]}")

print("")

# Test 2: Try gpt-3.5-turbo (cheapest)
print("Test 2: Trying gpt-3.5-turbo (cheapest)...")
try:
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'Say "API works!"'}],
        max_tokens=10
    )
    print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
except Exception as e:
    error = str(e)
    if '429' in error or 'quota' in error.lower():
        print(f"❌ QUOTA EXCEEDED - This API key has no credits")
    elif '401' in error or 'authentication' in error.lower():
        print(f"❌ INVALID KEY - This API key is not valid")
    else:
        print(f"❌ ERROR: {error[:200]}")

EOF

echo ""
echo "========================================="
echo "If you see 'QUOTA EXCEEDED' errors above:"
echo "1. Go to: https://platform.openai.com/account/billing"
echo "2. Add payment method and credits ($5 minimum)"
echo "3. Wait 2-3 minutes for activation"
echo "4. Run this test again"
echo "========================================="
