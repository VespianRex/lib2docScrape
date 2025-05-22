#!/usr/bin/env python3
from src.utils.search import DuckDuckGoSearch
import asyncio

async def test():
    s = DuckDuckGoSearch(max_results=2)
    r = await s.search('test')
    print(r)

if __name__ == "__main__":
    asyncio.run(test())
