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

## Limitations

### Disk Templates

The script currently assumes DRBD is used (it does not check what is actually configured on instances!). This affects the way available/used storage is calculated and it needs to be changed if other disk templates will be used.

### Cluster Allocation Tags

Although they are present in the cluster state file, they are currently ignored by the parser (simply not implemented yet). The script currently assumes the (hardcoded) cluster tag "a" (which is also the example used by the Ganeti man pages).
