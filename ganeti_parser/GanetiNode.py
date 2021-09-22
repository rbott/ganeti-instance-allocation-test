#!/usr/bin/python3
from typing import List
import re

class GanetiNode:
    name = ""
    shortname = ""
    total_memory = 0
    used_memory = 0
    free_memory = 0
    total_disk = 0
    free_disk = 0
    total_cpus = 0
    status = ""
    group_uuid = ""
    spindles = 0
    tags: List[str] = []
    exclusive_storage = ""
    free_spindles = 0
    node_cpus = 0
    cpu_speed = ""

    def __init__(self, name, total_memory, used_memory, free_memory, total_disk, free_disk, total_cpus, status, group_uuid, spindles, tags, exclusive_storage, free_spindles, node_cpus, cpu_speed):
        self.name = name
        self.shortname = re.sub(r'\..*', '', name)
        self.total_memory = total_memory
        self.used_memory = used_memory
        self.free_memory = free_memory
        self.total_disk = total_disk
        self.free_disk = free_disk
        self.total_cpus = total_cpus
        self.status = status
        self.group_uuid = group_uuid
        self.spindles = spindles
        self.tags = tags
        self.exclusive_storage = exclusive_storage
        self.free_spindles = free_spindles
        self.node_cpus = node_cpus
        self.cpu_speed = cpu_speed

    def __eq__(self, other):
        return self.name == other.name