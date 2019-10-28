import os
import re
from urllib.request import urlopen
from PyPDF2 import PdfFileMerger, PdfFileReader


def get_sino_html():
    url = "https://wiki.sinofsx.com/index.php?title=AD_2._%E6%9C%BA%E5%9C%BA_AERODROMES"
    return urlopen(url).read().decode('utf-8')


def get_group_index(name):
    return re.findall(r"[0-9]+", name)[0]


def get_group(filename):
    groupdict = {
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
    if filename[0:2].upper() == 'AD':
        return "<机场细则>"  # 直接返回
    return groupdict[get_group_index(filename)]


def get_title(filename, sinopage):
    """网站获得航图编号对应标题"""
    if filename[0:2].upper() == 'AD':
        return "AD"  # 直接返回
    pat = f"<td>{filename.replace('.pdf', '')}:([ \\S]*)</td>"
    try:
        title = re.findall(pat, sinopage)[0]
        return title
    except IndexError:  # 找不到匹配
        return ''


def regroup_files(filelist):
    """将文件列表分组"""
    regrouped = []
    tempgroup = []
    tempnum = 1
    for l in filelist:
        try:
            num = int(get_group_index(l))
        except IndexError:
            regrouped.append([l])
            continue
        if tempnum != num:
            tempnum = num
            regrouped.append(tempgroup)
            tempgroup = []
        tempgroup.append(l)
    regrouped.append(tempgroup)
    result = []
    for rg in regrouped:  # 简化只有一项的列表
        if len(rg) == 1:
            result.append(rg[0])
        else:
            result.append(rg)
    return result


def organize_key(filename):
    """用于sorted的key参数"""
    if filename[0:2].upper() == 'AD':
        return 0
    name = re.findall(r"-([0-9]+[A-Z]*).pdf", filename)[0]
    num = get_group_index(filename)
    alpha = name.replace(num, '')
    if len(alpha) == 1:
        return int(num)*100+ord(alpha)-64  # 使用ASCII码，A对应1，Z对应26
    else:
        return int(num)*100


def main():
    directory = input("请输入eAIP文件目录(单个机场)>")
    output = os.path.join(input("请输入保存文件夹>"),
                          os.path.basename(directory)+'.pdf')

    print("正在从wiki.sinofsx.com获取航图信息...")
    sino = get_sino_html()

    files = os.listdir(directory)
    files = [f for f in files if f.rsplit('.')[-1].lower() == 'pdf']
    files = sorted(files, key=organize_key)
    files = [f for f in files if get_title(f, sino)]  # 去除匹配失败的
    total = len(files)
    files = regroup_files(files)
    print(f"找到{total}个有效pdf文件，准备开始合并...")

    # 读取并合并pdf
    merger = PdfFileMerger(strict=False)
    count = 1
    pagenum = 0
    for group in files:
        if type(group) == str:
            title = get_title(group, sino)
            print(f"正在读取{group}:{title}...({count}/{total})")
            reader = PdfFileReader(os.path.join(
                directory, group), strict=False)
            merger.append(reader, bookmark=get_group(group)+title)
            pagenum += reader.getNumPages()
            count += 1
        elif type(group) == list:
            groupname = get_group(group[0])
            first = True
            for g in group:
                title = get_title(g, sino)
                print(f"正在读取{g}:{title}...({count}/{total})")
                reader = PdfFileReader(
                    os.path.join(directory, g), strict=False)
                merger.append(reader)
                # 添加书签（族）
                if first:
                    parent = merger.addBookmark(groupname, pagenum)
                    first = False
                merger.addBookmark(title, pagenum, parent)
                pagenum += reader.getNumPages()
                count += 1

    print("合并完成！正在写入...")
    merger.write(output)
    merger.close()
    print(f"合并后pdf已输出到{output}！")
    _exit = input("按回车键退出...")
    return 0


if __name__ == "__main__":
    main()
