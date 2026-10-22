-- 《超时》埋点事件表
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
  reason    TEXT,
  ref       TEXT,
  test      INTEGER NOT NULL DEFAULT 0,
  t_client  INTEGER,
  t_server  INTEGER,
  raw       TEXT
);

-- sendBeacon 在 pagehide 会重发同一批，用 (sid, seq) 去重
CREATE UNIQUE INDEX IF NOT EXISTS ux_events_sid_seq ON events(sid, seq);
CREATE INDEX IF NOT EXISTS ix_events_event ON events(event);
CREATE INDEX IF NOT EXISTS ix_events_site  ON events(site);
CREATE INDEX IF NOT EXISTS ix_events_t     ON events(t_server);
CREATE INDEX IF NOT EXISTS ix_events_run   ON events(run_id);
CREATE INDEX IF NOT EXISTS ix_events_ch    ON events(chapter);
