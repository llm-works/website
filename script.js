(function () {
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
  });

  var PYPI_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

  function readCachedVersion(pkg) {
    try {
      var raw = localStorage.getItem('llmw:pypi-version:' + pkg);
      if (!raw) return null;
      var entry = JSON.parse(raw);
      if (!entry || !entry.version || !entry.fetchedAt) return null;
      if (Date.now() - entry.fetchedAt > PYPI_CACHE_TTL_MS) return null;
      return entry.version;
    } catch (e) { return null; }
  }

  function writeCachedVersion(pkg, version) {
    try {
      localStorage.setItem('llmw:pypi-version:' + pkg, JSON.stringify({
        version: version,
        fetchedAt: Date.now()
      }));
    } catch (e) {}
  }

  function renderVersion(host, version) {
    var span = host.querySelector('.pkg-version');
    if (!span) {
      span = document.createElement('span');
      span.className = 'pkg-version';
      span.setAttribute('aria-hidden', 'true');
      host.appendChild(span);
    }
    span.textContent = 'v' + version;
  }

  function hydratePypiVersions() {
    var hosts = document.querySelectorAll('[data-package]');
    for (var i = 0; i < hosts.length; i++) {
      (function (host) {
        var pkg = host.getAttribute('data-package');
        if (!pkg) return;
        var cached = readCachedVersion(pkg);
        if (cached) { renderVersion(host, cached); return; }
        fetch('https://pypi.org/pypi/' + encodeURIComponent(pkg) + '/json')
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (data) {
            if (!data || !data.info || !data.info.version) return;
            writeCachedVersion(pkg, data.info.version);
            renderVersion(host, data.info.version);
          })
          .catch(function () {});
      })(hosts[i]);
    }
  }
})();
