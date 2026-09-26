import httpx, json, asyncio, sys

async def m():
    async with httpx.AsyncClient(timeout=30) as c:
        try:
            r = await c.post('http://127.0.0.1:17493/generate', json={'profile_id': 'f9b3a288-2e86-4156-8dfd-42b70ece7283', 'text': 'I like you baby', 'engine': 'qwen', 'model_size': '1.7B', 'language': 'en'})
            print("POST /generate status:", r.status_code)
            if r.status_code != 200:
                print("Error:", r.text)
                return
            jid = r.json()['id']
            for _ in range(60):
                await asyncio.sleep(2)
                st = await c.get(f'http://127.0.0.1:17493/history/{jid}')
                data = st.json()
                print('Status:', data['status'])
                if data['status'] in ['completed', 'failed']:
                    if data['status'] == 'failed':
                        print('Failed error:', data.get('error'))
                    break
            if data.get('status') == 'completed':
                audio = await c.get(f'http://127.0.0.1:17493/audio/{jid}')
                with open(r'c:\Users\Allen\OneDrive\Desktop\Voicebox\I_like_you_baby.wav', 'wb') as f:
                    f.write(audio.content)
                print('Downloaded successfully!')
        except Exception as e:
            print('Python Error:', e)

asyncio.run(m())
