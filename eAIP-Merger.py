import os
import re
from PyPDF2 import PdfFileMerger


def read_files(filelist):
    pass


def organize_key(filename):
    """用于sorted的key参数"""
    if filename[0:2].upper() == 'AD':
        return 0
    index = re.findall(r"-([0-9]+[A-Z]*).pdf", filename)[0]
    num = re.findall(r"[0-9]+", index)[0]
    alpha = index.replace(num, '')
    if len(alpha) == 1:
        return int(num)*100+ord(alpha)-64  # 使用ASCII码，A对应1，Z对应26
    else:
        return int(num)*100


def organize_files(filelist):
    """对pdf文件排序"""
    return sorted(filelist, key=organize_key)


def main():
    # 读取并筛选pdf文件
    files = os.listdir(input("Enter directory for PDFs>"))
    files = [f for f in files if f.rsplit('.')[-1].lower() == 'pdf']
    files = organize_files(files)
    print(files)


if __name__ == "__main__":
    main()
