#!/usr/bin/python

from ganeti_parser.GanetiCluster import GanetiCluster


def parse_datafile(filename: str):
    file = open(filename, 'r')
    lines = file.readlines()

    cluster = GanetiCluster(allocation_tag="a")

    GROUPS = 0
    NODES = 1
    INSTANCES = 2
    TAGS = 3
    POLICIES = 4

    SECTIONS = [
        GROUPS,
        NODES,
        INSTANCES,
        TAGS,
        POLICIES
    ]

    current_section = GROUPS
    for line in lines:
        line = line.strip()
        if line == "":
            current_section = SECTIONS[current_section + 1]
        else:
            if current_section == GROUPS:
                name, uuid, policy, tags, networks = line.split("|")
                cluster.add_node_group(name, uuid, policy, tags, networks)
            elif current_section == NODES:
                name, total_memory, used_memory, free_memory, total_disk, free_disk, total_cpus, status, group_uuid, spindles, tags, exclusive_storage, free_spindles, node_cpus, cpu_speed = line.split("|")
                # we will substract 4096 off the node's total memory as that amount is reserved anyways and can not be used for instances
                cluster.add_node(name, int(total_memory) - 4096, int(used_memory), int(free_memory), int(total_disk), int(free_disk), int(total_cpus), status, group_uuid, int(spindles), tags.split(","), exclusive_storage, int(free_spindles), int(node_cpus), cpu_speed)
            elif current_section == INSTANCES:
                name, memory_size, disk_size, vcpus, status, auto_balance, pnode, snodes, disk_template, tags, spindles, total_spindles, forthcoming = line.split("|")
                cluster.add_instance(name, int(memory_size), int(disk_size), int(vcpus), status, auto_balance, pnode, snodes, disk_template, tags.split(","), int(spindles), total_spindles, forthcoming)
            elif current_section == POLICIES:
                owner, ispec, min_max_ispec, disk_templates, vcpu_ratio, spindle_ratio = line.split("|")
                cluster.add_policy(owner, ispec, min_max_ispec, disk_templates.split(","), float(vcpu_ratio), float(spindle_ratio))
    
    return cluster
                