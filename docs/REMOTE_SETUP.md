# 远程控制设置

V1.2.0 支持从 GitHub Pages 页面请求一台指定 Windows 电脑启动已安装的 PCB_Defect_Detection.exe 或 Everything。

## 目标电脑

1. 确认 EXE 和 Everything 已安装。
2. 由当前登录 Windows 用户双击 BS/start_remote_server.bat。远程服务默认监听 127.0.0.1:8766。
3. 记录窗口显示的远程访问令牌。令牌保存在 BS/.remote_access_token，不要上传或发到公开仓库。
4. 使用 HTTPS 反向代理把公网地址转发到 127.0.0.1:8766。

例如：

```powershell
cloudflared tunnel --url http://127.0.0.1:8766
```

临时隧道重启后地址可能变化；长期使用应配置固定 HTTPS 隧道。

## 使用网页

打开 [板卡检测 B/S 平台](https://whsybzz.github.io/Work-pages/)，点击右上角远程连接设置，填写 HTTPS 隧道地址和访问令牌并测试连接。之后点击缺陷图片库或文档管理，请求会发送到目标电脑。

服务只接受两个固定目标，不接受任意命令或任意文件路径。目标电脑上的服务窗口和 HTTPS 隧道窗口必须保持运行。
