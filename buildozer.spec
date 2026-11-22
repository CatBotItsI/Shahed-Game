[app]

title = Shahed Game
package.name = shahedgame
package.domain = org.catbotits.shahedgame

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,mp3,json

version = 0.1

requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.build_tools_version = 33.0.2
android.archs = arm64-v8a,armeabi-v7a

[buildozer]

log_level = 2
warn_on_root = 1
