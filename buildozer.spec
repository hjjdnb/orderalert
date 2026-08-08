[app]

# 应用名称
title = 抢单软件告警


# 包名
package.name = orderalert


# 包域名
package.domain = com.orderalert


# 源代码目录
source.dir = .


# 包含文件
source.include_exts = py,png,jpg,jpeg,kv,json,txt


# 版本
version = 1.0


# 主程序
source.main = main.py


# Python依赖
requirements = python3,kivy,pyjnius,websocket-client,requests,certifi,openssl


# 屏幕方向
orientation = portrait


# 不全屏
fullscreen = 0



# =========================
# Android配置
# =========================


# Android API
android.api = 33


# 最低支持版本
android.minapi = 24


# 只打64位
android.archs = arm64-v8a


# 使用SDL2
p4a.bootstrap = sdl2


# 开启AndroidX
android.enable_androidx = True


# 接受SDK协议
android.accept_sdk_license = True



# =========================
# 权限
# =========================

android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS



# =========================
# 编译设置
# =========================

log_level = 2


# 使用新的Gradle
android.gradle_dependencies =



# =========================
# 优化
# =========================

android.release_artifact = apk
