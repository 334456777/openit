# 导入所需的库
import time  # 用于时间相关操作
import yaml  # 用于解析YAML配置文件
import requests  # 用于发送HTTP请求
from crawl import get_file_list, get_proxies  # 导入爬虫相关函数
from parse import parse, makeclash  # 导入解析和生成clash配置的函数
from clash import push  # 导入将配置推送到clash的函数
from multiprocessing import Process, Manager  # 导入多进程相关模块
from yaml.loader import SafeLoader  # 导入安全的YAML加载器

# 设置请求头，模拟Clash客户端
headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def local(proxy_list, file):
    """
    从本地文件读取代理配置并添加到代理列表中
    
    参数:
        proxy_list: 共享的代理列表
        file: 本地文件路径
    """
    try:
        # 打开并读取YAML文件
        with open(file, 'r') as reader:
            working = yaml.safe_load(reader)
        data_out = []
        # 提取所有代理配置
        for x in working['proxies']:
            data_out.append(x)
        # 将提取的代理添加到共享列表中
        proxy_list.append(data_out)
    except:
        print(file + ": No such file")

def url(proxy_list, link):
    """
    从URL获取代理配置并添加到代理列表中
    
    参数:
        proxy_list: 共享的代理列表
        link: 代理配置的URL链接
    """
    try:
        # 发送请求获取代理配置
        working = yaml.safe_load(requests.get(url=link, timeout=240, headers=headers).text)
        data_out = []
        # 提取所有代理配置
        for x in working['proxies']:
            data_out.append(x)
        # 将提取的代理添加到共享列表中
        proxy_list.append(data_out)
    except:
        print("Error in Collecting " + link )
        #pass

def fetch(proxy_list, filename):
    """
    从GitHub仓库获取特定日期的代理配置
    
    参数:
        proxy_list: 共享的代理列表
        filename: 文件名
    """
    # 获取当前日期
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    # GitHub仓库的基础URL
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    # 获取特定日期和文件名的代理配置
    working = yaml.safe_load(requests.get(url=baseurl + current_date + '/' + filename, timeout=240).text)
    data_out = []
    # 提取所有代理配置
    for x in working['proxies']:
        data_out.append(x)
    # 将提取的代理添加到共享列表中
    proxy_list.append(data_out)

# 初始化代理列表
proxy_list=[]
if __name__ == '__main__':
    # 使用Manager管理多进程间共享的数据
    with Manager() as manager:
        # 创建进程间共享的列表
        proxy_list = manager.list()
        # 获取当前日期
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        #print("Today is: " + current_date)
        
        # 记录开始时间
        start = time.time() #time start
        
        # 读取配置文件
        config = 'config.yaml'
        with open(config, 'r') as reader:
            config = yaml.load(reader, Loader=SafeLoader)
            # 获取订阅链接和本地文件配置
            subscribe_links = config['sub']
            subscribe_files = config['local']
        
        # 获取可用的文件列表和总数
        directories, total = get_file_list()
        # data = parse(directories)
        
        try:
            # 计算订阅链接数量
            sfiles = len(subscribe_links)
            tfiles = len(subscribe_links)# + len(data[current_date])
            processes=[]
            filenames = list()
            # filenames = data[current_date]
        except KeyError:
            # 找不到当前日期的数据时的输出
            print("Success: " + "find " + str(sfiles) + " Clash link")
        else:
            # 成功找到数据时的输出
            print("Success: " + "find " + str(tfiles) + " Clash link")

        # 初始化进程列表
        processes=[]

        try: # 使用多进程并行处理
            # 处理本地文件
            for i in subscribe_files:
                # 为每个本地文件创建一个进程
                p = Process(target=local, args=(proxy_list, i))
                p.start()
                processes.append(p)
            # 等待所有本地文件处理完成
            for p in processes:
                p.join()
            
            # 处理订阅链接
            for i in subscribe_links:
                # 为每个订阅链接创建一个进程
                p = Process(target=url, args=(proxy_list, i))
                p.start()
                processes.append(p)
            # 等待所有订阅链接处理完成
            for p in processes:
                p.join()
            
            # 处理GitHub仓库文件
            for i in filenames:
                # 为每个GitHub文件创建一个进程
                p = Process(target=fetch, args=(proxy_list, i))
                p.start()
                processes.append(p)
            # 等待所有GitHub文件处理完成
            for p in processes:
                p.join()
            
            # 记录结束时间和总用时
            end = time.time() #time end
            print("Collecting in " + "{:.2f}".format(end-start) + " seconds")
        except:
            # 发生异常时也记录用时
            end = time.time() #time end
            print("Collecting in " + "{:.2f}".format(end-start) + " seconds")

        # 将共享列表转换为普通列表
        proxy_list=list(proxy_list)
        # 生成clash配置
        proxies = makeclash(proxy_list)
        # 推送配置到clash
        push(proxies)
    
    """
    # 以下是被注释掉的旧代码，使用tqdm显示下载进度
    for i in tqdm(range(int(tfiles)), desc="Download"):
        proxy_list.append(get_proxies(current_date, data[current_date][i]))
    """
