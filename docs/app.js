(function () {
  "use strict";

  const toastRegion = document.querySelector(".toast-region");
  const launcherStatus = document.querySelector("#launcher-status");
  const launchButtons = document.querySelectorAll("button[data-launch]");
  const everythingButtons = document.querySelectorAll("button[data-launch-everything]");
  const localServiceUrl = "http://127.0.0.1:8765/";
  const remoteStorageKey = "pcb-remote-agent";
  const remoteDialog = document.querySelector("[data-remote-dialog]");
  const remoteUrlInput = document.querySelector("[data-remote-url]");
  const remoteTokenInput = document.querySelector("[data-remote-token]");

  function readRemoteConfig() {
    try {
      const saved = JSON.parse(window.localStorage.getItem(remoteStorageKey) || "null");
      if (saved && saved.serviceUrl && saved.token) return saved;
    } catch (_error) {
      // Ignore malformed browser storage and use the blank configuration.
    }
    const configured = window.PCB_REMOTE_CONFIG || {};
    return configured.serviceUrl && configured.token
      ? { serviceUrl: configured.serviceUrl, token: configured.token }
      : { serviceUrl: "", token: "" };
  }

  let remoteConfig = readRemoteConfig();

  function showToast(message, type) {
    const toast = document.createElement("div");
    toast.className = "toast" + (type === "error" ? " error" : "");
    toast.innerHTML = '<span class="toast-icon">' + (type === "error" ? "!" : "✓") + '</span><span></span>';
    toast.querySelector("span:last-child").textContent = message;
    toastRegion.appendChild(toast);
    window.setTimeout(function () {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-5px)";
      toast.style.transition = "opacity .2s ease, transform .2s ease";
      window.setTimeout(function () { toast.remove(); }, 220);
    }, 3600);
  }

  function setActiveNav(button) {
    document.querySelectorAll("[data-nav]").forEach(function (item) {
      item.classList.toggle("active", item === button);
      if (item.tagName === "BUTTON" && item.classList.contains("side-link")) {
        item.setAttribute("aria-current", item === button ? "page" : "false");
      }
    });
  }

  document.querySelectorAll("[data-nav]").forEach(function (button) {
    button.addEventListener("click", function () {
      setActiveNav(button);
      showToast("已切换至" + button.dataset.nav);
    });
  });

  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function (event) {
      if (event.target.classList.contains("tab-close")) {
        event.stopPropagation();
        tab.remove();
        return;
      }
      document.querySelectorAll(".tab").forEach(function (item) {
        item.classList.remove("active-entry");
        item.classList.toggle("active", item === tab);
        item.setAttribute("aria-selected", item === tab ? "true" : "false");
      });
    });
  });

  document.querySelectorAll("[data-toast]").forEach(function (button) {
    button.addEventListener("click", function () {
      showToast(button.dataset.toast + "功能已就绪");
    });
  });

  document.querySelectorAll(".module-card").forEach(function (card) {
    card.addEventListener("click", function (event) {
      if (event.target.closest("button")) return;
      const link = card.querySelector(".module-link");
      if (link) link.click();
    });
  });

  document.querySelector("[data-fullscreen]").addEventListener("click", function () {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(function () {
        showToast("当前浏览器不支持全屏显示", "error");
      });
    } else {
      document.exitFullscreen();
    }
  });

  function normalizedServiceUrl(value) {
    const url = new URL(value.trim());
    if (!/^https?:$/.test(url.protocol)) {
      throw new Error("远程服务地址必须使用 HTTP 或 HTTPS");
    }
    return url.toString().replace(/\/$/, "");
  }

  function remoteRequest(target) {
    if (!remoteConfig.serviceUrl || !remoteConfig.token) {
      return Promise.reject(new Error("请先打开远程连接设置，填写服务地址和访问令牌"));
    }
    return fetch(remoteConfig.serviceUrl + "/api/remote/launch", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + remoteConfig.token,
        "Content-Type": "application/json",
        "bypass-tunnel-reminder": "true"
      },
      body: JSON.stringify({ target: target })
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (result) {
        if (!response.ok || !result.ok) {
          throw new Error(result.message || "远程服务请求失败");
        }
        return result;
      });
    });
  }

  function openLocalLauncher(target, label) {
    const url = new URL(localServiceUrl);
    url.searchParams.set("launch", target);
    launcherStatus.textContent = "正在打开本机服务...";
    const launchWindow = window.open(url.toString(), "_blank", "noopener,noreferrer");
    if (!launchWindow) {
      window.location.assign(url.toString());
      return;
    }
    showToast("已请求打开" + label + "。如果新页面无法打开，请先启动 BS\\start_server.bat");
  }

  function launchTarget(target, label) {
    if (!remoteConfig.serviceUrl || !remoteConfig.token) {
      openLocalLauncher(target, label);
      return;
    }
    launcherStatus.textContent = "正在请求远程电脑...";
    remoteRequest(target).then(function (result) {
      const suffix = result.already_running ? "已在运行" : "已启动";
      launcherStatus.textContent = "远程电脑" + suffix;
      showToast("远程电脑的" + label + suffix);
    }).catch(function (error) {
      launcherStatus.textContent = "远程服务未连接";
      showToast(error.message || "无法连接远程电脑", "error");
    });
  }

  launchButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      launchTarget("defect-library", "缺陷检测客户端");
    });
  });

  everythingButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      launchTarget("everything", "文档管理");
    });
  });

  function showRemoteDialog() {
    remoteUrlInput.value = remoteConfig.serviceUrl;
    remoteTokenInput.value = remoteConfig.token;
    remoteDialog.hidden = false;
    remoteUrlInput.focus();
  }

  function hideRemoteDialog() {
    remoteDialog.hidden = true;
  }

  function inputRemoteConfig() {
    const serviceUrl = normalizedServiceUrl(remoteUrlInput.value);
    const token = remoteTokenInput.value.trim();
    if (!token) throw new Error("访问令牌不能为空");
    return { serviceUrl: serviceUrl, token: token };
  }

  function testRemoteConnection() {
    let candidate;
    try {
      candidate = inputRemoteConfig();
    } catch (error) {
      showToast(error.message, "error");
      return;
    }
    const button = document.querySelector("[data-remote-test]");
    button.disabled = true;
    fetch(candidate.serviceUrl + "/api/remote/status", {
      headers: {
        Authorization: "Bearer " + candidate.token,
        "bypass-tunnel-reminder": "true"
      }
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (result) {
        if (!response.ok || !result.ok) {
          throw new Error(result.message || "远程连接测试失败");
        }
        showToast("连接成功：远程电脑已找到" + (result.available ? "缺陷客户端" : "缺陷客户端未找到") + "、" + (result.everything_available ? "Everything" : "Everything 未找到"));
      });
    }).catch(function (error) {
      showToast(error.message || "无法连接远程电脑", "error");
    }).finally(function () {
      button.disabled = false;
    });
  }

  function saveRemoteConnection() {
    let candidate;
    try {
      candidate = inputRemoteConfig();
    } catch (error) {
      showToast(error.message, "error");
      return;
    }
    remoteConfig = candidate;
    window.localStorage.setItem(remoteStorageKey, JSON.stringify(remoteConfig));
    hideRemoteDialog();
    launcherStatus.textContent = "已连接远程电脑";
    showToast("远程连接已保存");
  }

  document.querySelector("[data-remote-settings]").addEventListener("click", showRemoteDialog);
  document.querySelector("[data-remote-close]").addEventListener("click", hideRemoteDialog);
  document.querySelector("[data-remote-test]").addEventListener("click", testRemoteConnection);
  document.querySelector("[data-remote-save]").addEventListener("click", saveRemoteConnection);
  remoteDialog.addEventListener("click", function (event) {
    if (event.target === remoteDialog) hideRemoteDialog();
  });

  launcherStatus.textContent = remoteConfig.serviceUrl
    ? "已配置远程电脑"
    : "在线网页，本机程序按需启动";
}());
