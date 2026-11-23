title: Tests that tell the truth
date: 2026-11-22
image: build-1.png
summary: Hundreds of tests in a real browser, and what made them flaky. Hint: it was rarely load.
---
Every change to Nexel Worlds is checked twice: unit tests on the simulation (665 of them now, a few seconds), and tests in real Chrome that join the game and play it with the keyboard.

## Slow and flaky

By the 17th the browser suite had 245 tests, took four minutes on six workers, and in a whole day of runs not one was fully green. A different handful failed each time.

We measured before changing anything. About 440 seconds of the run were fixed sleeps in the test helper: 0.4 s after every bit of land, 0.7 s for a cleared area, 0.8 s after a gift. They were too long when the machine was idle and too short when it was busy. Now the helper waits for the thing itself (the land is drawn, the item is in your bag), never for a fixed time. The suite got a fifth faster and much steadier.

## "Failed under load"

Later a few tests still failed now and then, and the easy answer was "the machine was busy". We reproduced each one and printed the state at the failing line. It was hardly ever load. Most often it was **where the test player woke up**: the world decorates each tile by its position, and a test that read a single pixel sometimes read a darker grass patch or a sparkle on the water.

## The rules now

- Print the state at the failing wait before guessing.
- The helper waits; tests never sleep and then check.
- A browser test must pass the first time. No second tries.
- Tests that look at pixels look at the real game picture, on a phone-sized screen too.

strip: build-1.png build-3.png | Build mode, as a browser test plays it: the same keys a player presses, then a look at the picture.
