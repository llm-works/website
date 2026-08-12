(function () {
  try {
    if (new URLSearchParams(window.location.search).has('reset')) {
      var toClearLocal = [];
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k && k.indexOf('llmw:') === 0) toClearLocal.push(k);
      }
      for (var j = 0; j < toClearLocal.length; j++) localStorage.removeItem(toClearLocal[j]);
      var toClearSession = [];
      for (var s = 0; s < sessionStorage.length; s++) {
        var sk = sessionStorage.key(s);
        if (sk && sk.indexOf('llmw:') === 0) toClearSession.push(sk);
      }
      for (var t = 0; t < toClearSession.length; t++) sessionStorage.removeItem(toClearSession[t]);
      var params = new URLSearchParams(window.location.search);
      params.delete('reset');
      var qs = params.toString();
      history.replaceState(null, '', window.location.pathname + (qs ? '?' + qs : '') + window.location.hash);
    }
  } catch (e) {}

  function getTheme() {
    try { return localStorage.getItem('theme'); } catch (e) { return null; }
  }
  function setTheme(v) {
    try { localStorage.setItem('theme', v); } catch (e) {}
  }
  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  var saved = getTheme();
  var isLight = saved ? saved === 'light' : !systemPrefersDark();
  if (isLight) document.documentElement.classList.add('light-mode');

  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('theme-switch');
    if (toggle) {
      toggle.checked = document.documentElement.classList.contains('light-mode');
      toggle.addEventListener('change', function () {
        document.documentElement.classList.toggle('light-mode', toggle.checked);
        setTheme(toggle.checked ? 'light' : 'dark');
      });
    }

    hydratePypiVersions();
    hydrateReleaseBanner();
  });

  var PACKAGES = ['appinfra', 'llm-saia', 'llm-infer', 'llm-kelt', 'llm-gent'];
  var PYPI_CACHE_TTL_MS = 24 * 60 * 60 * 1000;
  var NEW_WINDOW_MS = 14 * 24 * 60 * 60 * 1000;
  var CACHE_PREFIX = 'llmw:pkg:v2:';
  var DISMISS_KEY = 'llmw:banner-dismissed';

  function readCachedPackage(pkg) {
    try {
      var raw = localStorage.getItem(CACHE_PREFIX + pkg);
      if (!raw) return null;
      var entry = JSON.parse(raw);
      if (!entry || !entry.version || typeof entry.fetchedAt !== 'number') return null;
      if (Date.now() - entry.fetchedAt > PYPI_CACHE_TTL_MS) return null;
      return entry;
    } catch (e) { return null; }
  }

  function writeCachedPackage(pkg, version, uploadedAt) {
    try {
      localStorage.setItem(CACHE_PREFIX + pkg, JSON.stringify({
        version: version,
        uploadedAt: uploadedAt,
        fetchedAt: Date.now()
      }));
    } catch (e) {}
  }

  function extractUploadedAt(data) {
    var version = data && data.info && data.info.version;
    var files = (data && data.urls) || [];
    if ((!files || !files.length) && version && data.releases && data.releases[version]) {
      files = data.releases[version];
    }
    if (!files || !files.length) return null;
    var earliest = null;
    for (var i = 0; i < files.length; i++) {
      var raw = files[i].upload_time_iso_8601 || files[i].upload_time;
      if (!raw) continue;
      var t = Date.parse(raw);
      if (isNaN(t)) continue;
      if (earliest === null || t < earliest) earliest = t;
    }
    return earliest;
  }

  function renderPackage(host, entry) {
    var meta = host.querySelector('.pkg-meta');
    if (!meta) {
      meta = document.createElement('span');
      meta.className = 'pkg-meta';
      host.appendChild(meta);
    }
    var version = meta.querySelector('.pkg-version');
    if (!version) {
      var existing = host.querySelector('.pkg-version');
      if (existing) meta.appendChild(existing);
      version = existing;
    }
    if (!version) {
      version = document.createElement('span');
      version.className = 'pkg-version';
      meta.appendChild(version);
    }
    version.textContent = 'v' + entry.version;

    var isNew = typeof entry.uploadedAt === 'number' &&
                (Date.now() - entry.uploadedAt) < NEW_WINDOW_MS;
    var pill = meta.querySelector('.pkg-new');
    if (isNew && !pill) {
      pill = document.createElement('span');
      pill.className = 'pkg-new';
      pill.textContent = 'new';
      meta.insertBefore(pill, version);
    } else if (!isNew && pill) {
      pill.remove();
    }
  }

  var inflight = {};

  function getPackage(pkg) {
    var cached = readCachedPackage(pkg);
    if (cached) return Promise.resolve(cached);
    if (inflight[pkg]) return inflight[pkg];
    var p = fetch('https://pypi.org/pypi/' + encodeURIComponent(pkg) + '/json')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.info || !data.info.version) return null;
        var entry = {
          version: data.info.version,
          uploadedAt: extractUploadedAt(data)
        };
        writeCachedPackage(pkg, entry.version, entry.uploadedAt);
        return entry;
      })
      .catch(function () { return null; });
    inflight[pkg] = p;
    var cleanup = function () { delete inflight[pkg]; };
    p.then(cleanup, cleanup);
    return p;
  }

  function hydratePypiVersions() {
    var hosts = document.querySelectorAll('[data-package]');
    for (var i = 0; i < hosts.length; i++) {
      (function (host) {
        var pkg = host.getAttribute('data-package');
        if (!pkg) return;
        getPackage(pkg).then(function (entry) {
          if (entry) renderPackage(host, entry);
        });
      })(hosts[i]);
    }
  }

  function readBannerDismissed() {
    try { return localStorage.getItem(DISMISS_KEY); } catch (e) { return null; }
  }
  function writeBannerDismissed(key) {
    try { localStorage.setItem(DISMISS_KEY, key); } catch (e) {}
  }

  function hydrateReleaseBanner() {
    var promises = PACKAGES.map(function (pkg) {
      return getPackage(pkg).then(function (entry) {
        if (!entry) return null;
        return { pkg: pkg, version: entry.version, uploadedAt: entry.uploadedAt };
      });
    });
    Promise.all(promises).then(function (entries) {
      var now = Date.now();
      var recent = entries.filter(function (e) {
        return e && typeof e.uploadedAt === 'number' && (now - e.uploadedAt) < NEW_WINDOW_MS;
      }).sort(function (a, b) { return b.uploadedAt - a.uploadedAt; });

      if (!recent.length) return;

      var key = recent.map(function (e) { return e.pkg + '@' + e.version; }).sort().join(',');
      if (readBannerDismissed() === key) return;

      var banner = document.createElement('div');
      banner.className = 'release-banner';
      banner.setAttribute('role', 'status');
      banner.appendChild(document.createTextNode(
        recent.length === 1
          ? 'New platform lib release: '
          : 'New platform lib releases: '
      ));
      recent.forEach(function (e, idx) {
        if (idx > 0) banner.appendChild(document.createTextNode(', '));
        var link = document.createElement('a');
        link.href = 'https://github.com/llm-works/' + e.pkg;
        link.textContent = e.pkg + ' v' + e.version;
        banner.appendChild(link);
      });

      var btn = document.createElement('button');
      btn.className = 'release-banner-dismiss';
      btn.setAttribute('aria-label', 'Dismiss');
      btn.textContent = '×';
      btn.addEventListener('click', function () {
        window.removeEventListener('resize', syncBannerTop);
        writeBannerDismissed(key);
        banner.remove();
        document.documentElement.classList.remove('has-release-banner');
      });
      banner.appendChild(btn);

      var seen = false;
      try { seen = sessionStorage.getItem('llmw:banner-seen') === '1'; } catch (e) {}
      if (!seen) {
        banner.classList.add('is-fresh');
        try { sessionStorage.setItem('llmw:banner-seen', '1'); } catch (e) {}
      }

      document.documentElement.classList.add('has-release-banner');

      var nav = document.querySelector('nav');
      var syncBannerTop = function () {
        if (!nav) return;
        banner.style.top = nav.offsetHeight + 'px';
      };
      syncBannerTop();

      var skipLink = document.querySelector('.skip-link');
      var anchor = skipLink ? skipLink.nextSibling : document.body.firstChild;
      document.body.insertBefore(banner, anchor);

      window.addEventListener('resize', syncBannerTop);
    });
  }
})();
