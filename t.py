# -*- coding:utf-8 -*-
import asyncio
import aiohttp
import urllib.parse
import re
import json


async def http_get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return resp.status, resp.read()


def check_phone_number(phone_number):
    phone_number = phone_number.strip()
    if phone_number.startswith("+86"):
        phone_number = phone_number[3:]
    if len(phone_number) != 11:
        return False
    p = re.compile("1[358]\d{9}|147\d{8}|177\d{8}|178\d{8}")
    return p.match(phone_number) is not None


async def send_sms(phone_number, template_id, template_argv_dict):
    """
    新的短信发送接口，需要在后台定义模板
    现有模板：
        template_id: 14688 template_argv_dict: {"code": xxxxxx}  # 验证码
        template_id: 14689 template_argv_dict: {"open_user_id": xxxxxx}  # 兑换上限提示
        template_id: 14690 template_argv_dict: {"password": xxxx}  # 重置密码
    :param phone_number:
    :param template_id:
    :param template_argv_dict:
    :return:
    """
    if not check_phone_number(phone_number):
        return False
    template_value = ""
    for i, j in template_argv_dict.items():
        template_value += "#%s#=%s&" % (i, j)
    template_value = urllib.parse.quote(template_value[0:-1].encode("utf8"))
    key = "563957e250a5def3ec24ab92986f37dd"
    url = "http://v.juhe.cn/sms/send?mobile=%s&tpl_id=%s&tpl_value=%s&key=%s" % (
        phone_number, template_id, template_value, key)
    status, response = await http_get(url)
    print(type(response), dir(response), str(response))
    if status != 200:
        return False
    response = str(response, 'utf8')
    response = json.loads(response)
    error_code, reason = response.get("error_code"), response.get("reason")
    if error_code != 0:
        return False
    return True


loop = asyncio.get_event_loop()
asyncio.ensure_future(send_sms('18138755118', '14688', {"code":"111111"}))
loop.run_forever()
