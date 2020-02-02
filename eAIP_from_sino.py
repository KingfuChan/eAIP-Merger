import os
import re
from shutil import rmtree
from time import sleep
from urllib.error import HTTPError
from urllib.request import urlopen

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
        self.cycle = cycle.get_text()
        self.group = self.get_group()
        self.group_name = GROUP_DICT[self.group]

        if self.group == '0':  # 提前对AD输出目录变更
            self.path = os.path.join(
                OUTPUT_DIR, self.icao+'_'+self.cycle+"_AD.pdf")
        else:
            self.path = os.path.join(
                OUTPUT_DIR, self.icao+'_'+self.cycle, self.code+'.pdf')

    def __str__(self):
        """#For debugging purpose"""
        return self.code

    def get_group(self):
        key = re.findall(r"[A-Z]{4}-([0-9A-Z]+)", self.code)[0]
        group = '0' if key == 'AD' else re.findall(r"[0-9]+", key)[0]
        return group

    def download(self):
        print(f"正在下载...\t{self.code}:{self.name}")
        pdf = urlopen(self.url).read()
        if not os.path.isdir(os.path.dirname(self.path)):
            os.mkdir(os.path.dirname(self.path))
        with open(self.path, 'wb') as p:
            p.write(pdf)

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
            except HTTPError as he:
                print("下载时发生错误，跳过！"+repr(he))
                continue
            else:
                merger.append(reader, bookmark=cl[0].group_name+cl[0].name)
                pagenum += reader.getNumPages()
        elif len(cl) > 1:
            group = cl[0].group_name
            for i in range(len(cl)):
                try:
                    reader = cl[i].readPDF()
                except HTTPError as he:
                    print("下载时发生错误，跳过！"+repr(he))
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
    # preparations
    get_output_directory()
    print("获取wiki.sinofsx.com页面...")
    webpage = urlopen(SINO_URL).read()  # in bytes
    extracted = extract_all_airport_charts(webpage)
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
