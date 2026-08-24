(function () {
  "use strict";

  const toastRegion = document.querySelector(".toast-region");
  const launcherStatus = document.querySelector("#launcher-status");
  const launchButtons = document.querySelectorAll("button[data-launch]");
  const everythingButtons = document.querySelectorAll("button[data-launch-everything]");
  const localServiceUrl = "http://127.0.0.1:8765/";

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

  launchButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      openLocalLauncher("defect-library", "缺陷检测客户端");
    });
  });

  everythingButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      openLocalLauncher("everything", "文档管理");
    });
  });

  launcherStatus.textContent = "在线网页，本机程序按需启动";
}());
