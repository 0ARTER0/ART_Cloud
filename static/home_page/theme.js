// Simple theme toggle: saves to localStorage and sets data-theme on :root
(function(){
  const key = 'theme';
  function applyTheme(t){
    if(t === 'light') document.documentElement.setAttribute('data-theme','light');
    else document.documentElement.removeAttribute('data-theme');
  }
  const saved = localStorage.getItem(key) || 'dark';
  applyTheme(saved);

  window.toggleTheme = function(){
    const cur = localStorage.getItem(key) || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    localStorage.setItem(key, next);
    applyTheme(next);
  };
})();
