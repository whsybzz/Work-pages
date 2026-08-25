# Work-pages V1.1.0

这是板卡检测 B/S 平台的基础冻结版本。

## 与其它分支的区别

| 分支或标签 | 说明 |
| --- | --- |
| main | 默认基础分支，功能代码与本版本基本相同，后续开发可继续变化 |
| V1.1.0 | 本基础版本的固定快照 |
| V1.2.0 | 远程控制版本，增加令牌、HTTPS 隧道和远程启动代理 |

V1.1.0 的网页按钮只能访问点击按钮那台电脑自己的 127.0.0.1 本地服务。要在本机启动桌面程序，需要完整保留 docs/、BS/ 及本机安装的 EXE 和 Everything。

## 启动方式

1. 在安装程序的 Windows 电脑上启动 BS/start_server.bat。
2. 保持本地服务运行。默认地址是 http://127.0.0.1:8765。
3. 打开 docs/index.html 所在的网页或 GitHub Pages 页面。

这个版本没有 V1.2.0 的远程连接设置，不能让另一台电脑通过公网控制本机程序。

## 关于 index.html

docs/index.html 是网页入口，不是独立应用。它还需要同目录的 styles.css 和 app.js；只下载 index.html 不能启动 EXE。浏览器必须通过 BS/server.py 才能请求 Windows 程序。
