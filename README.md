# Work-pages V1.2.0

这是当前用于 GitHub Pages 的远程控制版本。

## 与其它分支的区别

| 分支或标签 | 说明 |
| --- | --- |
| main | 默认基础网页版本，只请求当前电脑的本地服务 |
| V1.1.0 | 基础功能的固定快照，只请求当前电脑的本地服务 |
| V1.2.0 | 远程控制版本，可从另一台电脑请求目标电脑启动两个已安装程序 |

V1.2.0 包含：

- docs/index.html、app.js、styles.css 和 remote-config.js；
- 右上角的远程连接设置；
- BS/server.py 的访问令牌校验、来源限制和目标白名单；
- 只允许启动 defect-library 和 everything 两个固定目标；
- BS/start_remote_server.bat，远程服务默认使用 8766 端口。

## 使用远程控制

目标电脑必须安装 PCB_Defect_Detection.exe 和 Everything，并由当前登录用户双击 BS/start_remote_server.bat。服务窗口会生成访问令牌。然后使用 HTTPS 隧道把公网地址转发到：

```text
http://127.0.0.1:8766
```

另一台电脑打开 <https://whsybzz.github.io/Work-pages/>，点击右上角远程连接设置，填写 HTTPS 地址和令牌。服务窗口和隧道窗口都必须保持运行。

详细步骤见 docs/REMOTE_SETUP.md 和 BS/README.md。不要把 BS/.remote_access_token 提交到仓库。

## 关于 index.html

docs/index.html 是 GitHub Pages 的入口，但不是完整程序。它依赖同目录的 CSS/JavaScript 文件；只下载 index.html 不能启动 EXE。EXE 始终运行在目标 Windows 电脑上，网页通过 BS/server.py 和 HTTPS 隧道发送受保护的启动请求。

BS/index.html 是本地 Python 服务使用的入口，不是 GitHub Pages 的入口。

## 分支和标签

GitHub Pages 使用 V1.2.0 分支的 docs/。V1.1.0 和 V1.2.0 标签是固定快照；后续修复会继续提交到 V1.2.0 分支。需要当前在线功能时，请使用 GitHub Pages 地址或 V1.2.0 分支。
