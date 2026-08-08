[app]

# (str) Title of the application
title = 抢单软件告警

# (str) Package name
package.name = orderalert

# (str) Package domain (needed for android/ios packaging)
package.domain = org.orderalert

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otf

# (list) List of inclusions (glob pattern)
source.include_dirs =

# (list) List of exclusions
source.exclude_dirs = tests, bin, .git, build, dist, __pycache__, chrome_data, EasyFlow*.exe_extracted

# (list) Source files to exclude (glob pattern)
source.exclude_patterns = test_*.py, remove_*.py, fix_*.py, *_debug.py

# (str) Application versioning (method 1)
version = 2.0.0

# (list) Application requirements
requirements = python3,kivy,pyjnius,websocket-client,requests

# (str) Supported orientation (one of 'portrait', 'landscape' or 'sensor' for automatic)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific directives
#

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (str) Android NDK version to use
# 完全注释掉 android.ndk，由 Buildozer 自动下载默认兼容的 NDK 版本，防止 404 下载报错
# android.ndk = 25b

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (list) Permission the application needs
android.permissions = INTERNET, VIBRATE, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, ACCESS_NETWORK_STATE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk or aar).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use, defaults to master
# 注释掉 stable 分支，自动选用默认 master 分支
# p4a.branch = stable

# (str) Bootstrap to use for python-for-android
p4a.bootstrap = sdl2

# (int) Number of parallel jobs to build with
p4a.njobs = 2

# (bool) Skip running-as-root warning
warn_on_root = 0

#
# iOS specific directives
#
ios.bundle_name = orderalert
ios.version = 2.0.0

#
# Commands
#
default_build_type = debug
