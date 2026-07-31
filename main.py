import httpx
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from x7m import *          # pastikan file x7m.py ada di proyek

app = FastAPI()

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

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        r = await client.request(
            request.method,
            target,
            params=dict(request.query_params),
            headers=headers,
            content=await request.body()
        )

    data = r.json()
    data["server_url"] = "http://proxy-cgu.vercel.app/"

    HOP_BY_HOP = {
        'transfer-encoding', 'connection', 'keep-alive',
        'proxy-authenticate', 'proxy-authorization', 'te',
        'trailers', 'upgrade', 'proxy-connection'
    }
    response_headers = {
        k: v for k, v in r.headers.items()
        if k.lower() not in HOP_BY_HOP
        and k.lower() not in ("content-length", "content-encoding")
    }

    return JSONResponse(content=data, status_code=r.status_code, headers=response_headers)


@app.api_route("/MajorLogin", methods=["POST"])
async def MajorLoginProxy(request: Request):
    PyL = await request.body()
    x7m = json.loads(get_available_room(decrypt_api(PyL.hex())))
    acess_token, open_id = x7m["29"], x7m["22"]

    nikomLhnoud = f""" [b][c][279CF5]














███████╗░█████╗░███╗░░░███╗░█████╗░
╚════██║██╔══██╗████╗░████║██╔══██╗
░░███╔═╝███████║██╔████╔██║███████║
██╔══╝░░██╔══██║██║╚██╔╝██║██╔══██║
█╗      ██║░░██║██║░╚═╝░██║██║░░██║



─────────────────────────────────────

[cccccc]access Token => [ff0000]{acess_token} [cccccc]| open id => [00ff00]{open_id}

[00ff00]TeLeGram => @iix1f | InsTagram => @ii_mh1md




















                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    """

    return FastAPIResponse(content=nikomLhnoud, status_code=500, media_type="application/octet-stream")


# ========== MODIFIKASI UNTUK VERCEL ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=6677, log_level='info')
# app tetap diekspor, Vercel akan mendeteksinya sebagai ASGI
