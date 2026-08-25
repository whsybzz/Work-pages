# Work-pages

板卡检测 B/S 平台的网页入口与本地桌面程序启动代理。

## 分支和版本

| 分支或标签 | 定位 | 启动能力 |
| --- | --- | --- |
| main | 默认基础分支，作为网页基础版本维护 | 只能请求当前电脑的本地服务 |
| V1.1.0 | 基础版的冻结版本，功能代码与 main 基本相同 | 只能请求当前电脑的本地服务 |
| V1.2.0 | 远程控制版本，当前 GitHub Pages 使用的版本 | 可由另一台电脑请求指定电脑启动 EXE 和 Everything |

main 和 V1.1.0 的网页功能代码是同一套基础版本；main 是默认开发分支，V1.1.0 是保留的基线版本。V1.2.0 增加了远程连接设置、访问令牌、HTTPS 隧道兼容和受限的远程启动接口。

当前在线页面：<https://whsybzz.github.io/Work-pages/>。GitHub Pages 的来源是 V1.2.0 分支的 docs/ 目录。

## index.html 不是完整程序

docs/index.html 是 GitHub Pages 的入口文件，但它依赖同目录的 styles.css、app.js 和 V1.2.0 的 remote-config.js。只下载 index.html：

- 页面样式和交互会缺失或不完整；
- 浏览器不会因此获得启动 Windows EXE 的权限；
- 它不能单独跳转并启动 PCB_Defect_Detection.exe 或 Everything。

EXE 和 Everything 必须安装在目标 Windows 电脑上。网页只能调用 BS/server.py 提供的本地或远程接口。在线使用时不需要单独下载 index.html，直接访问上面的 GitHub Pages 地址即可。

V1.2.0 还包含 BS/index.html，它是 Python 本地服务使用的页面入口，不是 GitHub Pages 的入口。

## 标签说明

V1.1.0 和 V1.2.0 标签是固定快照；分支可以在打标签后继续修复。需要使用当前在线功能时，以 V1.2.0 分支和 GitHub Pages 页面为准。
