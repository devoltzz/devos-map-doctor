// The site's Web Worker: Pyodide with the engine, the same jobs as the exe's worker process.
import { loadPyodide } from './pyodide/pyodide.mjs';
import { runWasi } from './wasi_mini.js';
import { windowsRules } from './fs_windows.js';
import { mpqNative } from './mpqcrypt.js';

const ENGINE = '/home/pyodide/engine';
const GAME = '/home/pyodide/game';
const VERSIONS = '/home/pyodide/wc3_versions';
let py = null;
let runJob = null;
let mounts = 0;
let queue = Promise.resolve();

function post(msg, transfer) { self.postMessage(msg, transfer || []); }

async function unpack(url, dir, required) {
  const r = await fetch(url);
  if (!r.ok) {
    if (required) throw new Error(url + ': ' + r.status);
    return false;
  }
  py.unpackArchive(await r.arrayBuffer(), 'zip', { extractDir: dir });
  return true;
}

async function boot() {
  post({ type: 'boot', label: 'Loading Python...' });
  py = await loadPyodide({ indexURL: new URL('pyodide/', import.meta.url).href, stdout: () => {}, stderr: () => {} });
  windowsRules(py.FS);
  post({ type: 'boot', label: 'Loading numpy and Pillow...' });
  await py.loadPackage(['numpy', 'pillow'], { messageCallback: () => {} });
  post({ type: 'boot', label: 'Loading the engine...' });
  await unpack('engine.zip', ENGINE, true);
  if (await unpack('data/game_data.zip', GAME, false)) {
    py.runPython(`import os; os.environ['WC3_GAME'] = os.environ['WC3_JOGO'] = '${GAME}'`);
  }
  if (await unpack('data/wc3_versions.zip', VERSIONS, false)) {
    py.runPython(`import os; os.environ['WC3_VERSOES_DADOS'] = '${VERSIONS}'`);
  }
  const pj = await fetch('pjass.wasm');
  if (pj.ok) {
    const mod = await WebAssembly.compile(await pj.arrayBuffer());
    self.runPjass = (args, files) => runWasi(mod, Array.from(args), files);
  }
  const mc = await fetch('mpqcrypt.wasm');
  if (mc.ok) {
    const native = mpqNative(await mc.arrayBuffer());
    self.mpqDecrypt = native.decrypt;
    if (native.keys) self.mpqKeys = native.keys;
    if (native.huffman) self.mpqHuffman = native.huffman;
    if (native.adpcm) self.mpqAdpcm = native.adpcm;
    if (native.explode) self.mpqExplode = native.explode;
    if (native.encrypt) self.mpqEncrypt = native.encrypt;
    if (native.jpegScan) { self.jpegScan = native.jpegScan; self.jpegWrite = native.jpegWrite; }
  }
  for (const d of ['/maps', '/in', '/out']) py.FS.mkdirTree(d);
  try {
    const idx = 'caches' in self ? await caches.match('names.npz') : null;
    if (idx) py.FS.writeFile(ENGINE + '/names.npz', new Uint8Array(await idx.arrayBuffer()));
  } catch (e) { }
  const glue = await (await fetch('worker.py')).text();
  py.FS.writeFile('/home/pyodide/doctor_worker.py', glue);
  py.runPython('import sys; sys.path.insert(0, "/home/pyodide")');
  const mod = py.pyimport('doctor_worker');
  runJob = mod.run;
  self.zipFolder = mod.zip_folder;
  self.zipFiles = mod.zip_files;
  post({ type: 'ready' });
}

function addFile(path, file) {
  const dir = '/in/' + (mounts++);
  py.FS.mkdirTree(dir);
  py.FS.mount(py.FS.filesystems.WORKERFS, { files: [file] }, dir);
  try { py.FS.unlink(path); } catch (e) { }
  py.FS.mkdirTree(path.slice(0, path.lastIndexOf('/')) || '/');
  py.FS.symlink(dir + '/' + file.name, path);
}

function readFile(rid, path) {
  try {
    let p = path;
    if (py.FS.isDir(py.FS.stat(path).mode)) {
      p = '/out/' + path.split('/').filter(Boolean).pop() + '.zip';
      self.zipFolder(path, p);
    }
    const bytes = py.FS.readFile(p);
    post({ type: 'read', rid, name: p.split('/').pop(), bytes }, [bytes.buffer]);
  } catch (e) {
    post({ type: 'read', rid, error: String(e && e.message || e) });
  }
}

const booted = boot().catch(e => { post({ type: 'boot_failed', message: String(e && e.message || e) }); throw e; });

self.onmessage = ev => {
  const m = ev.data;
  queue = queue.then(() => booted).then(() => {
    if (m.type === 'file') addFile(m.path, m.file);
    else if (m.type === 'read') readFile(m.rid, m.path);
    else if (m.type === 'delete') {
      try { py.FS.unlink(m.path); } catch (e) { }
      post({ type: 'read', rid: m.rid, name: '', bytes: new Uint8Array(0) });
    } else if (m.type === 'zip') {
      try {
        self.zipFiles(py.toPy(m.paths), '/out/' + m.name);
        readFile(m.rid, '/out/' + m.name);
        py.FS.unlink('/out/' + m.name);
      } catch (e) { post({ type: 'read', rid: m.rid, error: String(e && e.message || e) }); }
    } else if (m.type === 'index') return fetch(m.url).then(r => {
      if (!r.ok) throw new Error(m.url + ': ' + r.status);
      return r.arrayBuffer();
    }).then(b => {
      py.FS.writeFile(ENGINE + '/names.npz', new Uint8Array(b));
      post({ type: 'event', event: JSON.stringify({ type: 'index_done' }) });
    }).catch(e => post({ type: 'event', event: JSON.stringify({ type: 'index_failed', message: String(e) }) }));
    else if (m.type === 'job') runJob(JSON.stringify(m.job), s => post({ type: 'event', event: s }));
  }).catch(() => {});
};
