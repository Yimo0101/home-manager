# -*- coding: utf-8 -*-
"""居家管家 - 多语言（简体中文 / 日本語 / English）与可爱字体

界面文案统一走 t("key")；语言切换后由 ui_main 重建整个界面即时生效。
字体：中文用幼圆、日文用 UD デジタル教科書体、英文用 Comic Sans MS（均为本机已装字体）。
"""
import os
import tkinter as tk
import tkinter.font as tkfont

LANGS = [("zh", "简体中文"), ("ja", "日本語"), ("en", "English")]
DEFAULT_LANG = "zh"

_state = {"lang": DEFAULT_LANG, "families": None}

# 各语言 Tk 字体（按优先级自动挑本机可用的）
FONT_CANDIDATES = {
    "zh": ["幼圆", "YouYuan", "Microsoft YaHei UI"],
    "ja": ["UD Digi Kyokasho N", "Meiryo", "Yu Gothic UI", "Microsoft YaHei UI"],
    "en": ["Comic Sans MS", "Segoe UI", "Microsoft YaHei UI"],
}

# 各语言 PIL 字体（用于全屏弹窗绘制）
PIL_FONT_PATHS = {
    "zh": {"r": r"C:\Windows\Fonts\SIMYOU.TTF", "b": r"C:\Windows\Fonts\SIMYOU.TTF"},
    "ja": {"r": r"C:\Windows\Fonts\UDDigiKyokashoN-R.ttc",
           "b": r"C:\Windows\Fonts\UDDigiKyokashoN-B.ttc"},
    "en": {"r": r"C:\Windows\Fonts\comic.ttf", "b": r"C:\Windows\Fonts\comicbd.ttf"},
}

WEEKDAY_SHORT = {
    "zh": ["一", "二", "三", "四", "五", "六", "日"],
    "ja": ["月", "火", "水", "木", "金", "土", "日"],
    "en": ["M", "T", "W", "T", "F", "S", "S"],
}
WEEKDAY_FULL = {
    "zh": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    "ja": ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
MONTH_EN = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"]
MONTH_EN_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def set_lang(lang):
    if lang in dict(LANGS):
        _state["lang"] = lang


def get_lang():
    return _state["lang"]


def init_fonts(root=None):
    """在主 Tk() 创建后调用，探测可用字体族"""
    if root is None:
        root = tk._default_root
    try:
        _state["families"] = set(tkfont.families(root))
    except Exception:
        _state["families"] = set()


def family(lang=None):
    lang = lang or _state["lang"]
    fams = _state["families"] or set()
    for cand in FONT_CANDIDATES[lang]:
        if cand in fams:
            return cand
    return FONT_CANDIDATES[lang][-1]


def F(size, bold=False, lang=None):
    """Tk 字体元组，供所有界面控件使用"""
    return (family(lang), size, "bold" if bold else "normal")


def pil_font(size, bold=False, lang=None):
    """PIL 绘制用字体（全屏弹窗），失败回退默认"""
    from PIL import ImageFont
    lang = lang or _state["lang"]
    key = "b" if bold else "r"
    paths = PIL_FONT_PATHS.get(lang, PIL_FONT_PATHS["zh"])
    path = paths[key]
    fallback = PIL_FONT_PATHS["zh"][key]
    for p in (path, fallback):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---------------- 词条 ----------------
TR = {
    # 品牌 / 导航
    "brand": {"zh": "居家管家", "ja": "居家管家", "en": "Home Manager"},
    "tagline": {"zh": "今天也要元气满满哦♪", "ja": "今日もげんきいっぱい♪",
                "en": "Have a lovely day♪"},
    "nav_alarms": {"zh": "闹钟", "ja": "アラーム", "en": "Alarms"},
    "nav_tasks": {"zh": "定时任务", "ja": "タスク", "en": "Tasks"},
    "nav_calendar": {"zh": "日历日程", "ja": "カレンダー", "en": "Calendar"},
    "nav_settings": {"zh": "设置", "ja": "設定", "en": "Settings"},
    "sidebar_hint": {
        "zh": "后台运行中，关闭窗口将最小化到托盘",
        "ja": "バックグラウンド実行中。閉じるとトレイへ",
        "en": "Runs in background; close hides to tray"},

    # 通用
    "ok": {"zh": "确定", "ja": "OK", "en": "OK"},
    "cancel": {"zh": "取消", "ja": "キャンセル", "en": "Cancel"},
    "confirm": {"zh": "确认", "ja": "確認", "en": "Confirm"},
    "tip": {"zh": "提示", "ja": "お知らせ", "en": "Notice"},
    "edit": {"zh": "编辑", "ja": "編集", "en": "Edit"},
    "delete": {"zh": "删除", "ja": "削除", "en": "Delete"},
    "select": {"zh": "选择", "ja": "選択", "en": "Select"},
    "preview": {"zh": "试听", "ja": "試聴", "en": "Preview"},
    "stop": {"zh": "停止", "ja": "停止", "en": "Stop"},
    "reset_builtin": {"zh": "恢复自带", "ja": "標準に戻す", "en": "Reset"},
    "builtin_ring": {"zh": "程序自带铃声", "ja": "標準の着信音", "en": "Built-in ringtone"},
    "default_ring": {"zh": "默认铃声", "ja": "デフォルト", "en": "Default ringtone"},
    "default_bg_text": {"zh": "默认背景", "ja": "デフォルト背景", "en": "Default bg"},
    "every_day": {"zh": "每天", "ja": "毎日", "en": "Every day"},
    "workday": {"zh": "工作日", "ja": "平日", "en": "Weekdays"},
    "weekend": {"zh": "周末", "ja": "週末", "en": "Weekend"},
    "once": {"zh": "仅一次", "ja": "1回だけ", "en": "Once"},
    "all_day": {"zh": "全天", "ja": "終日", "en": "All day"},
    "minutes": {"zh": "%d 分钟", "ja": "%d 分", "en": "%d min"},
    "seconds": {"zh": "%d 秒", "ja": "%d 秒", "en": "%d sec"},
    "audio_files": {"zh": "音频文件", "ja": "オーディオファイル", "en": "Audio files"},
    "image_files": {"zh": "图片文件", "ja": "画像ファイル", "en": "Image files"},
    "all_files": {"zh": "所有文件", "ja": "すべてのファイル", "en": "All files"},

    # 闹钟页
    "alarms_title": {"zh": "闹钟", "ja": "アラーム", "en": "Alarms"},
    "alarms_sub": {
        "zh": "到点全屏响铃，支持自定义铃声与背景图",
        "ja": "時刻に全画面でお知らせ。着信音と背景をカスタマイズ",
        "en": "Full-screen alarms with your own ringtone & picture"},
    "add_alarm": {"zh": "＋ 添加闹钟", "ja": "＋ アラーム追加", "en": "+ Add alarm"},
    "no_alarms": {
        "zh": "还没有闹钟，点右上角“添加闹钟”吧♡",
        "ja": "アラームがありません。右上の「アラーム追加」を押してね♡",
        "en": "No alarms yet — tap \"Add alarm\" ♡"},
    "del_alarm_confirm": {
        "zh": "删除闹钟“%s”？", "ja": "アラーム「%s」を削除しますか？",
        "en": "Delete alarm \"%s\"?"},

    # 任务页
    "tasks_title": {"zh": "定时任务", "ja": "タスク", "en": "Tasks"},
    "tasks_sub": {
        "zh": "定时提醒（如吃药）、定时打开程序并自动点击",
        "ja": "定時リマインド（お薬など）・プログラム起動と自動クリック",
        "en": "Reminders (e.g. medicine) & scheduled app auto-click"},
    "add_reminder": {"zh": "＋ 添加提醒", "ja": "＋ リマインド追加", "en": "+ Add reminder"},
    "add_program": {"zh": "＋ 定时打开程序", "ja": "＋ アプリ起動", "en": "+ Launch app"},
    "no_tasks": {"zh": "还没有定时任务♡", "ja": "タスクがありません♡",
                 "en": "No tasks yet ♡"},
    "tag_program": {"zh": "打开程序", "ja": "アプリ起動", "en": "Launch app"},
    "tag_reminder": {"zh": "提醒", "ja": "リマインド", "en": "Reminder"},
    "once_date": {"zh": "仅一次 · %s", "ja": "1回のみ · %s", "en": "Once · %s"},
    "no_exe": {"zh": "未选择程序", "ja": "アプリ未選択", "en": "No app selected"},
    "n_clicks": {"zh": "（%d 个自动点击）", "ja": "（自動クリック%d件）",
                 "en": "(%d auto-clicks)"},
    "del_task_confirm": {"zh": "删除任务“%s”？", "ja": "タスク「%s」を削除しますか？",
                         "en": "Delete task \"%s\"?"},

    # 日历页
    "today_btn": {"zh": "今天", "ja": "今日", "en": "Today"},
    "add_event": {"zh": "＋ 添加日程", "ja": "＋ 予定追加", "en": "+ Add event"},
    "today_suf": {"zh": " · 今天", "ja": " · 今日", "en": " · Today"},
    "tomorrow_suf": {"zh": " · 明天", "ja": " · 明日", "en": " · Tomorrow"},
    "no_events": {"zh": "当天暂无日程♡", "ja": "この日の予定はありません♡",
                  "en": "No events this day ♡"},
    "cell_allday": {"zh": "全天 ", "ja": "終日 ", "en": ""},
    "more_n": {"zh": "还有 %d 条…", "ja": "他 %d 件…", "en": "+%d more"},
    "edit_short": {"zh": "改", "ja": "編", "en": "Edit"},
    "del_short": {"zh": "删", "ja": "削", "en": "Del"},
    "del_event_confirm": {"zh": "删除日程“%s”？", "ja": "予定「%s」を削除しますか？",
                          "en": "Delete event \"%s\"?"},

    # 设置页
    "settings_title": {"zh": "设置", "ja": "設定", "en": "Settings"},
    "card_language": {"zh": "界面语言", "ja": "表示言語", "en": "Language"},
    "language_hint": {
        "zh": "切换后整个界面立即变成所选语言（你的闹钟和日程不受影响）",
        "ja": "切り替えると画面全体が選択した言語になります（アラームと予定はそのまま）",
        "en": "The whole interface switches instantly (your alarms & events stay)"},
    "card_startup": {"zh": "启动与后台", "ja": "起動とバックグラウンド",
                     "en": "Startup & background"},
    "autostart": {"zh": "开机后自动启动居家管家", "ja": "Windows ログイン後に自動起動",
                  "en": "Launch Home Manager at Windows startup"},
    "autostart_desc": {
        "zh": "登录 Windows 后程序自动在后台运行，闹钟与定时任务才会生效。",
        "ja": "ログイン後にバックグラウンドで自動実行され、アラームとタスクが動きます。",
        "en": "Runs in the background after sign-in so alarms and tasks work."},
    "set_failed": {"zh": "设置失败", "ja": "設定に失敗", "en": "Settings failed"},
    "autostart_fail": {"zh": "无法修改开机启动：%s", "ja": "自動起動を変更できません：%s",
                       "en": "Cannot change startup: %s"},
    "card_wake": {"zh": "定时唤醒电脑", "ja": "PC の自動起床", "en": "Wake PC from sleep"},
    "wake_row": {
        "zh": "闹钟 / 任务到点前，自动把电脑从睡眠中唤醒",
        "ja": "アラーム / タスクの前に PC をスリープから復帰",
        "en": "Wake the PC from sleep before alarms / tasks"},
    "wake_checking": {"zh": "系统唤醒支持：检测中…", "ja": "ウェイクタイマー：確認中…",
                      "en": "Wake timers: checking…"},
    "enable_wake_btn": {"zh": "一键开启系统唤醒支持（弹 UAC）",
                        "ja": "ワンクリックで有効化（UAC）",
                        "en": "Enable wake timers (UAC)"},
    "wake_desc": {
        "zh": "说明：电脑处于「睡眠 / 休眠」时可被自动唤醒；若电脑是「完全关机」状态，"
              "任何软件都无法开机，需要在主板 BIOS 中开启 RTC 闹钟（见使用说明）。",
        "ja": "説明：「スリープ / 休止」からは自動復帰できます。「完全シャットダウン」からは、"
              "ソフトでは起動できません。BIOS の RTC アラームを設定してください（説明書参照）。",
        "en": "Note: the PC can wake from Sleep / Hibernate. No software can power on a "
              "fully shut-down PC — set an RTC alarm in the motherboard BIOS (see the guide)."},
    "wake_ahead": {"zh": "提前唤醒时间", "ja": "事前復帰時間", "en": "Wake ahead time"},
    "wake_unknown": {
        "zh": "系统唤醒支持：未知（可尝试点右侧按钮开启）",
        "ja": "ウェイクタイマー：不明（右のボタンで有効化を試せます）",
        "en": "Wake timers: unknown (try the button on the right)"},
    "wake_status": {
        "zh": "系统唤醒支持：%s（接通电源 %s / 用电池 %s）",
        "ja": "ウェイクタイマー：%s（AC %s / バッテリ %s）",
        "en": "Wake timers: %s (AC %s / Battery %s)"},
    "wake_on": {"zh": "已开启", "ja": "有効", "en": "On"},
    "wake_off": {"zh": "未开启", "ja": "無効", "en": "Off"},
    "wake_allow": {"zh": "允许", "ja": "許可", "en": "Allowed"},
    "wake_deny": {"zh": "禁止", "ja": "禁止", "en": "Blocked"},
    "wake_unk": {"zh": "未知", "ja": "不明", "en": "Unknown"},
    "uac_cancel_title": {"zh": "未执行", "ja": "未実行", "en": "Not executed"},
    "uac_cancel": {
        "zh": "没有获取到管理员权限（UAC 被取消）。",
        "ja": "管理者権限が取得できませんでした（UAC がキャンセルされました）。",
        "en": "Administrator permission was not granted (UAC canceled)."},
    "uac_done_title": {"zh": "提示", "ja": "お知らせ", "en": "Notice"},
    "uac_done": {
        "zh": "已请求开启，请在 UAC 窗口中选“是”。\n稍等几秒后状态会自动刷新。",
        "ja": "有効化をリクエストしました。UAC 画面で「はい」を選んでください。\n"
              "数秒後に状態が自動更新されます。",
        "en": "Requested. Please click Yes in the UAC prompt.\n"
              "The status refreshes automatically in a few seconds."},
    "card_media": {"zh": "默认铃声与闹钟背景", "ja": "着信音と背景の既定値",
                   "en": "Default ringtone & background"},
    "default_ring_row": {"zh": "默认铃声", "ja": "デフォルト着信音", "en": "Default ringtone"},
    "default_bg_row": {"zh": "默认背景", "ja": "デフォルト背景", "en": "Default background"},
    "choose_image": {"zh": "选择图片", "ja": "画像を選択", "en": "Choose image"},
    "use_default_image": {"zh": "用默认图", "ja": "デフォルト画像", "en": "Default image"},
    "snooze_len": {"zh": "贪睡时长", "ja": "スヌーズ時間", "en": "Snooze length"},
    "choose_ring_title": {"zh": "选择默认铃声", "ja": "デフォルト着信音を選択",
                          "en": "Choose default ringtone"},
    "choose_bg_title": {"zh": "选择默认闹钟背景", "ja": "デフォルト背景を選択",
                        "en": "Choose default background"},
    "card_data": {"zh": "数据", "ja": "データ", "en": "Data"},
    "data_saved": {"zh": "数据保存在：%s", "ja": "データの保存先：%s", "en": "Data folder: %s"},
    "open_data_folder": {"zh": "打开数据文件夹", "ja": "フォルダを開く",
                         "en": "Open data folder"},
    "data_desc": {
        "zh": "data.json 保存了你的全部闹钟、任务与日程，可备份；删除后恢复为示例数据。",
        "ja": "data.json にアラーム・タスク・予定が保存されます。バックアップでき、"
              "削除するとサンプルに戻ります。",
        "en": "data.json stores all alarms, tasks and events. Back it up freely; "
              "deleting it restores the sample data."},
    "card_about": {"zh": "关于", "ja": "このアプリ", "en": "About"},
    "about_line1": {"zh": "居家管家 HomeManager  v%s", "ja": "居家管家 HomeManager  v%s",
                    "en": "Home Manager  v%s"},
    "about_line2": {
        "zh": "闹钟 · 定时任务 · 日历日程 · 定时打开程序 · 睡眠唤醒 · 后台运行",
        "ja": "アラーム · タスク · カレンダー · アプリ起動 · スリープ復帰 · バックグラウンド",
        "en": "Alarms · Tasks · Calendar · App launch · Wake-from-sleep · Background"},
    "theme_note": {"zh": "结衣风粉桃主题 · 圆润可爱字体",
                   "ja": "ゆい風ピーチピンクテーマ · まるいかわいい書体",
                   "en": "Yui-style peach-pink theme · rounded cute fonts"},

    # 闹钟对话框
    "dlg_alarm_title": {"zh": "编辑闹钟", "ja": "アラーム編集", "en": "Edit alarm"},
    "new_alarm": {"zh": "新闹钟", "ja": "新しいアラーム", "en": "New alarm"},
    "alarm_name": {"zh": "闹钟名称", "ja": "アラーム名", "en": "Alarm name"},
    "time": {"zh": "时间", "ja": "時刻", "en": "Time"},
    "repeat": {"zh": "重复", "ja": "くり返し", "en": "Repeat"},
    "ring_bg": {"zh": "铃声 / 背景", "ja": "着信音 / 背景", "en": "Ringtone / picture"},
    "ringtone": {"zh": "铃声", "ja": "着信音", "en": "Ringtone"},
    "background": {"zh": "背景图", "ja": "背景画像", "en": "Background"},
    "warn_alarm_name": {"zh": "请填写闹钟名称", "ja": "アラーム名を入力してください",
                        "en": "Please enter the alarm name"},
    "warn_time": {"zh": "请选择正确的时间", "ja": "正しい時刻を選んでください",
                  "en": "Please choose a valid time"},
    "warn_days": {"zh": "请至少选择一个重复日（每天 / 工作日等）",
                  "ja": "曜日を1つ以上選んでください（毎日 / 平日など）",
                  "en": "Pick at least one weekday (Every day / Weekdays…)"},

    # 提醒对话框
    "dlg_reminder_title": {"zh": "编辑提醒", "ja": "リマインド編集", "en": "Edit reminder"},
    "new_reminder": {"zh": "新提醒", "ja": "新しいリマインド", "en": "New reminder"},
    "reminder_name": {"zh": "提醒名称", "ja": "リマインド名", "en": "Reminder name"},
    "message": {"zh": "提醒内容", "ja": "リマインド内容", "en": "Message"},
    "warn_reminder_name": {"zh": "请填写提醒名称", "ja": "リマインド名を入力してください",
                           "en": "Please enter the reminder name"},

    # 定时打开程序对话框
    "dlg_program_title": {"zh": "定时打开程序", "ja": "アプリ定時起動", "en": "Scheduled app launch"},
    "default_program_name": {"zh": "定时打开程序", "ja": "アプリ起動", "en": "Launch app"},
    "task_name": {"zh": "任务名称", "ja": "タスク名", "en": "Task name"},
    "exe_path": {"zh": "程序路径", "ja": "アプリのパス", "en": "App path"},
    "browse": {"zh": "浏览…", "ja": "参照…", "en": "Browse…"},
    "args": {"zh": "启动参数", "ja": "起動パラメータ", "en": "Arguments"},
    "repeat_weekly": {"zh": "按星期重复", "ja": "曜日でくり返し", "en": "Weekly"},
    "date_label": {"zh": "日期", "ja": "日付", "en": "Date"},
    "date_hint": {"zh": "格式 2026-10-06", "ja": "形式 2026-10-06", "en": "Format: 2026-10-06"},
    "warn_weekday": {"zh": "请至少选择一个星期", "ja": "曜日を1つ以上選んでください",
                     "en": "Pick at least one weekday"},
    "warn_date": {"zh": "日期格式应为 YYYY-MM-DD", "ja": "日付は YYYY-MM-DD 形式で入力",
                  "en": "Date must be YYYY-MM-DD"},
    "after_click": {"zh": "打开后自动点击", "ja": "開いた後に自動クリック",
                    "en": "Auto-click after launch"},
    "col_wait": {"zh": "等待(秒)", "ja": "待機(秒)", "en": "Wait (s)"},
    "col_pos": {"zh": "点击坐标", "ja": "クリック座標", "en": "Position"},
    "col_act": {"zh": "方式", "ja": "操作", "en": "Action"},
    "add_click": {"zh": "添加点击", "ja": "クリック追加", "en": "Add"},
    "pick_coord": {"zh": "拾取坐标", "ja": "座標を取得", "en": "Pick"},
    "toggle_double": {"zh": "切换双击", "ja": "ダブル切替", "en": "Double"},
    "del_selected": {"zh": "删除选中", "ja": "選択を削除", "en": "Delete"},
    "win_title": {"zh": "目标窗口标题（可选）", "ja": "目標ウィンドウ（任意）",
                  "en": "Target window title (optional)"},
    "win_wait": {"zh": "等待窗口出现(秒)", "ja": "ウィンドウ待機(秒)",
                 "en": "Wait for window (s)"},
    "bettergi_tpl": {"zh": "BetterGI 一条龙模板", "ja": "BetterGIテンプレート",
                     "en": "BetterGI template"},
    "bettergi_name": {"zh": "BetterGI 一条龙", "ja": "BetterGI オート周回",
                      "en": "BetterGI auto-run"},
    "bettergi_pick_exe": {
        "zh": "没有自动找到 BetterGI.exe，请点“浏览…”手动选择，再点一次模板按钮。",
        "ja": "BetterGI.exe が見つかりませんでした。「参照…」で手動選択してください。",
        "en": "BetterGI.exe was not found automatically. Click \"Browse…\" to choose it."},
    "test_run": {"zh": "试运行", "ja": "テスト実行", "en": "Test run"},
    "test_started": {
        "zh": "试运行已开始，请观察目标程序是否按步骤操作；窗口未出现时会等待设定的秒数。",
        "ja": "テストを開始しました。対象アプリが手順どおり動くか確認してください。",
        "en": "Test run started. Watch the target app perform the steps; it waits for "
              "the window if it is not open yet."},
    "pos_relative": {"zh": "窗口 %.1f%%, %.1f%%", "ja": "ウィンドウ %.1f%%, %.1f%%",
                     "en": "Window %.1f%%, %.1f%%"},
    "warn_wait": {"zh": "等待窗口秒数需为 1-300 的整数",
                  "ja": "待機秒数は 1〜300 の整数にしてください",
                  "en": "Wait seconds must be an integer from 1 to 300"},
    "click_hint": {
        "zh": "提示：填了“目标窗口标题”后，拾取到的点击会自动记为窗口相对位置，窗口移动也不会点偏；"
              "可先点“试运行”验证，再保存。模板已内置 BetterGI：点一条龙→点任务列表开始。",
        "ja": "ヒント：「目標ウィンドウ」を入力すると、クリック位置はウィンドウ相対で保存され、"
              "ウィンドウが動いてもずれません。保存前に「テスト実行」で確認できます。",
        "en": "Tip: with a target window title set, picked points are stored relative "
              "to that window, so they stay correct even if it moves. Use \"Test run\" "
              "to verify before saving."},
    "single_click": {"zh": "单击", "ja": "シングル", "en": "Single"},
    "double_click": {"zh": "双击", "ja": "ダブル", "en": "Double"},
    "choose_exe_title": {"zh": "选择要定时打开的程序", "ja": "起動するアプリを選択",
                         "en": "Choose a program to launch"},
    "exe_filter": {"zh": "程序 / 快捷方式", "ja": "プログラム / ショートカット",
                   "en": "Programs / shortcuts"},
    "pick_row_first": {
        "zh": "请先选中一行（没有就点“添加点击”）",
        "ja": "先に行を選択してください（なければ「クリック追加」）",
        "en": "Select a row first (add a click if the list is empty)"},
    "warn_task_name": {"zh": "请填写任务名称", "ja": "タスク名を入力してください",
                       "en": "Please enter the task name"},
    "warn_choose_exe": {"zh": "请选择要打开的程序", "ja": "アプリを選択してください",
                        "en": "Please choose a program"},
    "warn_no_coord": {"zh": "有点击步骤还没拾取坐标", "ja": "座標未取得のクリックがあります",
                      "en": "A click step is missing its position"},
    "pick_tip": {
        "zh": "把鼠标移动到要点击的位置\n%d 秒后自动拾取（单击立即拾取，Esc 取消）",
        "ja": "クリック位置へマウスを移動してください\n%d 秒後に取得（クリックで即取得、Esc で中止）",
        "en": "Move the mouse to the click point\nAuto-pick in %d s (click now, Esc cancels)"},

    # 日程对话框
    "dlg_event_title": {"zh": "日程安排", "ja": "予定の編集", "en": "Edit event"},
    "event_title": {"zh": "日程标题", "ja": "予定タイトル", "en": "Event title"},
    "date": {"zh": "日期", "ja": "日付", "en": "Date"},
    "all_day_check": {"zh": "全天（不设具体时间）", "ja": "終日（時刻なし）",
                      "en": "All day (no specific time)"},
    "start_time": {"zh": "开始时间", "ja": "開始時刻", "en": "Start time"},
    "end_time": {"zh": "结束时间", "ja": "終了時刻", "en": "End time"},
    "set_end": {"zh": "设置结束时间", "ja": "終了時刻を設定", "en": "Set end time"},
    "remind": {"zh": "提醒", "ja": "リマインド", "en": "Reminder"},
    "remind_on_time": {"zh": "准时提醒", "ja": "定刻", "en": "On time"},
    "remind_m_before": {"zh": "提前 %d 分钟", "ja": "%d 分前", "en": "%d min before"},
    "remind_h_before": {"zh": "提前 1 小时", "ja": "1 時間前", "en": "1 hour before"},
    "no_remind": {"zh": "不提醒", "ja": "リマインドなし", "en": "No reminder"},
    "note": {"zh": "备注", "ja": "メモ", "en": "Note"},
    "warn_event_title": {"zh": "请填写日程标题", "ja": "予定タイトルを入力してください",
                         "en": "Please enter the event title"},
    "warn_start_time": {"zh": "请选择正确的开始时间", "ja": "正しい開始時刻を選んでください",
                        "en": "Choose a valid start time"},

    # 全屏弹窗
    "popup_alarm_top": {"zh": "居家管家 · 闹钟", "ja": "居家管家 · アラーム",
                        "en": "Home Manager · Alarm"},
    "popup_reminder_top": {"zh": "居家管家 · 提醒", "ja": "居家管家 · リマインド",
                           "en": "Home Manager · Reminder"},
    "snooze_btn": {"zh": "贪睡 %d 分钟", "ja": "スヌーズ（%d 分）", "en": "Snooze %d min"},
    "stop_alarm": {"zh": "停止闹钟", "ja": "アラーム停止", "en": "Stop alarm"},
    "got_it": {"zh": "知道啦", "ja": "はいっ♡", "en": "Got it"},
    "snoozed_note": {"zh": "（贪睡后再次提醒）", "ja": "（スヌーズ後の再お知らせ）",
                     "en": "(Snoozed reminder)"},
    "test_alarm_title": {"zh": "测试闹钟", "ja": "テストアラーム", "en": "Test alarm"},
    "test_alarm_line": {
        "zh": "这是闹钟弹窗效果，可更换铃声与背景图哦",
        "ja": "アラーム画面のプレビューです。着信音と背景を変えられます",
        "en": "Alarm popup preview. Ringtone & picture are customizable"},

    # 调度器文案
    "default_msg": {"zh": "到点啦！", "ja": "時間ですよ！", "en": "Time's up!"},
    "event_now": {"zh": "现在开始", "ja": "まもなく開始", "en": "Starting now"},
    "event_min": {"zh": "%d 分钟后", "ja": "%d 分後", "en": "in %d min"},
    "event_reminder_title": {"zh": "日程提醒 · %s", "ja": "予定リマインド · %s",
                             "en": "Event reminder · %s"},
    "task_fail_title": {"zh": "定时任务执行失败", "ja": "タスク実行失敗",
                        "en": "Task failed"},

    # 托盘 / 退出
    "tray_open": {"zh": "打开主界面", "ja": "メイン画面を開く", "en": "Open main window"},
    "tray_test": {"zh": "测试闹钟弹窗", "ja": "アラームをテスト", "en": "Test alarm popup"},
    "tray_quit": {"zh": "退出居家管家", "ja": "終了", "en": "Quit"},
    "hide_title": {"zh": "居家管家正在后台运行", "ja": "バックグラウンドで実行中",
                   "en": "Running in the background"},
    "hide_body": {
        "zh": "闹钟与定时任务会照常生效，双击托盘图标可重新打开窗口。",
        "ja": "アラームとタスクは動き続けます。トレイアイコンのダブルクリックで画面を開けます。",
        "en": "Alarms and tasks keep running. Double-click the tray icon to reopen."},
    "quit_title": {"zh": "退出", "ja": "終了", "en": "Quit"},
    "quit_confirm": {
        "zh": "退出后闹钟和定时任务将停止，确定退出居家管家吗？",
        "ja": "終了するとアラームとタスクが停止します。終了しますか？",
        "en": "Alarms and tasks will stop after quitting. Quit Home Manager?"},
    "already_running": {
        "zh": "居家管家已经在运行了（请看屏幕右下角托盘图标）。",
        "ja": "居家管家はすでに起動しています（右下のトレイアイコンをご確認ください）。",
        "en": "Home Manager is already running (check the tray icon)."},

    # ---------- 集市 / 联网 ----------
    "nav_market": {"zh": "资源集市", "ja": "マーケット", "en": "Market"},
    "market_title": {"zh": "资源集市", "ja": "マーケット", "en": "Resource Market"},
    "market_sub": {
        "zh": "联网下载可爱壁纸、铃声与吉祥物装扮",
        "ja": "壁紙・着信音・マスコットをオンラインで",
        "en": "Download wallpapers, ringtones & mascots"},
    "tab_wallpaper": {"zh": "可爱壁纸", "ja": "壁紙", "en": "Wallpapers"},
    "tab_ringtone": {"zh": "铃声白噪音", "ja": "着信音", "en": "Ringtones"},
    "tab_mascot": {"zh": "吉祥物装扮", "ja": "マスコット", "en": "Mascot"},
    "tab_download": {"zh": "链接下载", "ja": "URL取得", "en": "URL Download"},
    "market_more": {"zh": "换一批 ♡", "ja": "もっと見る ♡", "en": "More ♡"},
    "market_loading": {"zh": "正在联网寻找可爱资源…", "ja": "かわいい素材を探しています…",
                       "en": "Fetching cute resources…"},
    "market_fail": {
        "zh": "网络连接失败了，检查一下网络再试试吧",
        "ja": "ネットワーク接続に失敗しました。通信を確認してください",
        "en": "Network failed. Please check your connection."},
    "cat_waifu": {"zh": "少女插画", "ja": "女の子イラスト", "en": "Girls"},
    "cat_neko": {"zh": "猫猫少女", "ja": "猫耳", "en": "Neko"},
    "cat_kitsune": {"zh": "狐娘", "ja": "きつね", "en": "Kitsune"},
    "cat_husbando": {"zh": "少年插画", "ja": "男の子イラスト", "en": "Boys"},
    "cat_hug": {"zh": "抱抱", "ja": "ハグ", "en": "Hug"},
    "cat_pat": {"zh": "摸摸头", "ja": "なでなで", "en": "Pat"},
    "cat_cuddle": {"zh": "贴贴", "ja": "くっつき", "en": "Cuddle"},
    "cat_wave": {"zh": "挥手", "ja": "手を振る", "en": "Wave"},
    "cat_smile": {"zh": "微笑", "ja": "笑顔", "en": "Smile"},
    "cat_blush": {"zh": "害羞", "ja": "照れ", "en": "Blush"},
    "market_set_bg": {"zh": "设为闹钟背景", "ja": "背景に設定", "en": "Set as bg"},
    "market_set_mascot": {"zh": "设为吉祥物", "ja": "マスコットに", "en": "Set mascot"},
    "market_save": {"zh": "保存", "ja": "保存", "en": "Save"},
    "market_saved_bg": {"zh": "已经设为默认闹钟背景啦 ♡", "ja": "アラーム背景に設定しました ♡",
                        "en": "Set as default alarm background ♡"},
    "market_saved_mascot": {"zh": "换上新装扮啦 ♡", "ja": "着せかえました ♡",
                            "en": "Mascot updated ♡"},
    "market_saved_file": {"zh": "已保存到资源文件夹 ♡", "ja": "フォルダに保存しました ♡",
                          "en": "Saved to assets folder ♡"},
    "market_downloading": {"zh": "下载中 %d%%", "ja": "ダウンロード中 %d%%",
                           "en": "Downloading %d%%"},
    "market_url_hint": {
        "zh": "粘贴任意图片或音频链接（jpg/png/gif/mp3/wav…）",
        "ja": "画像・音声のURLを貼り付け（jpg/png/gif/mp3/wav…）",
        "en": "Paste any image/audio URL (jpg/png/gif/mp3/wav…)"},
    "market_url_go": {"zh": "下载入库", "ja": "ダウンロード", "en": "Download"},
    "market_url_bad": {"zh": "这个链接好像无法下载，换一个试试？",
                       "ja": "このURLは取得できませんでした",
                       "en": "Cannot download this URL."},
    "market_ring_hint": {
        "zh": "内置助眠白噪音（可循环），也可在“链接下载”里添加更多铃声",
        "ja": "内蔵ホワイトノイズ（ループ可）。URL取得で追加も",
        "en": "Built-in looping ambient sounds; add more via URL Download."},
    "market_mascot_hint": {
        "zh": "透明底 PNG 效果最好；也可以先在“可爱壁纸”里挑图再点“设为吉祥物”",
        "ja": "背景透過PNGがおすすめ。壁紙タブからも設定できます",
        "en": "Transparent PNG works best; you can also pick from Wallpapers."},
    "market_mascot_pick": {"zh": "选择本地图片", "ja": "ローカル画像を選択",
                           "en": "Pick local image"},
    "market_mascot_reset": {"zh": "恢复自带吉祥物", "ja": "標準に戻す", "en": "Reset mascot"},
    "market_open_wallpapers": {"zh": "打开壁纸文件夹", "ja": "壁紙フォルダを開く",
                               "en": "Open wallpapers"},

    # ---------- 番茄钟 ----------
    "nav_focus": {"zh": "专注陪伴", "ja": "集中モード", "en": "Focus"},
    "focus_title": {"zh": "专注陪伴", "ja": "集中モード", "en": "Focus Companion"},
    "focus_sub": {"zh": "和吉祥物一起，25 分钟认真做一件事",
                  "ja": "マスコットと25分、ひとつのことに集中",
                  "en": "25 minutes of focus, together"},
    "focus_start": {"zh": "开始专注 ♡", "ja": "スタート ♡", "en": "Start focus ♡"},
    "focus_pause": {"zh": "暂停", "ja": "一時停止", "en": "Pause"},
    "focus_resume": {"zh": "继续", "ja": "再開", "en": "Resume"},
    "focus_skip": {"zh": "跳过", "ja": "スキップ", "en": "Skip"},
    "focus_focusing": {"zh": "专注中", "ja": "集中中", "en": "Focusing"},
    "focus_resting": {"zh": "休息一下吧", "ja": "休憩中", "en": "Break time"},
    "focus_today": {"zh": "今日已专注 %d 分钟", "ja": "今日の集中 %d 分",
                    "en": "Today: %d min focused"},
    "focus_rounds": {"zh": "今天完成 %d 个番茄", "ja": "今日 %d ポモドーロ",
                     "en": "%d pomodoros today"},
    "focus_focus_len": {"zh": "专注时长", "ja": "集中時間", "en": "Focus length"},
    "focus_break_len": {"zh": "休息时长", "ja": "休憩時間", "en": "Break length"},
    "focus_focus_end": {"zh": "专注完成啦，休息一下眼睛吧 ♡",
                        "ja": "集中完了！目を休めてね ♡",
                        "en": "Focus done! Rest your eyes ♡"},
    "focus_break_end": {"zh": "休息结束，继续加油 ♡", "ja": "休憩終わり、がんばろう ♡",
                        "en": "Break over, keep going ♡"},
    "focus_cheer_1": {"zh": "加油，你超棒的！", "ja": "がんばって、すごい！", "en": "You're doing great!"},
    "focus_cheer_2": {"zh": "静下心来，一步一步来", "ja": "落ち着いて、一歩ずつ",
                      "en": "One step at a time"},
    "focus_cheer_3": {"zh": "我会一直陪着你哦 ♡", "ja": "ずっとそばにいるよ ♡",
                      "en": "I'm right here with you ♡"},
    "focus_cheer_4": {"zh": "手机放远一点，效率翻倍～", "ja": "スマホは遠くに置こう",
                      "en": "Phone away, focus stays"},
    "focus_cheer_5": {"zh": "深呼吸，现在开始刚刚好", "ja": "深呼吸、いまからでも大丈夫",
                      "en": "Take a breath, begin now"},
    "focus_cheer_6": {"zh": "完成这一轮就奖励自己一下", "ja": "このセットが終わったらご褒美",
                      "en": "Reward yourself after this one"},

    # ---------- 纪念日 ----------
    "ann_add": {"zh": "+ 添加倒数日", "ja": "+ 記念日を追加", "en": "+ Add countdown"},
    "ann_name": {"zh": "名称（如：妈妈生日）", "ja": "名前（例：母の誕生日）",
                 "en": "Title (e.g. Mom's birthday)"},
    "ann_solar": {"zh": "公历", "ja": "西暦", "en": "Solar"},
    "ann_lunar": {"zh": "农历", "ja": "旧暦", "en": "Lunar"},
    "ann_yearly": {"zh": "每年重复", "ja": "毎年くり返す", "en": "Repeat yearly"},
    "ann_days_left": {"zh": "还有 %d 天", "ja": "あと %d 日", "en": "%d days left"},
    "ann_days_passed": {"zh": "已过 %d 天", "ja": "%d 日経過", "en": "%d days passed"},
    "ann_today": {"zh": "就是今天 ♡", "ja": "今日です ♡", "en": "Today! ♡"},
    "ann_reminder": {"zh": "纪念日提醒", "ja": "記念日のお知らせ", "en": "Anniversary reminder"},
    "ann_empty": {"zh": "还没有倒数日，添加一个重要的日子吧 ♡",
                  "ja": "記念日を追加してみましょう ♡",
                  "en": "No countdowns yet. Add a special day ♡"},
    "ann_countdown": {"zh": "倒数日", "ja": "記念日", "en": "Countdowns"},
    "ann_need_title": {"zh": "先填个名字吧", "ja": "名前を入れてね", "en": "Please enter a title"},
    "ann_lunar_hint": {
        "zh": "按农历月日填写，如 09-09 为重阳节",
        "ja": "旧暦の月日で入力（例：09-09）",
        "en": "Lunar month-day, e.g. 09-09"},

    # ---------- 每日日语 ----------
    "nihongo_title": {"zh": "今日日语单词", "ja": "今日の日本語", "en": "Japanese of the day"},
    "nihongo_example": {"zh": "例句", "ja": "例文", "en": "Example"},

    # ---------- 一键早安 ----------
    "card_morning": {"zh": "一键早安模式", "ja": "おはようモード", "en": "Good-morning mode"},
    "morning_row": {"zh": "起床后自动早安播报", "ja": "起床後に朝のお知らせ",
                    "en": "Morning briefing after alarm"},
    "morning_desc": {
        "zh": "关闭起床闹钟后弹出今日简报（日期、农历节日、今日日程、日语单词），并自动打开你选好的程序。",
        "ja": "アラーム停止後に日付・旧暦・予定・日本語単語を表示し、選んだアプリを起動します。",
        "en": "After stopping the alarm, shows a briefing (date, lunar/festivals, schedule, Japanese word) and launches chosen apps."},
    "morning_pick": {"zh": "选择要自动打开的程序", "ja": "自動起動するアプリを選択",
                     "en": "Choose apps to auto-launch"},
    "morning_apps_n": {"zh": "已选 %d 个程序", "ja": "%d 個のアプリを選択中",
                       "en": "%d app(s) selected"},
    "morning_clear": {"zh": "清空", "ja": "クリア", "en": "Clear"},
    "morning_brief": {"zh": "早安，今天也要元气满满哦 ♡", "ja": "おはよう、今日もげんきいっぱいで ♡",
                      "en": "Good morning! Have a lovely day ♡"},
    "morning_today_events": {"zh": "今日日程", "ja": "今日の予定", "en": "Today's schedule"},
    "morning_no_events": {"zh": "今天没有特别安排，轻松出发吧",
                          "ja": "今日は予定なし、ゆっくりどうぞ",
                          "en": "No plans today, take it easy"},
    "morning_launching": {"zh": "正在为你打开：%s", "ja": "起動中：%s",
                          "en": "Launching: %s"},
    "morning_start": {"zh": "开启元气一天 ♡", "ja": "いってきます ♡",
                      "en": "Start my day ♡"},

    # ---------- 更新 ----------
    "card_update": {"zh": "版本与更新", "ja": "バージョンと更新", "en": "Version & update"},
    "update_check": {"zh": "检查更新", "ja": "更新を確認", "en": "Check for updates"},
    "update_checking": {"zh": "正在检查更新…", "ja": "更新を確認中…", "en": "Checking…"},
    "update_latest": {"zh": "已经是最新版本啦 ♡", "ja": "最新バージョンです ♡",
                      "en": "You're up to date ♡"},
    "update_found": {"zh": "发现新版本 %s，要更新吗？", "ja": "新バージョン %s があります",
                     "en": "Version %s available. Update now?"},
    "update_fail": {"zh": "暂时连不上更新服务器", "ja": "更新サーバーに接続できません",
                    "en": "Cannot reach the update server"},
    "update_go": {"zh": "去下载页", "ja": "ダウンロードページへ", "en": "Open download page"},
}


def has(key):
    return key in TR


def t(key, *args):
    """取当前语言文案；支持 % 风格参数（与既有代码一致）"""
    entry = TR.get(key)
    if entry is None:
        return key
    s = entry.get(_state["lang"]) or entry.get(DEFAULT_LANG) or key
    if args:
        try:
            return s % args
        except Exception:
            return s
    return s


def weekday_short(i, lang=None):
    return WEEKDAY_SHORT[lang or _state["lang"]][i]


def weekday_full(i, lang=None):
    return WEEKDAY_FULL[lang or _state["lang"]][i]


def day_text(days, lang=None):
    """重复星期的人类可读描述"""
    lang = lang or _state["lang"]
    if not days:
        return t("once")
    dayset = set(days)
    if dayset >= set(range(7)):
        return t("every_day")
    if dayset == {0, 1, 2, 3, 4}:
        return t("workday")
    if dayset == {5, 6}:
        return t("weekend")
    names = WEEKDAY_FULL[lang]
    if lang == "zh":
        return "、".join(names[i] for i in sorted(days))
    if lang == "ja":
        return "・".join(names[i] for i in sorted(days))
    return ", ".join(names[i] for i in sorted(days))


def month_title(year, month, lang=None):
    lang = lang or _state["lang"]
    if lang == "zh":
        return "%d 年 %d 月" % (year, month)
    if lang == "ja":
        return "%d年%d月" % (year, month)
    return "%s %d" % (MONTH_EN[month - 1], year)


def day_panel_title(d, suffix="", lang=None):
    """右侧当日面板标题"""
    lang = lang or _state["lang"]
    if lang == "zh":
        return "%d月%d日 %s%s" % (d.month, d.day, WEEKDAY_FULL[lang][d.weekday()], suffix)
    if lang == "ja":
        return "%d月%d日（%s）%s" % (d.month, d.day, WEEKDAY_FULL[lang][d.weekday()], suffix)
    return "%s, %s %d%s" % (WEEKDAY_FULL[lang][d.weekday()],
                            MONTH_EN_SHORT[d.month - 1], d.day, suffix)


def popup_date(now, lang=None):
    """全屏弹窗上的日期行"""
    lang = lang or _state["lang"]
    if lang == "zh":
        return "%d月%d日  %s" % (now.month, now.day, WEEKDAY_FULL[lang][now.weekday()])
    if lang == "ja":
        return "%d月%d日  %s" % (now.month, now.day, WEEKDAY_FULL[lang][now.weekday()])
    return "%s, %s %d" % (WEEKDAY_FULL[lang][now.weekday()],
                          MONTH_EN_SHORT[now.month - 1], now.day)
