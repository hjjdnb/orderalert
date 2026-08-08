[app]

# 应用名称
title = 抢单软件告警


# 包名（只能英文）
package.name = orderalert


# 包域名
package.domain = com.orderalert


# 项目目录
source.dir = .


# 主程序
source.main = main.py


# 包含文件
source.include_exts = py,png,jpg,jpeg,kv,json,txt



# 版本
version = 1.0



# Python依赖
requirements = python3,kivy,requests,websocket-client,certifi,pyjnius



# 屏幕方向
orientation = portrait


# 非全屏
fullscreen = 0




# =====================
# Android设置
# =====================


# Android API
android.api = 33


# 最低版本
android.minapi = 24


# 只生成64位
android.archs = arm64-v8a



# 使用SDL2
p4a.bootstrap = sdl2



# 使用新版 python-for-android
p4a.branch = master



# 开启AndroidX
android.enable_androidx = True



# 自动接受SDK协议
android.accept_sdk_license = True




# =====================
# 权限
# =====================


android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS




# =====================
# 编译参数
# =====================


log_level = 2



# 输出APK
android.release_artifact = apk




# =====================
# 优化
# =====================


android.no-byte-compile-python = True
