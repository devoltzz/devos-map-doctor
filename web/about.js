// The About page: the version and the repository link from config.js.
'use strict';
(() => {
  const c = window.DOCTOR_WEB || {};
  document.getElementById('version').textContent = c.version ? 'v' + c.version : '';
  if (c.repository) {
    const p = document.getElementById('repo');
    const a = document.createElement('a');
    a.href = 'https://github.com/' + c.repository;
    a.textContent = 'github.com/' + c.repository;
    a.rel = 'noopener';
    p.textContent = 'The source code and the Windows program: ';
    p.appendChild(a);
    p.appendChild(document.createTextNode('.'));
  }
})();
