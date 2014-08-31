#!/usr/bin/python
# -*- coding: utf-8 -*-
# This is licensed under the:
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004
# Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#  0. You just DO WHAT THE FUCK YOU WANT TO.

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import PatternMatchingEventHandler
import os
import argparse
import logging
import time
import threading
import Queue
import random
import subprocess

class directory_watch(object):
    def __init__(self, directory, viewer, delay = 5):
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
        self._directory = directory
        self._viewer = viewer
        self._time = delay
        self._queue = Queue.Queue()
        self._list = []
        self._observer = Observer()
        print "initializing observer"
        #self._observer.schedule(LoggingEventHandler(), self._directory, recursive = True)
        self._display = Displayer(ignore_directories = True)
        self._display._viewer = self._viewer
        self._display._queue = self._queue
        self._display._list = self._list
        self._emptycount = 0 
        self._observer.schedule(self._display, self._directory, recursive = True)
        self._thread = threading.Thread(target = lambda: self._update())
        self._thread.setDaemon(True)
        self._thread.start()
        self._observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._observer.stop()
        self._observer.join()
    def _update(self):
        print "started!"
        while True:
            if self._queue.empty():
                self._emptycount += 1
                if self._emptycount >= 5:
                    #enqueue old one
                    total = len(self._list)
                    if total:
                        r = random.randint(0,total-1)
                        self._queue.put(self._list[r])
            if not self._queue.empty():
                self._emptycount -= 1
                if self._emptycount <= 0:
                    self._emptycount = 0
                fname = self._queue.get()
                fname = fname.replace(" ", "\ ")
                subprocess.Popen(self._viewer +  fname, shell = True)
            time.sleep(self._time)
                

class Displayer(PatternMatchingEventHandler):
    __init__ = PatternMatchingEventHandler.__init__
    def on_moved(self,event):
        absn_source = os.path.basename(event.src_path).lower()
        absn_dest = os.path.basename(event.dest_path).lower()
        if any([lambda s: absn_dest.endswith(s) for s in [".jpg", ".jpeg", ".jpe", ".png"]]):
            print "got", event.dest_path
            self._queue.put(event.dest_path)
            self._list.append(event.dest_path)
        else:
            print "ignoring", event.dest_path
if __name__ == "__main__":
    parser = argparse.ArgumentParser("autoimagedisplay", description="adds new files in a directory to a queue, and displays them automagically")
    parser.add_argument("directory", help="directory to watch")
    parser.add_argument("-t","--time", type=int, help="delay between new images", default=5)
    parser.add_argument("-x", "--execute", help="viewer (incl. arguments) to run, include space at end!", default="geeqie -r file:")
    args = parser.parse_args()
    directory_watch(args.directory, args.execute, args.time)
