from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import requests
import json

def decrypt_aes_ecb(encrypted_data: str) -> str:
    
    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    
    cipher = AES.new(key, AES.MODE_ECB)
    
    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)

    return decrypted_data.decode('utf-8')

def get_record(servicehall, idserial):
    # 获取数据
    url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime=2025-01-01&endtime=2025-12-31&idserial={idserial}&tradetype=-1"
    cookie = {"servicehall": servicehall}
    response = requests.post(url, cookies=cookie)
    
    encrypted_string = json.loads(response.text)["data"]
    decrypted_string = decrypt_aes_ecb(encrypted_string)
    data = json.loads(decrypted_string)
    return data