#!/usr/bin/python3
from typing import List

class GanetiInstance:
    name = ""
    memory_size = 0
    disk_size = 0
    vcpus = 0
    status = ""
    auto_balance = ""
    pnode = ""
    snodes = ""
    disk_template = ""
    tags: List[str] = []
    spindles = 0
    total_spindles = 0
    forthcoming = ""

    def __init__(self, name, memory_size, disk_size, vcpus, status, auto_balance, pnode, snodes, disk_template, tags, spindles, total_spindles, forthcoming):
        self.name = name
        self.memory_size = memory_size
        self.disk_size = disk_size
        self.vcpus = vcpus
        self.status = status
        self.auto_balance = auto_balance
        self.pnode = pnode
        self.snodes = snodes
        self.disk_template = disk_template
        self.tags = tags
        self.spindles = spindles
        self.total_spindles = total_spindles
        self.forthcoming = forthcoming

    def __eq__(self, other):
        return self.name == other.name