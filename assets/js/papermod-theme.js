(function () {
  var storageKey = 'papermod-theme';
  var root = document.documentElement;

  function getPreferred() {
    var stored = localStorage.getItem(storageKey);
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem(storageKey, theme);
  }

  apply(getPreferred());

  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var current = root.getAttribute('data-theme');
        apply(current === 'dark' ? 'light' : 'dark');
      });
    }

    var topLink = document.getElementById('top-link');
    if (topLink) {
      window.addEventListener('scroll', function () {
        if (window.scrollY > 200) {
          topLink.classList.remove('hidden');
        } else {
          topLink.classList.add('hidden');
        }
      });
    }
  });
})();
