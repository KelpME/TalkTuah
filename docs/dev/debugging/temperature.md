# Temperature Debugging Guide

## Current Status

Your temperature setting **IS being saved** correctly:
- Current value: **0.13**
- Settings file: `~/.config/tuivllm/settings.json`

## How to Verify Temperature is Working

### Step 1: Check Logs

**Frontend Logs (TUI):**
```bash
# In the TUI, send a message and check the logs
# You should see: "Using temperature: 0.13"
```

**API Proxy Logs:**
```bash
# In another terminal:
make logs

# Or specifically watch the API container:
docker logs -f vllm-proxy-api

# Look for lines like:
# [API Proxy] Temperature: 0.13, Model: Qwen/Qwen2.5-1.5B-Instruct, Stream: False
```

**vLLM Server Logs:**
```bash
docker logs -f vllm-server

# Look for the actual sampling parameters being used
```

### Step 2: Test Temperature Effect

**Temperature = 0.1 (Very Deterministic)**
- Should give nearly identical responses to repeated identical questions
- Very focused, predictable, "safe" answers
- **NOT garbage** - just very consistent

**Temperature = 1.0 (Balanced)**
- Normal creativity/randomness balance
- Different responses to same question

**Temperature = 1.8-2.0 (Very Creative)**
- Highly random, creative, sometimes incoherent
- This is where you'd expect "garbage" or weird outputs

## Common Misconceptions

❌ **WRONG:** "Temperature 0.1 should output garbage"  
✅ **CORRECT:** Temperature 0.1 outputs very deterministic, safe, boring text

❌ **WRONG:** "Temperature should make model dumber/smarter"  
✅ **CORRECT:** Temperature only affects randomness/creativity, not intelligence

## Test Commands

### 1. Verify Settings Load
```bash
python3 test_temperature.py
```

### 2. Test Request (with logging)
Start the TUI and send a message. You should see in logs:
```
[LLM Request] Temperature: 0.13, Model: Qwen/Qwen2.5-1.5B-Instruct
[API Proxy] Temperature: 0.13, Model: Qwen/Qwen2.5-1.5B-Instruct, Stream: False
```

### 3. Check vLLM Actually Uses It
```bash
# Enable debug logging in vLLM
# Add to docker-compose.yml under vllm service environment:
# - VLLM_LOGGING_LEVEL=DEBUG

# Then restart:
make restart

# Check logs for sampling params
docker logs -f vllm-server | grep -i temperature
```

## Potential Issues

### Issue 1: Settings Not Reloading
**Symptom:** Old temperature still being used  
**Solution:** The `get_settings()` is called fresh each request, so this shouldn't happen

### Issue 2: API Not Forwarding Temperature
**Symptom:** API logs show None or wrong temperature  
**Solution:** Check API default in `apps/api/models.py` (currently defaults to 1.0 if not provided)

### Issue 3: vLLM Ignoring Temperature
**Symptom:** API logs show correct temp, but responses don't change  
**Solution:** 
- Check vLLM version supports temperature parameter
- Check if model has sampling restrictions
- Verify vLLM logs show correct sampling params

## Quick Test

**Ask the same question 3 times:**

With temperature = 0.1:
- Responses should be nearly identical

With temperature = 1.5:
- Responses should vary significantly

## Debug Output Locations

1. **TUI Console Logs:** Built-in Textual logging
2. **API Logs:** `docker logs -f vllm-proxy-api`
3. **vLLM Logs:** `docker logs -f vllm-server`
4. **Settings File:** `~/.config/tuivllm/settings.json`

## Next Steps

1. Start TUI: `make frontend`
2. Open another terminal: `docker logs -f vllm-proxy-api`
3. Send a message
4. Verify logs show: `Temperature: 0.13`
5. Ask same question 3 times - responses should be very similar at 0.13

If responses are still varying wildly at 0.13, then vLLM is not applying the temperature parameter correctly.
