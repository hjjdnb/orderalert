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


# 包含文件类型
source.include_exts = py,png,jpg,jpeg,kv,json,txt


# 版本号
version = 1.0



# Python依赖
# 根据你的main.py实际导入修改
requirements = python3,kivy,requests,websocket-client,certifi,pyjnius


# 屏幕方向
orientation = portrait


# 不全屏
fullscreen = 0



# =====================
# Android配置
# =====================


# Android SDK版本
android.api = 33


# 最低支持Android版本
android.minapi = 24


# 只生成64位APK
android.archs = arm64-v8a


# 使用SDL2
p4a.bootstrap = sdl2


# 使用最新p4a
p4a.branch = develop



# 开启AndroidX
android.enable_androidx = True


# 接受SDK协议
android.accept_sdk_license = True



# =====================
# 权限
# =====================


android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS



# =====================
# 编译设置
# =====================


# 日志等级
log_level = 2


# 使用APK输出
android.release_artifact = apk



# =====================
# 优化
# =====================


# 保留符号
android.add_src = .


# 不压缩Python文件
android.no-byte-compile-python = True
