/* TN Gazette Archive — stats, dataset browser, live previews. No dependencies. */
(function () {
  "use strict";

  var REPO = "DigitalIndiaArchiver/TNGazette";
  var RAW = "https://raw.githubusercontent.com/" + REPO + "/main/data/";
  var BLOB = "https://github.com/" + REPO + "/blob/main/data/";
  var TREE = "https://github.com/" + REPO + "/tree/main/data/";

  var LEGACY = [
    { name: "Gazattes.csv", holds: "Weekly gazette parts (pre-redesign site, legacy)", count: "legacy" },
    { name: "GazatteIssues.csv", holds: "Weekly issue listings (legacy)", count: "legacy" },
    { name: "ExtraOrdinaryGazattes.csv", holds: "Extraordinary notifications (legacy)", count: "legacy" }
  ];

  function fetchText(url) {
    var ctl = new AbortController();
    var timer = setTimeout(function () { ctl.abort(); }, 20000);
    return fetch(url, { signal: ctl.signal }).then(function (r) {
      clearTimeout(timer);
      if (!r.ok) throw new Error(r.status + " " + url);
      return r.text();
    }).catch(function (e) { clearTimeout(timer); throw e; });
  }

  function parseCSV(text) {
    var rows = [], row = [], cur = "", inQ = false, i, c;
    for (i = 0; i < text.length; i++) {
      c = text[i];
      if (inQ) {
        if (c === '"') {
          if (text[i + 1] === '"') { cur += '"'; i++; } else inQ = false;
        } else cur += c;
      } else if (c === '"') inQ = true;
      else if (c === ",") { row.push(cur); cur = ""; }
      else if (c === "\n") { row.push(cur); rows.push(row); row = []; cur = ""; }
      else if (c !== "\r") cur += c;
    }
    if (cur !== "" || row.length) { row.push(cur); rows.push(row); }
    return rows;
  }

  function objectRows(text) {
    var rows = parseCSV(text), head = rows[0] || [], out = [];
    for (var i = 1; i < rows.length; i++) {
      if (!rows[i].length || (rows[i].length === 1 && !rows[i][0])) continue;
      var o = {};
      for (var j = 0; j < head.length; j++) o[head[j]] = rows[i][j] === undefined ? "" : rows[i][j];
      out.push(o);
    }
    return out;
  }

  function esc(s) {
    return String(s === undefined || s === null ? "" : s).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch];
    });
  }

  function nf(n) {
    return typeof n === "number" ? n.toLocaleString("en-IN") : esc(n);
  }

  function iso(d) {
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || "");
    return m ? m[3] + "/" + m[2] + "/" + m[1] : (d || "");
  }

  function trim(s, n) {
    s = String(s || "").replace(/\s+/g, " ").trim();
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function fillStats(stats) {
    var t = stats.totals || {};
    setText("stat-parts", nf(t.gazette_parts));
    setText("stat-issues", nf(t.gazette_issues));
    setText("stat-extra", nf(t.extraordinary));
    setText("stat-docs", nf(t.markdown_docs));
    setText("stat-latest", stats.latest_issue ? "no. " + stats.latest_issue : "—");
    setText("stat-date", stats.generated_at || "");
    setText("md-total", nf((stats.markdown || {}).total));
    setText("md-span", ((stats.markdown || {}).first_year || "") + "–" + ((stats.markdown || {}).last_year || ""));
  }

  function renderLatestIssues() {
    var wrap = document.getElementById("latest-table");
    if (!wrap) return;
    var year = new Date().getFullYear();
    Promise.all([
      fetchText(RAW + "GazatteIssues_" + year + ".csv"),
      fetchText(RAW + "Gazattes_" + year + ".csv").catch(function () { return ""; })
    ]).then(function (res) {
      var rows = objectRows(res[0]).filter(function (r) { return r["Issue No"]; });
      rows.sort(function (a, b) {
        return (parseInt(b["Issue No"], 10) || 0) - (parseInt(a["Issue No"], 10) || 0);
      });
      var perIssue = {};
      objectRows(res[1]).forEach(function (r) {
        var k = String(parseInt(r["Issue"], 10));
        if (r["Issue"] && k !== "NaN") perIssue[k] = (perIssue[k] || 0) + 1;
      });
      var html = '<table><thead><tr><th>Issue</th><th>Date</th><th class="num">Parts in archive</th><th>Read the text</th><th>Official listing</th></tr></thead><tbody>';
      rows.slice(0, 12).forEach(function (r) {
        var n = perIssue[String(parseInt(r["Issue No"], 10))];
        var mdYear = /^(\d{4})/.exec(String(r["Date"] || ""));
        var md = mdYear ? '<a href="' + TREE + 'markdown/ordinary/' + mdYear[1] + '/" rel="noopener">browse</a>' : "";
        html += "<tr><td>No. " + esc(r["Issue No"]) + "</td><td>" + esc(iso(r["Date"])) + "</td>" +
          '<td class="num">' + (n ? nf(n) : "\u2014") + "</td><td>" + md + "</td>" +
          '<td>' + (r["URL"] ? '<a href="' + esc(r["URL"]) + '" rel="noopener">open \u2197</a>' : "") + "</td></tr>";
      });
      html += "</tbody></table>";
      wrap.innerHTML = html;
    }).catch(function () {
      wrap.innerHTML = '<p class="note">Could not load the latest issue list — ' +
        'read the CSVs <a href="https://github.com/' + REPO + '/tree/main/data">in the repository</a>.</p>';
    });
  }

  function renderPreview() {
    var tbody = document.getElementById("preview-tbody");
    if (!tbody) return;
    var year = new Date().getFullYear();
    fetchText(RAW + "Gazattes_" + year + ".csv").then(function (t) {
      var rows = objectRows(t).filter(function (r) { return r["URL"]; });
      rows.sort(function (a, b) { return (b["Date"] || "").localeCompare(a["Date"] || ""); });
      var html = "";
      rows.slice(0, 25).forEach(function (r) {
        var links = r["URL"] ? '<a href="' + esc(r["URL"]) + '" rel="noopener">PDF ↗</a>' : "";
        if (r["Archived URL"]) {
          links += links ? " · " : "";
          links += '<a href="' + esc(r["Archived URL"]) + '" rel="noopener">archive ↗</a>';
        }
        if (String(r["Deleted"]).toLowerCase() === "true") {
          links += ' <span class="flag" title="Original link no longer works">dead</span>';
        }
        html += "<tr><td>" + esc(iso(r["Date"])) + "</td><td>" + esc(r["Issue"]) + "</td><td>" +
          esc(r["Part"]) + "</td><td>" + esc(trim(r["Content"], 110)) + "</td><td>" + links + "</td></tr>";
      });
      tbody.innerHTML = html || '<tr><td colspan="5">No rows yet.</td></tr>';
    }).catch(function () {
      tbody.innerHTML = '<tr><td colspan="5">Could not load the dataset file.</td></tr>';
    });
  }

  function renderFiles(stats) {
    var tbody = document.getElementById("files-tbody");
    if (!tbody) return;
    var rows = [];
    (stats.ordinary_years || []).forEach(function (y) {
      rows.push({
        name: "Gazattes_" + y.year + ".csv",
        holds: "Weekly gazette parts — one row per part, " + iso(y.first_date) + " → " + iso(y.last_date),
        count: nf(y.parts), year: y.year
      });
    });
    (stats.issue_years || []).forEach(function (y) {
      rows.push({
        name: "GazatteIssues_" + y.year + ".csv",
        holds: "Weekly issue listings — one row per issue",
        count: nf(y.issues), year: y.year
      });
    });
    (stats.extraordinary_years || []).forEach(function (y) {
      rows.push({
        name: "ExtraOrdinaryGazattes_" + y.year + ".csv",
        holds: "Extraordinary notifications — ordinances, appointments, acquisitions",
        count: nf(y.rows), year: y.year
      });
    });
    rows.sort(function (a, b) { return b.year - a.year; });
    LEGACY.forEach(function (f) {
      rows.push({ name: f.name, holds: f.holds, count: "—", year: -1 });
    });
    tbody.innerHTML = rows.map(function (r) {
      return "<tr><td><code>" + esc(r.name) + "</code></td><td>" + esc(r.holds) + "</td>" +
        '<td class="num">' + r.count + "</td><td>" +
        '<a href="' + RAW + esc(r.name) + '">CSV</a> · <a href="' + BLOB + esc(r.name) + '">browse</a></td></tr>';
    }).join("");
  }

  function renderMarkdown(stats) {
    var tbody = document.getElementById("md-tbody");
    if (!tbody) return;
    var md = stats.markdown || {};
    var byYear = {};
    (md.ordinary_years || []).forEach(function (y) { byYear[y.year] = { ordinary: y.docs, extraordinary: 0 }; });
    (md.extraordinary_years || []).forEach(function (y) {
      byYear[y.year] = byYear[y.year] || { ordinary: 0, extraordinary: 0 };
      byYear[y.year].extraordinary = y.docs;
    });
    var years = Object.keys(byYear).map(Number).sort(function (a, b) { return b - a; });
    tbody.innerHTML = years.map(function (y) {
      var r = byYear[y];
      return "<tr><td>" + y + "</td>" +
        '<td class="num">' + (r.ordinary ? '<a href="' + TREE + 'markdown/ordinary/' + y + '/">' + nf(r.ordinary) + "</a>" : "—") + "</td>" +
        '<td class="num">' + (r.extraordinary ? '<a href="' + TREE + 'markdown/extraordinary/' + y + '/">' + nf(r.extraordinary) + "</a>" : "—") + "</td></tr>";
    }).join("");
  }

  fetchText("stats.json").then(function (t) {
    var stats = JSON.parse(t);
    fillStats(stats);
    renderFiles(stats);
    renderMarkdown(stats);
    renderYears(stats);
  }).catch(function () {});


  var YEAR_NOTES = {
    2008: "Earliest year in the archive — coverage may start mid-year.",
    2023: "Last year on the old site; the redesign in late 2023 breaks the series.",
    2024: "Weekly listing lost to the site redesign; extraordinary index and text layer preserved.",
    2025: "Text layer only — the full extraordinary index exceeds GitHub's 100 MB file cap.",
    2026: "Current year — weekly window recovered to January; extraordinary index starts April."
  };

  function renderYears(stats) {
    var tbody = document.getElementById("years-tbody");
    if (!tbody) return;
    var rows = (stats.years || []).slice().reverse().map(function (y) {
      var official = '<span class="year-official">' +
        '<a href="https://www.stationeryprinting.tn.gov.in/gazette.php?id=' + btoa(String(y.year)) + '" title="Official weekly listing">weekly</a>' +
        ' · ' +
        '<a href="https://www.stationeryprinting.tn.gov.in/extra_ordinary_lists.php?id=' + btoa(String(y.year)) + '" title="Official extraordinary listing">extra</a>' +
        "</span>";
      function cell(n, file) {
        if (!n) return '<span class="muted">—</span>';
        var href = file ? (RAW + file) : (BLOB + "Gazattes.csv");
        return '<a href="' + href + '" title="open dataset file">' + nf(n) + "</a>";
      }
      var f = y.files || {};
      var text = [];
      if (y.ordinary_md) text.push('<a href="' + TREE + 'markdown/ordinary/' + y.year + '/">' + nf(y.ordinary_md) + " ord.</a>");
      if (y.extra_md) text.push('<a href="' + TREE + 'markdown/extraordinary/' + y.year + '/">' + nf(y.extra_md) + " extra</a>");
      return "<tr><td><strong>" + y.year + "</strong></td><td>" + official + "</td>" +
        '<td class="num">' + cell(y.parts, f.parts) + "</td>" +
        '<td class="num">' + cell(y.issues, f.issues) + "</td>" +
        '<td class="num">' + cell(y.extraordinary, f.extraordinary) + "</td>" +
        '<td class="num">' + (text.length ? text.join(" · ") : '<span class="muted">—</span>') + "</td>" +
        "<td>" + (YEAR_NOTES[y.year] || "") + "</td></tr>";
    });
    tbody.innerHTML = rows.join("");
  }

  renderLatestIssues();
  renderPreview();
})();
