#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AstroBlash
# Pwn2Win2019
# author: code@pauloklaus.com.br
# greetz: alisson@bertochi.com.br

import curses
from curses import KEY_RIGHT, KEY_LEFT
from random import randint
from time import time
from enum import Enum
import locale

locale.setlocale(locale.LC_ALL, '')

WIDTH = 30
HEIGHT = 12
MAX_X = WIDTH - 2
MAX_Y = HEIGHT - 2
FLAG = "[xxFLAGxx]"

KEY_ESC = 27
KEY_Q1 = 81
KEY_Q2 = 113
KEY_ENTER = 10
KEY_SPACE = 32

class Ship(object):
    REFRESH = 0.03

    def __init__(self, window, char='V'):
        self.window = window
        self.char = char
        self.x = MAX_X / 2
        self.y = MAX_Y
        self.startTime = time()

        self.direction = KEY_LEFT
        self.direction_map = {
            KEY_LEFT: self.moveLeft,
            KEY_RIGHT: self.moveRight
        }

    def render(self):
        self.window.addstr(0, 1, "[{}:{}]".format(self.y, self.x))
        self.window.addstr(self.y, self.x, self.char)

    def update(self):
        elapsed_time = time() - self.startTime

        if elapsed_time < self.REFRESH:
            return

        self.startTime = time()
        self.direction_map[self.direction]()

    def changeDirection(self, direction):
        if direction == KEY_SPACE:
            if self.direction == KEY_LEFT:
                direction = KEY_RIGHT
            else:
                direction = KEY_LEFT
        self.direction = direction

    def moveLeft(self):
        if self.x > 1:
            self.x -= 1
        else:
            self.direction = KEY_RIGHT

    def moveRight(self):
        if self.x < MAX_X:
            self.x += 1
        else:
            self.direction = KEY_LEFT

    @property
    def getX(self):
        return self.x

class AstroStatus(Enum):
    FALLING_DOWN = 1
    CAPTURED = 2
    EXPLODED = 3
    LOST = 4

class Astro(object):
    REFRESH = 0.05
    TARGET_CHAR = "*"
    CHARS = ['+', 'u', 'W', 'T']

    def __init__(self, window, y, x, captureChar=False):
        self.window = window
        self.startY = y
        self.startX = x
        if captureChar:
            self.startChar = self.TARGET_CHAR
        else:
            self.startChar = self.CHARS[randint(0, len(self.CHARS) - 1)]
        self.start()

    def start(self):
        self.ended = False
        self.startTime = time()
        self.y = self.startY
        self.x = self.startX
        self.char = self.startChar

    def update(self):
        if time() - self.startTime < self.REFRESH:
            return self.ended

        self.startTime = time()

        self.ended = self.y > MAX_Y
        if not self.ended:
            self.y += 1

        return self.ended

    def collided(self, x):
        if self.y != MAX_Y:
            return AstroStatus.FALLING_DOWN
        
        if self.x == x:
            self.window.addstr(self.y, self.x, "X")
            if self.char == self.TARGET_CHAR:
                self.y = MAX_Y + 1
                return AstroStatus.CAPTURED
            else:
                return AstroStatus.EXPLODED
        else:
            if self.char == self.TARGET_CHAR:
                self.window.addstr(self.y, self.x, "#")
                return AstroStatus.LOST
            else:
                return AstroStatus.FALLING_DOWN

    def render(self):
        if self.y > 0 and self.y <= MAX_Y and not self.ended:
            self.window.addstr(self.y, self.x, self.char)

class AstroSet(object):
    def __init__(self, window, astros):
        self.window = window
        self.astros = []

        for astro in astros:
            if len(astro) < 3:
                astro.append(False)
            self.astros.append(Astro(window, astro[0], astro[1], astro[2]))

    def render(self):
        for astro in self.astros:
            astro.render()

    def update(self):
        ended = True

        for astro in self.astros:
            astro_ended = astro.update()
            if not astro_ended:
                ended = False

        return ended

    def collided(self, x):
        for astro in self.astros:
            status = astro.collided(x)
            if status != AstroStatus.FALLING_DOWN:
                return status

        return AstroStatus.FALLING_DOWN

    def restart(self):
        for astro in self.astros:
            astro.start()

class GameBoard(object):
    TARGET_TIME = 137

    def __init__(self, window, astroSets):
        self.window = window
        self.astroSets = []
        self.pointer = 0
        self.startTime = time()
        self.capturedTargets = 0

        for astroSet in astroSets:
            self.astroSets.append(AstroSet(window, astroSet))

    def render(self):
        self.renderTitle()
        self.astroSets[self.pointer].render()

    def renderTitle(self):
        self.window.addstr(0, 10, "[{0:.2f}/{1}]".format(time() - self.startTime, self.capturedTargets))

    def update(self):
        if self.astroSets[self.pointer].update():
            self.astroSets[self.pointer].restart()

            self.pointer += 1
            if self.pointer >= len(self.astroSets):
                self.pointer = 0

    def bye(self):
        key = -1
        while key not in [KEY_ENTER, KEY_ESC, KEY_SPACE, KEY_Q1, KEY_Q2]:
            key = window.getch()

    def collided(self, x):
        status = self.astroSets[self.pointer].collided(x)
        if status == AstroStatus.CAPTURED:
            self.capturedTargets += 1
        elif status in [AstroStatus.EXPLODED, AstroStatus.LOST]:
            self.bye()
            return True

        return False

    def timeAchieved(self):
        if time() - self.startTime < self.TARGET_TIME:
            return False

        self.renderTitle()
        self.window.addstr(MAX_Y + 1, 1, FLAG)
        self.bye()

        return True

if __name__ == '__main__':
    curses.initscr()
    window = curses.newwin(HEIGHT, WIDTH, 0, 0)
    window.timeout(20)
    window.keypad(1)
    curses.noecho()
    curses.curs_set(0)
    window.border(0)

    asLeft3 = [[0,2], [-5,6,True], [-2,9]]
    asRight4 = [[0,MAX_X-2], [-3,MAX_X-4], [-7,MAX_X-7]]
    asLeftRight7 = asLeft3 + asRight4

    ship = Ship(window)
    gameBoard = GameBoard(window, [
        asLeft3,
        asRight4,
        asLeftRight7
    ])

    while True:
        window.clear()
        window.border()

        ship.render()
        gameBoard.render()

        event = window.getch()

        if event in [KEY_LEFT, KEY_RIGHT, KEY_SPACE]:
            ship.changeDirection(event)

        if event in [KEY_ESC, KEY_Q1, KEY_Q2]:
            break

        if gameBoard.collided(ship.getX):
            break

        if gameBoard.timeAchieved():
           break

        ship.update()
        gameBoard.update()

    curses.endwin()
