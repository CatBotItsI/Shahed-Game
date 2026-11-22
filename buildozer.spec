[app]

title = Shahed Game
package.name = shahedgame
package.domain = org.catbotitis

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,mp3

version = 0.1
requirements = python3,pygame
orientation = landscape
fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
