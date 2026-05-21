# Simple Todo

A small Windows desktop todo app built with Python and WebView.

## Features

- Create categories.
- Open categories as vertical task windows.
- Collapse or expand To Do and Completed sections.
- Add tasks under a category.
- Tick tasks complete or incomplete.
- Add a reminder with an exact time or quick timer.
- Choose one of 10 accent colors.
- Edit and delete tasks.
- Stores data locally in `%APPDATA%\SimpleTodo\todo.sqlite3`.

Reminder popups work while the app is running. This app does not install a background Windows service.

## Run From Source

```powershell
python app.py
```

Running from source requires `pywebview`. The built executable includes the app dependencies.

## Reminder Input

Use one of these formats:

```text
2026-05-15 14:30
14:30
+30m
+2h
```

## Build The Windows App

```powershell
.\build.ps1
```

The executable will be created at:

```text
dist\SimpleTodo.exe
```

## Install

After building:

```powershell
.\install.ps1
```

This copies the app to `%LOCALAPPDATA%\SimpleTodo` and creates a Start Menu shortcut named `Simple Todo`.

## Uninstall

```powershell
.\uninstall.ps1
```

To remove saved task data too:

```powershell
.\uninstall.ps1 -RemoveData
```
