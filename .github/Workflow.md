# Workflow的具体实现

## 更新CDN的具体实现
首先常规步骤，然后用Linux系统的curl命令访问jsdelivr的更新CDN地址（脚本里有）
然后用cron命令定时(这里有个方便的在线小工具测试定时是否符合期望https://tooltt.com/crontab/) 我定时每天从每小时的第5分钟开始每20分钟执行一次

然后添加一个触发按钮`workflow_dispatch`用于调试  [如图](#调试时点击绿框直接运行)
#### 具体实现

```yaml
name: CDN
on: 
   schedule:
      - cron: "5/20 * * * *"
   workflow_dispatch:
jobs:
  my-job:
    name: jsdelivr
    runs-on: ubuntu-latest
    steps:
    - name: long
      run: curl https://purge.jsdelivr.net/gh/git-yusteven/openit@main/long
    - name: Clash.yaml
      run: curl https://purge.jsdelivr.net/gh/git-yusteven/openit@main/Clash.yaml
```

## Base64 Encode 具体实现
通过对某一个或几个项目的更改，自动化把文件base64编码并输出
不用一个个复制，最后给出全部代码 (本人已不使用此workflow，但是脚本仍然好用)
### 首先设定环境
1. 设定触发条件，特定几个文件（写在paths下方xxx处）或者某些文件，不要定时运行(后文给出原因),最好加上手动触发`workflow_dispatch:`放在xxx的下一行与push对齐以备调试所用
[如图](#调试时点击绿框直接运行)
```yaml
name: xxx
on: 
  push:
    paths:
      - 'xxx'
  workflow_dispatch:
```
2. ubuntu系统即可，代码给出的是持续最新版ubuntu
```yaml
jobs:
  my-job:
    name: xxx
    runs-on: ubuntu-latest
```
3. 使用官方`actions/checkout@v3`命令检出代码(v1的改良版，v1用到了指针的概念，不易懂)
```yaml
    - uses: actions/checkout@v3
```
4. 配置git，注意把邮箱和名字改成自己GitHub的邮箱和名字，引号内添加（此处默认GitHub action）
```yaml
    # 配置 git
    - name: config git
      run: git config --global user.email "actions@github.com"; git config --global user.name "GitHub Action"
```
### 其次修改仓库文件
**只需使用Linux上的命令修改文件即可，不用去考虑cd到仓库文件夹**(本身仓库就是工作目录)

```yaml
    - name: xxxx
      run: 具体的命令,也可以是脚本
```
### 最后上传文件
这里有两种方式，分为手动推送或者运行一个bash脚本，下面给出详细解释

#### 其一，手动推送
<br>①检查change了什么文件
<br>②将文件提交到缓存区
<br>③给要上传的文件一个备注(不是名字)
<br>④push上传

```yaml
    - name: check for changes
      run: git status
    - name: stage changed files
      run: git add .
    - name: commit changed files
      run: git commit -m "By Github actions"
    - name: push code to main
      run: git push
````
#### 其二 运行一个bash脚本
理想情况是修改、提交、推送，但是或许存在一些情况，导致其实文件没有发生变化。如果这时执行`git commit`，会提示`nothing to commit, working tree clean`, 也有可能在action运行的过程中人为修改了仓库的某些文件导致冲突无法自动merge
<br>注意了，这是一个报错，意味着 action 执行失败，会出现一个红叉❌,注意避免分支运行此Action,会报错`error: src refspec main does not match any`
<br>这里提供了一个bash脚本，需要放在仓库中，建议命名为`update-repo.sh`

```bash
#!/bin/bash
status_log=$(git status -sb)
# 这里使用的是 main 分支，根据需求自行修改
if [ "$status_log" == "## main...origin/main" ];then
  echo -e "\033[32mnothing to commit, working tree clean.\033[0m"
else
  git status -s && git add . && git commit -m "$(date '+%Y.%m.%d %H:%M:%S') 订阅更新" && git pull origin main && git push origin main
  if [ $? == 1 ];then
    echo -e "\033[31mAutomatic merge failed; fix conflicts and then commit the result.\033[0m"
  fi
fi
```
然后action脚本里这样写
```yaml
    - name: <!--上方的四件套或者下方命令运行bash脚本两者选其一,update-repo.sh为上述bash文件名，放置在根目录，用chmod给了0755执行权限-->run script
      run: chmod +x ./update-repo.sh && ./update-repo.sh
```
#### 具体实现

```yaml
name: xxx
on: 
  push:
    paths:
      - 'xxx'
  workflow_dispatch:
jobs:
  my-job:
    name: xxx
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: config git
      run: git config --global user.email "actions@github.com" && git config --global user.name "GitHub Action"
    - name: xxxx
      run: 具体的命令
    - name: <!--下方是四件套-->check for changes
      run: git status
    - name: stage changed files
      run: git add .
    - name: commit changed files
      run: git commit -m "By GitHub Action"
    - name: push code
      run: git push
    - name: <!--上方的四件套或者下方命令运行bash脚本两者选其一,update-repo.sh为上述bash文件名，放置在根目录，用chmod给了0755执行权限-->run script
      run: chmod +x ./update-repo.sh && ./update-repo.sh
```
官方actions/checkout说明文档https://github.com/actions/checkout

参考：https://juejin.cn/post/6875857705282568200

来源：稀土掘金

著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
## 如何创建密钥
新建一个Token(workflows权限,其他权限自行斟酌)添加到仓库密钥区

在这里新建一个Token，指路链接：https://github.com/settings/tokens

在这里添加到仓库密钥区，指路链接：https://github.com/您的名字/您的仓库名/settings/secrets/actions/new


##### 调试时，点击绿框直接运行
##### [返回到CDN](#更新cdn的具体实现) /// [返回到Base64](#base64-encode-具体实现)

![workflows](https://github.com/git-yusteven/openit/raw/main/images/workflows.jpg)
