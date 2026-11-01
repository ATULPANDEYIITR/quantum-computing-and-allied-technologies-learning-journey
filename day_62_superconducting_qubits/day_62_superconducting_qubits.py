# Binary Tree Traversals

## Project Overview

This project implements four fundamental binary tree traversal algorithms using Python, JavaScript, C++17, Java 17, and PostgreSQL.

A binary tree is a hierarchical data structure in which each node can have at most two children:

- Left child
- Right child

Each node stores a value and references to its children. The topmost node is called the root. Nodes without children are called leaf nodes.

Traversal determines the order in which nodes are visited. The four standard traversal techniques are preorder, inorder, postorder, and level-order.

The implementations cover recursive algorithms, iterative algorithms, stack-based processing, queue-based processing, generator-based traversal, event-driven execution, tree analytics, and relational representation.

## Learning Objectives

- Understand binary tree structure and node relationships.
- Distinguish depth-first search from breadth-first search.
- Implement recursive traversal algorithms.
- Convert recursive algorithms into iterative implementations.
- Understand the relationship between recursion and explicit stacks.
- Implement breadth-first traversal using queues.
- Calculate tree height and node count.
- Group nodes according to their depth.
- Evaluate traversal performance and memory requirements.
- Represent hierarchical structures in a relational database.
- Validate traversal results using automated assertions.

## Binary Tree Structure

The implementations use the following sample tree:

    50
   /  \
  30   70
 / \   / \
20 40 60 80
/       \
10       65

The structure contains nine nodes.

| Property | Value |
|---|---|
| Root | 50 |
| Total nodes | 9 |
| Leaf nodes | 10, 40, 65, 80 |
| Height | 4 |
| Maximum children per node | 2 |
| Maximum width | 4 |

Height is measured in nodes rather than edges. Therefore, a tree containing only a root has height one, while an empty tree has height zero.

## 1. Preorder Traversal

Preorder follows the sequence:

**Root → Left → Right**

The current node is visited before its children.

For the sample tree:

`50, 30, 20, 10, 40, 70, 60, 65, 80`

### Recursive mechanism

1. Visit the current node.
2. Recursively traverse the left subtree.
3. Recursively traverse the right subtree.

### Iterative mechanism

An explicit stack replaces the function call stack.

The algorithm pushes the root initially. After visiting a node, it pushes the right child followed by the left child.

A stack follows Last In, First Out ordering. Consequently, the left child is processed first.

### Practical applications

- Generating hierarchical representations.
- Serializing tree structures.
- Processing parent entities before subordinate entities.
- Prefix expression generation.

## 2. Inorder Traversal

Inorder follows the sequence:

**Left → Root → Right**

The left subtree is processed before the current node, followed by the right subtree.

For the sample tree:

`10, 20, 30, 40, 50, 60, 65, 70, 80`

### Recursive mechanism

The algorithm recursively processes the left child, visits the current node, and then processes the right child.

### Iterative mechanism

The iterative implementation maintains an explicit stack and a current-node reference.

It repeatedly:

1. Moves down the left subtree.
2. Pushes each encountered node.
3. Processes the top node when no further left child exists.
4. Moves to its right subtree.

This approach avoids recursive function calls.

### Important distinction

Inorder traversal of a binary search tree produces values in ascending order when the search-tree ordering invariant is satisfied.

This property does not apply automatically to arbitrary binary trees.

### Practical applications

- Retrieving sorted values from binary search trees.
- Evaluating expression trees.
- Processing ordered hierarchical data.
- Validating binary search tree structures.

## 3. Postorder Traversal

Postorder follows the sequence:

**Left → Right → Root**

The children are processed before their parent.

For the sample tree:

`10, 20, 40, 30, 65, 60, 80, 70, 50`

### Recursive mechanism

The algorithm traverses the left subtree, traverses the right subtree, and visits the current node last.

### Iterative mechanism

The implementations use a stack containing a node and its visitation state.

Each node is initially marked as unvisited. It is pushed back with a visited state, followed by its right and left children.

When the node is encountered again in its visited state, its value is appended to the result.

This explicitly models the return phase of recursive execution.

Another common implementation uses two stacks. The first stack processes nodes while the second stores them in reverse postorder. Reversing the second stack produces the required result.

### Practical applications

- Deleting hierarchical structures.
- Calculating directory sizes.
- Evaluating expression trees.
- Processing dependencies before their parent entities.
- Releasing resources from nested structures.

## 4. Level-order Traversal

Level-order follows a breadth-first processing strategy.

Nodes are visited from top to bottom and from left to right within each level.

For the sample tree:

`50, 30, 70, 20, 40, 60, 80, 10, 65`

### Queue-based mechanism

The algorithm uses a First In, First Out queue.

1. Insert the root.
2. Remove the front node.
3. Visit its value.
4. Insert its left child, if present.
5. Insert its right child, if present.
6. Repeat until the queue is empty.

Unlike depth-first traversal, level-order processes all nodes at one depth before moving to the next depth.

### Level-wise representation

| Depth | Nodes |
|---|---|
| 0 | 50 |
| 1 | 30, 70 |
| 2 | 20, 40, 60, 80 |
| 3 | 10, 65 |

### Practical applications

- Organizational hierarchy processing.
- Network exploration.
- Shortest-path exploration in unweighted graphs.
- Tree serialization.
- Finding the minimum depth of a tree.
- Processing hierarchical records level by level.

## Traversal Comparison

| Traversal | Processing order | Main data structure |
|---|---|---|
| Preorder | Root, Left, Right | Stack |
| Inorder | Left, Root, Right | Stack |
| Postorder | Left, Right, Root | Stack |
| Level-order | Level by level | Queue |

The first three algorithms belong to depth-first traversal. Level-order belongs to breadth-first traversal.

## Recursive and Iterative Approaches

### Recursion

Recursive traversal uses function calls to process smaller subtrees.

Each recursive call receives a child node and applies the same traversal logic.

The system maintains execution state through the call stack.

Advantages:

- Direct correspondence with the tree structure.
- Compact implementation.
- Natural representation of recursive relationships.

Limitations:

- Function-call overhead.
- Risk of stack overflow for deeply unbalanced trees.
- Limited control over the execution stack.

### Iteration

Iterative traversal uses explicit data structures to manage execution state.

| Traversal | Iterative implementation |
|---|---|
| Preorder | Stack |
| Inorder | Stack and current-node pointer |
| Postorder | Stack with visitation state |
| Level-order | Queue |

Advantages:

- Explicit control over memory usage.
- No dependency on recursive call depth.
- Better control over processing and execution state.

The iterative implementation does not eliminate memory requirements. It moves traversal state from the call stack into explicitly managed containers.

## Algorithmic Complexity

Let:

- `n` represent the total number of nodes.
- `h` represent the height of the tree.
- `w` represent the maximum number of nodes at any level.

| Algorithm | Time complexity | Auxiliary space |
|---|---|---|
| Recursive preorder | O(n) | O(h) |
| Iterative preorder | O(n) | O(h) |
| Recursive inorder | O(n) | O(h) |
| Iterative inorder | O(n) | O(h) |
| Recursive postorder | O(n) | O(h) |
| Iterative postorder | O(n) | O(h) |
| Level-order | O(n) | O(w) |

The returned traversal list requires O(n) additional output space. Auxiliary-space figures exclude this output storage.

For a balanced tree, height is approximately O(log n).

For a completely skewed tree, height becomes O(n). Recursive traversal can therefore become unsafe for sufficiently deep trees.

## Python Implementation

The Python implementation uses:

| Mechanism | Purpose |
|---|---|
| `dataclass` | Defines the tree node structure |
| `Enum` | Represents traversal orders |
| `list` | Stores traversal results and explicit stacks |
| `collections.deque` | Implements efficient queue operations |
| Nested functions | Implements recursive traversal |
| Dictionaries | Maps traversal types to execution methods |
| Assertions | Validates algorithm results |
| Type hints | Clarifies node references and return types |

The `BinaryTree` class provides recursive and iterative implementations for all four traversal techniques.

The iterative postorder implementation uses visitation-state tuples. This preserves the required left-right-root sequence without requiring two separate stacks.

The additional `postorder_two_stacks()` method demonstrates an alternative implementation.

The tree analytics methods calculate height, count nodes, search for values, and check completeness.

The `traverse()` method provides a common interface for selecting a traversal strategy.

The implementation handles:

- Empty trees.
- Single-node trees.
- Missing left or right children.
- Unbalanced structures.
- Missing search values.
- Recursive and iterative result comparisons.

## JavaScript Implementation

The JavaScript implementation introduces an event-driven traversal engine.

Its main mechanisms include:

| Mechanism | Purpose |
|---|---|
| Classes | Encapsulate nodes and traversal operations |
| `Map` | Store performance measurements |
| `EventEmitter` | Publish traversal events |
| Generator functions | Produce traversal values incrementally |
| Promises | Coordinate asynchronous processing |
| `async` and `await` | Execute traversal in batches |
| `setImmediate()` | Yield control to the event loop |
| `process.hrtime.bigint()` | Measure execution duration |

The generator methods support preorder, inorder, and postorder traversal without constructing the complete result immediately.

The asynchronous implementation processes values in batches and emits:

- `visit`: indicates that a node has been processed.
- `batch`: reports a completed batch.
- `complete`: reports successful traversal completion.

An optional abort signal allows the caller to cancel processing between node visits.

The implementation also avoids repeated `Array.shift()` operations during breadth-first traversal. A head index provides efficient queue processing without repeatedly moving array elements.

This design is useful when traversal results must be streamed to another component or processed through event-driven workflows.

## C++17 Implementation

The C++ implementation emphasizes memory ownership, STL containers, and explicit traversal state.

| Mechanism | Purpose |
|---|---|
| `struct` | Defines binary tree nodes |
| `enum class` | Represents traversal categories |
| `vector` | Stores traversal results |
| `stack` | Supports depth-first traversal |
| `queue` | Supports breadth-first traversal |
| `pair` | Stores visitation state and depth |
| `chrono` | Measures execution duration |
| Exceptions | Handle invalid child attachment |
| `assert` | Validates traversal correctness |

The `BinaryTree` class owns the nodes allocated during construction.

Copy operations are deleted because copying the raw-pointer structure without implementing deep-copy semantics could lead to double deletion and invalid memory references.

The destructor releases the tree recursively using postorder deletion.

The attachment methods reject null parents and occupied child positions.

The implementation uses an explicit visitation state for iterative postorder traversal. This approach makes the required processing sequence clear while avoiding an additional result-reversal pass.

The program also calculates tree height, node count, and search results.

The implementation assumes a reasonably bounded tree depth for recursive destruction and recursive traversal. Extremely deep trees require iterative destruction and iterative traversal to avoid call-stack exhaustion.

## Java 17 Implementation

The Java implementation models traversal as an enterprise-oriented service.

It separates the node model, traversal strategy, execution result, and service responsibilities.

| Mechanism | Purpose |
|---|---|
| Classes | Encapsulate domain behavior |
| Enum | Defines supported traversal orders |
| Record | Represents immutable traversal results |
| Interface | Defines the traversal strategy |
| `EnumMap` | Associates traversal orders with strategies |
| `ArrayDeque` | Implements stack and queue operations |
| `List.copyOf()` | Produces immutable results |
| `Optional` | Represents optional search results |
| Custom exception | Represents traversal failures |
| `System.nanoTime()` | Measures execution duration |

The `TraversalStrategy` interface provides a common execution contract.

Each traversal is registered in an `EnumMap`, allowing the service to select an implementation based on the requested traversal order.

The `TraversalResult` record stores:

- Traversal type.
- Ordered node values.
- Execution duration.

Immutable result lists prevent callers from modifying completed traversal results.

The node attachment methods reject occupied child positions and prevent direct or indirect cycles when attaching an existing subtree.

This is an important structural safeguard because a cyclic structure is not a valid binary tree and can cause traversal algorithms to run indefinitely.

## PostgreSQL Implementation

The PostgreSQL implementation represents a binary tree using relational tables.

It uses an adjacency-list model, where every node stores its parent identifier.

### Relational structure

| Table | Responsibility |
|---|---|
| `binary_trees` | Stores tree metadata |
| `tree_nodes` | Stores node values and parent-child relationships |
| `tree_traversal_log` | Stores traversal execution history |

The `tree_nodes` table contains:

- `node_id`: unique node identifier.
- `tree_id`: associated tree.
- `parent_id`: identifier of the parent node.
- `node_value`: stored node value.
- `child_position`: left or right child indicator.

The child-position convention is:

| Value | Meaning |
|---|---|
| 0 | Left child |
| 1 | Right child |
| NULL | Root node |

### Database integrity

The relational design uses:

- Primary keys.
- Foreign keys.
- Composite foreign keys.
- Unique constraints.
- Check constraints.
- Partial unique indexes.
- Performance-oriented indexes.

The partial unique index ensures that a tree cannot contain multiple root records.

The composite foreign key ensures that a parent belongs to the same tree as its child.

The database uses a recursive validation function to detect invalid structures, including cycles, multiple roots, and unreachable nodes.

The validation function is important because a foreign key alone does not guarantee that the parent-child relationships form a valid tree.

### Recursive CTEs

PostgreSQL recursive common table expressions provide the mechanism for traversing the relational hierarchy.

A recursive CTE consists of:

1. An initial query identifying the root.
2. A recursive query identifying child nodes.
3. A termination condition when no additional children exist.

The traversal function constructs a path for every node.

It then derives an ordering key according to the requested traversal algorithm.

| Traversal | Ordering mechanism |
|---|---|
| Preorder | Parent before left and right subtrees |
| Inorder | Left subtree before parent and right subtree |
| Postorder | Both subtrees before parent |
| Level-order | Depth followed by left-to-right path |

The ordering keys are textual paths. This is suitable for the demonstration tree, but very deep or large trees can produce substantial path values and sorting overhead.

### Database reporting

The SQL implementation provides:

- Tree validation.
- Node counting.
- Height calculation.
- Traversal retrieval.
- Level-wise aggregation.
- Leaf-node identification.
- Parent-child relationship reporting.
- Traversal execution history.

The `traversal_summary` view provides structural information for each registered tree.

The execution log records the traversal type, number of visited nodes, execution status, and optional execution duration.

The SQL demonstration also verifies that invalid traversal names and duplicate root insertion are rejected.

## Important Edge Cases

| Scenario | Expected behavior |
|---|---|
| Empty tree | Return an empty traversal |
| Single-node tree | Return the root value |
| Missing left child | Continue with the available right subtree |
| Missing right child | Continue with the available left subtree |
| Completely skewed tree | Preserve the required traversal sequence |
| Duplicate node values | Visit each node independently |
| Unsuccessful search | Return no matching node |
| Deep recursion | Consider stack-depth limitations |
| Invalid traversal name | Reject the request |
| Cyclic structure | Reject or detect invalid tree structure |

Duplicate values do not affect traversal correctness because traversal is based on node identity and structural position rather than value uniqueness.

## Testing and Expected Results

The automated tests compare recursive and iterative implementations.

Expected outputs for the sample tree:

| Traversal | Expected result |
|---|---|
| Preorder | `[50, 30, 20, 10, 40, 70, 60, 65, 80]` |
| Inorder | `[10, 20, 30, 40, 50, 60, 65, 70, 80]` |
| Postorder | `[10, 20, 40, 30, 65, 60, 80, 70, 50]` |
| Level-order | `[50, 30, 70, 20, 40, 60, 80, 10, 65]` |

The tests also verify:

- Node count.
- Tree height.
- Search operations.
- Empty-tree behavior.
- Single-node behavior.
- Agreement between recursive and iterative implementations.
- Invalid structural modifications.

## Execution Requirements

| Implementation | Requirement |
|---|---|
| Python | Python 3.10 or later |
| JavaScript | Node.js 18 or later |
| C++17 | C++17-compatible compiler |
| Java | Java 17 or later |
| PostgreSQL | PostgreSQL 14 or later |

The Python and JavaScript implementations use standard-library functionality.

The C++ implementation requires no external libraries.

The Java implementation uses standard Java APIs.

The PostgreSQL script creates its own schema and demonstration tables. Execute it using a database role with permission to create schemas, tables, functions, and indexes.

The SQL script uses a transaction and is designed to be rerunnable for the demonstration schema.

## Practical Distinctions

The four traversal algorithms solve different ordering requirements.

Preorder processes parents before descendants. Inorder places each node between its left and right subtrees. Postorder processes descendants before their parents. Level-order processes the hierarchy one depth at a time.

Recursive and iterative approaches are alternative execution mechanisms for depth-first traversal. Breadth-first traversal requires a queue to preserve its level-based processing order.

The implementations demonstrate these distinctions across in-memory structures, event-driven processing, systems programming, enterprise domain modeling, and relational database queries.
