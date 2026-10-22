# 界面手感：点击热区、悬停与点击反馈
#
# 这一版解决的问题：
#   1. 底部快捷菜单的字只有 20px，行高不到 30px，触屏和触控板上都要点两次。
#      这里把热区抬到 ≥ 44px（WCAG 2.5.5 的触摸目标下限）。
#   2. 点按钮完全没有声音反馈，网页版尤其空。加了两个极轻的合成音：
#      悬停 1.6 kHz 的 46 ms 衰减，点击 760→520 Hz 的 96 ms 下滑。
#      音量压得很低，不抢 BGM。
#   3. 主菜单按钮只改字色、不改形状，鼠标移上去不明显。这里补一点行内留白，
#      顺手把热区也抬上去。
#
# 注意：这里只用字面量路径，不要引用 init python 里的变量 —— 风格语句与
# init 块的执行顺序不由文件内的书写顺序保证。

style button:
    hover_sound "audio/sfx/ui_hover.wav"
    activate_sound "audio/sfx/ui_select.wav"

## 底部快捷菜单：加高、加宽，行内不再挤在一起
style quick_button:
    xpadding 16
    ypadding 11
    hover_sound "audio/sfx/ui_hover.wav"
    activate_sound "audio/sfx/ui_select.wav"

style quick_button_text:
    size 19
    hover_color "#F2EDE4"
    selected_color "#C79A4B"
    insensitive_color "#5A5C60"

## 主菜单：字号不变，靠上下留白把热区做到 ~50px（30 号字本身约 42px 高）
style main_menu_textbutton:
    xpadding 6
    ypadding 5
    hover_sound "audio/sfx/ui_hover.wav"
    activate_sound "audio/sfx/ui_select.wav"
