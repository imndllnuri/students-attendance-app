/* The download section, driven by the GitHub Releases API.
 *
 * Hand-written links would name one version and rot at the next tag.
 * This reads the real releases, so a new tag publishes itself here: the
 * newest becomes the default, every older one stays reachable from the
 * picker, and the file sizes shown are the actual asset sizes.
 */
(function () {
  "use strict";

  var REPO = "imndllnuri/students-attendance-app";

  /* Pre-releases (tags like v2.2.0-beta.1) exist to be installed on a test
   * machine before a version goes public, so this page leaves them out for
   * everyone - unless it is opened as .../?channel=beta, which lists them
   * too and says so. Nothing secret: the same builds are on GitHub's
   * releases page, marked Pre-release. The point is that nobody who comes
   * here to download TapIn is handed a test build by accident. */
  var SHOW_PRERELEASES = /(?:^|&)channel=beta(?:&|$)/.test(window.location.search.slice(1));
  var API = "https://api.github.com/repos/" + REPO + "/releases";
  var RELEASES_PAGE = "https://github.com/" + REPO + "/releases";

  /* Assets are matched by how the release workflow names them
   * (.github/workflows/release.yml), newest match wins. `installer: true`
   * is what earns the "Installer" tag and the recommended border - the
   * difference between a setup program and a zip of the same bundle is
   * the whole point of the Windows column. */
  var TARGETS = [
    {
      id: "windows",
      name: "Windows",
      sub: "Windows 10 or 11, 64-bit",
      icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 5.5 10.2 4.5v6.9H3zM11.4 4.3 21 3v8.4h-9.6zM3 12.6h7.2v6.9L3 18.5zM11.4 12.6H21V21l-9.6-1.3z"/></svg>',
      match: function (n) { return /-setup\.exe$/i.test(n); },
      kind: "Installer (.exe)",
      installer: true,
      note: "Installs for your user — no administrator password needed."
    },
    {
      id: "debian",
      name: "Debian / Ubuntu",
      sub: "64-bit, glibc 2.38 or newer",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.5c0 2.5-2 3.6-2 6.5 0 2.4-2.5 5-2.5 7.5C4.5 20 7.5 21 12 21s7.5-1 7.5-3.5c0-2.5-2.5-5.1-2.5-7.5 0-2.9-2-4-2-6.5C15 2.1 13.7 1.5 12 1.5S9 2.1 9 3.5Z"/><circle cx="10.2" cy="7.4" r=".9" fill="currentColor"/><circle cx="13.8" cy="7.4" r=".9" fill="currentColor"/></svg>',
      match: function (n) { return /\.deb$/i.test(n); },
      kind: "Package (.deb)",
      installer: true,
      note: "Adds a menu entry, an icon and a tapin command."
    },
    {
      id: "linux",
      name: "Other Linux",
      sub: "Any 64-bit distribution",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
      match: function (n) { return /-linux\.zip$/i.test(n); },
      kind: "Archive (.zip)",
      installer: false,
      note: "Unpack and run — no installer, no menu entry."
    },
    {
      id: "macos",
      name: "macOS",
      sub: "64-bit",
      icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.4 12.7c0-2.3 1.9-3.4 2-3.4-1.1-1.6-2.8-1.8-3.4-1.9-1.4-.1-2.8.9-3.5.9-.7 0-1.9-.8-3.1-.8-1.6 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.4-1-2.4-3.8zM14.2 5.4c.6-.8 1.1-1.9 1-3-.9 0-2.1.6-2.8 1.4-.6.7-1.2 1.8-1 2.9 1 .1 2.1-.5 2.8-1.3z"/></svg>',
      match: function (n) { return /-macos\.zip$/i.test(n); },
      kind: "Archive (.zip)",
      installer: false,
      note: "Unpack and run. Unsigned, so allow it under Privacy & Security."
    }
  ];

  var select = document.getElementById("version-select");
  var cards = document.getElementById("download-cards");
  var status = document.getElementById("download-status");
  var dateEl = document.getElementById("release-date");
  var older = document.getElementById("older-releases");
  var bar = document.querySelector(".dl-bar");
  if (!select || !cards || !status) { return; }

  function humanSize(bytes) {
    if (!bytes && bytes !== 0) { return ""; }
    var mb = bytes / (1024 * 1024);
    return mb >= 1 ? mb.toFixed(1) + " MB" : Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function humanDate(iso) {
    if (!iso) { return ""; }
    var d = new Date(iso);
    if (isNaN(d)) { return ""; }
    return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
  }

  function showMessage(html) {
    bar.hidden = true;
    cards.innerHTML = "";
    status.hidden = false;
    status.innerHTML = html;
  }

  function assetFor(release, target) {
    var assets = release.assets || [];
    for (var i = 0; i < assets.length; i++) {
      if (target.match(assets[i].name)) { return assets[i]; }
    }
    return null;
  }

  function renderRelease(release) {
    status.hidden = true;
    dateEl.textContent = release.published_at ? "Released " + humanDate(release.published_at) : "";
    cards.innerHTML = "";

    var found = 0;
    TARGETS.forEach(function (target) {
      var asset = assetFor(release, target);
      if (!asset) { return; }
      found++;

      var card = document.createElement("article");
      card.className = "dl-card" + (target.id === "windows" ? " recommended" : "");
      card.innerHTML =
        '<div class="dl-os">' + target.icon + "<h3>" + target.name + "</h3></div>" +
        '<span class="tag ' + (target.installer ? "tag-accent" : "tag-ok") + '">' +
        (target.installer ? "Installer" : "Archive") + "</span>" +
        '<div><div class="dl-kind">' + target.kind + "</div>" +
        '<div class="dl-meta">' + target.sub + " · " + humanSize(asset.size) + "</div></div>" +
        '<p class="dl-note">' + target.note + "</p>" +
        '<a class="btn ' + (target.installer ? "btn-primary" : "btn-ghost") + '" href="' +
        asset.browser_download_url + '">Download ' + release.tag_name + "</a>";
      cards.appendChild(card);
    });

    if (!found) {
      showMessage(
        "<p><strong>" + release.tag_name + " has no downloadable files attached.</strong></p>" +
        '<p style="margin-top:8px">See it on <a href="' + release.html_url + '">GitHub</a>.</p>'
      );
    }
  }

  function renderOlder(releases) {
    if (releases.length < 2) { return; }
    var body = document.querySelector("#older-table tbody");
    releases.forEach(function (release) {
      var names = (release.assets || []).map(function (a) { return a.name; });
      var row = document.createElement("tr");
      row.innerHTML =
        "<td><a href=\"" + release.html_url + "\">" + release.tag_name + "</a></td>" +
        '<td class="num">' + humanDate(release.published_at) + "</td>" +
        '<td class="num">' + (names.length || "—") + "</td>" +
        "<td>" + (release.prerelease ? '<span class="tag tag-warn">Pre-release</span>' : "") + "</td>";
      body.appendChild(row);
    });
    older.hidden = false;
  }

  fetch(API, { headers: { Accept: "application/vnd.github+json" } })
    .then(function (response) {
      if (!response.ok) { throw new Error("HTTP " + response.status); }
      return response.json();
    })
    .then(function (all) {
      var releases = (all || []).filter(function (r) {
        return !r.draft && (SHOW_PRERELEASES || !r.prerelease);
      });
      if (SHOW_PRERELEASES && bar) {
        var note = document.createElement("p");
        note.style.margin = "0 0 14px";
        note.innerHTML = '<span class="tag tag-warn">Test channel</span> ' +
          "Pre-release builds are listed here. They are not announced to anyone, " +
          "and TapIn never offers them as an update.";
        bar.parentNode.insertBefore(note, bar);
      }
      if (!releases.length) {
        // The state before the first tag is pushed. Saying so plainly
        // beats a row of dead buttons.
        showMessage(
          "<p><strong>No release has been published yet.</strong></p>" +
          '<p style="margin-top:8px">Builds appear here automatically once the first version is published.</p>'
        );
        return;
      }

      // "Latest" is the newest full release. With the test channel on, the
      // newest entry may be a pre-release, and calling that "latest" would
      // be exactly the confusion this page is trying to avoid.
      var latest = -1;
      for (var k = 0; k < releases.length; k++) {
        if (!releases[k].prerelease) { latest = k; break; }
      }
      releases.forEach(function (release, i) {
        var option = document.createElement("option");
        option.value = String(i);
        option.textContent = release.tag_name + (release.prerelease ? " (pre-release)" : "") + (i === latest ? " — latest" : "");
        select.appendChild(option);
      });

      select.addEventListener("change", function () {
        renderRelease(releases[Number(select.value)]);
      });

      renderRelease(releases[0]);
      renderOlder(releases);
    })
    .catch(function (error) {
      // Rate limiting is the likely cause (the API allows 60 unauthenticated
      // requests an hour per IP), and it is temporary - so this points at
      // the releases page rather than pretending there is nothing to download.
      showMessage(
        "<p><strong>Could not reach GitHub to list the downloads.</strong></p>" +
        '<p style="margin-top:8px">Get them directly from the <a href="' + RELEASES_PAGE +
        '">releases page</a>. (' + error.message + ")</p>"
      );
    });
})();
