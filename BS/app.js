(function () {
  "use strict";

  const toastRegion = document.querySelector(".toast-region");
  const launcherStatus = document.querySelector("#launcher-status");
  const launchButtons = document.querySelectorAll("button[data-launch]");
  const everythingButtons = document.querySelectorAll("button[data-launch-everything]");

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

  async function launchDefectLibrary(button) {
    launchButtons.forEach(function (item) { item.disabled = true; });
    launcherStatus.textContent = "正在启动缺陷检测客户端...";
    try {
      const response = await fetch("/api/launch-defect-library", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}"
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.message || "缺陷检测客户端启动失败");
      }
      const suffix = result.already_running ? "客户端已在运行" : "客户端已启动";
      launcherStatus.textContent = suffix;
      showToast(suffix + (result.pid ? "，PID " + result.pid : ""));
    } catch (error) {
      launcherStatus.textContent = "缺陷检测客户端未启动";
      showToast(error.message || "无法连接本地启动服务", "error");
    } finally {
      window.setTimeout(function () {
        launchButtons.forEach(function (item) { item.disabled = false; });
      }, 650);
    }
  }

  launchButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      launchDefectLibrary(button);
    });
  });

  async function launchEverything() {
    everythingButtons.forEach(function (item) { item.disabled = true; });
    try {
      const response = await fetch("/api/launch-everything", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}"
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.message || "Everything 启动失败");
      }
      const suffix = result.already_running ? "Everything 已在运行" : "Everything 已启动";
      showToast(suffix + (result.pid ? "，PID " + result.pid : ""));
    } catch (error) {
      showToast(error.message || "无法连接本地启动服务", "error");
    } finally {
      window.setTimeout(function () {
        everythingButtons.forEach(function (item) { item.disabled = false; });
      }, 650);
    }
  }

  everythingButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      launchEverything();
    });
  });

  fetch("/api/launcher-status")
    .then(function (response) { return response.json(); })
    .then(function (result) {
      if (!result.available) {
        launcherStatus.textContent = "未找到缺陷检测客户端";
      }
      if (!result.everything_available) {
        showToast("未找到 Everything.exe，请检查桌面快捷方式", "error");
      }
    })
    .catch(function () {
      launcherStatus.textContent = "本地启动服务未连接";
    });
}());
