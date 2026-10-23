# 环境音与现场播报
#
# 三层声音，职责分开：
#   ambience —— 场所底噪（loop）。跟着 scene 走，也可以被 `ambient:` 指令显式改写。
#   pa       —— 店内叫号 / 车站广播 / 收款提示（一次性语音）。
#   sound    —— 原有的 `sfx:` 短事件音（碗筷、门、脚步……）。
#
# 为什么不并进 BGM：BGM 有调性、有情绪走向，环境音描述的是「空间」。
# 混在一条轨上，一换 BGM 就把空间感一起切断了；而且网页版按需下载时，
# 环境音需要比 BGM 更早到位，分轨才好各自调度。

init python:
    # ambience 跟随「音乐」音量滑杆：玩家把音乐关掉时，底噪也该一起安静。
    renpy.music.register_channel("ambience", mixer="music", loop=True)
    renpy.music.register_channel("pa", mixer="sfx", loop=False)

    # 场景 → 默认环境音。scene 语句之后由 gen_game.py 调用 implicit_amb()。
    # 只放"这个场景一定有"的声音，具体剧情点用 `ambient:` 覆盖。
    SCENE_AMB = {
        "bg_room": "room",
        "bg_home": "room",
        "bg_cao": "room",
        "bg_alley": "alley",
        "bg_road": "street",
        "bg_rain": "street",
        "bg_night_street": "street_night",
        "bg_office": "office",
        "bg_station": "depot",
        "bg_station_arrival": "busstation",
        "bg_hospital": "hospital",
        "bg_funeral": "funeral",
        "bg_shop": "shop",
        "bg_market": "wetmarket",
        "bg_ktv": "ktv",
        "bg_river": "riverside",
        "bg_wedding": "banquet",
    }

    # 当前环境音名。同名不重播 —— 一章里 bg_room 会出现十几次，
    # 每次都重放会让底噪每两分钟"抖"一下。
    _amb_current = None

    def amb(name, fade=1.6):
        """切换环境底噪。name=None/'none' 表示淡出。"""
        global _amb_current
        if not name or name == "none":
            if _amb_current is not None:
                renpy.music.stop(channel="ambience", fadeout=fade)
                _amb_current = None
            return
        if name == _amb_current:
            return
        path = "audio/amb/amb_%s.ogg" % name
        if not renpy.loadable(path):
            return
        renpy.music.play(path, channel="ambience", loop=True,
                         fadein=fade, relative_volume=0.75)
        _amb_current = name

    def implicit_amb(scene_name):
        """scene 之后自动套用默认环境音；没有对应项就安静下来。"""
        amb(SCENE_AMB.get(scene_name))

    def pa(name, duck=0.42, hold=4.2):
        """播报一条广播/叫号，同时把环境底噪压下去，播完恢复。

        真实现场里广播比环境音响得多，但玩家同时要读文字，所以这里只压
        环境音、不动 BGM —— 压多了会像突然断音。
        """
        path = "audio/pa/pa_%s.ogg" % name
        if not renpy.loadable(path):
            return
        renpy.sound.play(path, channel="pa")
        renpy.music.set_volume(duck, delay=0.3, channel="ambience")
        renpy.show_screen("_pa_duck", hold)

    def amb_layer_pause(fade=0.4):
        """进菜单、跳章时统一收掉环境音。"""
        amb(None, fade)


screen _pa_duck(sec):
    zorder 200
    timer sec action [Function(renpy.music.set_volume, 1.0, 0.9, "ambience"),
                      Hide("_pa_duck")]


## 章节入口统一清空，避免上一章的环境音漏进新章
label amb_reset:
    $ amb_layer_pause(0.0)
    return
