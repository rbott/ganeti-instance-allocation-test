#!/usr/bin/python3
from typing import List

class GanetiAllocationPolicy:

    owner: str
    ispec: str
    min_max_ispec: str
    disk_templates:List[str] = []
    vcpu_ratio: float
    spindle_ratio: float

    def __init__(self, owner, ispec, min_max_ispec, disk_templates, vcpu_ratio, spindle_ratio):
        self.owner = owner
        self.ispec = ispec
        self.min_max_ispec = min_max_ispec
        self.disk_templates = disk_templates
        self.vcpu_ratio = vcpu_ratio
        self.spindle_ratio = spindle_ratio