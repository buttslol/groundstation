Protocol Specification for groundstation
========================================

# Task queueing

Groundstation's task queue implementation is designed to be a superior replacement for beanstalk.

As such, it aims to deliver a product that is in no way inferior. To this end:

* When tasks are mined into the graph, they also retain a temporary reserve for
  each transit node they cross.
* Task claims by exector nodes implicitly mine a reserve on their adjacent transit node.
* Succesful completion is mined into the chain by the executor, and immediately
  propagated to ALL adjacent nodes.

Double processing is still possible- in the same conditions that beanstalk
will. Network partitions, executor timeout.

Mining work into the graph requires two steps:

* The actual graph append. This is basically a tip spanning from the last known
  (gref|checkpoint), including the details of the task to be executed.
* Propagating the new object to n peers, for n consistency.

The actual structure of a task's lifetime maps neatly onto the notion of a gref:

The gref describes all current "tasks in flight". Practically speaking, a gref
is akin to a tube in beanstalk.

Each tip in the gref is a discrete task. Task completion is defined as a child
node, descendant both from the original task mine, and from it's completion
node.

### Key

```
w       | Mined on worker
o       | Mined on transit node
p       | Mined on consumer
```

```
o    # Completion (mined into the gref)
|\
| \
| w  # Completion (work done)
| |
| |
| w  # Reserve (at worker)
| |
| | o # Recipt (Mined on an adjacent worker)
| o/ # Transit reservation (Only mined on the transit node the producer pushes to)
| o  # Receipt:
|/
p    # Task creation
```

The kick is that it's still a "push" system. All things going to plan, all
tasks are pushed to availble machines, who hold reservations on the system.

The useful guarantees come from the fact that while allocation is optimistic,
completion is pessimistic. The task is allocated at enqueue time, but not
considered allocated until it's mined by `n` machines, ensuring the tasks
eventual completion (failure or otherwise)

## Consistency

The consistency of the graph is dependant on always propagating the new
information to n nodes, establishing greater confidence for greater values of
n.

To avoid specialcasing lots of conditions for a local producer and consumer,
it's recommended to run a redundant pair as the producer, allowing sane values
for n consistency, and a single codepath.

## Terminology

##### Transit node

Every node which a task crosses, up until an executor. This includes the local
database instance on the machines that are enqueing tasks.

##### Adjacency

Implementation defined, specifically by the discovery and transit driver in use.

##### Checkpoint

A merged tip, descending from all completd tips in the graph. A checkpoint is
chiefly of use to a watchdog, or an archiver which can safely prune anything
descendant from a checkpoint.

##### Watchdog

A safeguard mechanism to ensure task completion. Watches all entries to the
graph, and maintains an array of uncompleted work.

Should never be responsible for executing work, rather for alerting and
notifying systems capable of delivering.

##### Archiver

The only agent capable of removing nodes from the graph. Implementation similar
to a watchdog, excepting that it serializes and stores data succesfully mined
out of the graph.
