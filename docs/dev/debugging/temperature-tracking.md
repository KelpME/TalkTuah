# Temperature Parameter Flow & Verification

## The Pipeline

```
TUI Settings (0.13)
    ↓ (saves to)
~/.config/tuivllm/settings.json
    ↓ (read by)
llm_client.py:74-85
    ↓ (HTTP POST)
API Proxy (/api/chat)
    ↓ (forwards to)
vLLM Server (/v1/chat/completions)
    ↓ (applies)
Model Sampling
```

## Added Logging

### 1. Frontend (llm_client.py)
```python
logging.info(f"[LLM Request] Temperature: {temperature}, Model: {current_model}")
```

### 2. API Proxy (main.py)
```python
logger.info(f"[API Proxy] Temperature: {request_data.get('temperature')}, Model: {request_data.get('model')}, Stream: {is_streaming}")
```

### 3. TUI Display (TuivLLM.py)
```python
self.log(f"[bold cyan]Using temperature: {temp}[/bold cyan]")
```

## Verification Steps

### 1. Check Settings Are Saved
```bash
python3 test_temperature.py
```
**Expected:** Shows temperature: 0.13

### 2. Test API Directly
```bash
./test_api_temperature.sh 0.1
```
**Expected:** API responds, logs show temperature parameter

### 3. Watch Logs While Using TUI
```bash
# Terminal 1: Start services
make up

# Terminal 2: Watch API logs
docker logs -f vllm-proxy-api

# Terminal 3: Watch vLLM logs  
docker logs -f vllm-server

# Terminal 4: Run TUI
make frontend
```

Send a message and verify all logs show correct temperature.

## Temperature Behavior Guide

| Temperature | Behavior | Use Case |
|------------|----------|----------|
| 0.0 - 0.3  | Very deterministic, safe, boring | Code generation, factual Q&A |
| 0.4 - 0.7  | Balanced (default) | General chat |
| 0.8 - 1.2  | Creative | Storytelling, brainstorming |
| 1.3 - 2.0  | Very random, sometimes incoherent | Experimental, artistic |

**Important:** Low temperature ≠ garbage output. Low temperature = consistent output.

## Why Temperature Might Not Seem to Work

### 1. Model Constraints
Some models have built-in sampling constraints that limit temperature effect.

### 2. Context Length
Short prompts may not show temperature differences as clearly.

### 3. Model Training
Instruction-tuned models are trained to be consistent, reducing temperature effect.

### 4. Expectations
- ❌ "Temperature 0.1 should break the model"
- ✅ "Temperature 0.1 should make responses very consistent"

## Test It Properly

### Test 1: Consistency (Low Temperature)
```bash
# Set temperature to 0.1 in TUI
# Ask: "What is the capital of France?" 
# Ask it 3 times
# Expected: Nearly identical responses
```

### Test 2: Creativity (High Temperature)
```bash
# Set temperature to 1.8 in TUI
# Ask: "Write a creative story about a robot"
# Ask it 3 times
# Expected: Very different stories each time
```

### Test 3: Side-by-Side
```bash
# Temperature 0.1: "Explain quantum computing"
# Temperature 1.5: "Explain quantum computing"
# Compare responses - 1.5 should be more varied/creative
```

## Troubleshooting

### Problem: Logs show correct temperature but behavior unchanged
**Possible causes:**
1. vLLM not applying parameter (check vLLM logs)
2. Model doesn't support temperature well
3. Testing methodology (need more iterations to see effect)

### Problem: API logs show wrong temperature
**Check:**
1. Settings file has correct value: `cat ~/.config/tuivllm/settings.json`
2. No caching issues: restart TUI
3. API default isn't overriding: check `apps/api/models.py` line 15

### Problem: Settings not saving
**Check:**
1. Settings modal `on_unmount()` is being called
2. File permissions on `~/.config/tuivllm/`
3. No errors in TUI logs

## Files Modified

- `frontend/llm_client.py` - Added temperature logging
- `apps/api/main.py` - Added proxy logging
- `frontend/TuivLLM.py` - Added temperature display
- `frontend/widgets/settings/settings_modal.py` - Added `on_unmount()` to save settings
- Created: `test_temperature.py` - Settings verification script
- Created: `test_api_temperature.sh` - Direct API test script
- Created: `DEBUG_TEMPERATURE.md` - Full debugging guide

## Summary

Your temperature **IS being saved** (verified: 0.13).  
Now you need to verify it's being **sent** and **applied**.

Run these commands in order:
1. `python3 test_temperature.py` - Verify saved
2. `docker logs -f vllm-proxy-api` - Watch in another terminal
3. `make frontend` - Start TUI
4. Send message - Check logs show temperature
5. Ask same question 3x - Verify consistency at low temp
