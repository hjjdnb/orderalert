#!/usr/bin/env python3
"""
抢单软件告警接收端 - Android App
基于 Kivy + websocket-client + Pyjnius
连接本地 auto_order.py 内置 WebSocket 服务端（端口 18888）接收实时告警推送
"""

import os
import sys
import json
import time
import threading
import random
import traceback
from datetime import datetime
from pathlib import Path

# ============================================================
#  崩溃日志兜底：任何未捕获异常都写到 /sdcard/crash.txt
#  让闪退可诊断（手机用「文件管理」找 crash.txt）
# ============================================================
CRASH_FILE = "/sdcard/crash.txt"

def _write_crash_log(exc_type, exc_value, exc_tb):
    """把崩溃堆栈写到多个位置：/sdcard/crash.txt + stderr + Android log"""
    try:
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = f"\n{'='*60}\n[{timestamp}] FATAL ERROR\n{'='*60}\n{tb_text}\n"
        
        # 1. 写到 /sdcard/crash.txt（手机文件管理可见）
        try:
            with open(CRASH_FILE, "a", encoding="utf-8") as f:
                f.write(log_content)
        except Exception:
            # /sdcard 写不了，尝试 App 私有目录
            try:
                alt_path = os.path.join(os.path.expanduser("~"), "crash.txt")
                with open(alt_path, "a", encoding="utf-8") as f:
                    f.write(log_content)
            except Exception:
                pass
        
        # 2. 写到 stderr（logcat 可抓）
        print(log_content, file=sys.stderr)
        sys.stderr.flush()
        
        # 3. 尝试写 Android logcat（如果 jnius 可用）
        try:
            from jnius import autoclass
            Log = autoclass("android.util.Log")
            Log.e("OrderAlertCrash", tb_text)
        except Exception:
            pass
        
    except Exception:
        pass

# 安装全局异常钩子
sys.excepthook = _write_crash_log

# 兼容 threading 异常
_orig_thread_run = threading.Thread.run
def _safe_thread_run(self):
    try:
        _orig_thread_run(self)
    except Exception:
        _write_crash_log(*sys.exc_info())
threading.Thread.run = _safe_thread_run
# ============================================================

# Kivy 配置
from kivy.config import Config
Config.set('graphics', 'orientation', 'portrait')
Config.set('graphics', 'resizable', False)

# ============================================================
# 【★中文显示关键 1/3】在 Kivy UI import 之前注册默认中文字体
# 防止任何控件使用无 CJK 字形的 Roboto 字体而渲染成豆腐块 □□□
# ============================================================
_FONT_CANDIDATES = [
    "DroidSansFallbackFull.ttf",
    "DroidSansFallback.ttf",
    "NotoSansSC-Regular.otf",
    "NotoSansCJKsc-Regular.otf",
    "SourceHanSansCN-Normal.otf",
    "WenQuanYiMicroHei.ttf",
    "wqy-microhei.ttc",
    "fonts/DroidSansFallbackFull.ttf",
    "data/DroidSansFallbackFull.ttf",
]
# Emoji 字体候选（用于补充 emoji 渲染，与中文字体叠加使用）
_EMOJI_FONT_CANDIDATES = [
    "Symbola.ttf",
    "NotoColorEmoji.ttf",
    "NotoEmoji-Regular.ttf",
    "DejaVuSans.ttf",
    "fonts/Symbola.ttf",
    "data/Symbola.ttf",
]
_FONT_FILE = None      # 最终找到的中文字体路径（绝对路径）
_EMOJI_FONT_FILE = None # 最终找到的 emoji 字体路径

def _find_bundled_font():
    """在 APK 资源目录/主程序目录里找打包进去的 CJK 字体"""
    global _FONT_FILE
    if _FONT_FILE and os.path.isfile(_FONT_FILE):
        return _FONT_FILE
    # 候选基础路径（覆盖 p4a 各种资源加载位置）
    bases = []
    try:
        bases.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    try:
        bases.append(os.path.abspath("."))
    except Exception:
        pass
    # p4a/Kivy 标准资源路径
    try:
        from kivy.app import App as _TmpApp
        if hasattr(_TmpApp, 'directory'):
            bases.append(_TmpApp.directory)
        if hasattr(_TmpApp, 'user_data_dir'):
            bases.append(_TmpApp.user_data_dir)
    except Exception:
        pass
    # Android 私有存储路径
    for env_key in ('ANDROID_PRIVATE', 'ANDROID_APP_PATH', 'PYTHONPATH'):
        v = os.environ.get(env_key, '')
        if v:
            bases.append(v)
    for base in bases:
        if not base:
            continue
        for fn in _FONT_CANDIDATES:
            p = os.path.join(base, fn)
            try:
                if os.path.isfile(p):
                    _FONT_FILE = p
                    return p
            except Exception:
                continue
    return None

def _find_emoji_font():
    """查找 emoji 补充字体"""
    global _EMOJI_FONT_FILE
    if _EMOJI_FONT_FILE and os.path.isfile(_EMOJI_FONT_FILE):
        return _EMOJI_FONT_FILE
    bases = []
    try:
        bases.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    try:
        bases.append(os.path.abspath("."))
    except Exception:
        pass
    for env_key in ('ANDROID_PRIVATE', 'ANDROID_APP_PATH', 'PYTHONPATH'):
        v = os.environ.get(env_key, '')
        if v:
            bases.append(v)
    for base in bases:
        if not base:
            continue
        for fn in _EMOJI_FONT_CANDIDATES:
            p = os.path.join(base, fn)
            try:
                if os.path.isfile(p):
                    _EMOJI_FONT_FILE = p
                    return p
            except Exception:
                continue
    return None

_FONT_FILE = _find_bundled_font()
if _FONT_FILE:
    # 方式 A：Config.set 在 kivy.core.text 加载前生效
    Config.set('kivy', 'default_font', [
        'ChineseDefault',
        _FONT_FILE,  # regular
        _FONT_FILE,  # bold
        _FONT_FILE,  # italic
        _FONT_FILE,  # bold-italic
    ])
    try:
        print("[FONT] Config.set default_font -> " + _FONT_FILE, file=sys.stderr)
    except Exception:
        pass
else:
    try:
        print("[FONT] WARNING: no bundled CJK font found! Chinese text may render as tofu □", file=sys.stderr)
    except Exception:
        pass

def _apply_chinese_font_override():
    """【★中文显示关键 2/3】覆盖 Kivy 内置 Roboto 字体，并启用 emoji 字体回退

    1) 把 Roboto 重新注册为我们的 CJK 字体
    2) 如果存在 emoji 字体，用 Kivy 的 font_concat/fallback 机制叠加
       这样 emoji 和中英文混排都能正常显示，无缺失、乱码现象
    """
    font_path = _find_bundled_font()
    if not font_path:
        return False
    emoji_path = _find_emoji_font()
    try:
        from kivy.core.text import LabelBase
        # 先删除旧条目（如果已注册），保证覆盖生效
        try:
            if 'Roboto' in LabelBase._fonts:
                del LabelBase._fonts['Roboto']
            if 'ChineseDefault' in LabelBase._fonts:
                del LabelBase._fonts['ChineseDefault']
            if 'ChineseEmoji' in LabelBase._fonts:
                del LabelBase._fonts['ChineseEmoji']
        except Exception:
            pass
        # 把默认的 Roboto 名字重新注册为我们的 CJK 字体
        LabelBase.register(
            name='Roboto',
            fn_regular=font_path,
            fn_bold=font_path,
            fn_italic=font_path,
            fn_bolditalic=font_path,
        )
        # 中文字体别名
        LabelBase.register(
            name='ChineseDefault',
            fn_regular=font_path,
            fn_bold=font_path,
            fn_italic=font_path,
            fn_bolditalic=font_path,
        )
        # 如果有 emoji 字体，注册一个中英文+emoji 叠加字体名
        # Kivy LabelBase 支持将多个字体路径合并，实现字形 fallback
        if emoji_path:
            try:
                LabelBase.register(
                    name='ChineseEmoji',
                    fn_regular=font_path + "," + emoji_path,
                    fn_bold=font_path + "," + emoji_path,
                    fn_italic=font_path + "," + emoji_path,
                    fn_bolditalic=font_path + "," + emoji_path,
                )
                # 用叠加字体覆盖 Roboto，让所有控件默认使用叠加字体
                LabelBase._fonts['Roboto'] = LabelBase._fonts['ChineseEmoji']
                try:
                    print("[FONT] emoji fallback enabled -> " + emoji_path, file=sys.stderr)
                except Exception:
                    pass
            except Exception as e:
                try:
                    print("[FONT] emoji concat failed (忽略，继续用单中文字体): " + str(e), file=sys.stderr)
                except Exception:
                    pass
        try:
            print("[FONT] Roboto overridden -> " + font_path, file=sys.stderr)
            sys.stderr.flush()
        except Exception:
            pass
        return True
    except Exception as e:
        try:
            print("[FONT] override Roboto failed: " + str(e), file=sys.stderr)
        except Exception:
            pass
        return False

# 在 App 构建之前就执行一次 Roboto 覆盖
_apply_chinese_font_override()
# ============================================================

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.window import Window

# websocket-client（连接本地 auto_order.py WS 服务端）
try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

# Android 原生 API
ANDROID_AVAILABLE = False
try:
    from jnius import autoclass, cast
    ANDROID_AVAILABLE = True
except ImportError:
    pass

# 本地 auto_order.py WebSocket 服务端地址（默认端口 18888）
LOCAL_WS_URL = "ws://192.168.1.100:18888"

# ================ 应用层心跳参数（按用户需求）================
HB_INTERVAL_SEC       = 180   # 心跳发送间隔：3分钟（180秒），精确固定频率
HB_PING_TIMEOUT_SEC   = 25    # 单次Ping超时：发送后25秒未收到Pong即判定本次Ping失败
HB_OFFLINE_THRESHOLD  = 3     # 连续失败阈值：连续3次未响应判定为离线
# ============================================================

# 配置文件路径（★ 延迟到 build() 里初始化，防止模块加载时触发闪退）
def get_app_dir():
    """安全获取 App 存储目录，任何错误都回退到当前目录，绝不抛异常"""
    try:
        if ANDROID_AVAILABLE:
            # 注意：python-for-android 没有 get_permissions 这个 API，直接用 mActivity 的 filesDir 更靠谱
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                ctx = activity.getApplicationContext()
                files_dir = ctx.getFilesDir().getAbsolutePath()
                if files_dir and os.path.isdir(files_dir):
                    return files_dir
            except Exception:
                pass
            # 兜底：用 home 目录
            return str(Path.home())
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))

# ★ 延迟初始化，在 App.build() 里赋值（防止模块加载期闪退）
APP_DIR = None
CONFIG_FILE = None

# ================ 告警级别与默认策略 ================
# 级别从低到高：info/warning/error/critical
ALERT_LEVEL_INFO     = "info"
ALERT_LEVEL_WARNING  = "warning"
ALERT_LEVEL_ERROR    = "error"
ALERT_LEVEL_CRITICAL = "critical"

# 每个级别的默认处置策略：vibrate(震动)/wake(唤醒屏)/notify(通知)/sound(响铃)
DEFAULT_LEVEL_POLICY = {
    ALERT_LEVEL_INFO:     {"vibrate": False, "wake": False, "notify": False, "sound": False, "vibrate_ms": 0,    "priority": "low"},
    ALERT_LEVEL_WARNING:  {"vibrate": True,  "wake": False, "notify": True,  "sound": False, "vibrate_ms": 200,  "priority": "default"},
    ALERT_LEVEL_ERROR:    {"vibrate": True,  "wake": True,  "notify": True,  "sound": True,  "vibrate_ms": 800,  "priority": "high"},
    ALERT_LEVEL_CRITICAL: {"vibrate": True,  "wake": True,  "notify": True,  "sound": True,  "vibrate_ms": 1500, "priority": "max"},
}

# 告警级别对应的颜色
ALERT_LEVEL_COLOR = {
    ALERT_LEVEL_INFO:     (0.7, 0.9, 1, 1),
    ALERT_LEVEL_WARNING:  (1, 0.8, 0, 1),
    ALERT_LEVEL_ERROR:    (1, 0.4, 0.4, 1),
    ALERT_LEVEL_CRITICAL: (1, 0, 0, 1),
}
# ====================================================

# 默认配置
DEFAULT_CONFIG = {
    "server_urls": [LOCAL_WS_URL],  # 服务端IP列表（支持多IP，同时监控多个客户端）
    # 告警关键字（与级别联动：匹配到关键字直接升级为 error）
    "alert_keywords": ["离线", "异常", "错误", "告警", "CRITICAL", "ALERT"],
    # 告警冷却时长（秒）：同一客户端 + 同一关键字 在该窗口内只触发一次强提醒
    "alert_cooldown_sec": 30,
    # 告警风暴抑制：N秒内同一客户端相同内容合并为1条，显示重复计数
    "alert_storm_window_sec": 10,
    # 告警级别策略（用户可在UI上修改，持久化到配置文件）
    "level_policy": DEFAULT_LEVEL_POLICY,
    # 静默时段配置：enabled开启后，在start~end时间段内（本地时间HH:MM）所有级别降级为仅通知不震动/响铃/唤醒
    "quiet_hours": {
        "enabled": False,
        "start": "23:00",
        "end":   "07:00",
    },
}

# 告警关键字默认值（用户可在设置面板修改并持久化到 config，此处仅作为兜底默认）
ALERT_KEYWORDS = ["离线", "异常", "错误", "告警", "CRITICAL", "ALERT"]

# 全局变量（兼容旧逻辑）
last_alert_time = {}  # {(client_name, keyword_dedup_key): timestamp}


class AlertStore:
    """告警 SQLite 持久化（轻量：仅落盘，不提供查询UI）

    设计要点：
      - 使用 Python 标准库 sqlite3，无需额外依赖（buildozer.spec 已隐式包含）
      - 单独线程写入，不阻塞 UI / WS 线程
      - 仅提供 insert_alert / close 两个方法
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._queue = []
        self._cv = threading.Condition(self._lock)
        self._running = True
        self._conn = None
        # 初始化库表（在写入线程第一次启动时执行，避免模块加载期 IO 报错）
        self._thread = threading.Thread(target=self._writer_loop, name="AlertStore", daemon=True)
        self._thread.start()

    def _ensure_db(self):
        if self._conn is not None:
            return
        try:
            import sqlite3
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          INTEGER NOT NULL,
                    level       TEXT    NOT NULL,
                    client_id   TEXT    NOT NULL DEFAULT '',
                    title       TEXT    NOT NULL DEFAULT '',
                    body        TEXT    NOT NULL DEFAULT '',
                    source      TEXT    NOT NULL DEFAULT '',
                    full_text   TEXT    NOT NULL DEFAULT ''
                )
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts)")
            self._conn.commit()
        except Exception as e:
            try:
                print("[AlertStore] init DB failed: " + str(e), file=sys.stderr)
            except Exception:
                pass
            self._conn = None

    def _writer_loop(self):
        self._ensure_db()
        while True:
            with self._cv:
                while self._running and not self._queue:
                    self._cv.wait(timeout=1.0)
                if not self._running and not self._queue:
                    break
                batch = self._queue[:]
                self._queue.clear()
            if self._conn is None:
                continue
            try:
                for row in batch:
                    self._conn.execute(
                        "INSERT INTO alerts(ts, level, client_id, title, body, source, full_text) VALUES(?,?,?,?,?,?,?)",
                        (row["ts"], row["level"], row["client_id"], row["title"],
                         row["body"], row["source"], row["full_text"]),
                    )
                self._conn.commit()
            except Exception as e:
                try:
                    print("[AlertStore] write failed: " + str(e), file=sys.stderr)
                except Exception:
                    pass

    def insert_alert(self, ts, level, client_id, title, body, source, full_text):
        if not self._running:
            return
        with self._cv:
            self._queue.append({
                "ts": int(ts), "level": level, "client_id": client_id or "",
                "title": title or "", "body": body or "",
                "source": source or "", "full_text": full_text or "",
            })
            self._cv.notify()

    def close(self):
        with self._cv:
            self._running = False
            self._cv.notify_all()
        try:
            self._thread.join(timeout=3.0)
        except Exception:
            pass
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass

class HeartbeatManager:
    """应用层心跳管理器（线程安全）

    设计要点：
      - 固定频率 HB_INTERVAL_SEC 秒发送一次应用层 Ping (JSON {"action":"ping"})
      - 发送后立即启动独立超时计时器，HB_PING_TIMEOUT_SEC 秒未收到 Pong 即计为一次失败
      - 连续失败达到 HB_OFFLINE_THRESHOLD 次，立即触发离线判定并记录时间戳
      - 成功收到 Pong 时连续失败计数器清零
      - 日志策略：成功不记日志，仅在心跳失败、超时、离线状态变更时记录异常日志
    """

    def __init__(self, app_ref, server_url, short_url):
        self.app = app_ref
        self.server_url = server_url
        self.short = short_url
        self._lock = threading.Lock()

        # 运行状态
        self._running = False
        self._heartbeat_thread = None
        self._timeout_timer = None
        self._wait_event = threading.Event()

        # 心跳计数与状态（加锁访问）
        self._seq = 0
        self._pending_seq = -1
        self._consecutive_fail = 0
        self._is_offline = False
        self._offline_since_ts = None
        self._last_pong_ts = None

    def start(self):
        """连接成功时调用：启动心跳线程"""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._reset_state_locked(log_on_reset=False)
            self._wait_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"HB-{self.short}",
            daemon=True,
        )
        self._heartbeat_thread.start()

    def stop(self):
        """连接断开时调用：停止心跳线程与任何待触发的超时计时器"""
        with self._lock:
            self._running = False
            self._wait_event.set()
            timer = self._timeout_timer
            self._timeout_timer = None
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass

    def _reset_state_locked(self, log_on_reset=True):
        if self._is_offline and log_on_reset:
            ts_str = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            offline_for = None
            if self._offline_since_ts:
                offline_for = int(time.time() - self._offline_since_ts)
            msg = f"[{self.short}] 心跳恢复在线（离线时长 {offline_for}秒  @ {ts_str}）"
            Clock.schedule_once(lambda dt, m=msg: self.app.log_msg(m, color=(0.4, 1, 0.4, 1)), 0)
        self._seq = 0
        self._pending_seq = -1
        self._consecutive_fail = 0
        self._is_offline = False
        self._offline_since_ts = None

    def on_pong_received(self, remote_ts):
        """收到服务端应用层 Pong 时调用"""
        with self._lock:
            running = self._running
            pending = self._pending_seq
            was_offline = self._is_offline
            fail_count_before = self._consecutive_fail
            timer = self._timeout_timer
            self._timeout_timer = None
            self._last_pong_ts = time.time()
            if pending >= 0:
                self._pending_seq = -1
                self._consecutive_fail = 0
                self._is_offline = False
                self._offline_since_ts = None
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass
        if running and (was_offline or fail_count_before > 0):
            if fail_count_before > 0 and not was_offline:
                msg = f"[{self.short}] 心跳恢复（前序连续失败 {fail_count_before} 次已清零）"
                Clock.schedule_once(lambda dt, m=msg: self.app.log_msg(m, color=(0.4, 1, 0.4, 1)), 0)

    def _heartbeat_loop(self):
        while True:
            deadline = time.time() + HB_INTERVAL_SEC
            while True:
                with self._lock:
                    if not self._running:
                        return
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._wait_event.wait(timeout=min(remaining, 1.0))
            with self._lock:
                if not self._running:
                    return
                ws_info = self.app.ws_connections.get(self.server_url) if hasattr(self.app, 'ws_connections') else None
                ws_obj = ws_info.get('ws') if ws_info else None
                if ws_obj is None:
                    self._mark_send_fail_locked("无可用连接")
                    continue
                self._seq += 1
                seq = self._seq
                self._pending_seq = seq
                payload = json.dumps({"action": "ping", "seq": seq, "timestamp": int(time.time())})
            try:
                ws_obj.send(payload)
            except Exception as e:
                with self._lock:
                    self._pending_seq = -1
                    self._mark_send_fail_locked(f"Ping发送失败: {e}")
                continue
            timeout_timer = threading.Timer(
                HB_PING_TIMEOUT_SEC,
                self._on_ping_timeout,
                args=(seq,)
            )
            timeout_timer.daemon = True
            with self._lock:
                if self._running and self._pending_seq == seq:
                    self._timeout_timer = timeout_timer
                    timeout_timer.start()
                else:
                    try:
                        timeout_timer.cancel()
                    except Exception:
                        pass

    def _mark_send_fail_locked(self, reason):
        self._consecutive_fail += 1
        seq_now = self._seq
        fail_now = self._consecutive_fail
        Clock.schedule_once(
            lambda dt, s=self.short, r=reason, n=seq_now, c=fail_now:
                self.app.log_msg(f"[{s}] 心跳异常 #{n}: {r}（连续失败 {c}/{HB_OFFLINE_THRESHOLD}）",
                                 color=(1, 0.6, 0.2, 1)),
            0
        )
        self._check_offline_locked()

    def _on_ping_timeout(self, seq):
        offline_msg_cache = None
        with self._lock:
            if not self._running:
                return
            if self._pending_seq != seq:
                return
            self._pending_seq = -1
            self._consecutive_fail += 1
            fail_now = self._consecutive_fail
            self._timeout_timer = None
            Clock.schedule_once(
                lambda dt, s=self.short, n=seq, c=fail_now, to=HB_PING_TIMEOUT_SEC:
                    self.app.log_msg(
                        f"[{s}] 心跳超时 #{n}: {to}秒未收到Pong（连续失败 {c}/{HB_OFFLINE_THRESHOLD}）",
                        color=(1, 0.5, 0.2, 1)),
                0
            )
            trigger_offline = self._check_offline_locked()
            if trigger_offline and not self.app._batch_alerts_off.get(self.server_url):
                ts = time.time()
                ts_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                offline_msg_cache = (
                    f"[{self.short}] 心跳连续失败 {HB_OFFLINE_THRESHOLD} 次，判定为离线（发生时间 {ts_str}）"
                )
                self.app._batch_alerts_off[self.server_url] = True
        if offline_msg_cache is not None:
            try:
                Clock.schedule_once(
                    lambda dt, m=offline_msg_cache: self.app._trigger_alert(m),
                    0
                )
            except Exception:
                pass

    def _check_offline_locked(self):
        if self._consecutive_fail >= HB_OFFLINE_THRESHOLD and not self._is_offline:
            self._is_offline = True
            self._offline_since_ts = time.time()
            ts = self._offline_since_ts
            ts_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            Clock.schedule_once(
                lambda dt, s=self.short, t=ts_str, c=self._consecutive_fail:
                    self.app.log_msg(
                        f"[{s}] ===== 设备离线 =====（连续失败 {c} 次，发生于 {t}）",
                        color=(1, 0.3, 0.3, 1)),
                0
            )
            Clock.schedule_once(lambda dt: self.app._update_overall_status(), 0)
            return True
        return False

    def is_offline(self):
        with self._lock:
            return self._is_offline

    def get_offline_since_ts(self):
        with self._lock:
            return self._offline_since_ts

    def get_consecutive_fail(self):
        with self._lock:
            return self._consecutive_fail


# UI 引用
class MonitorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_data = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝，避免污染常量
        self.log_lines = []
        self.max_log_lines = 200
        self._android_perms_requested = False  # 是否已申请运行时权限
        # ★ 预初始化 UI 引用，防止 build() 完成前被访问导致 AttributeError
        self.log_scroll = None
        self.log_grid = None
        self.status_label = None
        self._ui_ready = False
        # ★ 多连接管理：每个服务端IP一个独立连接
        self.ws_connections = {}   # {url: {"ws":App, "running":bool, "thread":Thread, "attempts":int}}
        self.hb_managers = {}      # {url: HeartbeatManager}  每个连接独立的应用层心跳管理器
        self._batch_alerts_off = {}  # {url: True}  离线强提醒去重标记
        self.ip_rows = []          # IP 列表 UI 行引用 [{row, input, remove_btn, url}]
        # ============ 新增：告警持久化与监控增强 ============
        self.alert_store = None       # AlertStore 实例，build() 后初始化
        # 客户端结构化状态看板：{short_url: {client_id, token_status, token_remain, connected, ts}}
        self.client_status = {}
        # 风暴抑制去重：{(client_id, content_hash): (count, last_ts)}
        self._storm_dedup = {}
        # UI 状态节流：_update_overall_status 频繁调用时合并
        self._status_update_scheduled = False
        # 前台服务状态
        self._foreground_running = False
        self._foreground_service_cls = None
        # 崩溃恢复标记
        self._last_crash_detected = False
        
    def build(self):
        global APP_DIR, CONFIG_FILE
        # 【★中文显示关键 3/3】App 构建初期再次覆盖 Roboto（三重保险）
        # p4a/Kivy SDL2 bootstrap 有时会在应用启动时重新加载字体注册表，
        # 顶部的那次 override 可能被冲掉，这里在 build() 里再做一次确保 100% 生效
        _apply_chinese_font_override()
        # ★ 安全初始化路径（任何错误都不抛异常，防模块加载期闪退）
        try:
            APP_DIR = get_app_dir()
            os.makedirs(APP_DIR, exist_ok=True)
        except Exception:
            APP_DIR = os.path.dirname(os.path.abspath(__file__))
        CONFIG_FILE = os.path.join(APP_DIR, "monitor_config.json")
        # ============ 新增：告警持久化初始化 ============
        try:
            db_file = os.path.join(APP_DIR, "alerts.db")
            self.alert_store = AlertStore(db_file)
        except Exception as e:
            try:
                print("[App] init AlertStore failed: " + str(e), file=sys.stderr)
            except Exception:
                pass
        # ============ 新增：检测上次崩溃 ============
        try:
            if os.path.exists(CRASH_FILE):
                size = os.path.getsize(CRASH_FILE)
                if size > 0:
                    self._last_crash_detected = True
        except Exception:
            pass
        # Android 13+：动态申请 POST_NOTIFICATIONS 权限（通知必备，晚一点执行确保 Activity 已初始化）
        Clock.schedule_once(lambda dt: self._request_android_permissions(), 1.0)
        # 启动前台服务（保活）——在权限申请之后做，确保通知渠道能正常创建
        Clock.schedule_once(lambda dt: self.start_foreground_service(), 2.0)
        # 崩溃提示：延迟 3 秒弹
        if self._last_crash_detected:
            Clock.schedule_once(lambda dt: self._show_crash_tip(), 3.0)
        self.title = "抢单软件告警"
        Window.clearcolor = (0.1, 0.1, 0.12, 1)
        
        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))
        
        # 顶部状态栏
        status_bar = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=dp(52),
            spacing=dp(6)
        )
        
        self.status_label = Label(
            text='[b][未连接][/b]',
            markup=True,
            size_hint_x=0.28,
            font_size=dp(13),
            color=(1, 0.3, 0.3, 1),
            halign='left',
            valign='middle',
            padding=[dp(6), 0]
        )
        self.status_label.bind(size=self._bind_header_size)
        
        self.connect_btn = Button(
            text='连接',
            size_hint_x=0.2,
            font_size=dp(12),
            background_color=(0.2, 0.6, 0.2, 1),
            on_press=self.toggle_connection
        )
        
        self.query_btn = Button(
            text='查状态',
            size_hint_x=0.16,
            font_size=dp(11),
            background_color=(0.2, 0.5, 0.8, 1),
            on_press=self.query_status
        )
        
        self.clear_btn = Button(
            text='清屏',
            size_hint_x=0.16,
            font_size=dp(11),
            background_color=(0.6, 0.4, 0.2, 1),
            on_press=self.clear_screen
        )
        
        self.settings_btn = Button(
            text='设置',
            size_hint_x=0.2,
            font_size=dp(11),
            background_color=(0.5, 0.4, 0.7, 1),
            on_press=self._open_settings
        )
        
        status_bar.add_widget(self.status_label)
        status_bar.add_widget(self.connect_btn)
        status_bar.add_widget(self.query_btn)
        status_bar.add_widget(self.clear_btn)
        status_bar.add_widget(self.settings_btn)
        
        root.add_widget(status_bar)
        
        # 服务端IP管理面板（支持多IP，同时监控多个客户端）
        ip_panel = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=[dp(8), dp(6)],
            spacing=dp(6)
        )
        ip_header = Label(
            text='[b]服务端IP管理（支持多IP同时监控）[/b]',
            markup=True,
            size_hint_y=None,
            height=dp(22),
            font_size=dp(13),
            color=(0.8, 0.95, 1, 1),
            halign='left',
            valign='middle'
        )
        ip_header.bind(size=self._bind_header_size)
        ip_panel.add_widget(ip_header)
        # 已添加IP列表（可滚动，支持增删改）
        self.ip_list_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            scroll_type=['bars', 'content']
        )
        self.ip_list_grid = GridLayout(
            cols=1,
            spacing=dp(6),
            size_hint_y=None,
            padding=[0, dp(2)]
        )
        self.ip_list_grid.bind(minimum_height=self.ip_list_grid.setter('height'))
        self.ip_list_scroll.add_widget(self.ip_list_grid)
        ip_panel.add_widget(self.ip_list_scroll)
        # 新IP输入行：输入框 + 添加按钮
        add_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        self.new_ip_input = TextInput(
            hint_text='输入IP:端口（如 192.168.1.100:18888）',
            size_hint_x=0.7,
            font_size=dp(13),
            multiline=False,
            padding=[dp(8), dp(6)]
        )
        add_btn = Button(
            text='添加',
            size_hint_x=0.3,
            font_size=dp(13),
            background_color=(0.2, 0.6, 0.2, 1),
            on_press=self.on_add_server
        )
        add_row.add_widget(self.new_ip_input)
        add_row.add_widget(add_btn)
        ip_panel.add_widget(add_row)
        root.add_widget(ip_panel)
        
        # 日志显示区
        log_label = Label(
            text='[b]消息日志[/b]',
            markup=True,
            size_hint_y=None,
            height=dp(22),
            font_size=dp(13),
            color=(0.8, 0.95, 1, 1),
            halign='left',
            valign='middle'
        )
        log_label.bind(size=self._bind_header_size)
        root.add_widget(log_label)
        
        self.log_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            scroll_type=['bars', 'content']
        )
        
        self.log_grid = GridLayout(
            cols=1,
            spacing=dp(6),
            padding=[dp(6), dp(4)],
            size_hint_y=None
        )
        self.log_grid.bind(minimum_height=self.log_grid.setter('height'))
        
        self.log_scroll.add_widget(self.log_grid)
        root.add_widget(self.log_scroll)
        
        # ★ UI 已就绪标志（log_msg 现在可以安全操作 UI）
        self._ui_ready = True
        
        # 加载配置
        self.load_config()
        self.apply_config()
        
        # 启动连接
        Clock.schedule_once(lambda dt: self.log_msg("App 已启动，点击[连接]开始接收消息"), 0.5)
        
        return root
    
    def _bind_header_size(self, instance, value):
        instance.text_size = (value[0], None)

    # ================ 新增：设置面板 ================
    def _open_settings(self, instance):
        """打开设置面板：静默时段 / 告警冷却 / 风暴抑制 / 关键字 / 级别策略"""
        from kivy.uix.switch import Switch
        from kivy.uix.checkbox import CheckBox
        
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=[0, dp(4)])
        form.bind(minimum_height=form.setter('height'))
        
        qh = self.config_data.get("quiet_hours", {})
        
        # ===== 1. 静默时段 =====
        form.add_widget(self._section_label("静默时段（夜间不震动不响铃）"))
        quiet_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(6))
        quiet_row.add_widget(Label(text='启用', size_hint_x=0.2, font_size=dp(12)))
        quiet_sw = Switch(active=bool(qh.get("enabled", False)), size_hint_x=0.2)
        quiet_row.add_widget(quiet_sw)
        quiet_row.add_widget(Label(text='起', size_hint_x=0.1, font_size=dp(11)))
        start_input = TextInput(text=str(qh.get("start", "23:00")), size_hint_x=0.2,
                                font_size=dp(12), multiline=False, padding=[dp(4), dp(4)])
        quiet_row.add_widget(start_input)
        quiet_row.add_widget(Label(text='止', size_hint_x=0.1, font_size=dp(11)))
        end_input = TextInput(text=str(qh.get("end", "07:00")), size_hint_x=0.2,
                              font_size=dp(12), multiline=False, padding=[dp(4), dp(4)])
        quiet_row.add_widget(end_input)
        form.add_widget(quiet_row)
        form.add_widget(Label(
            text='格式 HH:MM，跨午夜自动处理（如 23:00→07:00）',
            size_hint_y=None, height=dp(18), font_size=dp(10), color=(0.6, 0.6, 0.6, 1)
        ))
        
        # ===== 2. 告警冷却 / 风暴抑制 =====
        form.add_widget(self._section_label("告警去重"))
        cd_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(6))
        cd_row.add_widget(Label(text='冷却(秒)', size_hint_x=0.4, font_size=dp(12)))
        cd_input = TextInput(text=str(self.config_data.get("alert_cooldown_sec", 30)),
                             size_hint_x=0.6, font_size=dp(12), multiline=False,
                             input_filter='int', padding=[dp(4), dp(4)])
        cd_row.add_widget(cd_input)
        form.add_widget(cd_row)
        
        storm_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(6))
        storm_row.add_widget(Label(text='风暴窗口(秒)', size_hint_x=0.4, font_size=dp(12)))
        storm_input = TextInput(text=str(self.config_data.get("alert_storm_window_sec", 10)),
                                size_hint_x=0.6, font_size=dp(12), multiline=False,
                                input_filter='int', padding=[dp(4), dp(4)])
        storm_row.add_widget(storm_input)
        form.add_widget(storm_row)
        form.add_widget(Label(
            text='同客户端同内容在窗口内只强提醒1次，后续合并计数',
            size_hint_y=None, height=dp(18), font_size=dp(10), color=(0.6, 0.6, 0.6, 1)
        ))
        
        # ===== 3. 告警关键字 =====
        form.add_widget(self._section_label("告警关键字（逗号分隔，命中即升级为error）"))
        kw_input = TextInput(
            text=','.join(self.config_data.get("alert_keywords", ALERT_KEYWORDS)),
            size_hint_y=None, height=dp(40), font_size=dp(12), multiline=True,
            padding=[dp(6), dp(4)]
        )
        form.add_widget(kw_input)
        
        # ===== 4. 级别策略 =====
        form.add_widget(self._section_label("告警级别策略"))
        level_widgets = {}
        for lv, lv_name in [(ALERT_LEVEL_INFO, "信息"), (ALERT_LEVEL_WARNING, "警告"),
                            (ALERT_LEVEL_ERROR, "错误"), (ALERT_LEVEL_CRITICAL, "严重")]:
            policy = self._get_level_policy(lv)
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(34), spacing=dp(4))
            row.add_widget(Label(text=lv_name, size_hint_x=0.16, font_size=dp(12),
                                 color=ALERT_LEVEL_COLOR[lv]))
            vibrate_cb = CheckBox(active=bool(policy.get("vibrate", False)))
            wake_cb = CheckBox(active=bool(policy.get("wake", False)))
            notify_cb = CheckBox(active=bool(policy.get("notify", False)))
            sound_cb = CheckBox(active=bool(policy.get("sound", False)))
            row.add_widget(Label(text='震', size_hint_x=0.12, font_size=dp(10)))
            row.add_widget(vibrate_cb)
            row.add_widget(Label(text='亮', size_hint_x=0.12, font_size=dp(10)))
            row.add_widget(wake_cb)
            row.add_widget(Label(text='通', size_hint_x=0.12, font_size=dp(10)))
            row.add_widget(notify_cb)
            row.add_widget(Label(text='声', size_hint_x=0.12, font_size=dp(10)))
            row.add_widget(sound_cb)
            row.add_widget(Label(text='震动ms', size_hint_x=0.16, font_size=dp(10)))
            ms_input = TextInput(text=str(policy.get("vibrate_ms", 0)),
                                 size_hint_x=0.2, font_size=dp(11), multiline=False,
                                 input_filter='int', padding=[dp(4), dp(4)])
            row.add_widget(ms_input)
            form.add_widget(row)
            level_widgets[lv] = {
                "vibrate": vibrate_cb, "wake": wake_cb,
                "notify": notify_cb, "sound": sound_cb, "ms": ms_input,
            }
        
        scroll.add_widget(form)
        content.add_widget(scroll)
        
        # 底部按钮
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        save_btn = Button(text='保存', size_hint_x=0.5, font_size=dp(13),
                          background_color=(0.2, 0.6, 0.2, 1))
        cancel_btn = Button(text='取消', size_hint_x=0.5, font_size=dp(13),
                            background_color=(0.6, 0.4, 0.2, 1))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        
        popup = Popup(title='监控设置', content=content, size_hint=(0.95, 0.85))
        cancel_btn.bind(on_press=popup.dismiss)
        save_btn.bind(on_press=lambda inst: self._save_settings(
            popup, quiet_sw.active, start_input.text, end_input.text,
            cd_input.text, storm_input.text, kw_input.text, level_widgets
        ))
        popup.open()
    
    def _section_label(self, text):
        """设置面板分节标题"""
        lbl = Label(
            text='[b]' + text + '[/b]', markup=True,
            size_hint_y=None, height=dp(24), font_size=dp(13),
            color=(0.8, 0.95, 1, 1), halign='left', valign='middle'
        )
        lbl.bind(size=self._bind_header_size)
        return lbl
    
    def _save_settings(self, popup, quiet_enabled, start, end, cd, storm, kws, level_widgets):
        """保存设置面板的修改"""
        try:
            # 静默时段
            self.config_data["quiet_hours"] = {
                "enabled": bool(quiet_enabled),
                "start": start.strip() or "23:00",
                "end": end.strip() or "07:00",
            }
            # 冷却 / 风暴
            try:
                self.config_data["alert_cooldown_sec"] = max(0, int(cd or 30))
            except Exception:
                self.config_data["alert_cooldown_sec"] = 30
            try:
                self.config_data["alert_storm_window_sec"] = max(0, int(storm or 10))
            except Exception:
                self.config_data["alert_storm_window_sec"] = 10
            # 关键字
            kw_list = [k.strip() for k in (kws or '').split(',') if k.strip()]
            self.config_data["alert_keywords"] = kw_list if kw_list else list(ALERT_KEYWORDS)
            # 级别策略
            new_policy = {}
            for lv, w in level_widgets.items():
                try:
                    ms = int(w["ms"].text or 0)
                except Exception:
                    ms = 0
                new_policy[lv] = {
                    "vibrate": bool(w["vibrate"].active),
                    "wake": bool(w["wake"].active),
                    "notify": bool(w["notify"].active),
                    "sound": bool(w["sound"].active),
                    "vibrate_ms": ms,
                }
            self.config_data["level_policy"] = new_policy
            self.save_config()
            popup.dismiss()
            self.log_msg("设置已保存（静默/冷却/级别策略生效）", color=(0.5, 1, 0.8, 1))
        except Exception as e:
            self.log_msg("保存设置失败: " + str(e), color=(1, 0.5, 0.5, 1))
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
        except Exception as e:
            self.log_msg(f"配置加载失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_msg(f"配置保存失败: {e}")
    
    def apply_config(self):
        """应用配置到UI：渲染已保存的IP列表（兼容旧单 server_url 迁移）"""
        urls = self.config_data.get('server_urls', [])
        if not urls:
            old = self.config_data.get('server_url', '')
            urls = [old] if old else [LOCAL_WS_URL]
            self.config_data['server_urls'] = urls
            self.save_config()
        self.ip_rows = []
        self.ip_list_grid.clear_widgets()
        for url in urls:
            self._add_ip_row(url)
    
    def _validate_server_url(self, url):
        """校验服务端地址格式：支持 ws://IP:port / wss://IP:port / IP:port"""
        url = url.strip()
        if not url:
            return False, "地址为空"
        check = url
        for prefix in ('ws://', 'wss://'):
            if check.lower().startswith(prefix):
                check = check[len(prefix):]
                break
        check = check.split('/')[0]
        if ':' not in check:
            return False, "缺少端口（格式：IP:端口）"
        host, _, port = check.rpartition(':')
        if not host:
            return False, "缺少IP地址"
        try:
            p = int(port)
            if p < 1 or p > 65535:
                return False, "端口范围 1-65535"
        except ValueError:
            return False, "端口必须是数字"
        parts = host.split('.')
        if len(parts) == 4 and all(x.isdigit() and 0 <= int(x) <= 255 for x in parts if x.isdigit()):
            return True, "OK"
        if host.replace('-', '').replace('_', '').isalnum():
            return True, "OK"
        return False, "IP格式不合法"
    
    def _add_ip_row(self, url):
        """在IP列表UI中添加一行（可编辑输入框 + 删除按钮）"""
        idx = len(self.ip_rows) + 1
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(38), spacing=dp(6))
        idx_label = Label(
            text=str(idx),
            size_hint_x=0.08,
            font_size=dp(12),
            color=(0.7, 0.85, 1, 1),
            halign='center',
            valign='middle'
        )
        ip_input = TextInput(
            text=url,
            size_hint_x=0.67,
            font_size=dp(13),
            multiline=False,
            padding=[dp(8), dp(6)]
        )
        remove_btn = Button(
            text='删除',
            size_hint_x=0.25,
            font_size=dp(12),
            background_color=(0.8, 0.3, 0.3, 1)
        )
        row.add_widget(idx_label)
        row.add_widget(ip_input)
        row.add_widget(remove_btn)
        self.ip_list_grid.add_widget(row)
        row_info = {"row": row, "input": ip_input, "remove_btn": remove_btn, "url": url, "idx_label": idx_label}
        def _remove(instance):
            self._remove_ip_row(row_info)
        remove_btn.bind(on_press=_remove)
        def _on_text(instance, value):
            row_info["url"] = value.strip()
        ip_input.bind(on_text=_on_text)
        def _on_focus(instance, focused):
            if not focused:
                self._sync_ip_list_from_ui()
        ip_input.bind(focus=_on_focus)
        self.ip_rows.append(row_info)
    
    def _remove_ip_row(self, row_info):
        """删除一个IP行并同步配置"""
        if row_info in self.ip_rows:
            self.ip_rows.remove(row_info)
        self.ip_list_grid.remove_widget(row_info["row"])
        self._sync_ip_list_from_ui()
        self.log_msg("已移除一个服务端IP")
    
    def _sync_ip_list_from_ui(self):
        """从UI输入框同步IP列表到配置并保存"""
        urls = []
        for r in self.ip_rows:
            u = r["input"].text.strip()
            if u:
                urls.append(u)
        self.config_data['server_urls'] = urls
        self.save_config()
    
    def on_add_server(self, instance):
        """添加按钮：校验后加入IP列表"""
        raw = self.new_ip_input.text.strip()
        if not raw:
            self.log_msg("请先输入IP地址", color=(1, 0.8, 0, 1))
            return
        url = raw
        if not url.lower().startswith(('ws://', 'wss://')):
            url = 'ws://' + url
        ok, msg = self._validate_server_url(url)
        if not ok:
            self.log_msg("IP格式错误：" + msg + "（" + raw + "）", color=(1, 0.5, 0.5, 1))
            return
        existing = [r["input"].text.strip() for r in self.ip_rows]
        if url in existing:
            self.log_msg("该IP已存在：" + url, color=(1, 0.8, 0, 1))
            return
        self._add_ip_row(url)
        self._sync_ip_list_from_ui()
        self.new_ip_input.text = ''
        self.log_msg("已添加服务端IP：" + url, color=(0.5, 1, 0.5, 1))
    
    def _update_overall_status(self):
        """根据所有连接状态汇总显示总体状态（含心跳离线判定结果）"""
        total = len(self.ws_connections)
        if total == 0:
            self.update_status("[已断开]", (1, 0.3, 0.3, 1))
            return
        alive = 0
        offline_list = []
        for url, info in self.ws_connections.items():
            ws = info.get('ws')
            sock_ok = False
            try:
                if ws and ws.sock and ws.sock.connected:
                    sock_ok = True
            except Exception:
                pass
            # 心跳离线判定：即使WS socket显示已连接，只要心跳管理器标记为离线，就不算在线
            hb = self.hb_managers.get(url)
            hb_offline = hb.is_offline() if hb else False
            if sock_ok and not hb_offline:
                alive += 1
            if hb_offline:
                short = url
                for p in ('ws://', 'wss://'):
                    if short.lower().startswith(p):
                        short = short[len(p):]
                        break
                offline_list.append(short)
        offline_count = len(offline_list)
        if alive == total:
            self.update_status("[全部在线] (" + str(alive) + "/" + str(total) + ")", (0.3, 1, 0.3, 1))
        elif alive > 0:
            extra = f" 离线{offline_count}" if offline_count else ""
            self.update_status("[部分在线] (" + str(alive) + "/" + str(total) + ")" + extra, (1, 0.8, 0, 1))
        else:
            extra = f"（心跳离线 {offline_count} 个）" if offline_count else ""
            self.update_status("[全部断开]" + extra, (1, 0.3, 0.3, 1))
    
    def toggle_connection(self, instance):
        """切换连接状态（有任何活跃连接则全部断开，否则全部连接）"""
        any_running = any(info.get('running') for info in self.ws_connections.values())
        if any_running:
            self.stop_connection()
        else:
            self.start_connection()
    
    def start_connection(self):
        """启动连接：为每个配置的服务端IP各起一个独立连接线程"""
        if not WS_AVAILABLE:
            self.show_error("缺少 websocket-client 库，请先安装: pip install websocket-client")
            return
        self._sync_ip_list_from_ui()
        urls = [u for u in self.config_data.get('server_urls', []) if u.strip()]
        if not urls:
            self.show_error("请先添加至少一个服务端IP")
            return
        # 连接前先启动前台保活，避免后台立即被系统杀进程
        self.start_foreground_service()
        self.update_status("[连接中...]", (1, 0.8, 0, 1))
        self.connect_btn.text = '断开'
        self.connect_btn.background_color = (0.8, 0.2, 0.2, 1)
        self.log_msg("开始连接 " + str(len(urls)) + " 个服务端...", color=(0.8, 0.9, 1, 1))
        for url in urls:
            if url in self.ws_connections and self.ws_connections[url].get('running'):
                continue
            # 为该URL创建独立的心跳管理器（线程安全，与连接线程解耦）
            short = url
            for p in ('ws://', 'wss://'):
                if short.lower().startswith(p):
                    short = short[len(p):]
                    break
            if url not in self.hb_managers:
                self.hb_managers[url] = HeartbeatManager(self, url, short)
            self._batch_alerts_off.pop(url, None)
            self.ws_connections[url] = {"ws": None, "running": True, "thread": None, "attempts": 0}
            t = threading.Thread(target=self._ws_connect_thread, args=(url,), daemon=True)
            self.ws_connections[url]['thread'] = t
            t.start()
    
    def stop_connection(self):
        """停止所有连接：先停止各IP的应用层心跳管理器，再断开WS连接"""
        # 停止所有心跳管理器
        for url, hb in list(self.hb_managers.items()):
            try:
                hb.stop()
            except Exception:
                pass
        self.hb_managers.clear()
        self._batch_alerts_off.clear()
        for url, info in self.ws_connections.items():
            info['running'] = False
            ws = info.get('ws')
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass
        self.ws_connections = {}
        self._storm_dedup.clear()
        # 断开连接时停止前台保活（监控已停止，无必要常驻）
        self.stop_foreground_service()
        self.update_status("[已断开]", (1, 0.3, 0.3, 1))
        self.connect_btn.text = '连接'
        self.connect_btn.background_color = (0.2, 0.6, 0.2, 1)
        self.log_msg("已断开所有连接")
    
    def _ws_connect_thread(self, server_url):
        """单个服务端IP的连接线程（独立重连，互不影响）"""
        info = self.ws_connections.get(server_url)
        if not info:
            return
        short = server_url
        for p in ('ws://', 'wss://'):
            if short.lower().startswith(p):
                short = short[len(p):]
                break
        
        def on_open(ws):
            info['attempts'] = 0
            # 连接建立：启动应用层心跳，重置离线提醒标记
            hb = self.hb_managers.get(server_url)
            if hb:
                self._batch_alerts_off.pop(server_url, None)
                hb.start()
            Clock.schedule_once(lambda dt: self._schedule_overall_status(), 0)
            Clock.schedule_once(lambda dt: self.log_msg(f"已连接: {short}", color=(0.4,1,0.4,1)), 0)
            # 连接成功后确保前台保活处于运行态（用户可能在断开后重连）
            Clock.schedule_once(lambda dt: self.start_foreground_service(), 0)
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
            except (json.JSONDecodeError, TypeError):
                Clock.schedule_once(lambda dt, m=message, s=short: self.log_msg(f"[{s}] 非JSON消息: {m[:80]}"), 0)
                return
            if isinstance(data, dict):
                data['_source'] = short
            self._on_ws_message(data)
        
        def on_error(ws, error):
            err_str = str(error)
            err_lower = err_str.lower()
            is_timeout = ('timeout' in err_lower or 'ping' in err_lower or 'timed out' in err_lower)
            if is_timeout:
                Clock.schedule_once(lambda dt, s=short: self.log_msg(f"[{s}] 心跳超时: {error}", color=(1,0.4,0.4,1)), 0)
                alert_msg = f"[{short}] 心跳超时，连接已断开，将自动重连"
                Clock.schedule_once(lambda dt, m=alert_msg: self._trigger_alert(m), 0)
            else:
                Clock.schedule_once(lambda dt, e=error, s=short: self.log_msg(f"[{s}] WS错误: {e}", color=(1,0.5,0.5,1)), 0)
        
        def on_close(ws, code, reason):
            # 连接关闭：停止该连接的应用层心跳
            hb = self.hb_managers.get(server_url)
            if hb:
                hb.stop()
            Clock.schedule_once(lambda dt: self._schedule_overall_status(), 0)
            reason_str = str(reason).lower() if reason else ''
            is_timeout_close = (code in (1001, 1006) and ('timeout' in reason_str or 'ping' in reason_str))
            if is_timeout_close:
                Clock.schedule_once(lambda dt, s=short, c=code: self.log_msg(f"[{s}] 心跳超时断开 (code={c})", color=(1,0.4,0.4,1)), 0)
            else:
                Clock.schedule_once(lambda dt, s=short, c=code: self.log_msg(f"[{s}] 已关闭 (code={c})", color=(1,0.6,0.6,1)), 0)
        
        try:
            ws_app_obj = websocket.WebSocketApp(
                server_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            info['ws'] = ws_app_obj
            # 协议级ping完全禁用(ping_interval=0)，改用心跳管理器发送应用层JSON Ping（可精确计数与判定离线）
            ws_app_obj.run_forever(ping_interval=0)
        except Exception as e:
            Clock.schedule_once(lambda dt, s=short, e=e: self.log_msg(f"[{s}] 连接异常: {e}", color=(1,0.5,0.5,1)), 0)
        
        # 断线重连（仅在该连接仍处于运行意图时）
        if info.get('running'):
            info['attempts'] = info.get('attempts', 0) + 1
            delay = min(5 * (2 ** min(info['attempts'] - 1, 4)), 60)
            Clock.schedule_once(lambda dt, s=short, d=delay, n=info['attempts']: self.log_msg(f"[{s}] {d}秒后第{n}次重连..."), 0)
            time.sleep(delay)
            if info.get('running'):
                self._ws_connect_thread(server_url)
    
    def _on_ws_message(self, data):
        """处理 auto_order.py 推送的 JSON 消息
        
        消息格式：
          - 告警: {type:'alert', level, title, body, client_id, timestamp}
          - 状态: {type:'status', app_version, client_id, token_status, token_remain, connected_clients, timestamp}
          - 心跳响应: {type:'pong', timestamp, seq}
        """
        try:
            msg_type = data.get('type', '')
            client_id = data.get('client_id', '')
            ts = data.get('timestamp', 0)
            ts_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S') if ts else ''
            
            if msg_type == 'alert':
                level_field = data.get('level', 'info')
                title = data.get('title', '')
                body = data.get('body', '')
                source = data.get('_source', '')
                msg_text = (f"[{ts_str}] [{source}] {client_id} | {title}: {body}"
                            if source else f"[{ts_str}] {client_id} | {title}: {body}")
                # 【功能1】告警持久化（落盘 SQLite）——无论是否触发强提醒都要保存
                if self.alert_store:
                    try:
                        self.alert_store.insert_alert(
                            ts=ts or int(time.time()),
                            level=str(level_field),
                            client_id=client_id,
                            title=title,
                            body=body,
                            source=source,
                            full_text=msg_text,
                        )
                    except Exception:
                        pass
                # 级别综合判定（关键字 → 至少 error）
                actual_level = self._level_from_msg(level_field, msg_text)
                # 已取消客户端过滤，所有告警全部接收显示
                Clock.schedule_once(lambda dt, t=msg_text, lv=actual_level: self._display_message(t, lv), 0)
                # 按级别策略决定是否触发强提醒
                policy = self._get_level_policy(actual_level)
                need_strong = (policy["vibrate"] or policy["wake"] or policy["notify"] or policy["sound"])
                if need_strong:
                    Clock.schedule_once(lambda dt, t=msg_text, lv=actual_level: self._trigger_alert(t, lv), 0)
            
            elif msg_type == 'status':
                token_status = data.get('token_status', '')
                token_remain = data.get('token_remain', '')
                connected = data.get('connected_clients', 0)
                source = data.get('_source', '')
                prefix = f"[{source}] " if source else ""
                msg_text = (f"[{ts_str}] {prefix}{client_id} 状态: token={token_status}, "
                            f"剩余={token_remain}, App连接数={connected}")
                # 【功能2】客户端状态结构化看板：保存以便后续 UI 扩展使用
                if source:
                    try:
                        self.client_status[source] = {
                            "client_id": client_id,
                            "token_status": token_status,
                            "token_remain": token_remain,
                            "connected_clients": connected,
                            "ts": ts or int(time.time()),
                        }
                    except Exception:
                        pass
                Clock.schedule_once(lambda dt, m=msg_text: self.log_msg(f"[状态] {m}",
                    color=(0.6, 0.9, 1, 1)), 0)
            
            elif msg_type == 'pong':
                # 心跳Pong响应：交给对应来源的心跳管理器处理（清零连续失败、取消超时计时器）
                # 成功响应不记录正常日志（只记录异常）
                source = data.get('_source', '')
                remote_ts = data.get('timestamp', 0)
                hb = None
                if source:
                    # 按来源IP前缀反查对应的心跳管理器
                    for url, mgr in self.hb_managers.items():
                        if source in url:
                            hb = mgr
                            break
                if hb is None:
                    # 尝试全部管理器中第一个处于pending状态的
                    for mgr in self.hb_managers.values():
                        hb = mgr
                        break
                if hb:
                    hb.on_pong_received(remote_ts)
            
            else:
                Clock.schedule_once(lambda dt, d=data: self.log_msg(f"未知消息: {d}"), 0)
                
        except Exception as e:
            import traceback
            err_msg = f"消息处理异常: {e}\n{traceback.format_exc()}"
            Clock.schedule_once(lambda dt: self.log_msg(err_msg), 0)
    

    def _contains_alert_keywords(self, text):
        """检查是否包含告警关键字"""
        for keyword in ALERT_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _display_message(self, msg_text, level=None):
        """显示消息到日志区（log_msg 已自动添加本地接收时间戳）
        支持按告警级别差异化着色
        """
        lv = level or ALERT_LEVEL_INFO
        if lv in ALERT_LEVEL_COLOR:
            msg_color = ALERT_LEVEL_COLOR[lv]
        else:
            is_alert = self._contains_alert_keywords(msg_text)
            msg_color = (1, 0.4, 0.4, 1) if is_alert else (0.9, 0.9, 0.9, 1)
        lv_tag = "[%s] " % lv.upper() if lv != ALERT_LEVEL_INFO else ""
        prefix = "[告警] " if lv in (ALERT_LEVEL_ERROR, ALERT_LEVEL_CRITICAL) else "[消息] "
        # 显示格式: [本地接收时间] [告警] [级别] [服务端推送时间] 客户端 | 标题: 内容
        self.log_msg(f"{prefix}{lv_tag}{msg_text}", color=msg_color)
    
    def _trigger_alert(self, msg_text, level):
        """触发 Android 原生强提醒

        新增特性：
          - 风暴抑制：N秒内同一客户端同内容合并显示重复计数
          - 冷却键升级为 (client_id, 内容哈希)，避免不同告警互相抑制
          - 结合分级策略 + 静默时段，决定是否真正触发强提醒
        """
        # 1) 取分级策略，静默时段内自动降级
        policy = self._get_level_policy(level)
        need_vibrate = policy["vibrate"]
        need_wake    = policy["wake"]
        need_notify  = policy["notify"]
        need_sound   = policy["sound"]
        if not (need_vibrate or need_wake or need_notify or need_sound):
            # 静默时段或级别关闭所有提醒通道
            return

        # 2) 提取客户端名 + 内容摘要，用于冷却和风暴抑制
        client_name = self._extract_client_name(msg_text)
        # 内容哈希：去掉时间戳，只保留核心内容部分用于去重
        import re
        core = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*', '', msg_text)
        dedup_key = (client_name or "", hash(core) & 0xFFFFFFFF)
        current_time = time.time()

        # 3) 风暴抑制：告警合并
        storm_win = int(self.config_data.get("alert_storm_window_sec", 10))
        if dedup_key in self._storm_dedup:
            cnt, last_ts = self._storm_dedup[dedup_key]
            if current_time - last_ts <= storm_win:
                new_cnt = cnt + 1
                self._storm_dedup[dedup_key] = (new_cnt, current_time)
                # 窗口内只第一次触发，后续更新日志提示重复次数（不重复强提醒）
                self.log_msg(f"{client_name} 告警重复 {new_cnt} 次，已抑制", color=(1, 0.6, 0.2, 1))
                return
            # 超出窗口，重置计数继续处理
        self._storm_dedup[dedup_key] = (1, current_time)
        # 清理旧条目（避免内存泄漏）
        try:
            expired = [k for k, (_, ts) in self._storm_dedup.items()
                       if current_time - ts > storm_win * 3]
            for k in expired:
                self._storm_dedup.pop(k, None)
        except Exception:
            pass

        # 4) 告警冷却检查（同一客户端+同一内容 在冷却窗口内只触发一次强提醒）
        cooldown = int(self.config_data.get("alert_cooldown_sec", 30))
        if dedup_key in last_alert_time:
            if current_time - last_alert_time[dedup_key] < cooldown:
                self.log_msg(f"{client_name} 告警冷却中，仅上屏")
                return
        last_alert_time[dedup_key] = current_time

        # 5) 触发原生提醒（按级别差异化处置）
        self._android_alert(msg_text, level, policy)
    
    def _extract_client_name(self, msg_text):
        """从消息中提取客户端名"""
        import re
        # 优先匹配新格式: "[时间] 客户端名 | 内容"（auto_order.py 推送的 alert 格式）
        match = re.search(r'\]\s*([^|\s]+)\s*\|', msg_text)
        if match:
            return match.group(1)
        # 匹配 "客户端: XXX" 或 "客户端：XXX" 格式
        match = re.search(r'(?:客户端[:：]\s*)([^\s,，。]+)', msg_text)
        if match:
            return match.group(1)
        # 匹配 "XXX:" 格式（冒号前的非空白非时间内容）
        match = re.search(r'^([^\s:：,，。\[\]]+)', msg_text)
        if match:
            return match.group(1)
        return "unknown"
    
    def _android_alert(self, msg_text, level, policy):
        """Android 原生强提醒（按级别差异化：震动时长 / 唤醒 / 通知优先级 / 响铃）

        policy 字段：vibrate, wake, notify, sound, vibrate_ms, priority
        """
        if not ANDROID_AVAILABLE:
            self.log_msg("非 Android 环境，跳过原生提醒")
            return

        need_vibrate = bool(policy.get("vibrate", False))
        need_wake    = bool(policy.get("wake", False))
        need_notify  = bool(policy.get("notify", False))
        need_sound   = bool(policy.get("sound", False))
        vibrate_ms   = int(policy.get("vibrate_ms", 0) or 0)
        priority_tag = (policy.get("priority") or "default").lower()

        try:
            # 1. 震动（按级别差异化时长；critical 级走波形模式，更醒目）
            if need_vibrate and vibrate_ms > 0:
                try:
                    Vibrator = autoclass('android.os.Vibrator')
                    Activity = autoclass('org.kivy.android.PythonActivity')
                    activity = Activity.mActivity
                    vibrator = activity.getSystemService(
                        autoclass('android.content.Context').VIBRATOR_SERVICE
                    )
                    if vibrator:
                        BuildVERSION = autoclass('android.os.Build$VERSION')
                        SDK_INT = int(BuildVERSION.SDK_INT)
                        if SDK_INT >= 26:
                            try:
                                VibrationEffect = autoclass('android.os.VibrationEffect')
                                if level == ALERT_LEVEL_CRITICAL:
                                    # 严重级：波形震动（短-长-长，更急促）
                                    pattern = [0, 120, 60, 120, 60, 400]
                                    amplitudes = [-1, 255, 0, 255, 0, 255]
                                    effect = VibrationEffect.createWaveform(pattern, amplitudes, -1)
                                else:
                                    effect = VibrationEffect.createOneShot(vibrate_ms, 255)
                                vibrator.vibrate(effect)
                            except Exception:
                                effect = VibrationEffect.createOneShot(max(vibrate_ms, 400), 255)
                                vibrator.vibrate(effect)
                        else:
                            try:
                                if level == ALERT_LEVEL_CRITICAL:
                                    vibrator.vibrate([0, 120, 60, 120, 60, 400], -1)
                                else:
                                    vibrator.vibrate(vibrate_ms)
                            except Exception:
                                vibrator.vibrate(max(vibrate_ms, 400))
                except Exception as e:
                    self.log_msg(f"震动失败: {e}")

            # 2. 唤醒屏幕（仅 error/critical 级按策略唤醒）
            if need_wake:
                try:
                    PowerManager = autoclass('android.os.PowerManager')
                    activity = autoclass('org.kivy.android.PythonActivity').mActivity
                    power_manager = activity.getSystemService(
                        autoclass('android.content.Context').POWER_SERVICE
                    )
                    wake_lock = power_manager.newWakeLock(
                        PowerManager.SCREEN_BRIGHT_WAKE_LOCK
                        | PowerManager.ACQUIRE_CAUSES_WAKEUP,
                        "monitor_app:alert"
                    )
                    wake_lock.acquire(3000)
                except Exception as e:
                    self.log_msg(f"唤醒屏幕失败: {e}")

            # 3. 发送通知（按级别差异化优先级 + 渠道重要性）
            if need_notify:
                try:
                    NotificationManager = autoclass('android.app.NotificationManager')
                    NotificationChannel = autoclass('android.app.NotificationChannel')
                    NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
                    Intent = autoclass('android.content.Intent')
                    PendingIntent = autoclass('android.app.PendingIntent')

                    activity = autoclass('org.kivy.android.PythonActivity').mActivity
                    notification_manager = activity.getSystemService(
                        autoclass('android.content.Context').NOTIFICATION_SERVICE
                    )

                    # 不同级别走不同渠道，用户可在系统设置中分别关闭声音/震动
                    level_channel_map = {
                        ALERT_LEVEL_INFO:     ("alert_info",     "信息通知",     NotificationManager.IMPORTANCE_LOW,
                                               NotificationCompat.PRIORITY_LOW),
                        ALERT_LEVEL_WARNING:  ("alert_warning",  "警告通知",     NotificationManager.IMPORTANCE_DEFAULT,
                                               NotificationCompat.PRIORITY_DEFAULT),
                        ALERT_LEVEL_ERROR:    ("alert_error",    "错误告警",     NotificationManager.IMPORTANCE_HIGH,
                                               NotificationCompat.PRIORITY_HIGH),
                        ALERT_LEVEL_CRITICAL: ("alert_critical", "严重告警",     NotificationManager.IMPORTANCE_MAX,
                                               NotificationCompat.PRIORITY_MAX),
                    }
                    default_entry = level_channel_map[ALERT_LEVEL_ERROR]
                    ch_id, ch_name, ch_imp, ntf_priority = level_channel_map.get(level, default_entry)

                    try:
                        channel = NotificationChannel(ch_id, ch_name, ch_imp)
                        channel.enableVibration(need_vibrate)
                        channel.enableLights(level in (ALERT_LEVEL_ERROR, ALERT_LEVEL_CRITICAL))
                        if need_sound and level in (ALERT_LEVEL_ERROR, ALERT_LEVEL_CRITICAL):
                            # 使用系统默认提示音；如后续要自定义铃声可在这里替换 Uri
                            channel.setSound(
                                autoclass('android.media.RingtoneManager').getDefaultUri(
                                    autoclass('android.media.RingtoneManager').TYPE_NOTIFICATION
                                ), None
                            )
                        notification_manager.createNotificationChannel(channel)
                    except Exception:
                        pass

                    intent = Intent(activity, activity.getClass())
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)

                    BuildVERSION = autoclass('android.os.Build$VERSION')
                    SDK_INT = int(BuildVERSION.SDK_INT)
                    if SDK_INT >= 31:
                        flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
                    else:
                        flags = PendingIntent.FLAG_UPDATE_CURRENT

                    pending_intent = PendingIntent.getActivity(activity, 0, intent, flags)

                    AndroidR = autoclass('android.R$drawable')
                    small_icon = getattr(AndroidR, 'ic_dialog_alert', 0) or 17301543

                    # 标题带级别，用户一眼识别严重程度
                    title_map = {
                        ALERT_LEVEL_INFO:     "[信息]",
                        ALERT_LEVEL_WARNING:  "[警告]",
                        ALERT_LEVEL_ERROR:    "[错误告警]",
                        ALERT_LEVEL_CRITICAL: "[严重告警]",
                    }
                    show_title = title_map.get(level, "[告警]")

                    builder = NotificationCompat.Builder(activity, ch_id) \
                        .setSmallIcon(small_icon) \
                        .setContentTitle(show_title) \
                        .setContentText(msg_text[:120]) \
                        .setStyle(NotificationCompat.BigTextStyle().bigText(msg_text)) \
                        .setPriority(ntf_priority) \
                        .setAutoCancel(True) \
                        .setContentIntent(pending_intent)
                    if level in (ALERT_LEVEL_ERROR, ALERT_LEVEL_CRITICAL):
                        builder.setDefaults(0)  # 不重复走默认，震动和声音由渠道控制
                    # 每条告警用一个独立 ID，避免新旧告警互相覆盖丢失；critical 保留一个高优ID
                    notif_id = 2000 + (hash(msg_text) & 0x7FF)
                    if level == ALERT_LEVEL_CRITICAL:
                        notif_id = 2999
                    notification_manager.notify(notif_id, builder.build())
                except Exception as e:
                    self.log_msg(f"通知发送失败: {e}")

            # 4. 响铃（error/critical 级按策略播放系统通知音，用于没有配通知渠道或渠道静音兜底）
            if need_sound:
                try:
                    RingtoneManager = autoclass('android.media.RingtoneManager')
                    Uri = autoclass('android.net.Uri')
                    uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                    if uri:
                        ringtone = RingtoneManager.getRingtone(
                            autoclass('org.kivy.android.PythonActivity').mActivity, uri
                        )
                        if ringtone:
                            ringtone.play()
                except Exception as e:
                    self.log_msg(f"响铃失败: {e}")

            self.log_msg(f"强提醒已触发({level})")

        except Exception as e:
            self.log_msg(f"原生提醒异常: {e}")
    
    def query_status(self, instance):
        """查询所有已连接客户端状态（向每个活跃连接发送 query_status 指令）"""
        active = [(url, info) for url, info in self.ws_connections.items()
                  if info.get('ws')]
        if not active:
            self.show_error("请先连接到抢单软件")
            return
        sent = 0
        fail = 0
        payload = json.dumps({"action": "query_status"})
        for url, info in active:
            ws = info.get('ws')
            try:
                ws.send(payload)
                sent += 1
            except Exception as e:
                fail += 1
                self.log_msg(f"[{url}] 查询发送失败: {e}")
        self.log_msg(f"已向 {sent} 个服务端发送状态查询" + (f"，{fail} 个失败" if fail else ""))
    

    def clear_screen(self, instance):
        """清空日志"""
        self.log_lines = []
        self.log_grid.clear_widgets()
        self.log_msg("日志已清空")
    
    def log_msg(self, msg, color=None):
        """添加日志（线程安全，UI 未就绪时只写 stderr）"""
        # 始终写 stderr（logcat 可抓）
        try:
            print("[" + datetime.now().strftime("%H:%M:%S") + "] " + str(msg), file=sys.stderr)
            sys.stderr.flush()
        except Exception:
            pass
        
        # UI 未就绪时不操作 UI（防 AttributeError 闪退）
        if not getattr(self, "_ui_ready", False) or self.log_scroll is None or self.log_grid is None:
            return
        
        def _add_log():
            # 双重检查（防止竞态）
            if self.log_scroll is None or self.log_grid is None:
                return
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                line_color = color or (0.9, 0.9, 0.9, 1)
                
                scroll_w = self.log_scroll.width if self.log_scroll.width > 0 else 300
                
                label = Label(
                    text=f"[{timestamp}] {msg}",
                    size_hint_y=None,
                    height=dp(34),
                    text_size=(scroll_w - dp(16), None),
                    valign='middle',
                    halign='left',
                    color=line_color,
                    font_size=dp(12),
                    padding=[dp(4), dp(2)]
                )
                label.bind(size=self._bind_label_size)
                
                self.log_grid.add_widget(label)
                self.log_lines.append(label)
                
                # 限制日志数量
                while len(self.log_lines) > self.max_log_lines:
                    old = self.log_lines.pop(0)
                    self.log_grid.remove_widget(old)
                
                # 自动滚动到底部
                self.log_scroll.scroll_y = 0
            except Exception as e:
                try:
                    print("log_msg _add_log error: " + str(e), file=sys.stderr)
                except Exception:
                    pass
        
        try:
            if threading.current_thread() != threading.main_thread():
                Clock.schedule_once(lambda dt: _add_log(), 0)
            else:
                _add_log()
        except Exception:
            pass
    
    def _bind_label_size(self, instance, value):
        instance.text_size = (value[0], None)
    
    def update_status(self, text, color):
        """更新状态栏"""
        self.status_label.text = text
        self.status_label.color = color
    
    def show_error(self, msg):
        """显示错误弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=msg, font_size=dp(14)))
        
        close_btn = Button(text='确定', size_hint_y=None, height=dp(40))
        popup = Popup(title='错误', content=content, size_hint=(0.8, 0.3))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    # ================ 新增：崩溃检测与前台服务保活 ================
    def _show_crash_tip(self):
        """上次异常退出的提示（仅在检测到 crash.txt 非空时触发）"""
        try:
            self.log_msg("[注意] 检测到上次异常退出日志，请查看 /sdcard/crash.txt", color=(1, 0.5, 0, 1))
        except Exception:
            pass

    def start_foreground_service(self):
        """启动 Android 前台服务：创建常驻通知栏，防止 App 退后台后被系统杀进程
        任何错误都不抛异常，前台服务失败不影响核心告警功能
        """
        if not ANDROID_AVAILABLE or self._foreground_running:
            return
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            BuildVERSION = autoclass('android.os.Build$VERSION')
            SDK_INT = int(BuildVERSION.SDK_INT)

            # 1) 创建通知渠道（前台服务必须）
            NotificationManager = autoclass('android.app.NotificationManager')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
            Context = autoclass('android.content.Context')
            nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)
            fg_channel_id = "monitor_foreground"
            try:
                channel = NotificationChannel(
                    fg_channel_id,
                    "监控保活",
                    NotificationManager.IMPORTANCE_MIN  # 前台服务不需要声音，保持最低打扰
                )
                channel.setShowBadge(False)
                channel.enableVibration(False)
                nm.createNotificationChannel(channel)
            except Exception:
                pass

            # 2) 构建前台服务通知（常驻通知栏）
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            intent = Intent(activity, activity.getClass())
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
            if SDK_INT >= 31:
                flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            else:
                flags = PendingIntent.FLAG_UPDATE_CURRENT
            pending_intent = PendingIntent.getActivity(activity, 0, intent, flags)

            AndroidR = autoclass('android.R$drawable')
            small_icon = getattr(AndroidR, 'stat_sys_download', 0) or 17301633
            notification = NotificationCompat.Builder(activity, fg_channel_id) \
                .setSmallIcon(small_icon) \
                .setContentTitle("抢单告警监控运行中") \
                .setContentText("后台保活已开启，实时接收告警") \
                .setOngoing(True) \
                .setContentIntent(pending_intent) \
                .setPriority(NotificationCompat.PRIORITY_MIN) \
                .build()

            # 3) 使用 Activity.startForeground 将当前应用窗口提升为前台服务态
            #    说明：Kivy SDL2 bootstrap 本身就是一个 Activity，直接在其上启动前台
            #    即可达到保活效果，无需额外写 Java Service 类
            FG_NOTIF_ID = 2025
            try:
                if SDK_INT >= 29:  # Android 10+ 需要 FOREGROUND_SERVICE 权限（已在 spec 声明）
                    activity.startForeground(FG_NOTIF_ID, notification)
                else:
                    activity.startForeground(FG_NOTIF_ID, notification)
                self._foreground_running = True
                self.log_msg("[保活] 前台服务已启动", color=(0.5, 1, 0.8, 1))
            except Exception as e:
                # 兜底方案：直接 notify 一个常驻通知（不保活但至少用户可见）
                try:
                    nm.notify(FG_NOTIF_ID, notification)
                    self.log_msg("[保活] startForeground 失败，降级为常驻通知：" + str(e),
                                 color=(1, 0.7, 0.4, 1))
                except Exception as ee:
                    self.log_msg("[保活] 启动失败：" + str(ee), color=(1, 0.5, 0.5, 1))
        except Exception as e:
            try:
                self.log_msg("[保活] 启动异常：" + str(e), color=(1, 0.5, 0.5, 1))
            except Exception:
                pass

    def stop_foreground_service(self):
        """停止前台服务（用户手动断开连接时调用）"""
        if not ANDROID_AVAILABLE or not self._foreground_running:
            return
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            activity.stopForeground(True)
            self._foreground_running = False
            self.log_msg("[保活] 前台服务已停止", color=(0.8, 0.8, 0.4, 1))
        except Exception as e:
            try:
                self.log_msg("[保活] stop 失败：" + str(e), color=(1, 0.5, 0.5, 1))
            except Exception:
                pass

    # ================ 新增：静默时段 / 告警分级策略 ================
    def _is_quiet_now(self):
        """判断当前是否在静默时段内（本地时间）
        跨午夜场景：start=23:00, end=07:00 → 23:00~次日07:00 都算静默
        """
        qh = self.config_data.get("quiet_hours", {})
        if not qh.get("enabled"):
            return False
        try:
            def _h(s):
                hh, mm = s.split(":")
                return int(hh) * 60 + int(mm)
            now = datetime.now()
            cur = now.hour * 60 + now.minute
            s = _h(qh["start"])
            e = _h(qh["end"])
            if s <= e:
                return s <= cur < e
            else:
                # 跨午夜：start(23:00) → 24:00，00:00 → end(07:00)
                return cur >= s or cur < e
        except Exception:
            return False

    def _get_level_policy(self, level):
        """获取指定告警级别的处置策略；若处于静默时段，则把震动/响铃/唤醒全部关闭
        """
        policy = DEFAULT_LEVEL_POLICY.get(level, DEFAULT_LEVEL_POLICY[ALERT_LEVEL_WARNING])
        # 用户配置覆盖
        user_policies = self.config_data.get("level_policy", {}) or {}
        if level in user_policies and isinstance(user_policies[level], dict):
            merged = dict(policy)
            merged.update(user_policies[level])
            policy = merged
        if self._is_quiet_now():
            policy = dict(policy)
            policy["vibrate"] = False
            policy["wake"] = False
            policy["sound"] = False
        return policy

    def _level_from_msg(self, level_field, text):
        """结合消息自带的 level 字段 + 关键字匹配，综合判定实际告警级别
        """
        lv = (level_field or "").lower()
        if lv in (ALERT_LEVEL_INFO, ALERT_LEVEL_WARNING, ALERT_LEVEL_ERROR, ALERT_LEVEL_CRITICAL):
            final = lv
        else:
            final = ALERT_LEVEL_INFO
        # 关键字命中 → 至少升级到 error
        kws = self.config_data.get("alert_keywords") or ALERT_KEYWORDS
        for kw in kws:
            if kw and kw in (text or ""):
                if final in (ALERT_LEVEL_INFO, ALERT_LEVEL_WARNING):
                    final = ALERT_LEVEL_ERROR
                break
        return final

    # ================ 新增：节流版总体状态更新 ================
    def _schedule_overall_status(self):
        """节流版 _update_overall_status：500ms 内多次调用合并为一次 UI 刷新"""
        if self._status_update_scheduled:
            return
        self._status_update_scheduled = True
        Clock.schedule_once(self._do_throttled_status, 0.5)

    def _do_throttled_status(self, _dt):
        self._status_update_scheduled = False
        try:
            self._update_overall_status()
        except Exception:
            pass

    def on_stop(self):
        """Kivy App 生命周期钩子：进程退出前清理资源（关闭 AlertStore、前台服务、心跳等）"""
        try:
            super().on_stop()
        except Exception:
            pass
        # 关闭告警存储，确保落盘
        try:
            if self.alert_store:
                self.alert_store.close()
                self.alert_store = None
        except Exception:
            pass
        # 停止前台保活
        try:
            self.stop_foreground_service()
        except Exception:
            pass
        # 清空风暴抑制/冷却缓存
        try:
            self._storm_dedup.clear()
            last_alert_time.clear()
        except Exception:
            pass

    def _request_android_permissions(self):
        """动态申请运行时权限：Android 13+ 必须先申请 POST_NOTIFICATIONS 才能发送通知
        任何错误都不抛异常，权限缺失只是通知不能用，绝不闪退
        """
        if not ANDROID_AVAILABLE or self._android_perms_requested:
            return
        try:
            from android.permissions import request_permissions, Permission
            BuildVERSION = autoclass('android.os.Build$VERSION')
            SDK_INT = int(BuildVERSION.SDK_INT)
            perms = []
            # Android 13+ (API 33)：POST_NOTIFICATIONS 必须动态申请
            if SDK_INT >= 33:
                try:
                    perms.append(Permission.POST_NOTIFICATIONS)
                except Exception:
                    # 老版本 p4a 没定义这个常量，直接写字符串兜底
                    perms.append("android.permission.POST_NOTIFICATIONS")
            if perms:
                try:
                    request_permissions(perms)
                    self._android_perms_requested = True
                    self.log_msg(f"已申请运行时权限: {perms}")
                except Exception as e:
                    self.log_msg(f"权限申请失败（不影响使用）: {e}")
            else:
                self._android_perms_requested = True
        except Exception as e:
            # 权限模块任何问题都不影响 App 启动，只是通知/震动可能不可用
            self.log_msg(f"权限初始化跳过（不影响使用）: {e}")
            self._android_perms_requested = True

if __name__ == '__main__':
    try:
        MonitorApp().run()
    except Exception as e:
        # 主线程异常也写崩溃日志
        _write_crash_log(type(e), e, e.__traceback__)
        # 试图弹窗显示（如果 Kivy 还能弹）
        try:
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            from kivy.app import App
            class CrashApp(App):
                def build(self):
                    return Label(
                        text="App 崩溃：" + str(e) + "\n\n崩溃日志已写到：\n/sdcard/crash.txt\n\n请截图发开发者",
                        color=(1,0,0,1),
                        size_hint=(1,1),
                        halign="center",
                        valign="middle"
                    )
            CrashApp().run()
        except Exception:
            pass
        raise