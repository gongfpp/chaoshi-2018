# 全文阅读：把小说正文单独做成一页
#
# 从主菜单「全文」或游戏内底部快捷栏进来，直接读文字，不播音乐、不出立绘、
# 不写存档 —— 它是阅读器，不是另一条剧情线。
#
# 正文数据在 gen/text_novel.rpy（tools/gen_game.py 从 novel/*.md 生成）。
# 这个文件只管排版，**不要在这里写死任何一句正文**。
#
# 排版口径：
#   · 主线 = 所有选项 flag 取 defs.rpy 的默认值，与「章节目录」跳章的口径一致；
#   · 另一条分支由生成器收进 alts，附在该篇正文之后，标注「岔路」。

init python:
    def tn_entry(nid):
        for e in TEXT_NOVEL:
            if e["id"] == nid:
                return e
        return TEXT_NOVEL[0]

    def tn_position(nid):
        for i, e in enumerate(TEXT_NOVEL):
            if e["id"] == nid:
                return i
        return 0


## 目录 ########################################################################

screen text_novel_index():
    tag menu

    add Solid("#E9E2D4")

    $ total = "%.1f 万字" % (TEXT_NOVEL_TOTAL / 10000.0)

    key "game_menu" action Return()

    text "全文":
        xpos 90
        ypos 40
        font "NotoSerifSC-Regular.otf"
        size 52
        color "#2B2620"

    text "文字版 · 共 [total]　按默认路线排版，另一条岔路附在所属篇章之后":
        xpos 94
        ypos 108
        font "NotoSansSC-Regular.otf"
        size 18
        color "#7A6E5C"

    add Solid("#2B26200F"):
        xpos 90
        ypos 148
        xsize 1100
        ysize 1

    viewport:
        xpos 90
        ypos 164
        xsize 1100
        ysize 448
        scrollbars "vertical"
        mousewheel True
        draggable True
        pagekeys True

        vpgrid:
            cols 2
            spacing 2
            xfill True

            for e in TEXT_NOVEL:
                button:
                    action ShowMenu("text_novel_reader", nid=e["id"])
                    xsize 546
                    ysize 30
                    background None
                    hover_background Solid("#8A6A3C12")
                    xpadding 8

                    hbox:
                        yalign 0.5
                        spacing 10

                        text e["num"]:
                            font "NotoSansSC-Regular.otf"
                            size 17
                            color "#9A8C74"
                            yalign 0.5

                        text e["title"]:
                            font "NotoSerifSC-Regular.otf"
                            size 23
                            color "#2B2620"
                            yalign 0.5

                        if e["time"]:
                            text e["time"]:
                                font "NotoSansSC-Regular.otf"
                                size 15
                                color "#A79B85"
                                yalign 0.5

    textbutton "返回":
        xpos 90
        yalign 0.955
        action Return()
        style "tn_link"

    text "滚轮 / 拖动翻页，Esc 返回":
        xalign 0.96
        yalign 0.955
        font "NotoSansSC-Regular.otf"
        size 15
        color "#A79B85"


## 正文 ########################################################################

screen text_novel_reader(nid="ch01"):
    tag menu

    add Solid("#E9E2D4")

    $ e = tn_entry(nid)
    $ pos = tn_position(nid)
    $ prev_id = TEXT_NOVEL[pos - 1]["id"] if pos > 0 else None
    $ next_id = TEXT_NOVEL[pos + 1]["id"] if pos + 1 < len(TEXT_NOVEL) else None

    key "game_menu" action ShowMenu("text_novel_index")

    ## 顶部：篇名
    text e["num"]:
        xpos 90
        ypos 38
        font "NotoSansSC-Regular.otf"
        size 17
        color "#9A8C74"
        kerning 2

    text e["title"]:
        xpos 90
        ypos 60
        font "NotoSerifSC-Regular.otf"
        size 40
        color "#2B2620"

    hbox:
        xalign 0.965
        ypos 52
        spacing 16

        textbutton "目录" action ShowMenu("text_novel_index") style "tn_link"
        textbutton "关闭" action Return() style "tn_link"

    add Solid("#2B26200F"):
        xpos 90
        ypos 122
        xsize 1100
        ysize 1

    ## 正文
    viewport:
        xpos 170
        ypos 142
        xsize 940
        ysize 462
        scrollbars "vertical"
        mousewheel True
        draggable True
        pagekeys True

        vbox:
            xsize 886
            spacing 15

            for spk, txt, kind in e["paras"]:
                if kind == "say":
                    text ("{color=#8A6A3C}" + spk + "{/color}　　" + txt):
                        font "NotoSerifSC-Regular.otf"
                        size 25
                        line_spacing 13
                        color "#2B2620"
                elif kind == "note":
                    text txt:
                        font "NotoSansSC-Regular.otf"
                        size 18
                        line_spacing 8
                        color "#8E7F66"
                        xoffset 12
                else:
                    text ("　　" + txt):
                        font "NotoSerifSC-Regular.otf"
                        size 25
                        line_spacing 13
                        color "#2B2620"

            for a in e["alts"]:
                null height 24
                text ("—— 岔路 · " + a["label"] + " ——"):
                    xalign 0.5
                    font "NotoSerifSC-Regular.otf"
                    size 19
                    color "#8A6A3C"
                null height 6

                for aspk, atxt, akind in a["paras"]:
                    if akind == "say":
                        text ("{color=#8A6A3C}" + aspk + "{/color}　　" + atxt):
                            font "NotoSerifSC-Regular.otf"
                            size 24
                            line_spacing 12
                            color "#4A4238"
                    elif akind == "note":
                        text atxt:
                            font "NotoSansSC-Regular.otf"
                            size 18
                            line_spacing 8
                            color "#8E7F66"
                            xoffset 12
                    else:
                        text ("　　" + atxt):
                            font "NotoSerifSC-Regular.otf"
                            size 24
                            line_spacing 12
                            color "#4A4238"

            null height 30

    ## 底部：翻篇
    hbox:
        xpos 90
        ypos 620
        spacing 12

        if prev_id:
            textbutton "‹ 上一篇" action ShowMenu("text_novel_reader", nid=prev_id) style "tn_link"
        else:
            text "‹ 上一篇":
                font "NotoSerifSC-Regular.otf"
                size 26
                color "#C2B7A2"
                xoffset 8
                yoffset 3

        if next_id:
            textbutton "下一篇 ›" action ShowMenu("text_novel_reader", nid=next_id) style "tn_link"
        else:
            text "下一篇 ›":
                font "NotoSerifSC-Regular.otf"
                size 26
                color "#C2B7A2"
                xoffset 8
                yoffset 3

    text ("%d / %d" % (pos + 1, len(TEXT_NOVEL))):
        xalign 0.93
        ypos 626
        font "NotoSansSC-Regular.otf"
        size 17
        color "#A79B85"


style tn_link is button:
    background None
    hover_background Solid("#8A6A3C12")
    xpadding 8
    ypadding 3

style tn_link_text is button_text:
    font "NotoSerifSC-Regular.otf"
    size 26
    color "#6B6153"
    hover_color "#8A6A3C"
    insensitive_color "#C2B7A2"
