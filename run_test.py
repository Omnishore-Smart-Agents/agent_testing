import asyncio
from agent.core_agent import CoreAgent

async def main():
    agent = CoreAgent()
    url = "https://auth-page-alpha.vercel.app?_vercel_share=MEVC75iBMFkKTIiH9y0VjsDJpCnghee2"
    result = await agent.run(url)
    print(f"Total: {result.get('summary', {}).get('total')}")
    print(f"Passed: {result.get('summary', {}).get('passed')}")
    print(f"Failed: {result.get('summary', {}).get('failed')}")

asyncio.run(main())