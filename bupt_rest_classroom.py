import json
import base64
from aiohttp import ClientSession
from datetime import datetime
from urllib.parse import urlencode
from functools import reduce
from typing import Any
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


TODAY_CLASSROOMS_API = "http://jwglweixin.bupt.edu.cn/bjyddx/todayClassrooms?campusId=%s"
LOGIN_URL = "http://jwglweixin.bupt.edu.cn/bjyddx/login?"

async def get_content(userNo: str, pwd: str, shahe: bool = True, **kwargs: Any) -> list[dict[str, str]]:
    # cache
    if (f := Path(__file__).parent / 'data.json').exists():
        with open(f, 'r') as fp:
            try:
                resp = json.load(fp)
                f_date = datetime.strptime(resp['date'], '%y-%m-%d').date()
                if f_date == datetime.today().date():
                    return resp['data']
            except json.decoder.JSONDecodeError:
                pass
            except ValueError:
                pass

    def encrypt():
        key_bytes = "qzkj1kjghd=876&*".encode('utf-8')

        data = '"' + pwd + '"'
        data = data.encode('utf-8')

        cipher = AES.new(key_bytes, AES.MODE_ECB)

        encrypted = base64.b64encode(cipher.encrypt(pad(data, AES.block_size)))
        return base64.b64encode(encrypted).decode('utf-8')
        
    async with ClientSession() as session:
        query_dict = {
            "userNo": userNo,
            "pwd": encrypt(),
            "encode": 1,
            "captchaData": "",
            "codeVal": ""
        }
        async with session.post(LOGIN_URL + urlencode(query_dict, safe='ascii'), **kwargs) as r:
            if r.status != 200:
                raise ConnectionError(f"[{r.status} 登录] {r.content}")
            if (resp := await r.json())['code'] != '1' and resp['Msg'] != '登录成功！':
                raise ConnectionError(f"[登录] {resp['Msg']}")
        token = resp['data']['token']
        async with session.post(TODAY_CLASSROOMS_API.format('04' if shahe else '01'), headers={"token": token}, **kwargs) as r:
            if r.status != 200:
                raise ConnectionError(f"[{r.status} 获取空闲教室] {r.content}")
            if (resp := await r.json())['code'] != '1' and resp['Msg'] != 'success':
                raise ConnectionError(f"[获取空闲教室] {resp['Msg']}")
            with open(f, 'w') as fp:
                json.dump({
                    'date': datetime.strftime(datetime.today().date(), '%y-%m-%d'),
                    'data': resp['data']
                    }, fp, indent=2, ensure_ascii=False)
            return resp['data']


async def get_all_day_free_classrooms(userNo: str, pwd: str, **kwargs: Any) -> list[str]:
    resp = await get_content(userNo, pwd, **kwargs)
    current = datetime.now().time()
    resp = filter(lambda x: datetime.strptime(x['NODETIME'].split('-')[-1], "%H:%M").time()>current, resp)
    rooms = [set(map(lambda x: x[:x.index('(')], row)) 
             for row in map(lambda x: x['CLASSROOMS'].split(','), resp)]
    return list(reduce(lambda x, y: x & y, rooms))


async def get_now_free_classrooms(userNo: str, pwd: str, **kwargs: Any) -> list[str]:
    resp = await get_content(userNo, pwd, **kwargs)
    current = datetime.now().time()
    for node in resp:
        time = datetime.strptime(node['NODETIME'].split('-')[-1], "%H:%M").time()
        if time > current:
            return list(map(lambda x: x[:x.index('(')], node['CLASSROOMS'].split(',')))
    return ["太晚啦，别去啦宝贝"]

def beautifier(data: list[str]) -> str:
    N_building = sorted(list(filter(lambda x: x.startswith('N'), data)))
    S_building = sorted(list(filter(lambda x: x.startswith('S') and x[:3] != 'S1-', data)))
    S1_building = sorted(list(filter(lambda x: x.startswith('S1-'), data)))

    return "\n\n".join(("  ".join(N_building), "  ".join(S_building), "  ".join(S1_building)))
