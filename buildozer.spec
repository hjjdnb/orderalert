[app]

# 应用名称
title = 抢单软件告警


# 包名（只能英文）
package.name = orderalert


# 包域名
package.domain = com.orderalert


# 源代码目录
source.dir = .


# 主程序
source.main = main.py


# 包含文件
source.include_exts = py,png,jpg,kv,json,txt


# 版本
version = 1.0


# Python依赖
requirements = python3,kivy,pyjnius,websocket-client,requests,certifi,openssl


# Kivy入口
orientation = portrait


# 是否全屏
fullscreen = 0



# -----------------------
# Android设置
# -----------------------


# Android API
android.api = 33


# 最低安卓版本
android.minapi = 24


# 64位
android.archs = arm64-v8a


# NDK版本
android.ndk = 25b


# NDK API
android.ndk_api = 24


# 使用SDL2
p4a.bootstrap = sdl2



# -----------------------
# 权限
# -----------------------

android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS



# -----------------------
# 日志
# -----------------------

log_level = 2



# -----------------------
# Android启动模式
# -----------------------

android.entrypoint = org.kivy.android.PythonActivity



# -----------------------
# 构建优化
# -----------------------

android.accept_sdk_license = True


android.enable_androidx = True



# -----------------------
# 打包设置
# -----------------------

# 不打包无用架构
android.release_artifact = apk


# 保留Python代码
android.add_src = .
