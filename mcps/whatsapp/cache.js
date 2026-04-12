// cache.js — JSON cache operations for contacts, chats, messages, and tags.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

const DATA_DIR = "C:/Francisco/github-repositories/mcp_servers/mcps/whatsapp";
export const CONTACTS_CACHE = join(DATA_DIR, "contacts.json");
export const CHATS_CACHE = join(DATA_DIR, "chats.json");
export const TAGS_CACHE = join(DATA_DIR, "tags.json");
export const MESSAGES_DIR = join(DATA_DIR, "messages");

const DEFAULT_TAGS = {
  family: { description: "Family members" },
  work: { description: "Work and professional contacts" },
  partner: { description: "Partner" },
  followup: { description: "Follow-ups and things to track" },
};

// ── Low-level cache I/O ───────────────────────────────────────

export function readCache(path) {
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, "utf-8"));
}

export function writeCache(path, data) {
  try {
    writeFileSync(path, JSON.stringify(data, null, 2));
  } catch {}
}

// ── Mention map (number → contact name) ───────────────────────

/** Maps both @c.us phone numbers and @lid internal IDs so mentions resolve
 *  regardless of which form WhatsApp embeds in the message body. */
export function getMentionMap() {
  const map = {};

  const contacts = readCache(CONTACTS_CACHE) || [];
  for (const c of contacts) {
    const name = c.name || c.pushname || null;
    if (!name) continue;
    const num = c.id.split("@")[0];
    if (num && !map[num]) map[num] = name;
    if (c.number && !map[c.number]) map[c.number] = name;
  }

  const chatCache = readCache(CHATS_CACHE);
  if (chatCache?.data) {
    for (const c of chatCache.data) {
      if (!c.name || c.id.endsWith("@g.us") || c.id.endsWith("@broadcast")) continue;
      const num = c.id.split("@")[0];
      if (num && !map[num]) map[num] = c.name;
    }
  }

  return map;
}

// ── Chat / contact resolution ────────────────────────────────

function wordMatch(name, queryWords) {
  if (!name) return false;
  const nameWords = name.toLowerCase().split(/\s+/);
  return queryWords.every((qw) => nameWords.some((nw) => nw === qw));
}

export function resolveContact(query) {
  const q = query.toLowerCase();
  const queryWords = q.split(/\s+/);

  const contacts = readCache(CONTACTS_CACHE);
  if (contacts) {
    const preferCus = (matches) => matches.find((c) => c.id.endsWith("@c.us")) || matches[0];

    const exactAll = contacts.filter(
      (c) => c.name?.toLowerCase() === q || c.pushname?.toLowerCase() === q || c.id === query
    );
    if (exactAll.length > 0) {
      const pick = preferCus(exactAll);
      return { id: pick.id, name: pick.name || pick.pushname || pick.number };
    }

    const wordAll = contacts.filter(
      (c) => wordMatch(c.name, queryWords) || wordMatch(c.pushname, queryWords)
    );
    if (wordAll.length > 0) {
      const pick = preferCus(wordAll);
      return { id: pick.id, name: pick.name || pick.pushname || pick.number };
    }
  }

  const chats = readCache(CHATS_CACHE);
  if (chats?.data) {
    const exact = chats.data.find((c) => c.name?.toLowerCase() === q || c.id === query);
    if (exact) return { id: exact.id, name: exact.name };

    const word = chats.data.find((c) => wordMatch(c.name, queryWords));
    if (word) return { id: word.id, name: word.name };
  }

  return null;
}

/** Partial matches to surface when `resolveContact` finds nothing exact. */
export function findCandidates(query) {
  const words = query.toLowerCase().split(/\s+/);
  const candidates = [];
  const seenIds = new Set();
  const seenNames = new Set();

  function addCandidate(id, name) {
    if (seenIds.has(id) || seenNames.has(name)) return;
    seenIds.add(id);
    seenNames.add(name);
    candidates.push({ id, name });
  }

  const contacts = readCache(CONTACTS_CACHE);
  if (contacts) {
    for (const c of contacts) {
      const nameWords = (c.name || "").toLowerCase().split(/\s+/);
      const pushnameWords = (c.pushname || "").toLowerCase().split(/\s+/);
      const allWords = [...nameWords, ...pushnameWords];
      if (words.some((w) => allWords.some((nw) => nw === w))) {
        addCandidate(c.id, c.name || c.pushname || c.number);
      }
    }
  }

  const chats = readCache(CHATS_CACHE);
  if (chats?.data) {
    for (const c of chats.data) {
      const nameWords = (c.name || "").toLowerCase().split(/\s+/);
      if (words.some((w) => nameWords.some((nw) => nw === w))) {
        addCandidate(c.id, c.name);
      }
    }
  }

  return candidates;
}

// ── Contacts merge ────────────────────────────────────────────

const CONTACT_TRACKED_FIELDS = ["name", "pushname", "number"];

export function mergeContacts(freshContacts) {
  const cached = readCache(CONTACTS_CACHE);
  if (!cached) {
    writeCache(CONTACTS_CACHE, freshContacts);
    return { synced: freshContacts.length, added: freshContacts.length, changed: 0 };
  }

  const cacheIndex = Object.fromEntries(cached.map((c) => [c.id, c]));
  let added = 0;
  let changed = 0;

  const merged = freshContacts.map((fc) => {
    const old = cacheIndex[fc.id];
    if (!old) { added++; return fc; }

    const hasChanged = CONTACT_TRACKED_FIELDS.some((f) => fc[f] !== old[f]);
    if (!hasChanged) {
      if (old.previous) fc.previous = old.previous;
      return fc;
    }

    changed++;
    const snapshot = {};
    for (const f of CONTACT_TRACKED_FIELDS) snapshot[f] = old[f];
    snapshot.changedAt = new Date().toISOString();
    fc.previous = [...(old.previous || []), snapshot];
    return fc;
  });

  writeCache(CONTACTS_CACHE, merged);
  return { synced: merged.length, added, changed };
}

// ── Chats merge ───────────────────────────────────────────────

const CHAT_TRACKED_FIELDS = ["name"];

export function mergeChats(freshChats) {
  const cached = readCache(CHATS_CACHE);
  if (!cached) {
    const result = { lastRefresh: new Date().toISOString(), data: freshChats };
    writeCache(CHATS_CACHE, result);
    return { synced: freshChats.length, added: freshChats.length, changed: 0, updated: 0, updatedChats: [] };
  }

  const cacheIndex = Object.fromEntries(cached.data.map((c) => [c.id, c]));
  let added = 0;
  let changed = 0;
  const updatedChats = [];

  const merged = freshChats.map((fc) => {
    const old = cacheIndex[fc.id];
    if (!old) { added++; return fc; }

    const hasChanged = CHAT_TRACKED_FIELDS.some((f) => fc[f] !== old[f]);
    if (hasChanged) {
      changed++;
      const snapshot = {};
      for (const f of CHAT_TRACKED_FIELDS) snapshot[f] = old[f];
      snapshot.changedAt = new Date().toISOString();
      fc.previous = [...(old.previous || []), snapshot];
    } else {
      if (old.previous) fc.previous = old.previous;
    }

    if (fc.timestamp !== old.timestamp || fc.unreadCount !== old.unreadCount) {
      updatedChats.push({ name: fc.name, id: fc.id, archived: fc.archived, unreadCount: fc.unreadCount });
    }

    return fc;
  });

  const result = { lastRefresh: new Date().toISOString(), data: merged };
  writeCache(CHATS_CACHE, result);
  return { synced: merged.length, added, changed, updated: updatedChats.length, updatedChats };
}

// ── Messages merge ────────────────────────────────────────────

/** Deduplicates by message id so growing-batch syncs can safely overlap. */
export function mergeMessages(chatId, freshMessages) {
  if (!existsSync(MESSAGES_DIR)) mkdirSync(MESSAGES_DIR);
  const filePath = join(MESSAGES_DIR, `${chatId}.json`);
  const existing = readCache(filePath) || [];

  const index = Object.fromEntries(existing.map((m) => [m.id, m]));
  for (const m of freshMessages) index[m.id] = m;
  const merged = Object.values(index).sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  writeCache(filePath, merged);
  return { total: merged.length, added: merged.length - existing.length };
}

// ── Incremental-sync lookups ──────────────────────────────────

export function getNewestCachedMessageTimestamp(chatId) {
  const filePath = join(MESSAGES_DIR, `${chatId}.json`);
  const cached = readCache(filePath);
  if (!cached || cached.length === 0) return null;
  return cached[cached.length - 1].timestamp;
}

export function getCachedChatTimestamp(chatId) {
  const chatCache = readCache(CHATS_CACHE);
  if (!chatCache?.data) return null;
  const chat = chatCache.data.find((c) => c.id === chatId);
  return chat?.timestamp || null;
}

/** Falls back to the raw id when the chat isn't in either cache. */
export function getCachedChatName(chatId) {
  const chatCache = readCache(CHATS_CACHE);
  const chat = chatCache?.data?.find((c) => c.id === chatId);
  if (chat?.name) return chat.name;
  const contacts = readCache(CONTACTS_CACHE) || [];
  const contact = contacts.find((c) => c.id === chatId);
  return contact?.name || contact?.pushname || chatId;
}

// ── Filtered reads ────────────────────────────────────────────

function textMatch(entry, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  if (entry.id === query) return true;
  if (entry.id?.toLowerCase().includes(q)) return true;
  if (entry.name?.toLowerCase().includes(q)) return true;
  if (entry.pushname?.toLowerCase().includes(q)) return true;
  if (entry.number?.includes(query)) return true;

  const qWords = q.split(/\s+/);
  const nameWords = (entry.name || "").toLowerCase().split(/\s+/);
  if (qWords.every((qw) => nameWords.some((nw) => nw === qw))) return true;
  const pushnameWords = (entry.pushname || "").toLowerCase().split(/\s+/);
  if (qWords.every((qw) => pushnameWords.some((nw) => nw === qw))) return true;
  return false;
}

export function listChatsFiltered({ query, since } = {}) {
  const chatCache = readCache(CHATS_CACHE);
  let results = chatCache?.data || [];

  if (query) results = results.filter((c) => textMatch(c, query));

  if (since) {
    const sinceISO = new Date(since).toISOString();
    results = results.filter((c) => c.timestamp && c.timestamp >= sinceISO);
  }

  results.sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
  return results;
}

/** Merges contacts + chats so tagged groups and @lid entries still surface. */
export function listContactsFiltered({ query, tag } = {}) {
  const contacts = readCache(CONTACTS_CACHE) || [];
  const chatCache = readCache(CHATS_CACHE);
  const chats = chatCache?.data || [];
  const tagData = readTags();

  const index = {};
  for (const c of contacts) {
    index[c.id] = { ...c, tags: tagData.contacts[c.id] || [] };
  }
  for (const c of chats) {
    if (index[c.id]) {
      Object.assign(index[c.id], {
        timestamp: c.timestamp,
        unreadCount: c.unreadCount,
        archived: c.archived,
        pinned: c.pinned,
        lastMessage: c.lastMessage,
      });
    } else {
      index[c.id] = { ...c, tags: tagData.contacts[c.id] || [] };
    }
  }

  let results = Object.values(index);

  if (tag) results = results.filter((r) => r.tags.includes(tag));
  if (query) results = results.filter((r) => textMatch(r, query));

  results.sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
  return results;
}

export function readCachedMessages(chatId, since) {
  const filePath = join(MESSAGES_DIR, `${chatId}.json`);
  const cached = readCache(filePath) || [];
  const cutoff = since ? new Date(since) : new Date(Date.now() - 48 * 60 * 60 * 1000);
  return cached.filter((m) => new Date(m.timestamp) >= cutoff);
}

// ── Tags ──────────────────────────────────────────────────────

function readTags() {
  const cached = readCache(TAGS_CACHE);
  if (cached) return cached;
  const fresh = { tags: { ...DEFAULT_TAGS }, contacts: {} };
  writeCache(TAGS_CACHE, fresh);
  return fresh;
}

export function tagContact(contact, tags) {
  const resolved = resolveContact(contact);
  if (!resolved) {
    const words = contact.split(/\s+/);
    if (words.length > 1) {
      const candidates = findCandidates(contact);
      if (candidates.length > 0) return { candidates: candidates.map((c) => c.name), query: contact };
    }
    return { error: `No contact found matching "${contact}".` };
  }

  const data = readTags();
  for (const tag of tags) {
    if (!data.tags[tag]) data.tags[tag] = { description: null };
  }
  const existing = data.contacts[resolved.id] || [];
  const merged = [...new Set([...existing, ...tags])];
  data.contacts[resolved.id] = merged;
  writeCache(TAGS_CACHE, data);
  return { contact: resolved.name, id: resolved.id, tags: merged };
}

export function untagContact(contact, tags) {
  const resolved = resolveContact(contact);
  if (!resolved) return { error: `No contact found matching "${contact}".` };

  const data = readTags();
  const existing = data.contacts[resolved.id] || [];
  const remaining = existing.filter((t) => !tags.includes(t));
  if (remaining.length === 0) delete data.contacts[resolved.id];
  else data.contacts[resolved.id] = remaining;
  writeCache(TAGS_CACHE, data);
  return { contact: resolved.name, id: resolved.id, tags: remaining };
}
