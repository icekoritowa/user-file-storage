PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY CHECK(id > 0), name TEXT NOT NULL UNIQUE,
 quota INTEGER NOT NULL CHECK(quota >= 0), email TEXT
);
CREATE TABLE IF NOT EXISTS folders (
 id INTEGER PRIMARY KEY CHECK(id > 0), name TEXT NOT NULL,
 owner_id INTEGER NOT NULL REFERENCES users(id), UNIQUE(owner_id, name)
);
CREATE TABLE IF NOT EXISTS files (
 id INTEGER PRIMARY KEY CHECK(id > 0), name TEXT NOT NULL,
 folder_id INTEGER NOT NULL REFERENCES folders(id),
 size INTEGER NOT NULL CHECK(size >= 0), uploaded_at TEXT NOT NULL,
 UNIQUE(folder_id, name)
);
CREATE TABLE IF NOT EXISTS accesses (
 user_id INTEGER NOT NULL REFERENCES users(id),
 folder_id INTEGER NOT NULL REFERENCES folders(id),
 level TEXT NOT NULL CHECK(level IN ('read', 'write')),
 PRIMARY KEY(user_id, folder_id)
);
