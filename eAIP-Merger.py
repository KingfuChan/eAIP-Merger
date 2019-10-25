import os
import re
from urllib.request import urlopen
from PyPDF2 import PdfFileMerger

CHART_DICT = {
    '1': "机场图",
    '2': "停机位置图",
    '4': "机场障碍物A型图(运行限制)",
    '5': "精密进近地形图",
    '6': "最低监视引导高度图",
    '7': "标准仪表离场图",
    '9': "标准仪表进场图",
    '10': "仪表进近图",
    '11': "目视进近图",
    '20': "仪表进近图(RNAV)",
}


def get_sino_html():
    url = "https://wiki.sinofsx.com/index.php?title=AD_2._%E6%9C%BA%E5%9C%BA_AERODROMES"
    return urlopen(url).read().decode('utf-8')


def generate_bookmark(filename, sinopage):
    """网站获得航图编号对应标题"""
    # 识别航图类型
    if filename[0:2].upper() == 'AD':
        return "<机场细则>AD"  # 直接返回
    index = re.findall(r"-([0-9]+[A-Z]*).pdf", filename)[0]
    num = re.findall(r"[0-9]+", index)[0]
    group = CHART_DICT[num]

    # 获得航图标题
    filename = filename.replace('.pdf', '')
    pat = f"<td>{filename.replace('.pdf', '')}:([ \\S]*)</td>"
    try:
        title = re.findall(pat, sinopage)[0]
        return f"<{group}>{title}"
    except IndexError:  # 找不到匹配
        return ''


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


def main():
    directory = input("请输入eAIP文件目录(单个机场)>")
    output = os.path.join(input("请输入保存文件夹>"),
                          os.path.basename(directory)+'.pdf')
    files = os.listdir(directory)
    files = [f for f in files if f.rsplit('.')[-1].lower() == 'pdf']
    files = sorted(files, key=organize_key)

    print("正在从wiki.sinofsx.com获取航图信息...")
    sino = get_sino_html()

    merger = PdfFileMerger(strict=False)
    count = 0
    for p in files:
        count += 1
        bookmark = generate_bookmark(p, sino)
        if not bookmark:
            print(f"警告！{p}有误，跳过...")
            continue
        print(f"正在读取{p}:{bookmark}...({count}/{len(files)})")
        merger.append(os.path.join(directory, p), bookmark=bookmark)
    print("合并完成！正在写入...")
    merger.write(output)
    print(f"合并后pdf已输出到{output}！")
    _exit = input("按回车键退出...")


if __name__ == "__main__":
    main()
