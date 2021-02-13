#!/usr/bin/python3
from typing import List

class GanetiNodeGroup:
    name = ""
    uuid = ""
    policy = ""
    tags: List[str] = []
    networks = ""

    def __init__(self, name, uuid, policy, tags, networks):
        self.name = name
        self.uuid = uuid
        self.policy = policy
        self.tags = tags
        self.networks = networks

    def __eq__(self, other):
        return self.name == other.name