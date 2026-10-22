# 界面手感：点击热区与点击反馈
#
# 这一版解决的问题：
#   1. 底部快捷菜单的字只有 20px，行高不到 30px，触屏和触控板上都要点两次。
#      这里把热区抬到 ≥ 44px（WCAG 2.5.5 的触摸目标下限）。
#   2. 主菜单按钮只改字色、不改形状，鼠标移上去不明显。这里补一点行内留白，
#      顺手把热区也抬上去。
#
# 关于悬停音效：上一版给 `style button` 全局挂了 hover_sound，结果每个按钮
# （包括对白里每个选项、章节目录 20 行、设置页每一条）在鼠标划过时都要走一次
# Python → mixer 的播放调用。网页版是单线程 wasm，快速划过一串按钮时这些调用
# 排在渲染前面，视觉上的高亮要等音频处理完才出来，玩家感受就是「选中效果有延迟」。
# 现在只保留点击音（activate_sound），划过不再发声，高亮由绘制直接响应。
#
# 注意：这里只用字面量路径，不要引用 init python 里的变量 —— 风格语句与
# init 块的执行顺序不由文件内的书写顺序保证。

style button:
    activate_sound "audio/sfx/ui_select.wav"

## 底部快捷菜单：加高、加宽，行内不再挤在一起
style quick_button:
    xpadding 16
    ypadding 11
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
    activate_sound "audio/sfx/ui_select.wav"
