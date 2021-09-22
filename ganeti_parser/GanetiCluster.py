#!/usr/bin/python3
from typing import List, Tuple

from tabulate import tabulate

from ganeti_parser.GanetiNodeGroup import GanetiNodeGroup
from ganeti_parser.GanetiNode import GanetiNode
from ganeti_parser.GanetiInstance import GanetiInstance
from ganeti_parser.GanetiAllocationPolicy import GanetiAllocationPolicy

class GanetiCluster:
    node_groups: List[GanetiNodeGroup] = []
    nodes: List[GanetiNode] = []
    instances: List[GanetiInstance] = []
    policies: List[GanetiAllocationPolicy] = []
    allocation_tag: str = None

    def __init__(self, allocation_tag: str = None):
        self.allocation_tag = allocation_tag

    # retrieve a GanetiNodeGroup object the given GanetiInstance object belongs to
    def _get_node_group_from_instance(self, instance: GanetiInstance) -> GanetiNodeGroup:
        group_uuid = None
        for node in self.nodes:
            if node.name == instance.pnode:
                group_uuid = node.group_uuid
        for node_group in self.node_groups:
            if node_group.uuid == group_uuid:
                return node_group

    # retrieve all memory occupied by primary instances on a given GanetiNode
    def _get_node_used_memory(self, node: GanetiNode) -> int:
        memory_used = 0
        for instance in self.instances:
            if instance.pnode == node.name:
                memory_used += instance.memory_size
        return memory_used

    # retrieve all disk space occupied by primary and secondary instances on a given GanetiNode
    def _get_node_used_disk(self, node: GanetiNode) -> int:
        disk_used = 0
        for instance in self.instances:
            if instance.pnode == node.name or instance.snodes == node.name:
                disk_used += instance.disk_size
        return disk_used

    # determine if a given GanetiNode has enough unallocated memory to run the given GanetiInstance
    def _node_has_enough_memory(self, node: GanetiNode, new_instance: GanetiInstance) -> bool:
        memory_used = self._get_node_used_memory(node)
        if memory_used + new_instance.memory_size > node.total_memory:
            print("  {}*** Not enough memory for {} on {} ({}MB already used on node, {}MB total available){}".format(
                "\033[91m", new_instance.name, node.name, memory_used, node.total_memory, "\033[0m"
            ))
            return False
        print("  {}*** {} has enough memory left ({}MB already used on node, {}MB total available){}".format(
            "\033[92m", node.name, memory_used, node.total_memory, "\033[0m"
        ))
        return True

    # determine if a given GanetiNode has enough unallocated disk space to run the given GanetiInstance
    def _node_has_enough_disk(self, node: GanetiNode, new_instance: GanetiInstance) -> bool:
        disk_used = self._get_node_used_disk(node)
        if disk_used + new_instance.disk_size > node.total_disk:
            print("  {}*** Not enough disk for {} on {} ({}MB already used on node, {}MB total available){}".format(
                "\033[91m", new_instance.name, node.name, disk_used, node.total_disk, "\033[0m"
            ))
            return False
        print("  {}*** {} has enough disk left ({}MB already used on node, {}MB total available){}".format(
            "\033[92m", node.name, disk_used, node.total_disk, "\033[0m"
        ))
        return True

    # get the CPU ratio for a given GanetiNode
    def _get_cpu_ratio_by_node(self, node: GanetiNode) -> float:
        vcpu_ratio = 0.0

        for group in self.node_groups:
            if group.uuid == node.group_uuid:
                for policy in self.policies:
                    if policy.owner == group.name:
                        return policy.vcpu_ratio
        return vcpu_ratio

    # determine if a given GanetiNode has enough unallocated vCPUs to run the given GanetiInstance
    def _node_has_enough_cpus(self, node: GanetiNode, new_instance: GanetiInstance) -> bool:
        cpus_used = 0
        vcpu_ratio = self._get_cpu_ratio_by_node(node)
        for instance in self.instances:
            if instance.pnode == node.name or instance.snodes == node.name:
                cpus_used += instance.vcpus
        if cpus_used + new_instance.vcpus > ( node.total_cpus * vcpu_ratio ):
            print("  {}*** Not enough CPUs for {} on {} ({} already used on node, {} total available){}".format(
                "\033[91m", new_instance.name, node.name, cpus_used, node.total_cpus * vcpu_ratio, "\033[0m"
            ))
            return False
        print("  {}*** {} has enough CPUs left ({} already used on node, {} total available){}".format(
            "\033[92m", node.name, cpus_used, node.total_cpus * vcpu_ratio, "\033[0m"
        ))
        return True
    
    # get the spindle ratio for a given GanetiNode
    def _get_spindle_ratio_by_node(self, node: GanetiNode) -> float:
        spindle_ratio = 0.0

        for group in self.node_groups:
            if group.uuid == node.group_uuid:
                for policy in self.policies:
                    if policy.owner == group.name:
                        return policy.spindle_ratio
        return spindle_ratio

    # determine if a given GanetiNode has enough unallocated spindles to run the given GanetiInstance
    def _node_has_enough_spindles(self, node: GanetiNode, new_instance: GanetiInstance) -> bool:
        spindles_used = 0
        spindle_ratio = self._get_spindle_ratio_by_node(node)
        for instance in self.instances:
            if instance.pnode == node.name or instance.snodes == node.name:
                spindles_used += instance.spindles
        if spindles_used + new_instance.spindles > ( node.spindles * spindle_ratio ):
            print("  {}*** Not enough spindles for {} on {} ({} already used on node, {} total available){}".format(
                "\033[91m", new_instance.name, node.name, spindles_used, node.spindles * spindle_ratio, "\033[0m"
            ))
            return False
        print("  {}*** {} has enough spindles left ({} already used on node, {} total available){}".format(
            "\033[92m", node.name, spindles_used, node.spindles * spindle_ratio, "\033[0m"
        ))
        return True

    # determine if a given GanetiNode already holds a primary instance with the given instance tag
    def _is_this_instance_tag_already_on_this_node(self, tag: str, node: GanetiNode) -> bool:
        for instance in self.instances:
            if instance.pnode == node.name and tag in instance.tags:
                print("  {}*** Tag {} already present on primary instance on {}".format(
                    "\033[91m", tag, node.name, "\033[0m"
                ))
                return True
        return False

    # determine if allocation tags need to be checked (is it set on the cluster? is it set on the instance?)
    def _node_has_no_conflicting_migration_tags(self, node: GanetiNode, new_instance: GanetiInstance) -> bool:
        if not self.allocation_tag:
            return True

        for tag in new_instance.tags:
            if tag.startswith("{}:".format(self.allocation_tag)):
                return not self._is_this_instance_tag_already_on_this_node(tag, node)
        else:
            return True
            
    # go through all nodes and find one that is able to accept the given GanetiInstance as a new primary
    def _find_new_primary_for_instance(self, instance: GanetiInstance, illegal_nodes: List[GanetiNode]) -> GanetiNode:
        node_group = self._get_node_group_from_instance(instance)
        nodes = self.get_nodes_by_group(node_group)
        for node in nodes:
            if node not in illegal_nodes and \
                self._node_has_enough_memory(node, instance) and \
                self._node_has_enough_disk(node, instance) and \
                self._node_has_enough_cpus(node, instance) and \
                self._node_has_enough_spindles(node, instance) and \
                self._node_has_no_conflicting_migration_tags(node, instance):
                return node
        return None

    # go through all nodes and find one that is able to accept the given GanetiInstance as a new secondary
    def _find_new_secondary_for_instance(self, instance: GanetiInstance, illegal_nodes: List[GanetiNode]) -> GanetiNode:
        node_group = self._get_node_group_from_instance(instance)
        nodes = self.get_nodes_by_group(node_group)
        for node in nodes:
            if node not in illegal_nodes and \
                self._node_has_enough_memory(node, instance) and \
                self._node_has_enough_disk(node, instance) and \
                self._node_has_enough_cpus(node, instance) and \
                self._node_has_enough_spindles(node, instance):
                return node
        return None

    # swap primary/secondary *if* there is enough capacity on the secondary
    def _failover_instance(self, instance: GanetiInstance) -> bool:
        old_primary = instance.pnode
        old_secondary = instance.snodes
        instance.pnode = old_secondary
        instance.snodes = old_primary

        new_primary = self.get_node_by_name(instance.pnode)
        memory_used = self._get_node_used_memory(new_primary)
        if memory_used > new_primary.total_memory:
            instance.pnode = old_primary
            instance.snodes = old_secondary
            print("  {}*** Instance failover failed (not enough resources on target){}".format(
                "\033[91m","\033[0m"
            ))
            return False

        print("  {}*** Instance failover performed{}".format(
            "\033[93m","\033[0m"
        ))
        return True

    # try to move a given GanetiInstance away from the given node
    def _evacuate_instance(self, node_name: str, instance: GanetiInstance):
        pnode = self.get_node_by_name(instance.pnode)
        snode = self.get_node_by_name(instance.snodes)
        if instance.pnode == node_name:
            print("** Looking for a new primary node for {} (Memory: {}MB, Disk: {}MB)".format(instance.name, instance.memory_size, instance.disk_size))
            new_node = self._find_new_primary_for_instance(instance, [pnode, snode])
            if new_node:
                instance.pnode = new_node.name
            else:
                if not self._failover_instance(instance):
                    raise Exception("Unable to find new primary node for {}".format(instance.name))
        elif instance.snodes == node_name:
            print("** Looking for a new secondary node for {} (Memory: {}MB, Disk: {}MB)".format(instance.name, instance.memory_size, instance.disk_size))
            new_node = self._find_new_secondary_for_instance(instance, [pnode, snode])
            if new_node:
                instance.snodes = new_node.name
            else:
                raise Exception("Unable to find new secondary node for {}".format(instance.name))

    def _count_primary_instances(self, node: GanetiNode) -> int:
        counter = 0
        for instance in self.instances:
            if instance.pnode == node.name:
                counter += 1
        return counter

    def _count_secondary_instances(self, node: GanetiNode) -> int:
        counter = 0
        for instance in self.instances:
            if instance.snodes == node.name:
                counter += 1
        return counter

    def _get_memory_used_percentage(self, node: GanetiNode) -> int:
        memory_sum = 0
        for instance in self.instances:
            if instance.pnode == node.name:
                memory_sum += instance.memory_size

        return int(memory_sum / node.total_memory * 100)

    def _get_disk_used_percentage(self, node: GanetiNode) -> int:
        disk_sum = 0
        for instance in self.instances:
            if instance.pnode == node.name or instance.snodes == node.name:
                disk_sum += instance.disk_size
        return int(disk_sum / node.total_disk * 100)

    def _get_cpu_used_percentage(self, node: GanetiNode) -> int:
        cpu_sum = 0
        vcpu_ratio = self._get_cpu_ratio_by_node(node)
        allowed_virtual_cpus = node.total_cpus * vcpu_ratio
        for instance in self.instances:
            if instance.pnode == node.name:
                cpu_sum += instance.vcpus
        return int(cpu_sum / allowed_virtual_cpus * 100)

    def _get_spindles_used_percentage(self, node: GanetiNode) -> int:
        spindles_sum = 0
        spindles_ratio = self._get_spindle_ratio_by_node(node)
        allowed_spindles = node.spindles * spindles_ratio
        for instance in self.instances:
            if instance.pnode == node.name:
                spindles_sum += instance.spindles
        return int(spindles_sum / allowed_spindles * 100)

    def _get_max_failn1_memory_used_percentage(self, node: GanetiNode) -> Tuple[str, int]:
        memory_sum = 0
        memory_sum_by_node = {}
        for secondary_node in self.nodes:
            if secondary_node.name != node.name:
                memory_sum_by_node[secondary_node.name] = 0

        # get memory for primary and secondary instances
        for instance in self.instances:
            if instance.pnode == node.name:
                memory_sum += instance.memory_size
            elif instance.snodes == node.name:
                memory_sum_by_node[instance.pnode] += instance.memory_size
        
        node_with_largest_memory_amount_on_nodefail = max(memory_sum_by_node, key=memory_sum_by_node.get)
        failn1_memory_sum = memory_sum + memory_sum_by_node[node_with_largest_memory_amount_on_nodefail]

        return (node_with_largest_memory_amount_on_nodefail, int(failn1_memory_sum / node.total_memory * 100))
    
    def _get_max_failn1_cpu_used_percentage(self, node: GanetiNode) -> Tuple[str, int]:
        cpu_sum = 0
        cpu_sum_by_node = {}
        for secondary_node in self.nodes:
            if secondary_node.name != node.name:
                cpu_sum_by_node[secondary_node.name] = 0

        vcpu_ratio = self._get_cpu_ratio_by_node(node)
        allowed_virtual_cpus = node.total_cpus * vcpu_ratio

        # get CPU for primary and secondary instances
        for instance in self.instances:
            if instance.pnode == node.name:
                cpu_sum += instance.vcpus
            elif instance.snodes == node.name:
                cpu_sum_by_node[instance.pnode] += instance.vcpus
        
        node_with_largest_vcpu_count_on_nodefail = max(cpu_sum_by_node, key=cpu_sum_by_node.get)
        failn1_vcpu_sum = cpu_sum + cpu_sum_by_node[node_with_largest_vcpu_count_on_nodefail]

        return (node_with_largest_vcpu_count_on_nodefail, int(failn1_vcpu_sum / allowed_virtual_cpus * 100))

    def _get_max_failn1_spindles_used_percentage(self, node: GanetiNode) -> Tuple[str, int]:
        spindles_sum = 0
        spindles_sum_by_node = {}
        for secondary_node in self.nodes:
            if secondary_node.name != node.name:
                spindles_sum_by_node[secondary_node.name] = 0

        spindle_ratio = self._get_spindle_ratio_by_node(node)
        allowed_spindles = node.spindles * spindle_ratio

        # get spindles for primary and secondary instances
        for instance in self.instances:
            if instance.pnode == node.name:
                spindles_sum += instance.spindles
            elif instance.snodes == node.name:
                spindles_sum_by_node[instance.pnode] += instance.spindles
        
        node_with_largest_spindle_count_on_nodefail = max(spindles_sum_by_node, key=spindles_sum_by_node.get)
        failn1_spindles_sum = spindles_sum + spindles_sum_by_node[node_with_largest_spindle_count_on_nodefail]

        return (node_with_largest_spindle_count_on_nodefail, int(failn1_spindles_sum / allowed_spindles * 100))

    # public methods

    # add elements to the cluster
    def add_node_group(self, name, uuid, policy, tags, networks):
        new_node_group = GanetiNodeGroup(name, uuid, policy, tags, networks)
        self.node_groups.append(new_node_group)

    def add_node(self, name, total_memory, used_memory, free_memory, total_disk, free_disk, total_cpus, status, group_uuid, spindles, tags, exclusive_storage, free_spindles, node_cpus, cpu_speed):
        new_node = GanetiNode(name, total_memory, used_memory, free_memory, total_disk, free_disk, total_cpus, status, group_uuid, spindles, tags, exclusive_storage, free_spindles, node_cpus, cpu_speed)
        self.nodes.append(new_node)

    def add_instance(self, name, memory_size, disk_size, vcpus, status, auto_balance, pnode, snodes, disk_template, tags, spindles, total_spindles, forthcoming):
        new_instance = GanetiInstance(name, memory_size, disk_size, vcpus, status, auto_balance, pnode, snodes, disk_template, tags, spindles, total_spindles, forthcoming)
        self.instances.append(new_instance)

    def add_policy(self, owner, ispec, min_max_ispec, disk_templates, vcpu_ratio, spindle_ratio):
        new_policy = GanetiAllocationPolicy(owner, ispec, min_max_ispec, disk_templates, vcpu_ratio, spindle_ratio)
        self.policies.append(new_policy)

    def get_nodes_by_group(self, group: GanetiNodeGroup) -> List[GanetiNode]:
        filtered_nodes: List[GanetiNode] = []
        for node in self.nodes:
            if node.group_uuid == group.uuid:
                filtered_nodes.append(node)
        return filtered_nodes
    
    def get_instances_by_nodes(self, nodes: List[GanetiNode]) -> List[GanetiInstance]:
        filtered_instances: List[GanetiInstance] = []
        for instance in self.instances:
            for node in nodes:
                if instance.pnode == node.name:
                    filtered_instances.append(instance)
        return filtered_instances

    # retrieve a GanetiNode object through its node name
    def get_node_by_name(self, node_name) -> GanetiNode:
        for node in self.nodes:
            if (node_name == node.name) or (node_name == node.shortname):
                return node
        raise Exception("Node {} not found".format(node_name))

    # try to remove a node from the cluster by moving away all instances
    def remove_node(self, node_name: str):
        node_to_remove = self.get_node_by_name(node_name)

        if node_name == node_to_remove.shortname:
            node_name = node_to_remove.name

        for instance in self.instances:
            self._evacuate_instance(node_name, instance)

        # Double-tap - find instances which swapped primary/secondary during the first run
        for instance in self.instances:
            self._evacuate_instance(node_name, instance)

        self.nodes.remove(node_to_remove)

    # print out the current cluster state (with usage percentages)
    def dump_cluster(self):
        for node_group in self.node_groups:
            print("\nNode-Group: {}".format(node_group.name))
            lines = []
            lines.append([
                "Node",
                "Primary Inst",
                "Secondary Inst",
                "Memory",
                "Disk",
                "CPUs",
                "Spindles"
            ])
            for node in self.get_nodes_by_group(node_group):

                lines.append([
                    node.name.split(".")[0],
                    self._count_primary_instances(node),
                    self._count_secondary_instances(node),
                    "{}%".format(self._get_memory_used_percentage(node)),
                    "{}%".format(self._get_disk_used_percentage(node)),
                    "{}%".format(self._get_cpu_used_percentage(node)),
                    "{}%".format(self._get_spindles_used_percentage(node))
                    ]
                )

                failn1_mem_node, failn1_mem_percentage = self._get_max_failn1_memory_used_percentage(node)
                failn1_cpu_node, failn1_cpu_percentage = self._get_max_failn1_cpu_used_percentage(node)
                failn1_spindle_node, failn1_spindle_percentage = self._get_max_failn1_spindles_used_percentage(node)

                lines.append([
                    "* simulate Fail-N-1",
                    "",
                    "",
                    "{}% (by {})".format(failn1_mem_percentage, failn1_mem_node.split(".")[0]),
                    "",
                    "{}% (by {})".format(failn1_cpu_percentage, failn1_cpu_node.split(".")[0]),
                    "{}% (by {})".format(failn1_spindle_percentage, failn1_spindle_node.split(".")[0]),
                ])
                lines.append([
                    "", "", "", "", "", "", ""
                ])

            print()
            print(tabulate(lines, headers="firstrow", tablefmt="github"))
            print()
