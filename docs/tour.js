/* The screenshot tour. Tabs rather than a long stack of full-width
 * images: at 1440px wide each shot is most of a screen on its own, and
 * seven of them stacked buries everything below. */
(function () {
  "use strict";

  var SHOTS = [
    {
      id: "dashboard",
      label: "Dashboard",
      file: "images/dashboard.png",
      w: 1440, h: 995,
      alt: "Dashboard: counts of active, pinned, total and archived classes, an at-risk warning strip, recently viewed classes, and a card per class.",
      caption: "Opens on what needs attention: how many students are below your attendance policy, which classes meet today, and where you left off."
    },
    {
      id: "take-attendance",
      label: "Take Attendance",
      file: "images/take-attendance.png",
      w: 2021, h: 995,
      alt: "Take Attendance: a live session on Wednesday 09-09-2026, 13:00-14:50, showing seven students recorded with their tap times, five Present in green and two Late in yellow.",
      caption: "The live session. Each tap appends a row with the exact time, and the app decides Present or Late from the session start and your late threshold. Present 5 · Late 2 · 7 of 12 recorded."
    },
    {
      id: "class-detail",
      label: "Class &amp; roster",
      file: "images/class-detail.png",
      w: 2021, h: 966,
      alt: "A class page: the roster and attendance grid with a column per session, attendance colour-coded per cell, and a side panel with class info, schedule and notes.",
      caption: "One row per student, one column per session. Double-click a cell to correct a record, or a name to open that student's history and card binding."
    },
    {
      id: "statistics",
      label: "Statistics",
      file: "images/statistics.png",
      w: 1440, h: 966,
      alt: "Attendance statistics: a Present/Late/Absent pie chart for COMP101 and an attendance-rate trend line across sessions.",
      caption: "Per class: the Present/Late/Absent split and how the rate moved session by session."
    },
    {
      id: "statistics-heatmap",
      label: "Heatmap",
      file: "images/statistics-heatmap.png",
      w: 1440, h: 995,
      alt: "An attendance heatmap with students down the side and sessions across the top, each cell shaded by attendance.",
      caption: "Students down the side, sessions across the top. A student drifting away shows up as a row that darkens; a bad session shows up as a column."
    },
    {
      id: "statistics-comparison",
      label: "Compare classes",
      file: "images/statistics-comparison.png",
      w: 1440, h: 995,
      alt: "A bar chart comparing overall attendance rates across every class.",
      caption: "Every class you teach on one axis, so an outlier is obvious without opening each one."
    },
    {
      id: "my-classes",
      label: "My Classes",
      file: "images/my-classes.png",
      w: 1440, h: 966,
      alt: "The My Classes list with a card per class showing code, schedule and attendance rate, grouped into active and inactive.",
      caption: "Pin the classes you teach this term, archive the ones you do not, and search across all of them."
    },
    {
      id: "session-calendar",
      label: "Session history",
      file: "images/session-calendar.png",
      w: 1440, h: 947,
      alt: "A month calendar with recorded attendance sessions marked on their dates.",
      caption: "Every recorded session on a calendar — useful when a student asks about a specific date."
    },
    {
      id: "settings",
      label: "Settings",
      file: "images/settings.png",
      w: 1440, h: 995,
      alt: "Settings: vault location, language, appearance and reader options.",
      caption: "Where the vault lives, English or Turkish, text size, and the card reader's connection."
    }
  ];

  var tabs = document.querySelector(".tour-tabs");
  var panel = document.getElementById("tour-panel");
  if (!tabs || !panel) { return; }

  function show(index) {
    var shot = SHOTS[index];
    Array.prototype.forEach.call(tabs.children, function (button, i) {
      button.setAttribute("aria-selected", String(i === index));
      button.tabIndex = i === index ? 0 : -1;
    });
    // Rebuilt rather than toggling nine pre-rendered panels: only one is
    // ever visible, so this keeps eight large images out of the initial
    // page load.
    panel.innerHTML =
      '<div class="tour-frame"><img src="' + shot.file + '" width="' + shot.w +
      '" height="' + shot.h + '" alt="' + shot.alt.replace(/"/g, "&quot;") +
      '" loading="lazy"></div>' +
      '<p class="tour-caption">' + shot.caption + "</p>";
  }

  SHOTS.forEach(function (shot, i) {
    var button = document.createElement("button");
    button.className = "tour-tab";
    button.type = "button";
    button.role = "tab";
    button.innerHTML = shot.label;
    button.setAttribute("aria-selected", "false");
    button.addEventListener("click", function () { show(i); });
    button.addEventListener("keydown", function (event) {
      var step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      if (!step) { return; }
      event.preventDefault();
      var next = (i + step + SHOTS.length) % SHOTS.length;
      show(next);
      tabs.children[next].focus();
    });
    tabs.appendChild(button);
  });

  show(0);
})();
