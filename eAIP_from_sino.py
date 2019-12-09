import os
import re
from urllib.request import urlopen

from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger, PdfFileReader

SINO_URL = "https://wiki.sinofsx.com/index.php?title=AD_2._%E6%9C%BA%E5%9C%BA_AERODROMES"


class Chart(object):
    def __init__(self, icao, code, name, url):
        self.icao = icao
        self.code = code
        self.name = name
        self.url = url
        self.path = os.path.join(self.icao, self.code)

    def download(self):
        pdf = urlopen(self.url).read()
        if not os.path.exists(self.icao):
            os.mkdir(self.icao)
        with open(self.path, 'wb') as p:
            p.write(pdf)

    def readPDF(self):
        if os.path.exists(self.path):
            pdfobject = PdfFileReader(self.path, strict=False)
            return pdfobject
        else:
            self.download()
            return self.readPDF


def parse_airport_from_table(html):
    # html shall be a BeautifulSoup object
    caption = html.find('caption').get_text()
    icao = re.findall(r"(Z[A-Z]{3})-*", caption)[0]
    rows = [r for r in html.find_all('tr') if len(r.find_all('td')) == 3]
    apt_charts_list = []
    for r in rows:
        info, _cycle, link = r.find_all('td')
        code, name = info.get_text().split(':')
        href = link.find('a').get('href')
        apt_charts_list.append(Chart(icao, code, name, href))
    return {'icao': icao, 'charts': apt_charts_list, 'count': len(apt_charts_list)}


def extract_airports(html):
    soup = BeautifulSoup(html, 'html.parser')
    apt_tables = soup.find_all(
        'table', attrs={'class': "wikitable mw-collapsible"})
    airports = [parse_airport_from_table(aptt) for aptt in apt_tables]
    return airports


def merge_pdf():
    pass


def main():
    print("获取wiki.sinofsx.com页面...")
    webpage = urlopen(SINO_URL).read()  # in bytes
    extracted = extract_airports(webpage)

    # initialize
    icao = 'AAAA'
    chart_list = []
    count = 0
    while 1:
        icao = input("请输入机场ICAO码，或按回车键退出>").strip().upper()
        if not icao:
            return 0
        for et in extracted:
            if et['icao'] == icao:
                chart_list = et['charts']
                count = et['count']
                print(f"找到{icao}，共{count}份pdf文件！")
                merge_pdf()


if __name__ == "__main__":
    c = Chart('ZBSJ', "ZBSJ-7C", "SID RNAV RWY15",
              "https://wiki.sinofsx.com/Charts/AD/ZBSJ/ZBSJ-7C.pdf")
    c.readPDF()
