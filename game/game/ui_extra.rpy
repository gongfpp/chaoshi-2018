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

## 账本：把小说里的记账本做成可查看的界面
screen ledger():
    tag menu
    use game_menu(_("账本"), scroll="viewport"):
        vbox:
            spacing 14
            text "杨保祥的账本" font "NotoSerifSC-Regular.otf" size 30 color "#C79A4B"
            null height 8
            grid 2 4:
                xspacing 40
                yspacing 12
                text "存款" size 24 color "#8A8F96"
                text "¥ [qian]" size 26 color "#E8E4DC"
                text "欠款" size 24 color "#8A8F96"
                text "¥ [debt]" size 26 color "#C98A62"
                text "体力" size 24 color "#8A8F96"
                text "[shen] / 10" size 26 color "#E8E4DC"
                text "人情" size 24 color "#8A8F96"
                text "[xin] / 10" size 26 color "#E8E4DC"
            null height 16
            text "他记了五年账。最后一页停在 2021 年 1 月。" size 22 color "#6E7378" italic True

## 快捷菜单加一个“账本”入口
init python:
    config.overlay_screens.append("ledger_button")

screen ledger_button():
    zorder 100
    if quick_menu:
        textbutton "账本":
            style "quick_button"
            xalign 0.99
            yalign 0.005
            action ShowMenu("ledger")


## 立绘位置：缩到 0.82，底部对齐，避免顶部被裁
transform sprite_left:
    xpos 20
    yalign 1.0
    zoom 0.82

transform sprite_right:
    xpos 700
    yalign 1.0
    zoom 0.82
