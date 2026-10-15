document.addEventListener('DOMContentLoaded', function () {
  function syncButtons() {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      button.innerHTML = dark ? '☀ <span>Light mode</span>' : '☾ <span>Dark mode</span>';
      button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
      button.setAttribute('title', dark ? 'Switch to light mode' : 'Switch to dark mode');
    });
  }
  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-theme-toggle]');
    if (!button) return;
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('school-theme', next); } catch (e) {}
    syncButtons();
  });
  syncButtons();
});
