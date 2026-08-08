[app]

# (str) Title of the application
title = 抢单软件告警

# (str) Package name
package.name = orderalert

# (str) Package domain (needed for android/ios packaging)
package.domain = com.orderalert

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
# comma separated e.g. requirements = sqlite3,kivy
# pyjnius: Android native API (Vibrator/Notification/PowerManager)
# websocket-client: WS client connecting to auto_order.py:18888
requirements = python3,kivy,pyjnius,websocket-client,requests,certifi,openssl

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
garden_requirements =

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of 'portrait', 'landscape' or 'sensor' for automatic)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Extra arguments to pass to the android build
# e.g. extra_manifest_arguments = --use-permissions-opt

#
# Android specific directives
#

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
# API 24+ required for NotificationChannel (Android 8.0+) used in _android_alert
android.minapi = 24

# Android 64位
android.archs = arm64-v8a

# (int) Android SDK version to use
#android.sdk = 24

# (str) Android NDK version to use
# p4a stable 分支最兼容 NDK r19c（避免 ndk_ver 解析失败）
android.ndk = r19c

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
# WSL: /home/username/.buildozer/android/platform/android-ndk-r19c
# Colab: /root/.buildozer/android/platform/android-ndk-r19c
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path =

# (str) ANT executable (if empty, it will be automatically downloaded.)
#android.ant_path =

# (bool) skip aversio check
#android.skip_aapt = True

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars are only
# a burden.
# See https://python-for-android.readthedocs.io/en/latest/buildoptions.html#androidjni
#android.add_jars = foo.jar,bar.jar

# (list) List of Java files to add to the android project (can be java or a
# temporary directory)
#android.add_src =

# (list) Android AAR archives to add
#android.add_aars =

# (list) Gradle dependencies to add
#android.gradle_dependencies =

# (list) Android .aar files to add dependencies from
#android.add_aar =

# (list) The Android embeddable libary to use (for now only one)
#android.embed_marker = true

# (str) XML file to include as an extract in AndroidMainfest.xml
#android.extra_manifest_filename =

# (list) Permission the application needs
# INTERNET: WebSocket connection
# VIBRATE: alert vibration
# WAKE_LOCK: keep CPU running for push alerts in background
# FOREGROUND_SERVICE: long-running connection service
# POST_NOTIFICATIONS: Android 13+ notification permission
# ACCESS_NETWORK_STATE: detect network changes for reconnect
# REQUEST_IGNORE_BATTERY_OPTIMIZATIONS: bypass Doze mode for reliable push
android.permissions = INTERNET, VIBRATE, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, ACCESS_NETWORK_STATE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS

# (list) features (adds uses-feature -tags to manifest)
#android.features = android.hardware.usb.host

# (int) Target Android Platform which is the earliest Android platform the application supported on
# 2.2 = actual Android 2.2. On Android 4+ (this is the only version of interest) the number
# doesn't matter, it's the codenames that are used.
#android.platform = android-27

# (str) NDK 版本：r19c 与 p4a stable 最兼容
# 已在上方 android.ndk 处指定，这里不重复

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk or aar).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android fork to use in case of main python-for-android being not
# compatible
#p4a.fork = python-for-android

# (str) python-for-android branch to use, defaults to master
# 锁定 stable 分支（2024.07.05），避免 latest 自动切换 NDK r28c 导致不兼容
p4a.branch = stable

# (str) python-for-android specific commit to use, defaults to HEAD, must be within
# the specified branch
#p4a.commit = HEAD

# (str) python-for-android url to use in case of need of a custom fork
#p4a.url =

# (list) The Android API level for which the APK is built, defaulting to the minSdkVersion
#p4a.bootstrap_startup.restart = False

# (str) command to be executed at every build
#p4a.bootstrap_startup = .
#p4a.mainline_always = python3

# (list) List of python-for-android recipes to include
#p4a.local_recipes =

# (str) Filename to the hook for p4a
#p4a.hook =

# (str) Bootstrap to use for python-for-android
# SDL2 bootstrap: required for Kivy UI + pyjnius Java classes access
p4a.bootstrap = sdl2

# (int) Number of parallel jobs to build with
# Reduce if build fails with memory error
p4a.njobs = 1

# (bool) Skip running-as-root warning (WSL / Colab are always root)
warn_on_root = 0

#
# iOS specific directives
#

# (str) Path to a custom signature certificate
ios.certificate =

# (str) Path to a custom provisioning profile
ios.provisioning_profile =

# (str) Path to a custom distribution certificate
#ios.certificate =

# (str) Path to a custom distribution provisioning profile
#ios.provisioning_profile =

# (str) iOS app name to use if application bundle name differs from package name
ios.bundle_name = nasmonitor

# (str) Version to use for the app, defaulting to the version key
ios.version = 2.0.0

# (dict) requirements map
ios.requirements =

# (str) A custom URL schemes (comma separated)
ios.url_schemes =

# (str) The path to the Apple Developer SDK typically located at /Developer/Platforms/iPhoneOS.platform/Developer
#ios.sdk = /Developer/Platforms/iPhoneOS.platform/Developer

# (str) The path to the xcode
#ios.xcode =

# (list) The list of frameworks that must be added to the final application
#ios.frameworks =

# (list) The list of libraries that must be added to the final application
#ios.libraries =

# (str) A custom Localizable.strings file to be added to the ios App
#ios.extra_manifest_filename =

#
# Commands
#

# (str) Custom data directory for the application
# (Defaults to buildozer data path, but can be changed)
#data.dir = %(OSPATH)s/share

# (str) The command to run buildozer with, or build commands
build_cmd =

# (list) The build commands to run
#build_cmd = update_icons

# (str) Custom default command to run when "buildozer" is invoked without any
# argument. Options are "debug", "release", "deploy", and "deploy_dev"
default_build_type = debug

# (list) Set of commands that will be run when `buildozer <app>` is invoked
# without any argument. If not specified, defaults to the `default_build_type`
# which can be "debug" or "release"
# build_cmd =

# (bool) Set to True to start the application after the build
# auto_build = True

# (bool) Set to True to use libffi from system package
# use_system_ffi = False

# (list) The names of recipes that have been updated
#recipes =

# (list) The names of the recipes to be deleted
#recipes_dir =

# (str) The directory in which to search for python-for-android recipes
#p4a_recipes_dir =

# (str) The directory in which to search for recipes
#recipes_dir =

# (bool) Indicates whether to use a repository for the packages, default is False
#package_repositories =

# (str) The URL of the repository to use for the packages
#package_repository =

# (str) The directory where the bootstrap script will create the environment
#build_dir = ./%s

# (str) The path to the build directory
#build_dir = ./%s

# (str) Path to build output not required
#build_dir = %(source.dir)s/bin

# (str) The directory in which to search for the bootstrap script
#bootstrap_dir = %(source.dir)s/bootstrap

# (str) Bootstrap to use for the current platform, if not defined in spec
#bootstrap =

# (list) The list of bootstrap to use for the current platform
#bootstraps = sdl2

# (str) The directory in which to search for the bootstrap script
#bootstrap_dir = %(source.dir)s/bootstrap

# (str) Directory containing icons
#icon_dir =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) The version to use
#version = 2.0.0

# (str) The title of the application
#title = 抢单软件告警

# (str) The package name
#package.name = nasmonitor

# (str) Package domain
#package.domain = org.nas