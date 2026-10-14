// The 3D preview of a model (the Files tab): the war3-model renderer, orbit by mouse.
(function () {
  'use strict';

  var script = document.currentScript;
  var base = script && script.src ? script.src.replace(/[^\/]*([?#].*)?$/, '') : '';
  var Model3D = {
    libUrl: base + 'vendor/war3-model.browser.js',
    t: function (s) { return s; },
    supported: supported,
    show: show
  };
  var loading = null;
  var FOV = Math.PI / 4;

  function tr(s) { try { return Model3D.t(s) || s; } catch (e) { return s; } }

  function supported() {
    try {
      var c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl'));
    } catch (e) {
      return false;
    }
  }

  function loadLib() {
    if (window.war3model) return Promise.resolve(window.war3model);
    if (!loading) {
      loading = new Promise(function (resolve, reject) {
        var s = document.createElement('script');
        s.src = Model3D.libUrl;
        s.onload = function () { window.war3model ? resolve(window.war3model) : reject(new Error('the 3D library did not start')); };
        s.onerror = function () { loading = null; reject(new Error('the 3D library could not be loaded')); };
        document.head.appendChild(s);
      });
    }
    return loading;
  }

  function bytesOf(x) {
    if (typeof x === 'string') {
      var bin = atob(x), out = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
      return out;
    }
    if (x instanceof ArrayBuffer) return new Uint8Array(x);
    if (x && x.buffer instanceof ArrayBuffer) return new Uint8Array(x.buffer, x.byteOffset, x.byteLength);
    throw new Error('no model data');
  }

  function versionOf(x) {
    try {
      var d = bytesOf(x);
      if (d.length > 16 && String.fromCharCode(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]) === 'MDLXVERS') {
        return d[12] | d[13] << 8 | d[14] << 16 | d[15] << 24;
      }
    } catch (e) { }
    return 0;
  }

  function norm(p) { return String(p || '').replace(/\//g, '\\').replace(/^\\+/, '').toLowerCase(); }
  function baseOf(p) { return norm(p).split('\\').pop(); }

  function perspective(fovy, aspect, near, far) {
    var f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far), o = new Float32Array(16);
    o[0] = f / aspect; o[5] = f; o[10] = (far + near) * nf; o[11] = -1; o[14] = 2 * far * near * nf;
    return o;
  }
  function norm3(v) {
    var l = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) || 1;
    return [v[0] / l, v[1] / l, v[2] / l];
  }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function lookAt(eye, c, up) {
    var z = norm3([eye[0] - c[0], eye[1] - c[1], eye[2] - c[2]]);
    var x = norm3(cross(up, z)), y = cross(z, x), o = new Float32Array(16);
    o[0] = x[0]; o[1] = y[0]; o[2] = z[0];
    o[4] = x[1]; o[5] = y[1]; o[6] = z[1];
    o[8] = x[2]; o[9] = y[2]; o[10] = z[2];
    o[12] = -(x[0] * eye[0] + x[1] * eye[1] + x[2] * eye[2]);
    o[13] = -(y[0] * eye[0] + y[1] * eye[1] + y[2] * eye[2]);
    o[14] = -(z[0] * eye[0] + z[1] * eye[1] + z[2] * eye[2]);
    o[15] = 1;
    return o;
  }
  function rotationTo(a, b) {
    var d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2], t;
    if (d < -0.999999) {
      t = cross([1, 0, 0], a);
      if (Math.sqrt(t[0] * t[0] + t[1] * t[1] + t[2] * t[2]) < 1e-6) t = cross([0, 1, 0], a);
      t = norm3(t);
      return [t[0], t[1], t[2], 0];
    }
    if (d > 0.999999) return [0, 0, 0, 1];
    t = cross(a, b);
    var q = [t[0], t[1], t[2], 1 + d], l = Math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
    return [q[0] / l, q[1] / l, q[2] / l, q[3] / l];
  }
  function qmul(a, b) {
    return [a[0] * b[3] + a[3] * b[0] + a[1] * b[2] - a[2] * b[1],
            a[1] * b[3] + a[3] * b[1] + a[2] * b[0] - a[0] * b[2],
            a[2] * b[3] + a[3] * b[2] + a[0] * b[1] - a[1] * b[0],
            a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]];
  }

  function bounds(model) {
    var lo = [1e30, 1e30, 1e30], hi = [-1e30, -1e30, -1e30], n = 0;
    (model.Geosets || []).forEach(function (g) {
      var v = g.Vertices;
      if (!v) return;
      for (var i = 0; i + 2 < v.length; i += 3) {
        if (!isFinite(v[i]) || !isFinite(v[i + 1]) || !isFinite(v[i + 2])) continue;
        n++;
        for (var k = 0; k < 3; k++) { if (v[i + k] < lo[k]) lo[k] = v[i + k]; if (v[i + k] > hi[k]) hi[k] = v[i + k]; }
      }
    });
    if (!n) {
      var a = model.Info && model.Info.MinimumExtent, b = model.Info && model.Info.MaximumExtent;
      if (a && b && (a[0] || a[1] || a[2] || b[0] || b[1] || b[2])) { lo = [a[0], a[1], a[2]]; hi = [b[0], b[1], b[2]]; }
      else { lo = [-50, -50, 0]; hi = [50, 50, 100]; }
    }
    var c = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
    var r = Math.sqrt(Math.pow(hi[0] - lo[0], 2) + Math.pow(hi[1] - lo[1], 2) + Math.pow(hi[2] - lo[2], 2)) / 2;
    return { center: c, radius: Math.max(r, 5), zmin: lo[2], zmax: hi[2] };
  }

  function imageOf(t) {
    if (t.rgba && t.width && t.height) {
      var px = t.rgba instanceof Uint8Array || t.rgba instanceof Uint8ClampedArray ? t.rgba : bytesOf(t.rgba);
      if (px.length < t.width * t.height * 4) return Promise.reject(new Error('texture too short'));
      var c = document.createElement('canvas');
      c.width = t.width; c.height = t.height;
      c.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(px.buffer.slice(px.byteOffset, px.byteOffset + t.width * t.height * 4)), t.width, t.height), 0, 0);
      return Promise.resolve(c);
    }
    if (t.data) {
      return new Promise(function (ok, bad) {
        var im = new Image();
        im.onload = function () { ok(im); };
        im.onerror = function () { bad(new Error('texture not readable')); };
        im.src = 'data:' + (t.mime || 'image/png') + ';base64,' + t.data;
      });
    }
    return Promise.reject(new Error('empty texture'));
  }

  function message(canvas, text) {
    var box = document.createElement('div');
    box.className = 'model3d-msg';
    box.style.cssText = 'padding:24px 12px;text-align:center;opacity:.8;font-size:13px';
    box.textContent = text;
    canvas.style.display = 'none';
    canvas.parentNode.insertBefore(box, canvas.nextSibling);
    return box;
  }

  function show(canvas, mdx, textures, options) {
    options = options || {};
    var failure = null, box = null, dead = false, raf = 0, gl = null, renderer = null, model = null;
    var ctl = { sequences: [], sequence: 0, error: null, setSequence: function () {}, setTeamColor: function () {},
                resetView: function () {}, destroy: destroy };

    function fail(text) {
      ctl.error = text;
      if (!box && canvas.parentNode) box = message(canvas, text);
      return ctl;
    }
    function destroy() {
      dead = true;
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      try { if (renderer && renderer.destroy) renderer.destroy(); } catch (e) { }
      renderer = null;
      listeners.forEach(function (l) { l[0].removeEventListener(l[1], l[2], l[3]); });
      listeners = [];
      if (box && box.parentNode) box.parentNode.removeChild(box);
      box = null;
      canvas.style.display = '';
    }
    var listeners = [];
    function on(target, type, fn, opts) { target.addEventListener(type, fn, opts); listeners.push([target, type, fn, opts]); }

    if (!supported()) return Promise.resolve(fail(tr('The 3D preview needs WebGL, and this browser has none.')));
    return loadLib().then(function (lib) {
      if (dead) return ctl;
      try {
        var data = bytesOf(mdx);
        var isMdx = data.length > 4 && String.fromCharCode(data[0], data[1], data[2], data[3]) === 'MDLX';
        model = isMdx ? lib.parseMDX(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength))
                      : lib.parseMDL(new TextDecoder('utf-8').decode(data));
      } catch (e) {
        var v = versionOf(mdx);
        if (v > 1100) return fail(tr('This model is version %d; the 3D preview draws versions 800 to 1100.').replace('%d', v));
        return fail(tr('This model cannot be shown in 3D') + ' (' + (e && e.message ? e.message : '?') + ').');
      }
      if (!model.Geosets || !model.Geosets.length) return fail(tr('This model has no geometry to show.'));
      var lookup = {}, byBase = {};
      Object.keys(textures || {}).forEach(function (k) { lookup[norm(k)] = textures[k]; byBase[baseOf(k)] = textures[k]; });
      var wanted = [];
      (model.Textures || []).forEach(function (t) {
        if (!t.Image) return;
        var src = lookup[norm(t.Image)] || byBase[baseOf(t.Image)];
        if (src) wanted.push([t.Image, src]);
      });
      return Promise.all(wanted.map(function (w) {
        return imageOf(w[1]).then(function (img) { return [w[0], img]; }, function () { return null; });
      })).then(function (images) {
        if (dead) return ctl;
        var opts = { antialias: true, alpha: false, preserveDrawingBuffer: false };
        gl = canvas.getContext('webgl2', opts) || canvas.getContext('webgl', opts);
        if (!gl) return fail(tr('The 3D preview needs WebGL, and this browser has none.'));
        var bg = options.background || [0.15, 0.15, 0.15];
        gl.clearColor(bg[0], bg[1], bg[2], 1);
        gl.enable(gl.DEPTH_TEST);
        gl.depthFunc(gl.LEQUAL);
        try {
          renderer = new lib.ModelRenderer(model);
          renderer.setTeamColor(new Float32Array(options.teamColor || [0.7, 0.7, 0.7]));
          renderer.initGL(gl);
          images.forEach(function (im) { if (im) renderer.setTextureImage(im[0], im[1]); });
        } catch (e) {
          return fail(tr('The 3D preview could not start') + ' (' + (e && e.message ? e.message : 'WebGL') + ').');
        }

        var seqs = model.Sequences || [];
        ctl.sequences = seqs.map(function (s) { return s.Name; });
        var cur = 0;
        if (typeof options.sequence === 'number') cur = options.sequence;
        else {
          var i = ctl.sequences.findIndex(function (n) { return /^stand\b/i.test(n); });
          cur = i >= 0 ? i : 0;
        }
        function setSeq(i) {
          if (!seqs.length || i < 0 || i >= seqs.length) return;
          cur = ctl.sequence = i;
          renderer.setSequence(i);
        }
        setSeq(cur);
        ctl.setSequence = setSeq;
        ctl.setTeamColor = function (c) { renderer.setTeamColor(new Float32Array(c)); };

        var bb = bounds(model);
        var view = { theta: Math.PI / 6, phi: Math.PI / 4, dist: 0, tz: 0 };
        function reset() {
          view.theta = Math.PI / 6; view.phi = Math.PI / 4;
          view.dist = bb.radius / Math.sin(FOV / 2) * 1.05;
          view.tz = 0;
        }
        reset();
        ctl.resetView = reset;

        var drag = null, pinch = 0;
        function down(e) {
          if (e.pointerType === 'touch' || e.button === 0 || e.button === 1 || e.button === 2) {
            drag = { x: e.clientX, y: e.clientY, pan: e.button === 1 || e.button === 2 };
            try { canvas.setPointerCapture(e.pointerId); } catch (x) { }
            e.preventDefault();
          }
        }
        function move(e) {
          if (!drag) return;
          var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
          drag.x = e.clientX; drag.y = e.clientY;
          if (drag.pan) {
            view.tz = Math.max(bb.zmin - bb.center[2], Math.min(bb.zmax - bb.center[2], view.tz + dy * bb.radius * 0.004));
          } else {
            view.phi -= dx * 0.01;
            view.theta = Math.max(-1.5, Math.min(1.5, view.theta + dy * 0.01));
          }
        }
        function up() { drag = null; }
        function zoom(f) { view.dist = Math.max(bb.radius * 0.4, Math.min(bb.radius * 12, view.dist * f)); }
        on(canvas, 'pointerdown', down);
        on(canvas, 'pointermove', move);
        on(canvas, 'pointerup', up);
        on(canvas, 'pointercancel', up);
        on(canvas, 'contextmenu', function (e) { e.preventDefault(); });
        on(canvas, 'dblclick', reset);
        on(canvas, 'wheel', function (e) { e.preventDefault(); zoom(Math.exp(e.deltaY * 0.001)); }, { passive: false });
        on(canvas, 'touchstart', function (e) { if (e.touches.length === 2) pinch = touchDist(e); }, { passive: true });
        on(canvas, 'touchmove', function (e) {
          if (e.touches.length === 2 && pinch) { var d = touchDist(e); zoom(pinch / d); pinch = d; e.preventDefault(); }
        }, { passive: false });
        function touchDist(e) {
          return Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY) || 1;
        }
        on(canvas, 'webglcontextlost', function (e) { e.preventDefault(); if (raf) cancelAnimationFrame(raf); raf = 0; fail(tr('The 3D preview lost its WebGL context.')); });

        var last = 0;
        function frame(now) {
          raf = 0;
          if (dead) return;
          if (!canvas.isConnected) { destroy(); return; }
          raf = requestAnimationFrame(frame);
          if (document.hidden || !canvas.clientWidth || !canvas.clientHeight) { last = 0; return; }
          var dpr = window.devicePixelRatio || 1;
          var w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
          if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
          var dt = last ? Math.min(now - last, 100) : 0;
          last = now;
          try {
            renderer.update(dt);
            var s = seqs[cur];
            if (s && s.NonLooping && renderer.getFrame() >= s.Interval[1]) renderer.setFrame(s.Interval[0]);
            var target = [bb.center[0], bb.center[1], bb.center[2] + view.tz];
            var pos = [target[0] + Math.cos(view.theta) * Math.cos(view.phi) * view.dist,
                       target[1] + Math.cos(view.theta) * Math.sin(view.phi) * view.dist,
                       target[2] + Math.sin(view.theta) * view.dist];
            var rel = [pos[0] - target[0], pos[1] - target[1], pos[2] - target[2]];
            var flat = norm3([rel[0], rel[1], 0]), dir = norm3(rel);
            var q = qmul(rotationTo(flat, dir), rotationTo([1, 0, 0], flat));
            var mv = lookAt(pos, target, [0, 0, 1]);
            var pr = perspective(FOV, w / h, Math.max(bb.radius * 0.02, 0.1), bb.radius * 60);
            gl.viewport(0, 0, w, h);
            gl.depthMask(true);
            gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
            var light = [pos[0] + bb.radius, pos[1] + bb.radius, pos[2] + bb.radius * 2];
            renderer.setLightPosition(new Float32Array(light));
            renderer.setLightColor(new Float32Array([1, 1, 1]));
            renderer.setCamera(new Float32Array(pos), new Float32Array(q));
            renderer.render(mv, pr, {});
          } catch (e) {
            if (raf) cancelAnimationFrame(raf);
            raf = 0;
            fail(tr('The 3D preview stopped') + ' (' + (e && e.message ? e.message : 'WebGL') + ').');
          }
        }
        raf = requestAnimationFrame(frame);
        return ctl;
      });
    }).catch(function (e) {
      return fail(tr('The 3D preview could not start') + ' (' + (e && e.message ? e.message : '?') + ').');
    });
  }

  window.Model3D = Model3D;
})();
