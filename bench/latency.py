#!/usr/bin/env python3
"""
Benchmark script for vLLM chat API.

Measures:
- Time to First Byte (TTFB)
- End-to-end latency
- Tokens per second
- GPU VRAM usage

Usage:
    python bench/latency.py [--runs N] [--warmup N]
"""

import asyncio
import time
import json
import os
import subprocess
import statistics
from typing import List, Dict, Optional
import argparse

import httpx


# Configuration
API_URL = os.getenv("TEST_API_URL", "http://localhost:8787")
API_KEY = os.getenv("PROXY_API_KEY", "change-me")
MODEL = os.getenv("DEFAULT_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")

# Test prompt (approximately 25 tokens)
TEST_PROMPT = "Write a short paragraph about the importance of artificial intelligence in modern technology."


def get_gpu_memory() -> Optional[int]:
    """Get current GPU memory usage in MB using rocm-smi (AMD GPU)."""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram", "--csv"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse CSV output to get used VRAM
            lines = result.stdout.strip().split("\n")
            # Look for used memory in output
            for line in lines[1:]:  # Skip header
                if "," in line:
                    # Extract used memory value (typically in MB)
                    parts = line.split(",")
                    if len(parts) > 1:
                        try:
                            # rocm-smi shows memory in MB
                            return int(float(parts[1].strip()))
                        except (ValueError, IndexError):
                            pass
    except FileNotFoundError:
        print(f"Warning: rocm-smi not found. Install ROCm tools to enable GPU memory tracking.")
    except Exception as e:
        print(f"Warning: Could not get GPU memory: {e}")
    return None


async def run_streaming_request() -> Dict[str, float]:
    """
    Run a single streaming chat request and measure latencies.
    
    Returns:
        Dictionary with timing metrics
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    request_data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": TEST_PROMPT}
        ],
        "max_tokens": 256,
        "temperature": 0.7,
        "stream": True
    }
    
    start_time = time.perf_counter()
    ttfb = None
    tokens_received = 0
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{API_URL}/api/chat",
            headers=headers,
            json=request_data
        ) as response:
            
            if response.status_code != 200:
                raise Exception(f"Request failed: {response.status_code} - {await response.aread()}")
            
            async for line in response.aiter_lines():
                if not line.strip() or not line.startswith("data: "):
                    continue
                
                # Record TTFB on first data chunk
                if ttfb is None:
                    ttfb = time.perf_counter() - start_time
                
                data_str = line[6:]  # Remove "data: " prefix
                
                if data_str.strip() == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(data_str)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        choice = chunk["choices"][0]
                        if "delta" in choice and "content" in choice["delta"]:
                            # Rough token count (words + punctuation)
                            content = choice["delta"]["content"]
                            tokens_received += len(content.split()) + content.count(",") + content.count(".")
                except json.JSONDecodeError:
                    pass
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    return {
        "ttfb": ttfb or 0.0,
        "total_time": total_time,
        "tokens": tokens_received,
        "tokens_per_second": tokens_received / total_time if total_time > 0 else 0
    }


async def run_benchmark(num_runs: int = 10, warmup_runs: int = 2):
    """
    Run benchmark with warmup and multiple iterations.
    
    Args:
        num_runs: Number of benchmark runs
        warmup_runs: Number of warmup runs (not counted)
    """
    print("=" * 70)
    print("vLLM Chat API Benchmark")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print(f"Model: {MODEL}")
    print(f"Warmup runs: {warmup_runs}")
    print(f"Benchmark runs: {num_runs}")
    print("=" * 70)
    
    # Get initial GPU memory
    initial_vram = get_gpu_memory()
    if initial_vram:
        print(f"Initial GPU VRAM: {initial_vram} MB")
    
    # Warmup
    print(f"\nWarming up ({warmup_runs} runs)...")
    for i in range(warmup_runs):
        try:
            await run_streaming_request()
            print(f"  Warmup {i+1}/{warmup_runs} complete")
        except Exception as e:
            print(f"  Warmup {i+1} failed: {e}")
            return
    
    # Benchmark runs
    print(f"\nRunning benchmark ({num_runs} runs)...")
    results: List[Dict[str, float]] = []
    
    for i in range(num_runs):
        try:
            result = await run_streaming_request()
            results.append(result)
            print(f"  Run {i+1}/{num_runs}: TTFB={result['ttfb']:.3f}s, "
                  f"Total={result['total_time']:.3f}s, "
                  f"Tokens/s={result['tokens_per_second']:.1f}")
        except Exception as e:
            print(f"  Run {i+1} failed: {e}")
    
    if not results:
        print("\nNo successful runs. Exiting.")
        return
    
    # Calculate statistics
    ttfb_values = [r["ttfb"] for r in results]
    total_time_values = [r["total_time"] for r in results]
    tokens_per_sec_values = [r["tokens_per_second"] for r in results]
    
    # Get final GPU memory
    final_vram = get_gpu_memory()
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print("\nTime to First Byte (TTFB):")
    print(f"  Mean:   {statistics.mean(ttfb_values):.3f}s")
    print(f"  Median: {statistics.median(ttfb_values):.3f}s")
    print(f"  Min:    {min(ttfb_values):.3f}s")
    print(f"  Max:    {max(ttfb_values):.3f}s")
    if len(ttfb_values) > 1:
        print(f"  StdDev: {statistics.stdev(ttfb_values):.3f}s")
    
    print("\nEnd-to-End Latency:")
    print(f"  Mean:   {statistics.mean(total_time_values):.3f}s")
    print(f"  Median: {statistics.median(total_time_values):.3f}s")
    print(f"  P95:    {statistics.quantiles(total_time_values, n=20)[18]:.3f}s")
    print(f"  Min:    {min(total_time_values):.3f}s")
    print(f"  Max:    {max(total_time_values):.3f}s")
    
    print("\nThroughput:")
    print(f"  Mean:   {statistics.mean(tokens_per_sec_values):.1f} tokens/s")
    print(f"  Median: {statistics.median(tokens_per_sec_values):.1f} tokens/s")
    print(f"  Min:    {min(tokens_per_sec_values):.1f} tokens/s")
    print(f"  Max:    {max(tokens_per_sec_values):.1f} tokens/s")
    
    if initial_vram and final_vram:
        print("\nGPU Memory:")
        print(f"  Initial: {initial_vram} MB")
        print(f"  Final:   {final_vram} MB")
        print(f"  Delta:   {final_vram - initial_vram:+d} MB")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Benchmark vLLM chat API")
    parser.add_argument("--runs", type=int, default=10, help="Number of benchmark runs")
    parser.add_argument("--warmup", type=int, default=2, help="Number of warmup runs")
    args = parser.parse_args()
    
    asyncio.run(run_benchmark(num_runs=args.runs, warmup_runs=args.warmup))


if __name__ == "__main__":
    main()
