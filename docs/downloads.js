/* The download section, driven by the GitHub Releases API.
 *
 * Hand-written links would name one version and rot at the next tag. This reads the real releases, so a new
 * tag publishes itself here: the newest becomes the default, every older one stays reachable from the picker,
 * and the file sizes and checksums shown are the real ones.
 *
 * The page works without this script, and when the API cannot be reached: the HTML already holds one card
 * per system that opens the newest release on GitHub. This script replaces those cards with the real files,
 * and only then shows the version picker, so a version number is never shown that was not just fetched.
 *
 * The page is built from text nodes, never from markup in the API's answer.
 */
(function () {
  "use strict";

  var REPO = "imndllnuri/students-attendance-app";

  /* Every sentence this script shows, in one table. A page in another language sets window.TAPIN_I18N before
   * loading this file, with any of these keys; what it leaves out stays English. {name}, {tag} and {error}
   * are filled in. */
  var STR = {
    locale: document.documentElement.lang || undefined,
    download: "Download ", released: "Released ", latest: " — latest", prerelease: "pre-release", preTag: "Pre-release",
    installer: "Installer", archive: "Archive",
    windowsSub: "Windows 10 or 11, 64-bit", windowsKind: "Installer (.exe)", windowsNote: "Installs for your user, with no administrator password needed.",
    macosSub: "macOS 13 or newer · Apple Silicon (arm64)", macosKind: "Archive (.zip)", macosNote: "Unzip, move it to Applications and open it. It is not signed by Apple, so allow it once under Privacy & Security.",
    debianName: "Debian / Ubuntu", debianSub: "Ubuntu 24.04 or newer · 64-bit", debianKind: "Package (.deb)", debianNote: "Adds a menu entry, an icon and a tapin command.",
    linuxName: "Other Linux", linuxSub: "Any 64-bit distribution", linuxKind: "Archive (.zip)", linuxNote: "Unpack and run. No installer and no menu entry.",
    copy: "Copy", copied: "Copied", copyLabel: "Copy the SHA-256 checksum of the {name} download",
    sumsBefore: "All checksums for {tag} in one file: ", howToCheck: "How to check a download",
    noFiles: "{tag} has no downloadable files attached.", seeOn: "See it on ", noRelease: "No release has been published yet.",
    noReleaseBody: "Builds appear here automatically once the first version is published.",
    testChannel: "Test channel", testChannelNote: " Pre-release builds are listed here. They are not announced to anyone, and TapIn never offers them as an update.",
    errorTitle: "Could not reach GitHub to list the files.", errorBefore: "The buttons above open the newest release, where every file is listed. You can also use the ", releasesPage: "releases page"
  };
  var USER = window.TAPIN_I18N || {};
  for (var key in USER) { if (Object.prototype.hasOwnProperty.call(USER, key)) { STR[key] = USER[key]; } }
  function say(key, vars) {
    var text = STR[key];
    if (vars) { for (var v in vars) { text = text.split("{" + v + "}").join(vars[v]); } }
    return text;
  }

  /* Pre-releases (tags like v3.0.0-beta.1) exist to be installed on a test machine before a version goes
   * public, so this page leaves them out for everyone - unless it is opened as .../?channel=beta, which lists
   * them too and says so. Nothing secret: the same builds are on GitHub's releases page, marked Pre-release.
   * The point is that nobody who comes here to download TapIn is handed a test build by accident. */
  var SHOW_PRERELEASES = /(?:^|&)channel=beta(?:&|$)/.test(window.location.search.slice(1));
  var API = "https://api.github.com/repos/" + REPO + "/releases";
  var RELEASES_PAGE = "https://github.com/" + REPO + "/releases";
  var LATEST_PAGE = RELEASES_PAGE + "/latest";

  /* Assets are matched by how the release workflow names them (.github/workflows/package-electron.yml for
   * TapIn 3: a *-setup.exe, a tapin_*_amd64.deb and a *-macos.zip). The *-linux.zip is what TapIn 2 shipped; a
   * release without one simply gets no card for it. `installer: true` earns the "Installer" tag. */
  var ICONS = {
    windows: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><path d="M3 5.5 10.2 4.5v6.9H3zM11.4 4.3 21 3v8.4h-9.6zM3 12.6h7.2v6.9L3 18.5zM11.4 12.6H21V21l-9.6-1.3z"/></svg>',
    macos: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><path d="M16.4 12.7c0-2.3 1.9-3.4 2-3.4-1.1-1.6-2.8-1.8-3.4-1.9-1.4-.1-2.8.9-3.5.9-.7 0-1.9-.8-3.1-.8-1.6 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.4-1-2.4-3.8zM14.2 5.4c.6-.8 1.1-1.9 1-3-.9 0-2.1.6-2.8 1.4-.6.7-1.2 1.8-1 2.9 1 .1 2.1-.5 2.8-1.3z"/></svg>',
    debian: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.5c0 2.5-2 3.6-2 6.5 0 2.4-2.5 5-2.5 7.5C4.5 20 7.5 21 12 21s7.5-1 7.5-3.5c0-2.5-2.5-5.1-2.5-7.5 0-2.9-2-4-2-6.5C15 2.1 13.7 1.5 12 1.5S9 2.1 9 3.5Z"/><circle cx="10.2" cy="7.4" r=".9" fill="currentColor"/><circle cx="13.8" cy="7.4" r=".9" fill="currentColor"/></svg>',
    linux: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>'
  };
  /* Which system the visitor is on, so that card is the highlighted one. A guess from the browser; nothing is sent. */
  function visitorOs() {
    var hint = ((navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "") + " " + (navigator.userAgent || "");
    if (/win/i.test(hint) && !/darwin/i.test(hint)) { return "windows"; }
    if (/mac|iphone|ipad/i.test(hint)) { return "macos"; }
    if (/linux|x11|cros/i.test(hint) && !/android/i.test(hint)) { return "linux"; }
    return "";
  }
  var OS = visitorOs();

  var TARGETS = [
    {
      id: "windows", os: "windows", name: "Windows", sub: STR.windowsSub, icon: ICONS.windows,
      match: function (n) { return /-setup\.exe$/i.test(n); },
      kind: STR.windowsKind, installer: true,
      note: STR.windowsNote
    },
    {
      id: "macos", os: "macos", name: "macOS", sub: STR.macosSub, icon: ICONS.macos,
      match: function (n) { return /-macos\.zip$/i.test(n); },
      kind: STR.macosKind, installer: false,
      note: STR.macosNote
    },
    {
      id: "debian", os: "linux", name: STR.debianName, sub: STR.debianSub, icon: ICONS.debian,
      match: function (n) { return /\.deb$/i.test(n); },
      kind: STR.debianKind, installer: true,
      note: STR.debianNote
    },
    {
      id: "linux", os: "linux", name: STR.linuxName, sub: STR.linuxSub, icon: ICONS.linux,
      match: function (n) { return /-linux\.zip$/i.test(n); },
      kind: STR.linuxKind, installer: false,
      note: STR.linuxNote
    }
  ];

  var select = document.getElementById("version-select");
  var cards = document.getElementById("download-cards");
  var status = document.getElementById("download-status");
  var dateEl = document.getElementById("release-date");
  var older = document.getElementById("older-releases");
  var bar = document.querySelector(".dl-bar");
  var fallbackNote = document.getElementById("download-fallback-note");
  var sums = document.getElementById("download-sums");
  if (!select || !cards || !status) { return; }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  function link(href, text, className) {
    var a = el("a", className, text);
    a.href = href;
    return a;
  }

  function humanSize(bytes) {
    if (!bytes && bytes !== 0) { return ""; }
    var mb = bytes / (1024 * 1024);
    return mb >= 1 ? mb.toFixed(1) + " MB" : Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function humanDate(iso) {
    if (!iso) { return ""; }
    var d = new Date(iso);
    if (isNaN(d)) { return ""; }
    return d.toLocaleDateString(STR.locale, { year: "numeric", month: "long", day: "numeric" });
  }

  /* The SHA-256 GitHub computed for an asset, as plain hex, or "" when the API did not give one. */
  function sha256Of(asset) {
    var d = asset && typeof asset.digest === "string" ? asset.digest : "";
    var m = /^sha256:([0-9a-f]{64})$/i.exec(d);
    return m ? m[1].toLowerCase() : "";
  }

  function checksumRow(target, hash) {
    var row = el("div", "dl-hash");
    row.appendChild(el("span", "dl-hash-label", "SHA-256"));
    var code = el("code", "mono", hash.slice(0, 12) + "…" + hash.slice(-8));
    code.title = hash;
    row.appendChild(code);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      var copy = el("button", "dl-copy", say("copy"));
      copy.type = "button";
      copy.setAttribute("aria-label", say("copyLabel", { name: target.name }));
      copy.addEventListener("click", function () {
        navigator.clipboard.writeText(hash).then(function () {
          copy.textContent = say("copied");
          window.setTimeout(function () { copy.textContent = say("copy"); }, 1600);
        }, function () { /* the full value is in the tooltip and in SHA256SUMS.txt */ });
      });
      row.appendChild(copy);
    }
    return row;
  }

  /* A message under the cards. `keepCards` leaves the static fallback cards in place (the API failed: the
   * buttons still work); without it the cards go too (there is nothing to download yet). */
  function showMessage(lines, keepCards) {
    bar.hidden = true;
    if (!keepCards) {
      cards.textContent = "";
      if (fallbackNote) { fallbackNote.hidden = true; }
    }
    status.hidden = false;
    status.textContent = "";
    lines.forEach(function (line, i) {
      var p = el("p");
      if (i === 0) { p.appendChild(el("strong", "", line.text)); }
      else {
        p.style.marginTop = "8px";
        p.appendChild(document.createTextNode(line.text));
        if (line.href) { p.appendChild(link(line.href, line.linkText)); }
        if (line.after) { p.appendChild(document.createTextNode(line.after)); }
      }
      status.appendChild(p);
    });
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
    if (fallbackNote) { fallbackNote.hidden = true; }
    dateEl.textContent = release.published_at ? say("released") + humanDate(release.published_at) : "";
    cards.textContent = "";

    /* The highlighted card is the visitor's own system when this release has a file for it, else the first one. */
    var available = TARGETS.filter(function (t) { return assetFor(release, t); });
    var pick = available.filter(function (t) { return t.os === OS; })[0] || available[0];

    var found = 0;
    TARGETS.forEach(function (target) {
      var asset = assetFor(release, target);
      if (!asset) { return; }
      found++;
      var chosen = target === pick;

      var card = el("article", "card dl-card" + (chosen ? " recommended" : ""));
      var os = el("div", "dl-os");
      var icon = el("span");
      icon.innerHTML = target.icon; /* a fixed string in this file, not from the network */
      os.appendChild(icon);
      os.appendChild(el("h3", "", target.name));
      card.appendChild(os);
      card.appendChild(el("span", "tag " + (target.installer ? "tag-accent" : "tag-ok"), target.installer ? say("installer") : say("archive")));

      var meta = el("div");
      meta.appendChild(el("div", "dl-kind", target.kind));
      meta.appendChild(el("div", "dl-meta", target.sub + " · " + humanSize(asset.size)));
      var hash = sha256Of(asset);
      if (hash) { meta.appendChild(checksumRow(target, hash)); }
      card.appendChild(meta);
      card.appendChild(el("p", "dl-note", target.note));
      card.appendChild(link(asset.browser_download_url, say("download") + release.tag_name,
        "btn " + (chosen ? "btn-primary" : "btn-secondary")));
      cards.appendChild(card);
    });

    /* One file with every checksum, if the release has it. */
    if (sums) {
      sums.textContent = "";
      var sumsAsset = (release.assets || []).filter(function (a) { return /^SHA256SUMS\.txt$/i.test(a.name); })[0];
      if (sumsAsset) {
        sums.appendChild(document.createTextNode(say("sumsBefore", { tag: release.tag_name })));
        sums.appendChild(link(sumsAsset.browser_download_url, "SHA256SUMS.txt"));
        sums.appendChild(document.createTextNode(". "));
        sums.appendChild(link("#verify", say("howToCheck")));
        sums.appendChild(document.createTextNode("."));
      }
      sums.hidden = !sums.firstChild;
    }

    if (!found) {
      showMessage([
        { text: say("noFiles", { tag: release.tag_name }) },
        { text: say("seeOn"), href: release.html_url, linkText: "GitHub", after: "." }
      ]);
    }
  }

  function renderOlder(releases) {
    if (releases.length < 2) { return; }
    var body = document.querySelector("#older-table tbody");
    releases.forEach(function (release) {
      var names = (release.assets || []).length;
      var row = el("tr");
      var cell = el("td");
      cell.appendChild(link(release.html_url, release.tag_name));
      row.appendChild(cell);
      row.appendChild(el("td", "num", humanDate(release.published_at)));
      row.appendChild(el("td", "num", names ? String(names) : "—"));
      var notes = el("td");
      if (release.prerelease) { notes.appendChild(el("span", "tag tag-warn", say("preTag"))); }
      row.appendChild(notes);
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
        var note = el("p");
        note.style.textAlign = "center";
        note.style.margin = "0 0 14px";
        note.appendChild(el("span", "tag tag-warn", say("testChannel")));
        note.appendChild(document.createTextNode(say("testChannelNote")));
        bar.parentNode.insertBefore(note, bar);
      }
      if (!releases.length) {
        /* The state before the first tag is published. Saying so plainly beats a row of dead buttons. */
        showMessage([
          { text: say("noRelease") },
          { text: say("noReleaseBody") }
        ]);
        return;
      }

      /* "Latest" is the newest full release. With the test channel on, the newest entry may be a pre-release,
       * and calling that "latest" would be exactly the confusion this page is trying to avoid. */
      var latest = -1;
      for (var k = 0; k < releases.length; k++) {
        if (!releases[k].prerelease) { latest = k; break; }
      }
      releases.forEach(function (release, i) {
        var option = el("option", "", release.tag_name + (release.prerelease ? " (" + say("prerelease") + ")" : "") + (i === latest ? say("latest") : ""));
        option.value = String(i);
        select.appendChild(option);
      });

      select.addEventListener("change", function () {
        renderRelease(releases[Number(select.value)]);
      });

      /* Only now, with real data in hand, is a version shown. */
      bar.hidden = false;
      renderRelease(releases[0]);
      renderOlder(releases);
    })
    .catch(function (error) {
      /* Rate limiting is the likely cause (the API allows 60 unauthenticated requests an hour per IP), and it
       * is temporary. The static cards stay, and every one of them opens the newest release. */
      showMessage([
        { text: say("errorTitle") },
        { text: say("errorBefore"), href: RELEASES_PAGE, linkText: say("releasesPage"), after: ". (" + error.message + ")" }
      ], true);
    });
})();
