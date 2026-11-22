name: Build Android APK

on:
  workflow_dispatch:
  push:
    branches: [ "main" ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install system dependencies for Buildozer
        run: |
          sudo apt-get update
          sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf automake libtool libltdl-dev pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev

      - name: Install Buildozer, python-for-android and Cython
        run: |
          python -m pip install --upgrade pip "setuptools<80" wheel "cython<3.1" buildozer python-for-android

      - name: Build APK with Buildozer
        run: |
          buildozer android debug

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: shahed-game-apk
          path: bin/*.apk
