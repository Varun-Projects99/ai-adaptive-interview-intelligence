/**
 * InterviewIQ — Light / Dark Theme
 * =================================
 * The actual FOUC-free theme APPLICATION already happened via a tiny
 * inline, blocking script at the very top of <head> on every page (reads
 * localStorage, sets data-theme="light" on <html> before the stylesheet
 * loads). This file re-applies it (a harmless no-op if already correct),
 * exposes window.IQTheme for any page's controls (Settings > Appearance)
 * to call, injects a compact toggle button into the navbar on pages that
 * have one, and best-effort syncs the choice to the candidate's stored
 * Settings preference so it follows them across devices once logged in.
 *
 * Deliberately NOT authoritative for the first paint -- that's the inline
 * snippet's job. This can load late (it's `defer`) without ever causing a
 * flash of the wrong theme.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "iq_theme";
  var VALID = ["dark", "light"];

  function getStored() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return VALID.indexOf(v) !== -1 ? v : null;
    } catch (e) {
      return null;
    }
  }

  function apply(theme) {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }

  function getTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function updateToggleIcons(theme) {
    var buttons = document.querySelectorAll(".theme-toggle-btn");
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      btn.textContent = theme === "light" ? "☀" : "☽"; // sun / crescent moon
      var label = theme === "light" ? "Switch to dark theme" : "Switch to light theme";
      btn.setAttribute("aria-label", label);
      btn.title = label;
    }
  }

  function setTheme(theme, opts) {
    if (VALID.indexOf(theme) === -1) theme = "dark";
    apply(theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      // Private browsing / storage blocked -- theme still applies for this
      // page view, it just won't persist across reloads.
    }
    updateToggleIcons(theme);

    var shouldSync = !opts || opts.sync !== false;
    if (shouldSync) {
      // Best-effort only: an unauthenticated visitor gets 401 here, which
      // is expected and fine -- the choice simply stays local (localStorage)
      // until they're logged in. Never surfaces an error to the user.
      fetch("/api/settings/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme: theme }),
      }).catch(function () {});
    }

    try {
      document.dispatchEvent(new CustomEvent("iq-theme-changed", { detail: { theme: theme } }));
    } catch (e) {
      // Ignore in environments without CustomEvent (not expected in any
      // browser this app targets, but never let this throw).
    }
  }

  function toggleTheme() {
    setTheme(getTheme() === "light" ? "dark" : "light");
  }

  function injectToggleButton() {
    if (document.querySelector(".theme-toggle-btn")) return; // already added
    var container =
      document.querySelector(".navbar .navbar-right") ||
      document.querySelector(".navbar-right") ||
      document.querySelector(".nav-links");
    if (!container) return; // no known navbar shape on this page -- do nothing

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "theme-toggle-btn";
    btn.addEventListener("click", toggleTheme);

    // Sit right after the global main menu button when present, so the
    // order reads [Theme] [Menu] [existing chips...]; otherwise lead the
    // container, same placement rule global-menu.js itself uses.
    var gmenuWrap = container.querySelector(".gmenu-wrap");
    if (gmenuWrap) {
      container.insertBefore(btn, gmenuWrap);
    } else {
      container.insertBefore(btn, container.firstChild);
    }
    updateToggleIcons(getTheme());
  }

  // Re-apply whatever the inline <head> snippet already set (or the
  // default dark theme if nothing is stored yet) so window.IQTheme's own
  // idea of the current theme is always correct from this point on.
  var stored = getStored();
  if (stored) apply(stored);

  window.IQTheme = { get: getTheme, set: setTheme, toggle: toggleTheme };

  document.addEventListener("DOMContentLoaded", function () {
    updateToggleIcons(getTheme());
    injectToggleButton();
  });
})();
