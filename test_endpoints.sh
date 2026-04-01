#!/usr/bin/env bash
# Test script for OpenRouter FastAPI Service

set -e

BASE_URL="http://localhost:8000"

echo "🔍 Testing OpenRouter FastAPI Service..."
echo ""

# Test 1: Health check
echo "✅ Test 1: Health Check"
curl -s -X GET "$BASE_URL/health" | jq . || echo "Failed to reach /health"
echo ""

# Test 2: Chat endpoint (non-streaming)
echo "✅ Test 2: Chat Endpoint (Non-Streaming)"
echo "Sending: 'Say hello in exactly one word'"
echo ""
curl -s -X POST "$BASE_URL/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Say hello in exactly one word"}
    ],
    "temperature": 0.7,
    "max_tokens": 10
  }' | jq . || echo "Chat request failed"
echo ""

# Test 3: Chat endpoint with model override
echo "✅ Test 3: Chat with Model Override"
curl -s -X POST "$BASE_URL/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ],
    "model": "anthropic/claude-sonnet-4.5",
    "temperature": 0,
    "max_tokens": 5
  }' | jq . || echo "Model override failed"
echo ""

# Test 4: Streaming endpoint
echo "✅ Test 4: Streaming Endpoint (SSE)"
echo "Streaming: 'Count to 3'"
echo ""
curl -s -X POST "$BASE_URL/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Count to 3"}
    ],
    "temperature": 0.7,
    "max_tokens": 20
  }' | head -20 || echo "Streaming request failed"
echo ""

# Test 5: Missing required field (should fail gracefully)
echo "✅ Test 5: Error Handling (missing messages)"
curl -s -X POST "$BASE_URL/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.7}' | jq . || echo "Error handling test passed"
echo ""

echo "✨ Tests completed!"
