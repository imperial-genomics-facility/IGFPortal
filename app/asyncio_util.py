import asyncio
from concurrent.futures import ThreadPoolExecutor

def run_async(coroutine):
    """Helper to run async code from sync context"""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coroutine)
                return future.result()
        else:
            # If loop exists but not running, use it
            return loop.run_until_complete(coroutine)
    except RuntimeError:
        # No event loop exists, create new one
        return asyncio.run(coroutine)
