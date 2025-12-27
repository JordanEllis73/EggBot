#!/usr/bin/env python3
"""
Test script to reproduce the race condition by making concurrent API calls
"""
import asyncio
import aiohttp
import time

async def set_setpoint(session, value, client_id):
    """Set setpoint value"""
    try:
        async with session.post(
            'http://192.168.1.194:8000/setpoint',
            json={'setpoint_c': value}
        ) as response:
            result = await response.json()
            print(f"[CLIENT {client_id}] Set setpoint to {value}: {result}")
            return result
    except Exception as e:
        print(f"[CLIENT {client_id}] Error setting setpoint {value}: {e}")

async def get_status(session, client_id):
    """Get current status"""
    try:
        async with session.get('http://192.168.1.194:8000/status') as response:
            result = await response.json()
            print(f"[CLIENT {client_id}] Status: setpoint={result.get('setpoint_c')}, meat={result.get('meat_setpoint_c')}")
            return result
    except Exception as e:
        print(f"[CLIENT {client_id}] Error getting status: {e}")

async def race_condition_test():
    """Test concurrent setpoint changes"""
    print("=== Starting Race Condition Test ===")
    
    async with aiohttp.ClientSession() as session:
        # First, get initial status
        print("\n--- Initial Status ---")
        await get_status(session, "INIT")
        
        # Create concurrent tasks that set different values
        print("\n--- Concurrent Setpoint Changes ---")
        tasks = []
        
        # Client 1: Set to 130°C repeatedly
        for i in range(5):
            tasks.append(set_setpoint(session, 130, f"1-{i}"))
            
        # Client 2: Set to 110°C repeatedly  
        for i in range(5):
            tasks.append(set_setpoint(session, 110, f"2-{i}"))
            
        # Execute all concurrently
        await asyncio.gather(*tasks)
        
        # Monitor status for 10 seconds
        print("\n--- Monitoring Status Changes ---")
        for i in range(10):
            await asyncio.sleep(1)
            await get_status(session, f"MONITOR-{i}")
            
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(race_condition_test())