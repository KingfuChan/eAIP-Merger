# 声明：
# 本人保证没有从来没有攻击过任何国内模拟飞行论坛！
# 本脚本若不作改动直接使用不会对sinofsx服务器造成影响。

import os
import re
from shutil import rmtree
from time import sleep
import requests

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger, PdfFileReader

SINO_URL = "https://wiki.sinofsx.com/index.php?title=AD_2._%E6%9C%BA%E5%9C%BA_AERODROMES"
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


class Chart(object):
    def __init__(self, icao, html_soup):
        """航图类，传入参数为该航图对应行的BeautifulSoup对象"""
        self.icao = icao
        info, cycle, link = html_soup.find_all('td')
        self.code, self.name = info.get_text().split(':')
        self.url = link.find('a').get('href')
        self.cycle = cycle.get_text()[2:4]+cycle.get_text()[-2:]
        self.group = self.get_group()
        self.group_name = GROUP_DICT[self.group]

        if self.group == '0':  # 提前对AD输出目录变更
            self.path = os.path.join(
                OUTPUT_DIR, self.icao+'_AD_'+self.cycle+".pdf")
        else:
            self.path = os.path.join(
                OUTPUT_DIR, self.icao+'_'+self.cycle, self.code+'.pdf')

    def __str__(self):
        """For debugging purpose"""
        return self.code

    def get_group(self):
        key = re.findall(r"[A-Z]{4}-([0-9A-Z]+)", self.code)[0]
        group = '0' if key == 'AD' else re.findall(r"[0-9]+", key)[0]
        return group

    def download(self):
        print(f"正在下载...\t{self.code}:{self.name}")
        #pdf = urlopen(self.url).read()
        res = session.get(self.url)
        res.raise_for_status()
        if not os.path.isdir(os.path.dirname(self.path)):
            os.mkdir(os.path.dirname(self.path))
        with open(self.path, 'wb') as p:
            p.write(res.content)

    def readPDF(self):
        if os.path.exists(self.path):
            print(f"正在读取...\t{self.code}")
            pdfobject = PdfFileReader(self.path, strict=False)
            return pdfobject
        else:
            self.download()
            return self.readPDF()


def get_output_directory():
    d = os.path.abspath(input("请输入输出文件夹>"))
    if not os.path.isdir(d):
        os.mkdir(d)
    global OUTPUT_DIR
    OUTPUT_DIR = os.path.abspath(d)


def parse_airport_from_table(html):
    """解析单个机场的所有航图信息，传入参数为单个机场对应BeautifulSoup对象"""
    caption = html.find('caption').get_text()
    icao = re.findall(r"(Z[A-Z]{3})-*", caption)[0]
    chart_list = [Chart(icao, r) for r in html.find_all(
        'tr') if len(r.find_all('td')) == 3]
    return {'icao': icao, 'charts': chart_list, 'count': len(chart_list)}


def extract_all_airport_charts(html):
    """解析网页，读取所有机场的航图信息"""
    soup = BeautifulSoup(html, 'html.parser')
    apt_tables = soup.find_all(
        'table', attrs={'class': "wikitable mw-collapsible"})
    airports = [parse_airport_from_table(aptt) for aptt in apt_tables]
    return airports


def regroup_charts(chart_list):
    """打包各组航图，传入参数为Charts对象的列表"""
    chart_list.reverse()
    ad = chart_list.pop()  # 处理AD
    chart_list.reverse()
    group = chart_list[0].group
    temp = [chart_list[0]]
    final = []
    for c in chart_list[1:]:
        if c.group != group:
            group = c.group
            final.append(temp)
            temp = []
        temp.append(c)
    final.append(temp)
    return (ad, final)


def merge_pdf(chart_list):
    """合并PDF，传入参数为Chart对象的列表，返回缓存目录"""
    foldername = chart_list[0].icao+'_'+chart_list[0].cycle
    tempfolder = os.path.join(OUTPUT_DIR, foldername)
    filename = os.path.join(OUTPUT_DIR, foldername+'.pdf')
    aerodrome, chart_list = regroup_charts(chart_list)
    # 单独处理AD文件
    aerodrome.download()
    # 合并文件
    merger = PdfFileMerger(strict=False)
    pagenum = 0
    for cl in chart_list:
        if len(cl) == 1:
            try:
                reader = cl[0].readPDF()
            except Exception as e:
                print("下载时发生错误，跳过！"+repr(e))
                continue
            else:
                merger.append(reader, bookmark=cl[0].group_name+cl[0].name)
                pagenum += reader.getNumPages()
        elif len(cl) > 1:
            group = cl[0].group_name
            for i in range(len(cl)):
                try:
                    reader = cl[i].readPDF()
                except Exception as e:
                    print("下载时发生错误，跳过！"+repr(e))
                    continue
                else:
                    merger.append(reader)
                    if i == 0:
                        parent = merger.addBookmark(group, pagenum)
                    merger.addBookmark(cl[i].name, pagenum, parent)
                    pagenum += reader.getNumPages()

    print("合并完成，正在保存文件...")
    merger.write(filename)
    print(f"已保存到{filename}！")
    print(f"机场细则（AD）文件已保存到{aerodrome.path}！")
    return tempfolder


def main():
    get_output_directory()

    print("获取wiki.sinofsx.com页面...")
    global session
    session = requests.Session()
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "dnt": "1",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111",
    }
    session.headers.update(headers)
    res = session.get(SINO_URL).content
    extracted = extract_all_airport_charts(res)
    icao_list = [e['icao'] for e in extracted]

    while 1:
        print("机场及航图信息已获取！")
        icao = input("请输入机场ICAO码，或按回车键退出>").strip().upper()
        if not icao:
            break
        elif icao in icao_list:
            target = [et for et in extracted if et['icao'] == icao][0]
            chart_list = target['charts']
            count = target['count']
            print(f"找到{icao}，共{count}份pdf文件！")
            tempfolder = merge_pdf(chart_list)
            if input("是否删除缓存文件？（Y/N）>").strip().upper() == 'Y':
                rmtree(tempfolder)
            os.system('cls')
        else:
            print("无法找到此机场！")


if __name__ == "__main__":
    main()
