# BS 本地服务

BS/server.py 是网页与 Windows 桌面程序之间的本地代理。浏览器不能直接启动 EXE，必须由这个服务接收请求。

## 两种模式

| 模式 | 批处理 | 端口 | 用途 |
| --- | --- | --- | --- |
| 本机模式 | start_server.bat | 8765 | 只让当前电脑的网页启动当前电脑程序 |
| 远程模式 | start_remote_server.bat | 8766 | 让其它电脑通过 HTTPS 隧道请求当前电脑启动程序 |

## 远程模式

在安装 PCB_Defect_Detection.exe 和 Everything 的电脑上，由当前登录用户双击 start_remote_server.bat。首次启动会生成 .remote_access_token，并在窗口显示令牌。

HTTPS 隧道必须转发到：

```powershell
cloudflared tunnel --url http://127.0.0.1:8766
```

然后在 GitHub Pages 的远程连接设置中填写隧道地址和令牌。不要把未加密的 8766 端口直接暴露到公网，也不要提交 .remote_access_token。

服务只接受两个固定启动目标：缺陷检测客户端和 Everything，不接受任意命令或任意文件路径。服务和隧道窗口都必须保持运行。

## index.html 的关系

BS/index.html 是本地服务通过 http://127.0.0.1:8766 提供的页面入口；GitHub Pages 使用的是 docs/index.html。任意一个 index.html 都不能单独启动 EXE，必须配合对应的 CSS/JavaScript、BS/server.py 以及目标电脑上的桌面程序。
