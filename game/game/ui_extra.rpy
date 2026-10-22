# 界面与演出扩展

## 章节标题卡
screen chapter_card(num, title):
    zorder 200
    modal True
    add Solid("#0B0E12")
    add Solid("#0B0E12"):
        alpha 0.0
    vbox:
        align (0.5, 0.5)
        spacing 18
        text num:
            xalign 0.5
            font "NotoSansSC-Regular.otf"
            size 26
            color "#C79A4B"
            kerning 4
        text title:
            xalign 0.5
            font "NotoSerifSC-Regular.otf"
            size 62
            color "#E8E4DC"
        text "2018 — 2023　杭州":
            xalign 0.5
            font "NotoSansSC-Regular.otf"
            size 18
            color "#6E7378"
    timer 2.4 action Return()

## 结局卡
screen ending_card():
    zorder 200
    modal True
    add Solid("#080A0C")
    vbox:
        align (0.5, 0.5)
        spacing 20
        text "全文完":
            xalign 0.5
            font "NotoSerifSC-Regular.otf"
            size 54
            color "#E8E4DC"
        text "感谢你陪他跑完这一段。":
            xalign 0.5
            font "NotoSerifSC-Regular.otf"
            size 24
            color "#8A8F96"
    timer 4.0 action Return()

## 立绘位置：缩到 0.82，底部对齐，避免顶部被裁
transform sprite_left:
    xpos 20
    yalign 1.0
    zoom 0.82

transform sprite_right:
    xpos 700
    yalign 1.0
    zoom 0.82


## 章节目录：任意章节直接进入，使用该章的标准入口状态（不依赖前序存档）
screen chapter_list():
    tag menu

    use game_menu(_("Chapters"), scroll="viewport"):
        vbox:
            spacing 6

            text _("跳转会以该章的标准起始状态进入，不会修改你原来的存档。") size 20 color "#A9A49A"

            null height 8

            for cid, num, title, when in CHAPTERS:
                textbutton (num + "　" + title + "　" + when):
                    action Start(cid + "_entry")
                    text_size 24
                    xsize 720
