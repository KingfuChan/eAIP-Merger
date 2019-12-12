import os
import re
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
        self.path = os.path.join(self.icao, self.code+'.pdf')

    def get_group(self):
        key = re.findall(r"[A-Z]{4}-([0-9A-Z]+)", self.code)[0]
        if key == 'AD':
            return '0'
        else:
            key = re.findall(r"[0-9]+", key)[0]
            return key

    def download(self):
        print(f"正在下载\t{self.code}:{self.name}")
        pdf = urlopen(self.url).read()
        if not os.path.exists(self.icao):
            os.mkdir(self.icao)
        with open(self.path, 'wb') as p:
            p.write(pdf)

    def readPDF(self):
        if os.path.exists(self.path):
            print(f"正在读取\t{self.code}")
            pdfobject = PdfFileReader(self.path, strict=False)
            return pdfobject
        else:
            self.download()
            return self.readPDF()


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


def merge_pdf(chart_list):
    """合并PDF，传入参数为Chart对象的列表"""
    filename = chart_list[0].icao + '_' + chart_list[0].cycle + '.pdf'
    merger = PdfFileMerger(strict=False)
    for cl in chart_list:

        merger.append(cl.readPDF(), import_bookmarks=True)
    print("合并完成，正在保存文件...")
    merger.write(filename)


def main():
    print("获取wiki.sinofsx.com页面...")
    webpage = urlopen(SINO_URL).read()  # in bytes
    extracted = extract_all_airport_charts(webpage)

    # initialize
    icao = 'AAAA'
    chart_list = []
    count = 0
    while 1:
        icao = input("请输入机场ICAO码，或按回车键退出>").strip().upper()
        if not icao:
            return
        for et in extracted:
            if et['icao'] == icao:
                chart_list = et['charts']
                count = et['count']
                print(f"找到{icao}，共{count}份pdf文件！")
                merge_pdf(chart_list)


if __name__ == "__main__":
    main()
