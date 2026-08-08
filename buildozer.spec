[app]


title = 抢单软件告警


package.name = orderalert


package.domain = com.orderalert


source.dir = .


source.main = main.py


source.include_exts = py,png,jpg,jpeg,kv,json,txt



version = 1.0



requirements = python3,kivy,requests,websocket-client,certifi,pyjnius



orientation = portrait


fullscreen = 0




# Android


android.api = 33


android.minapi = 24


android.archs = arm64-v8a



p4a.bootstrap = sdl2


p4a.branch = master



android.enable_androidx = True


android.accept_sdk_license = True



android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS



log_level = 2


android.release_artifact = apk


android.no-byte-compile-python = True
