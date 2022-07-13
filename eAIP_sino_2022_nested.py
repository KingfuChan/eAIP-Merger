# 声明：
# 本人保证没有从来没有攻击过任何国内模拟飞行论坛！
# 本脚本已加入随机sleep机制，建议不要改动，以免增加服务器压力。

import json
import os
import random
import re
from shutil import rmtree
from time import sleep

import requests
from PyPDF2 import PdfMerger, PdfReader

BASE_URL = "https://aip.sinofsx.com"
JSON_URL = "/json/AerodromeShow.json"
GROUP_DICT = {
    '0': "<机场细则>",
    '1':  "<机场图>",
    '2':  "<停机位置图>",
    '4':  "<机场障碍物A型图(运行限制)>",
    '5':  "<精密进近地形图>",
    '6':  "<最低监视引导高度图>",
    '7':  "<标准仪表离场图>",
    '9':  "<标准仪表进场图>",
    '10': "<仪表进近图>",
    '11': "<目视进近图>",
    '20': "<仪表进近图(RNAV)>",
}


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
            print(f"找到{icao}，共{len(adc_full[icao])}份pdf文件！")
            tempfolder = os.path.join(OUTPUT_DIR, icao)
            os.makedirs(tempfolder, exist_ok=True)
            merger = PdfMerger()

            prevgrp = ""
            pagenum = 0
            bmrkinfo = {}
            for label, url in adc_full[icao].items():
                currgrp = get_group_name(label)
                pdffile = download_pdf(url, tempfolder, label)
                merger.append(pdffile)
                if prevgrp != currgrp:
                    bmrkinfo[currgrp] = {}
                    prevgrp = currgrp
                lbl = label.split('-', 1)[-1]
                bmrkinfo[currgrp][lbl] = pagenum
                pagenum += len(pdffile.pages)

            for g, pdfgroup in bmrkinfo.items():
                pgrp = list(pdfgroup.values())[0]
                currmrk = merger.add_bookmark(g, pgrp)
                if len(pdfgroup) > 1:
                    for l, p in pdfgroup.items():
                        merger.add_bookmark(l, p, currmrk)

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


def download_pdf(url, path, label) -> PdfReader:
    filename = label.split(':')[0]+'.pdf'
    fullname = os.path.join(path, filename)
    if not os.path.exists(fullname):
        print(f"正在下载...\t{label}")
        res = session.get(url)
        res.raise_for_status()
        sleep(1+3*random.random())
        open(fullname, 'wb').write(res.content)
    print(f"正在读取...\t{label}")
    return PdfReader(fullname)


def get_group_name(label) -> str:
    index = label.split("-")[1].split(":")[0]
    matches = re.findall(r"([0-9]+)[A-Z]?", index)
    if len(matches):
        return GROUP_DICT[matches[0]]
    else:
        return GROUP_DICT["0"]


if __name__ == "__main__":
    main()
