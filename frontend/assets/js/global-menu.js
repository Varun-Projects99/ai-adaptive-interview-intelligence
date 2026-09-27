/**
 * InterviewIQ — Global Main Menu
 * ==============================
 * A single, compact dropdown menu reused across every authenticated page,
 * instead of duplicating navigation markup/CSS per page. Include with:
 *   <script src="/assets/js/global-menu.js" defer></script>
 * right after the page's existing navbar. It finds the navbar's own
 * right-hand container (.navbar-right, falling back to .nav-links) and
 * inserts the menu button as its FIRST child -- every existing chip,
 * back-button, or link already in that container is left completely
 * untouched, so this is purely additive.
 *
 * Deliberately NOT included on: /interview (must stay focused, no nav
 * distraction), /login, /register, /invite/<token> (unauthenticated pages).
 *
 * Menu structure (per InterviewIQ's navigation spec):
 *   MAIN     -> Dashboard, AI Interview, Resume Analyzer, History & Reports,
 *               AI Assistant
 *   PRACTICE -> Coding Practice
 *   ACCOUNT  -> Settings, Logout
 * Secondary/legacy features (Career Roadmap, the old AI Coach page) are
 * intentionally NOT listed here -- they still work by direct link, they are
 * just not promoted into primary navigation.
 *
 * Every href below is an EXISTING route already served by app.py -- no new
 * routes are introduced by this file.
 */
(function () {
  "use strict";

  function buildItem(href, label, icon) {
    var a = document.createElement("a");
    a.href = href;
    a.className = "gmenu-item";
    a.setAttribute("role", "menuitem");
    if (window.location && window.location.pathname === href) {
      a.classList.add("active");
      a.setAttribute("aria-current", "page");
    }
    a.innerHTML = '<span class="gmenu-item-icon">' + icon + '</span><span>' + label + '</span>';
    return a;
  }

  function buildSectionLabel(text) {
    var div = document.createElement("div");
    div.className = "gmenu-section-label";
    div.textContent = text;
    return div;
  }

  function buildMenu(role) {
    var panel = document.createElement("div");
    panel.className = "gmenu-panel";
    panel.setAttribute("role", "menu");

    var isPrivileged = role === "recruiter" || role === "admin";

    if (isPrivileged) {
      panel.appendChild(buildSectionLabel("MAIN"));
      panel.appendChild(buildItem("/recruiter", "Recruiter Portal", "💼"));
      panel.appendChild(buildItem("/ai-assistant", "AI Assistant", "🤖"));
    } else {
      panel.appendChild(buildSectionLabel("MAIN"));
      panel.appendChild(buildItem("/dashboard", "Dashboard", "⌂"));
      panel.appendChild(buildItem("/upload", "AI Interview", "🎤"));
      panel.appendChild(buildItem("/analyzer", "Resume Analyzer", "📄"));
      panel.appendChild(buildItem("/history", "History & Reports", "📊"));
      panel.appendChild(buildItem("/ai-assistant", "AI Assistant", "🤖"));

      var divider1 = document.createElement("div");
      divider1.className = "gmenu-divider";
      panel.appendChild(divider1);

      panel.appendChild(buildSectionLabel("PRACTICE"));
      panel.appendChild(buildItem("/coding", "Coding Practice", "⌨"));
    }

    var divider2 = document.createElement("div");
    divider2.className = "gmenu-divider";
    panel.appendChild(divider2);

    panel.appendChild(buildSectionLabel("ACCOUNT"));
    panel.appendChild(buildItem("/settings", "Settings", "⚙"));

    var logoutItem = document.createElement("a");
    logoutItem.href = "#";
    logoutItem.className = "gmenu-item gmenu-logout";
    logoutItem.setAttribute("role", "menuitem");
    logoutItem.innerHTML = '<span class="gmenu-item-icon">→</span><span>Logout</span>';
    logoutItem.addEventListener("click", function (e) {
      e.preventDefault();
      if (typeof window.logout === "function") {
        window.logout();
      } else {
        fetch("/api/auth/logout", { method: "POST" }).finally(function () {
          window.location.href = "/login";
        });
      }
    });
    panel.appendChild(logoutItem);

    return panel;
  }

  function init(role) {
    var container = document.querySelector(".navbar .navbar-right") ||
      document.querySelector(".navbar-right") ||
      document.querySelector(".nav-links");
    if (!container) return; // No known navbar shape on this page -- do nothing.
    if (document.querySelector(".gmenu-toggle")) return; // Already initialized.

    var wrap = document.createElement("div");
    wrap.className = "gmenu-wrap";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "gmenu-toggle";
    toggle.setAttribute("aria-haspopup", "true");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Open main menu");
    toggle.innerHTML = '<span class="gmenu-toggle-icon">☰</span><span class="gmenu-toggle-label">Menu</span>';

    var panel = buildMenu(role);

    function closeMenu() {
      panel.classList.remove("gmenu-open");
      toggle.setAttribute("aria-expanded", "false");
    }
    function openMenu() {
      panel.classList.add("gmenu-open");
      toggle.setAttribute("aria-expanded", "true");
    }

    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      if (panel.classList.contains("gmenu-open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    document.addEventListener("click", function (e) {
      if (!wrap.contains(e.target)) closeMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });

    wrap.appendChild(toggle);
    wrap.appendChild(panel);
    container.insertBefore(wrap, container.firstChild);
  }

  document.addEventListener("DOMContentLoaded", function () {
    fetch("/api/auth/me")
      .then(function (res) { return res.ok ? res.json() : { authenticated: false }; })
      .then(function (data) {
        var role = (data && data.user && data.user.role) || "candidate";
        init(role);
      })
      .catch(function () {
        init("candidate");
      });
  });
})();
