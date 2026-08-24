# 远程控制设置

`V1.2.0` 支持从 GitHub Pages 页面请求一台指定 Windows 电脑启动已安装的 `PCB_Defect_Detection.exe` 或 Everything。

## 目标电脑

在安装了桌面程序的电脑上：

1. 双击 `BS/start_remote_server.bat`。
2. 记录窗口显示的远程访问令牌。令牌保存在 `BS/.remote_access_token`，不要上传或发到公开仓库。
3. 使用 HTTPS 反向代理把公网地址转发到 `127.0.0.1:8765`。例如安装 Cloudflare Tunnel 后运行：

```powershell
cloudflared tunnel --url http://127.0.0.1:8765
```

## 使用网页

打开 [板卡检测 B/S 平台](https://whsybzz.github.io/Work-pages/)，点击顶部的远程连接设置，填写 HTTPS 隧道地址和访问令牌并测试连接。之后点击“缺陷图片库”或“文档管理”，请求会发送到目标电脑。

远程代理只接受两个固定目标，不接受任意命令或任意文件路径。生产环境应使用固定的 HTTPS 隧道地址，不要直接把 HTTP 8765 端口暴露到公网。
