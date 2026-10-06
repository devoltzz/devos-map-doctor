// fs_windows.js - 1.6: the Windows rules for paths in Pyodide's file system. The engine was written and measured on
// Windows (and the MPQ, too, is case-insensitive and uses `\`): the site runs it on the browser's POSIX file system and
// emulates the two rules it relies on, so its output is the exe's.
//
//  1. Case: a name keeps the case it was written with, and a lookup that misses with the exact case finds the entry
//     that differs only in case (creating a name that exists in another case finds it, as on Windows). Without it the
//     map extracted `Units\UnitData.slk`, the port asked for `units\unitdata.slk` and built its tables from the game
//     base (w3u mode) instead of the map's SLK.
//  2. Separator: in an absolute path `\` separates folders like `/` (`/tmp/x/Units\UnitData.slk`, a folder joined
//     with a name from the MPQ). Python's side of the same rule is in worker.py (`os.path` with ntpath's splits).
//
// `windowsRules(FS)` wraps `FS.lookupNode` (rule 1) and the FS calls that take a path (rule 2: only the path arguments,
// never the data written; the syscalls reach the file system through these, after an absolute path is kept as is).

const ENOENT = 44;
// the FS calls that take a path, and which arguments are paths
const PATH_ARGS = {
  lookupPath: [0], analyzePath: [0], open: [0], stat: [0], lstat: [0], mkdir: [0], mkdirTree: [0], mknod: [0],
  create: [0], mkdev: [0], rename: [0, 1], rmdir: [0], unlink: [0], readdir: [0], symlink: [0, 1], readlink: [0],
  chmod: [0], lchmod: [0], chown: [0], lchown: [0], truncate: [0], utime: [0], readFile: [0], writeFile: [0],
  chdir: [0], statfs: [0], findObject: [0],
};

const slashes = p => (typeof p === 'string' && p.startsWith('/') && p.includes('\\') ? p.replace(/\\/g, '/') : p);

export function windowsRules(FS) {
  if (FS.lookupNode.windowsRules) return;
  const exact = FS.lookupNode;
  const lookup = function (parent, name) {
    try {
      return exact.call(FS, parent, name);
    } catch (e) {
      if (!e || e.errno !== ENOENT || name === '.' || name === '..') throw e;
      let names;
      try {
        names = parent.node_ops.readdir(parent);
      } catch (e2) {
        throw e;
      }
      const low = name.toLowerCase();
      const hit = names.find(n => n !== name && n.toLowerCase() === low);
      if (hit === undefined) throw e;
      return exact.call(FS, parent, hit);
    }
  };
  lookup.windowsRules = true;
  FS.lookupNode = lookup;
  for (const [name, idx] of Object.entries(PATH_ARGS)) {
    const fn = FS[name];
    if (typeof fn !== 'function') continue;
    FS[name] = function (...args) {
      for (const i of idx) args[i] = slashes(args[i]);
      return fn.apply(FS, args);
    };
  }
}
