from backend.main import app
import httpx
import asyncio

async def test_all():
    print("--- Starting Backend Tests ---")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # TEST 1: GET rules
        response = await client.get('/api/rules?tier=UNACCEPTABLE')
        print('[GET /api/rules] Status:', response.status_code)
        data = response.json()
        print('[GET /api/rules] Count:', data.get('count'))
        if data.get('count', 0) > 0:
            print('[GET /api/rules] Example:', data['rules'][0]['title'])

        # TEST 2: POST /api/assess
        payload = {
            'submitter_email': 'omar@example.com',
            'system_name': 'Automated CV Screener',
            'domain': 'HR',
            'purpose_description': 'Screens CVs automatically',
            'tech_stack': 'Python, PyTorch'
        }
        res2 = await client.post('/api/assess', json=payload)
        print('\n[POST /api/assess] Status:', res2.status_code)
        print('[POST /api/assess] Response:', res2.json())
        print("\n--- Backend Tests Completed Successfully ---")

if __name__ == '__main__':
    asyncio.run(test_all())
