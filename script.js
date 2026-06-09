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
    if (!toggle) return;
    toggle.checked = document.documentElement.classList.contains('light-mode');
    toggle.addEventListener('change', function () {
      document.documentElement.classList.toggle('light-mode', toggle.checked);
      setTheme(toggle.checked ? 'light' : 'dark');
    });
  });
})();
