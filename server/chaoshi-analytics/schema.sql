-- 《超时》自部署埋点 —— 事件表
--
-- 与 worker/schema.sql 同一套字段，另加 sec（累计游玩秒数）与 opt（选项短标签），
-- 以及 test（测试流量标记，看板默认排除）。
--
-- 去重口径：sendBeacon 在 pagehide 会重投同一批，(sid, seq) 唯一索引兜住。

CREATE TABLE IF NOT EXISTS events (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  event     TEXT    NOT NULL,
  vid       TEXT,
  sid       TEXT,
  seq       INTEGER,
  run_id    TEXT,
  build     TEXT,
  site      TEXT,
  chapter   TEXT,
  choice    TEXT,
  opt       TEXT,
  ending    TEXT,
  ms        INTEGER,
  sec       INTEGER,
  reason    TEXT,
  ref       TEXT,
  test      INTEGER NOT NULL DEFAULT 0,
  t_client  INTEGER,
  t_server  INTEGER,
  raw       TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_events_sid_seq ON events(sid, seq);
CREATE INDEX IF NOT EXISTS ix_events_event ON events(event);
CREATE INDEX IF NOT EXISTS ix_events_t     ON events(t_server);
CREATE INDEX IF NOT EXISTS ix_events_run   ON events(run_id);
CREATE INDEX IF NOT EXISTS ix_events_ch    ON events(chapter);
CREATE INDEX IF NOT EXISTS ix_events_vid   ON events(vid);
