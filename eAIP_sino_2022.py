# 声明：
# 本人保证没有从来没有攻击过任何国内模拟飞行论坛！
# 本脚本已加入随机sleep机制，建议不要改动，以免增加服务器压力。

import json
import os
import re
import random
from shutil import rmtree
from time import sleep

import requests
from PyPDF2 import PdfFileMerger, PdfFileReader

BASE_URL = "https://aip.sinofsx.com"
JSON_URL = "/json/AerodromeShow.json"


def main():
    OUTPUT_DIR = get_output_directory()

    print("获取 aip.sinofsx.com 航图信息...")
    global session
    session = requests.Session()
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "dnt": "1",
        # "referer":"https://aip.sinofsx.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        # "sec-fetch-user": "?1",
        # "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36 Edg/102.0.1245.30",
    }
    session.headers.update(headers)
    res = json.loads(session.get(BASE_URL+JSON_URL).text)
    adc_full = transform_full_json(res)

    while True:
        icao = input("请输入机场ICAO码，或按回车键退出>").strip().upper()
        if not icao:
            break
        elif icao in adc_full.keys():
            count = len(adc_full[icao])
            print(f"找到{icao}，共{count}份pdf文件！")
            tempfolder = os.path.join(OUTPUT_DIR, icao)
            os.makedirs(tempfolder, exist_ok=True)
            merger = PdfFileMerger(strict=False)
            for label in adc_full[icao].keys():
                pdffile = download_pdf(
                    adc_full[icao][label], tempfolder, label)
                bmtitle = re.sub(f"{icao}-[0-9A-Z]*:", "", label)
                merger.append(pdffile, bookmark=bmtitle)
            merger.write(os.path.join(OUTPUT_DIR, icao+'.pdf'))
            if input("导出完成！是否删除缓存文件？（Y/N）>").strip().upper() == 'Y':
                rmtree(tempfolder)
            os.system('cls')
        else:
            print("无法找到此机场！")


def get_output_directory() -> str:
    d = os.path.abspath(input("请输入输出文件夹>"))
    if not os.path.isdir(d):
        os.mkdir(d)
    return os.path.abspath(d)


def transform_full_json(info) -> dict:
    """传入为dict对象"""
    ap_ori = info[0]['children'][2]['children']  # list
    ap_new = {}
    for a in ap_ori:
        icao = a['label'][0:4]
        charts = a['children']  # list
        ap_new[icao] = {}
        for c in charts:
            ap_new[icao][c['label']] = BASE_URL + c['pdfPath']
    return ap_new


def download_pdf(url, path, label) -> PdfFileReader:
    filename = label.split(':')[0]+'.pdf'
    fullname = os.path.join(path, filename)
    if not os.path.exists(fullname):
        print(f"正在下载...\t{label}")
        res = session.get(url)
        res.raise_for_status()
        sleep(1+3*random.random())
        open(fullname, 'wb').write(res.content)
    print(f"正在读取...\t{label}")
    return PdfFileReader(fullname, strict=False)


if __name__ == "__main__":
    main()
