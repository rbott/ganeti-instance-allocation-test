# Ganeti instance allocation/relocation tests

With this script 

## Requirements

This script has been tested against plain Python 3.8 and does not rely on any non-standard modules. As it uses type hints according to the [Python 3.8 documentation](https://docs.python.org/3.8/library/typing.html) it might not run on older or newer versions. Ganeti data has been successfully parsed from 2.15 and 2.16 clusters. 3.0 should also work, but is untested. It requires the `tabulate` Python module for output formatting (use your favorite Python dependency manager):

```shell
$ pip install tabulate
$ apt install python3-tabulate
```

## Usage

Generate the cluster state on your Ganeti master (this will generate a `LOCAL.data` file in the current folder):
```shell
hscan -L
```

Copy the cluster state file to your Python environment and see if the state parses successfully:
```shell
./start.py --mode dump LOCAL.data
```

Tell it to try and remove the first node from each node group (there will be at least one `default` group):
```shell
./start.py --mode remove-first-of-group LOCAL.data
```

If everything works out fine, you should see how the tool tries to move primary/secondary instances away from the selected Ganeti node. You might see some error messages about not enough memory/disks/cpus/spindles etc. while it loops over all nodes to find a suitiable one for the current instance. This is fine as long as it finally succeeds in finding a new node. If it fails, it will stop the process, print out `Failed to remove first node` and move on to the next node group. 

You can also tell it to remove a specific Ganeti node:

```shell
./start.py --mode remove --node node01.ganeti.local LOCAL.data
```

## Interpretation

The output from `--mode dump` will look something like this:
```shell
$ ./start.py --mode dump LOCAL.data
Found 1 Node-Groups, 5 Nodes, 87 Instances, 2 Allocation Policies
  default: 5 Nodes with 87 Instances
Node-Group: default
| Node                | Primary Inst   | Secondary Inst   | Memory        | Disk   | CPUs          | Spindles      |
|---------------------|----------------|------------------|---------------|--------|---------------|---------------|
| GNT1                | 17             | 18               | 67%           | 97%    | 51%           | 35%           |
| * simulate Fail-N-1 |                |                  | 90% (by GNT4) |        | 65% (by GNT4) | 50% (by GNT4) |
|                     |                |                  |               |        |               |               |
| GNT2                | 17             | 18               | 55%           | 59%    | 43%           | 35%           |
| * simulate Fail-N-1 |                |                  | 88% (by GNT4) |        | 62% (by GNT4) | 54% (by GNT3) |
|                     |                |                  |               |        |               |               |
| GNT3                | 18             | 16               | 57%           | 61%    | 42%           | 37%           |
| * simulate Fail-N-1 |                |                  | 83% (by GNT5) |        | 65% (by GNT1) | 47% (by GNT1) |
|                     |                |                  |               |        |               |               |
| GNT4                | 18             | 18               | 26%           | 29%    | 23%           | 37%           |
| * simulate Fail-N-1 |                |                  | 33% (by GNT2) |        | 29% (by GNT2) | 47% (by GNT1) |
|                     |                |                  |               |        |               |               |
| GNT5                | 17             | 17               | 66%           | 58%    | 49%           | 35%           |
| * simulate Fail-N-1 |                |                  | 95% (by GNT2) |        | 74% (by GNT2) | 52% (by GNT2) |
```

The first two lines are general information about the cluster and cluster node-groups.  In this case, there is a single node group named "default".

The large table is broken into rows of two lines each:  where each row corresponds to a node in the cluster/node-group.  The first line shows current information about a node.  For example, the node GNT1 has 17 primary instances running on it, and acts as a secondary for 18 other instances.  The remaining columns show 67% of the RAM available on the host is in use, as well as 75% of the disk, 51% of the vCPUs allocated to Ganeti (after accounting for over-subscription ratios), and 35% of the disk "spindles".

The second line for each row, starting with "simulate Fail-N-1", shows the projected state of the node if the worst case failure happened for each resource.  Using GNT3 as an example, memory usage is expected to rise from 57% to 83% if node GNT5 fails.  If a different node failed, the memory increase would lower.  Note for CPU and Spindle utilization, the worst case situation would be a failure of a different node: GNT1 not GNT5.  This can happen due to differences in instance sizes as distributed over the various nodes in the cluster.

This output can give you an overall sense of current cluster and in an N-1 failure situation.  In theory, so long as all "simulate Fail-N-1" metrics are <100%, the cluster should be fine after losing a node.  In practice...

```shell
$ ./start.py --mode remove --node GNT4 LOCAL.data
Found 1 Node-Groups, 5 Nodes, 87 Instances, 2 Allocation Policies
  default: 5 Nodes with 87 Instances
** Looking for a new primary node for instance01.example.com (CPU: 2, Memory: 6144MB, Disk: 204928MB)
  *** GNT2.example.com has enough memory left (141312MB already used on node, 253608MB total available)
  *** GNT2.example.com has enough disk left (7108992MB already used on node, 11915008MB total available)
  *** GNT2.example.com has enough CPUs left (115 already used on node, 128.0 total available)
  *** GNT2.example.com has enough spindles left (35 already used on node, 48.0 total available)

[...]

** Looking for a new secondary node for instance42.example.com (CPU: 4, Memory: 8192MB, Disk: 256128MB)
  *** GNT1.example.com has enough memory left (172032MB already used on node, 253608MB total available)
  *** Not enough disk for instance42.example.com on GNT1.example.com (5886464MB already used on node, 5909376MB total available)
  *** GNT3.example.com has enough memory left (147072MB already used on node, 253608MB total available)
  *** GNT3.example.com has enough disk left (7288064MB already used on node, 11915008MB total available)
  *** Not enough CPUs for instance42.example.com on GNT3.example.com (127 already used on node, 128.0 total available)
  *** GNT5.example.com has enough memory left (184320MB already used on node, 253608MB total available)
  *** GNT5.example.com has enough disk left (7319024MB already used on node, 11915008MB total available)
  *** Not enough CPUs for instance42.example.com on GNT5.example.com (125 already used on node, 128.0 total available)
```

Using the same data, removing node GNT1 fails after iterating through a number of instance migrations.  In this case, instance42 (4 CPUs, 8G RAM, 250G disk) has a primary on node GNT2 (not shown, but can be inferred because GNT2 is not checked for migation attempt), and a secondary on GNT4.  An attempt to relocate the instance42 secondary fails because:
1. GNT1 does not have 250G of disk free
2. GNT2 houses the primary
3. GNT3 also lacks 250G of disk space
4. GNT4 is the current (failed!) secondary
5. GNT5 does not have sufficient vCPUs free (4 required, but only 3 available)

Even though the `--mode dump` output looked okay initially, there is a good chance that the cluster is in a precarious state regarding N-1 capacity, with the current instance allocation.  Rebalancing the cluster _may_ help, but adding an additional node is likely a better solution.  Note that `gnt-cluster verify` reports N+1 redundancy is okay in this current configuration.


## Limitations

### Disk Templates

The script currently assumes DRBD is used (it does not check what is actually configured on instances!). This affects the way available/used storage is calculated and it needs to be changed if other disk templates will be used.

### Cluster Allocation Tags

Although they are present in the cluster state file, they are currently ignored by the parser (simply not implemented yet). The script currently assumes the (hardcoded) cluster tag "a" (which is also the example used by the Ganeti man pages).
