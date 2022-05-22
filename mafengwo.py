import json
import re
import hashlib
import requests
import execjs

session = requests.session()

url = "https://www.mafengwo.cn/i/9754893.html"


def start():
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
        "Host": "www.mafengwo.cn",
        "Referer": url
    }

    # 获取第一次js代码和cookie_uid
    resp = session.get(url=url)
    tmp = resp.headers['Set-Cookie'].split("=")
    _cookie_jsl = {tmp[0]: tmp[1].split(";")[0]}

    # 执行js加密获取cookie_clearance
    jstext = re.findall(r'document.cookie=(.*?);location', resp.text)
    cookie = execjs.eval(jstext[0]).split(";")[0]
    tmp = cookie.split("=")
    _cookie_jsl.setdefault(tmp[0], tmp[1])

    # 第二次请求获取js代码
    resp = session.get(url=url, cookies=_cookie_jsl)
    go = json.loads(re.findall(r'};go\((.*?)\)</script>', resp.text)[0])

    # 将chars值 循环替换cookies与ct进行签名计算比对 相同则返回cookies
    for i in range(len(go['chars'])):
        for j in range(len(go['chars'])):
            values = go['bts'][0] + go['chars'][i:i + 1] + go['chars'][j:j + 1] + go['bts'][1]

            if go['ha'] == 'md5':
                ha = hashlib.md5(values.encode()).hexdigest()
            elif go['ha'] == 'sha1':
                ha = hashlib.sha1(values.encode()).hexdigest()
            elif go['ha'] == 'sha256':
                ha = hashlib.sha256(values.encode()).hexdigest()
            if ha == go['ct']:
                _cookie_jsl.update({"__jsl_clearance_s": values})

    session.headers.update({"cookie": "__jsluid_s=" + _cookie_jsl['__jsluid_s'] + "; __jsl_clearance_s=" + _cookie_jsl[
        '__jsl_clearance_s']})
    resp = session.get(url=url).text

    hasmore = re.findall('has_more\":(.*?),', resp)[0]
    seqlist = re.findall(r'data-seq="(.*?)"', resp)
    videolist = re.findall(r'data-url="(.*?)"', resp)
    print(videolist)
    print(seqlist)

    if hasmore == "true":
        while True:
            id = re.findall(r'i/(.*).html', url)[-1]
            iid = re.findall(r'([0-9]{9})', resp)[0]
            seq = seqlist[-1]

            hasmore, seqlist, videolist = getmore(id, iid, seq)
            print(videolist)
            print(seqlist)
            if hasmore == "false":
                break


def getmore(id, iid, seq):
    url = "https://www.mafengwo.cn/note/ajax/detail/getNoteDetailContentChunk?id=" + id + "&iid=" + iid + "&seq=" + seq + "&back=0"

    resp = session.get(url=url).text.replace("\\", "")

    # data-seq=\"340424976\"
    seqlist = re.findall(r'data-seq=\"(.*?)"', resp)
    # data-url=\"http:\\www.mafengwo.cn\rest\app\note\video\1130705?jsondata=%7B%22data_style%22%3A%22jump%22%7D&type=.m3u8\"
    videolist = re.findall(r'data-url=\"(.*?)"', resp)

    hasmore = re.findall('has_more\":(.*?),', resp)[0]

    return hasmore, seqlist, videolist


if __name__ == '__main__':
    start()
