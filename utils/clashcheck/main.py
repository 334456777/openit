import time  # 导入time模块，用于延时操作
import subprocess  # 导入subprocess模块，用于创建子进程
from multiprocessing import Process, Manager, Semaphore  # 导入多进程相关组件
from check import check  # 导入check模块，用于检查代理可用性
from tqdm import tqdm  # 导入tqdm模块，用于显示进度条
from init import init, clean  # 导入init和clean模块，用于初始化和清理Clash配置
from clash import push, checkenv, checkuse  # 导入clash相关函数

if __name__ == '__main__':
    with Manager() as manager:  # 使用Manager创建共享内存管理器
        alive = manager.list()  # 创建一个共享列表，用于存储检查通过的代理
        http_port, api_port, threads, source, timeout, outfile, proxyconfig, apiurl, testurl, config = init()  # 初始化Clash配置和参数
        clashname, operating_system = checkenv()  # 检查操作系统和Clash可执行文件名称
        checkuse(clashname[2::], operating_system)  # 检查Clash使用情况和兼容性
        clash = subprocess.Popen([clashname, '-f', './temp/working.yaml', '-d', '.'])  # 启动Clash进程，加载配置文件并设置日志目录

        processes = []  # 创建一个列表，用于存储子进程对象
        sema = Semaphore(threads)  # 创建一个信号量，限制并发执行的代理数量

        time.sleep(5)  # 等待5秒，让Clash启动并初始化

        for i in tqdm(range(int(len(config['proxies']))), desc="Testing"):  # 循环遍历配置中的所有代理
            sema.acquire()  # 获取信号量，限制并发执行的代理数量
            p = Process(target=check, args=(alive, config['proxies'][i], apiurl, sema, timeout, testurl))  # 创建一个子进程，用于检查代理
            p.start()  # 启动子进程
            processes.append(p)  # 将子进程对象添加到列表中

        for p in processes:  # 等待所有子进程结束
            p.join()

        time.sleep(5)  # 等待5秒，让所有检查完成

        alive = list(alive)  # 将共享列表转换为普通列表
        push(alive, outfile)  # 将可用的代理列表写入文件
        clean(clash)  # 清理Clash进程和临时文件
