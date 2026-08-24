# PCB B/S 平台

这是参考页面的本地 B/S 实现。浏览器通过本地 Python 服务调用桌面端，避免让网页直接绕过浏览器安全限制执行 Windows 程序。

## 启动

在 Windows 桌面用户自己的会话中启动服务。最简单的方式是双击 `start_server.bat`；也可以在 `BS` 目录执行：

```powershell
python server.py
```

然后打开 <http://127.0.0.1:8765>。

不要从其它服务账户、后台任务或 Codex 沙盒启动服务：Windows GUI 程序只能显示在启动它的桌面用户会话中。

## 从公网页面启动本机程序

也可以先在本机双击 `start_server.bat`，再打开 GitHub Pages 页面：
`https://whsybzz.github.io/Work-pages/`。

页面中的“缺陷图片库”和“文档管理”会打开当前电脑的 `http://127.0.0.1:8765`，并请求本机服务启动对应程序。每台需要使用这些入口的电脑都必须有本地服务、对应桌面程序和 Everything。

## 远程控制已安装程序的电脑

如果希望其它电脑通过公网页面控制这台电脑：

1. 在安装了 `PCB_Defect_Detection.exe` 和 Everything 的电脑上双击 `start_remote_server.bat`。首次启动会在本目录生成 `.remote_access_token`，窗口中也会显示令牌。
2. 使用 HTTPS 隧道或反向代理把 `https://你的远程地址` 转发到这台电脑的 `127.0.0.1:8765`。不要直接把未加密的 8765 端口暴露到公网。
3. 在 GitHub Pages 页面点击右上角的远程连接按钮，填写隧道地址和令牌，然后保存。

Cloudflare Tunnel 的临时方式示例：

```powershell
cloudflared tunnel --url http://127.0.0.1:8765
```

把命令输出的 `https://*.trycloudflare.com` 地址填到网页中。临时地址在隧道重启后会变化；正式使用请配置固定的命名隧道或其它 HTTPS 反向代理。

## 缺陷图片库客户端

点击页面中的“缺陷图片库”时，服务会自动查找并启动 `PCB_Defect_Detection.exe`。默认查找顺序包含：

- `BS\PCB_Defect_Detection.exe`
- `BS\PCB_Defect_Detection\PCB_Defect_Detection.exe`
- `BS\release\PCB_Defect_Detection\PCB_Defect_Detection.exe`
- 当前项目相邻的 `PCB_yolo_detection_20260817_exe\release\PCB_Defect_Detection\PCB_Defect_Detection.exe`
- 当前项目相邻的 `PCB_yolo_detection_20260817_exe\build_exe\PCB_Defect_Detection\PCB_Defect_Detection.exe`

也可以显式指定路径：

```powershell
$env:PCB_DEFECT_EXE = "D:\path\to\PCB_Defect_Detection.exe"
python server.py
```

## 文档管理

点击“文档管理”会通过本地服务调用 Windows Shell 启动桌面 Everything 软件，并自动打开搜索窗口。服务会优先查找以下位置：

- `EVERYTHING_EXE` 环境变量指定的路径
- `D:\AppGallery\Downloads\everything\Everything.exe`
- `C:\Program Files\Everything\Everything.exe`
- `C:\Program Files (x86)\Everything\Everything.exe`
- 当前用户的 `AppData\Local\Everything\Everything.exe` 或 `AppData\Roaming\Everything\Everything.exe`

桌面快捷方式查找顺序为：`EVERYTHING_LNK` 环境变量、`C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Everything.lnk`、当前用户桌面和开始菜单。快捷方式存在时优先使用它，以保留 Everything 的管理员权限配置。

如果 Everything 安装在其它位置，可以显式指定路径：

```powershell
$env:EVERYTHING_EXE = "D:\path\to\Everything.exe"
$env:EVERYTHING_LNK = "C:\path\to\Everything.lnk"
python server.py
```
