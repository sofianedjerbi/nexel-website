title: The whole game in a browser tab
date: 2026-11-09
image: phone.png
summary: The server is plain Python, so we ran it inside the page. Then on a phone.
---
The game server is plain Python with no outside packages. That gave us an idea: run it in the browser with Pyodide (Python compiled for the web), talk to it through in-page sockets, and save the world in the browser's storage. No server to pay for, nothing to install.

It worked on the first try more or less: the world was up about two seconds after the page loaded, and your saved player was still there after a reload. That is the demo you can play on this site.

## Then a phone

A phone has no keyboard, so it got a thumb stick on the left and two buttons on the right, each labelled with what it will do right now. We tested in emulated phones (390 by 844) before calling it done.

## Testing in a real browser

From day two every change was checked in real Chrome, driven by a script: join, walk, chop a tree, read what is on the screen. Bugs that unit tests could never see showed up at once, like a chat feed that had been silently dead since the first version.

![The demo on a phone screen](img/phone.png)
