## 埋点桥：Ren'Py 事件 → 宿主网页 → 采集端
##
## 只在 Web 构建里生效（依赖 emscripten.run_script）；桌面版会静默跳过。
## 事件字段由 tools/gen_game.py 在生成脚本时注入，见 game/game/gen/*.rpy。

init -20 python:
    import json as _ana_json
    import time as _ana_time

    ## 允许上报的事件白名单：新增事件必须在这里登记，避免误传正文内容
    ANA_EVENTS = {
        "run_start", "chapter_enter", "chapter_complete", "chapter_jump",
        "choice_shown", "choice_pick", "ending_enter", "ending_complete",
        "save_ok", "save_fail", "load_ok", "load_fail",
        "skip_on", "auto_on", "mute_on", "voice_fail",
    }

    ## 只允许这些键，防止把整段对白塞进埋点
    ANA_FIELDS = {
        "chapter", "choice", "option", "ending", "from", "to",
        "amount", "reason", "ms", "target",
    }

    ## 最近一次失败原因，便于在游戏内排查（不影响正常游玩）
    ANA_LAST_ERROR = []

    def track(event, **fields):
        if event not in ANA_EVENTS:
            return
        try:
            payload = {"event": event}
            for k, v in fields.items():
                if k in ANA_FIELDS:
                    payload[k] = v
            try:
                payload["run_id"] = getattr(renpy.store, "run_id", "") or ""
            except Exception:
                payload["run_id"] = ""
            payload["t"] = int(_ana_time.time() * 1000)

            raw = _ana_json.dumps(payload, ensure_ascii=False)
            quoted = _ana_json.dumps(raw, ensure_ascii=True)
            # 主线程直接用 window.chaoshiTrack；若运行在 worker 里则 postMessage 给宿主
            js = (
                "(function(){var s=(typeof window!=='undefined')?window"
                ":(typeof self!=='undefined'?self:null);"
                "if(s&&s.chaoshiTrack){s.chaoshiTrack(%s);}"
                "else if(typeof postMessage==='function'){"
                "postMessage({__chaoshi_event:%s});}})()"
            ) % (quoted, quoted)

            import emscripten
            emscripten.run_script(js)
        except Exception as e:
            if len(ANA_LAST_ERROR) < 20:
                ANA_LAST_ERROR.append("%s: %s" % (event, e))

