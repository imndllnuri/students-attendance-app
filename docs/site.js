/* TapIn website: the theme switch, the screens tabs, and the small-screen menu.
 * Everything works without this file except those three things, and the page says nothing it cannot do. */
(function () {
  "use strict";
  var root = document.documentElement;

  /* ── Theme: Dark / Light / System, like Settings → Theme in the app ── */
  var KEY = "tapin-site-theme";
  var group = document.getElementById("theme-switch");
  function stored() {
    try { var t = localStorage.getItem(KEY); return t === "light" || t === "dark" ? t : "system"; } catch (e) { return "system"; }
  }
  function apply(choice) {
    if (choice === "light" || choice === "dark") root.setAttribute("data-theme", choice);
    else root.removeAttribute("data-theme");
    try {
      if (choice === "system") localStorage.removeItem(KEY); else localStorage.setItem(KEY, choice);
    } catch (e) { /* private window or blocked storage: the choice just lasts until the page closes */ }
    if (!group) return;
    var buttons = group.querySelectorAll("[data-theme-choice]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("aria-checked", String(buttons[i].getAttribute("data-theme-choice") === choice));
    }
  }
  if (group) {
    group.hidden = false;
    apply(stored());
    group.addEventListener("click", function (event) {
      var button = event.target.closest("[data-theme-choice]");
      if (button) apply(button.getAttribute("data-theme-choice"));
    });
    group.addEventListener("keydown", function (event) {
      var order = ["dark", "light", "system"];
      var at = order.indexOf(stored());
      if (event.key === "ArrowRight" || event.key === "ArrowDown") at = (at + 1) % 3;
      else if (event.key === "ArrowLeft" || event.key === "ArrowUp") at = (at + 2) % 3;
      else return;
      event.preventDefault();
      apply(order[at]);
      group.querySelector('[data-theme-choice="' + order[at] + '"]').focus();
    });
  }

  /* ── Screens: tabs with the arrow keys, Home and End ─────────────── */
  var tabsWrap = document.querySelector(".tabs");
  if (tabsWrap) {
    var tabs = Array.prototype.slice.call(tabsWrap.querySelectorAll('[role="tab"]'));
    var panels = tabs.map(function (tab) { return document.getElementById(tab.getAttribute("aria-controls")); });
    var select = function (index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute("aria-selected", String(on));
        tab.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      if (focus) tabs[index].focus();
      if (tabs[index].scrollIntoView) tabs[index].scrollIntoView({ block: "nearest", inline: "center" });
    };
    tabsWrap.hidden = false;
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { select(i, false); });
      tab.addEventListener("keydown", function (event) {
        var to = null;
        if (event.key === "ArrowRight") to = (i + 1) % tabs.length;
        else if (event.key === "ArrowLeft") to = (i + tabs.length - 1) % tabs.length;
        else if (event.key === "Home") to = 0;
        else if (event.key === "End") to = tabs.length - 1;
        if (to === null) return;
        event.preventDefault();
        select(to, true);
      });
    });
    select(0, false);
  }

  /* ── The demo video: plays by itself while it is on screen, and rests when it is not ──
   * Not at all for anyone who asked their system for less motion; they press play. If a visitor pauses it
   * themselves it stays paused. Without this file the video simply waits behind its poster picture, with
   * its own controls. */
  var video = document.querySelector(".demo-video");
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (video && "IntersectionObserver" in window && !reduced) {
    video.preload = "metadata";
    var mode = "idle";      /* idle (never started), playing, away (we paused it when it left), user (the visitor paused it) */
    var ourPause = false;   /* the next "pause" event is ours, not the visitor's */
    video.addEventListener("pause", function () {
      if (ourPause) { ourPause = false; } else { mode = "user"; }
    });
    video.addEventListener("play", function () {
      if (mode === "user") { mode = "playing"; } /* the visitor pressed play again */
    });
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          if (mode === "idle" || mode === "away") {
            mode = "playing";
            var played = video.play();
            if (played && played.catch) played.catch(function () { /* blocked: the poster and the controls remain */ });
          }
        } else if (!video.paused) {
          ourPause = true;
          mode = "away";
          video.pause();
        }
      });
    }, { threshold: 0.5 }).observe(video);
  }

  /* ── Menu on small screens ─────────────────────────────────────── */
  var toggle = document.getElementById("nav-toggle");
  var links = document.getElementById("nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    links.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        links.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && links.classList.contains("open")) {
        links.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }
})();
