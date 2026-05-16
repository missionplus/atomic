// Template: tiny in-memory store for stateful-lite surfaces.
// Process-local. Wiped by POST /__reset.

const store = new Map();   // collection -> Map<key, value>
const seq = new Map();     // name -> integer

function bucket(name) {
  if (!store.has(name)) store.set(name, new Map());
  return store.get(name);
}

export function put(collection, key, value) {
  bucket(collection).set(key, value);
}

export function get(collection, key) {
  return bucket(collection).get(key) ?? null;
}

export function listAll(collection) {
  return Array.from(bucket(collection).values());
}

export function nextSeq(name) {
  const next = (seq.get(name) ?? 0) + 1;
  seq.set(name, next);
  return next;
}

export function reset() {
  store.clear();
  seq.clear();
}
