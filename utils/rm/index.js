const fs = require('fs')  // 导入文件系统模块，用于读写文件
const location = require('./location')  // 导入位置模块，用于获取IP地址所在国家
const config = require('./config')  // 导入配置模块

//此处输入, 当前默认'./url'------↓
let urls = fs.readFileSync('./url','utf8');  // 从url文件读取代理服务器链接
let flags = JSON.parse(fs.readFileSync('./flags.json','utf8'))  // 读取国家标志配置文件

// 初始化各种列表和对象
let urlList = urls.split('\n');  // 将输入的URL分割成数组
let resList = [];  // 存储解析后的代理服务器信息
let stringList = [];  // 用于去重的字符串列表
let finalList = [];  // 去重后的最终代理服务器信息列表
let finalURLs = [];  // 最终输出的URL列表
let countryList = ['unknown'];  // 国家代码列表，默认包含unknown
let emojiList =[''];  // 国家对应的表情列表，默认为空
let countryCount = {unknown:0};  // 各国家节点计数
let urlCountryList = {unknown:[]}  // 按国家分类的URL列表

async function run(){
    //处理flags - 初始化国家相关数据结构
    for(let i=0;i<flags.length;i++){
        countryList.push(flags[i].code);  // 添加国家代码
        emojiList.push(flags[i].emoji);  // 添加国家表情
        countryCount[flags[i].code] = 0;  // 初始化国家节点计数
        urlCountryList[flags[i].code] = [];  // 初始化国家URL列表
    }

    //解析URL - 将不同协议的代理URL解析为统一格式
    for(let i=0;i<urlList.length;i++){
        let url = urlList[i];
        switch (url.split('://')[0]) {
            case 'vmess':  // 处理vmess协议
                let vmessJSON = JSON.parse(Buffer.from(url.split('://')[1], 'base64').toString('utf-8'));  // 解码base64并解析JSON
                vmessJSON.ps = null  // 清空备注字段，后续会重新设置
                resList.push({type: 'vmess', data: vmessJSON, address: vmessJSON.add})  // 添加到结果列表
                break
            case 'trojan':  // 处理trojan协议
                let trojanData = url.split('://')[1].split('#')[0];  // 获取主要数据部分
                let trojanAddress = trojanData.split('@')[1].split('?')[0].split(':')[0];  // 提取服务器地址
                resList.push({type: 'trojan', data: trojanData, address: trojanAddress})  // 添加到结果列表
                break
            case 'ss':  // 处理shadowsocks协议
                let ssData = url.split('://')[1].split('#')[0];  // 获取主要数据部分
                let ssAddress = ssData.split('@')[1].split('#')[0].split(':')[0];  // 提取服务器地址
                resList.push({type: 'ss', data: ssData, address: ssAddress})  // 添加到结果列表
                break
            case 'ssr':  // 处理shadowsocksR协议
                let ssrData = Buffer.from(url.split('://')[1], 'base64').toString('utf-8');  // 解码base64
                let ssrAddress = ssrData.split(':')[0];  // 提取服务器地址
                resList.push({type: 'ssr', data: ssrData.replace(/remarks=.*?(?=&)/, "remarks={name}&"), address: ssrAddress})  // 添加到结果列表并替换备注标记
                break
            case 'https':  // 处理https协议
                let httpsData = url.split('://')[1].split('#')[0];  // 获取主要数据部分
                let httpsAddress = Buffer.from(httpsData.split('?')[0],"base64").toString('utf8').split('@')[1].split(':')[0]  // 解码base64并提取服务器地址
                resList.push({type: 'https', data: httpsData, address: httpsAddress})  // 添加到结果列表
                break
            default:
                break  // 忽略不支持的协议
        }
    }

    //去重时要先将对象转为字符串 - 对解析后的代理服务器信息进行去重
    for(let i=0;i<resList.length;i++){
        stringList.push(JSON.stringify(resList[i]))  // 将对象转为字符串以便去重
    }

    //去重 - 使用Set数据结构特性进行去重
    let afterList = Array.from(new Set(stringList))  // 转为Set去重后再转回数组

    //转回来 - 将去重后的字符串转回对象
    for(let i=0;i<afterList.length;i++){
        finalList.push(JSON.parse(afterList[i]))  // 将JSON字符串解析回对象
    }

    //批量测试国家 - 使用IP查询服务确定每个节点的国家
    for(let i=0;i<finalList.length;i++){
        finalList[i].country = await location.get(finalList[i].address)  // 异步获取IP所在国家
    }

    //变回链接 - 将处理后的节点信息重新转为URL格式
    for(let i=0;i<finalList.length;i++){
        let item = finalList[i];
        countryCount[finalList[i].country]++  // 增加该国家的节点计数
        // 生成节点名称：国旗表情+国家代码+序号+自定义后缀
        let name = emojiList[countryList.indexOf(finalList[i].country)]+finalList[i].country+' '+countryCount[finalList[i].country]+config.nodeAddName
        switch (item.type){
            case 'vmess':  // 处理vmess协议
                try{
                item.data.ps = (name).toString();  // 设置节点名称
                // 转为标准vmess URL并添加到对应国家的列表
                urlCountryList[finalList[i].country].push('vmess://'+Buffer.from(JSON.stringify(item.data),'utf8').toString('base64'))
                }catch(e){console.log('vmess node err')}  // 错误处理
                break
            case 'trojan':  // 处理trojan协议
                try{
                // 转为标准trojan URL并添加到对应国家的列表
                urlCountryList[finalList[i].country].push('trojan://'+item.data+'#'+(name).toString())
                }catch(e){console.log('trojan node err')}  // 错误处理
                break
            case 'ss':  // 处理shadowsocks协议
                try{
                // 转为标准ss URL并添加到对应国家的列表
                urlCountryList[finalList[i].country].push('ss://'+item.data+'#'+(name).toString())
                }catch(e){console.log('ss node err')}  // 错误处理
                break
            case 'ssr':  // 处理shadowsocksR协议
                try{
                // 转为标准ssr URL并添加到对应国家的列表，需要进行多次base64编码
                urlCountryList[finalList[i].country].push('ssr://'+Buffer.from(item.data.replace('{name}', Buffer.from((name).toString(),'utf8').toString('base64')),'utf8').toString('base64'))
                }catch(e){console.log('ssr node err')}  // 错误处理
                break
            case 'https':  // 处理https协议
                try{
                // 转为标准https URL并添加到对应国家的列表，使用URL编码处理名称
                urlCountryList[finalList[i].country].push('https://'+item.data+'#'+encodeURIComponent(name.toString()))
                }catch(e){console.log('https node err')}  // 错误处理
                break
            default:
                break  // 忽略不支持的协议
        }
    }
    
    // 合并所有国家的URL列表到最终列表
    for(const i in urlCountryList){
        if(urlCountryList[i].length === 0 ){
            // 跳过没有节点的国家
        }else{
            // 将该国家的所有节点添加到最终列表
            for (let a=0;a<urlCountryList[i].length;a++){
                finalURLs.push(urlCountryList[i][a])
            }
        }
    }
    
    // 输出处理结果统计信息
    console.log(`去重改名完成\n一共${urlList.length}个节点，去重${urlList.length-finalURLs.length}个节点，剩余${finalURLs.length}个节点`)
    
    //此处输出, 当前默认'./out'
    fs.writeFileSync('./out',finalURLs.join('\n'))  // 将最终URL列表写入输出文件
}

// 执行主函数
run()
