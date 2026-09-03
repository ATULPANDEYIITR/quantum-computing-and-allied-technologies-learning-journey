"""
===============================================================================
LIMITATIONS OF CLASSICAL COMPUTING
Complexity, Scaling, and NP-Hard Problems
===============================================================================

PURPOSE
-------
This program provides a detailed learning journey from the fundamentals of
classical computation to advanced ideas involving:

    1. What classical computing is
    2. Computational resources
    3. Time complexity
    4. Space complexity
    5. Big-O notation
    6. Constant, logarithmic, linear, linearithmic, polynomial,
       exponential, and factorial complexity
    7. Why scaling creates computational problems
    8. Brute-force search
    9. Combinatorial explosion
    10. P, NP, NP-complete, and NP-hard problems
    11. Important NP-hard examples
    12. Traveling Salesperson Problem
    13. Knapsack Problem
    14. Subset Sum
    15. Boolean satisfiability
    16. Graph coloring
    17. Hamiltonian cycle
    18. Why verification can be easier than finding a solution
    19. Polynomial-time reductions
    20. Approximation algorithms
    21. Heuristics
    22. Dynamic programming
    23. Memoization
    24. Branch and bound
    25. The difference between theoretical difficulty and practical difficulty
    26. Why faster hardware does not solve exponential scaling
    27. Classical computing versus quantum computing
    28. Why quantum computing does NOT simply solve all NP-hard problems
    29. Practical strategies for difficult computational problems

IMPORTANT
---------
This is an educational program. The examples are intentionally small so that
their behavior can be observed directly.

===============================================================================
"""


# =============================================================================
# SECTION 1: WHAT IS CLASSICAL COMPUTING?
# =============================================================================

print("=" * 80)
print("CLASSICAL COMPUTING")
print("=" * 80)

"""
Classical computing is based on classical bits.

A classical bit has one of two values:

    0
    1

Modern classical computers use physical systems such as transistors to
represent and manipulate these binary states.

At the logical level, classical computers perform operations using:

    AND
    OR
    NOT
    XOR
    NAND
    NOR

A classical computer executes algorithms using computational resources such as:

    - CPU time
    - Memory
    - Storage
    - Network bandwidth
    - Energy

The important limitation is that these resources are finite.

For small problems, this is usually not a problem.

For sufficiently large problems, the number of operations required by an
algorithm can become enormous.

That is where computational complexity becomes important.
"""


# =============================================================================
# SECTION 2: WHAT DOES "LIMITATION" MEAN?
# =============================================================================

"""
A computational limitation does not necessarily mean that a computer
physically cannot perform a calculation.

Instead, a problem may require an impractical amount of:

    - time
    - memory
    - energy
    - hardware
    - communication

For example, imagine an algorithm requiring:

    2^n operations

For n = 10:

    2^10 = 1,024

This is trivial.

For n = 50:

    2^50 = 1,125,899,906,842,624

This is already enormous.

For n = 100:

    2^100 ≈ 1.27 × 10^30

The growth of the problem is the key issue.

The computer may be extremely powerful, but the number of possible
calculations can grow much faster than the available computational resources.
"""


# =============================================================================
# SECTION 3: A SIMPLE EXAMPLE OF SCALING
# =============================================================================

print("\nSCALING EXAMPLE")
print("-" * 80)

def linear_work(n):
    """
    Performs approximately n units of work.

    Complexity:
        O(n)
    """
    operations = 0

    for _ in range(n):
        operations += 1

    return operations


for n in [10, 100, 1000, 10000]:
    print(f"n = {n:5d} -> operations = {linear_work(n)}")


"""
This is a linear algorithm.

If the input doubles:

    n -> 2n

the approximate amount of work also doubles.

This is generally manageable.

Now compare it with exponential growth.
"""


# =============================================================================
# SECTION 4: EXPONENTIAL GROWTH
# =============================================================================

print("\nEXPONENTIAL GROWTH")
print("-" * 80)

def exponential_work(n):
    """
    Conceptually represents 2^n possible states.

    Complexity:
        O(2^n)
    """
    return 2 ** n


for n in range(1, 21):
    print(f"n = {n:2d} -> 2^n = {exponential_work(n):10d}")


"""
Notice how rapidly the values grow.

This is one of the central ideas behind computational complexity.

An algorithm that is acceptable for n = 20 may become completely impractical
for n = 100.

This is called poor scaling.

===============================================================================
"""


# =============================================================================
# SECTION 5: TIME COMPLEXITY
# =============================================================================

print("\nTIME COMPLEXITY")
print("-" * 80)

"""
Time complexity describes how the number of computational steps grows as the
input size increases.

It does NOT necessarily mean exact clock time.

Instead, it describes the growth behavior of an algorithm.

Examples:

    O(1)       Constant
    O(log n)   Logarithmic
    O(n)       Linear
    O(n log n) Linearithmic
    O(n^2)     Quadratic
    O(n^3)     Cubic
    O(n^k)     Polynomial
    O(2^n)     Exponential
    O(n!)      Factorial
"""


# =============================================================================
# SECTION 6: O(1) CONSTANT COMPLEXITY
# =============================================================================

def constant_time_example(items):
    """
    Accessing an element by index in a Python list is approximately O(1).
    """
    if not items:
        return None

    return items[0]


print("\nO(1) EXAMPLE")

data = list(range(1_000_000))

print(constant_time_example(data))


"""
The size of the list can increase dramatically, but retrieving the first
element still requires approximately the same number of operations.

Therefore:

    O(1)

is considered excellent scaling.
"""


# =============================================================================
# SECTION 7: O(log n) LOGARITHMIC COMPLEXITY
# =============================================================================

def binary_search(sorted_list, target):
    """
    Binary search.

    Complexity:
        O(log n)

    Requirement:
        The list must be sorted.
    """

    low = 0
    high = len(sorted_list) - 1

    while low <= high:

        middle = (low + high) // 2

        if sorted_list[middle] == target:
            return middle

        elif sorted_list[middle] < target:
            low = middle + 1

        else:
            high = middle - 1

    return -1


numbers = list(range(1_000_000))

print("\nBINARY SEARCH")
print("-" * 80)
print("Index:", binary_search(numbers, 987654))


"""
Binary search repeatedly eliminates approximately half of the remaining
search space.

For n elements:

    n
    n/2
    n/4
    n/8
    ...

The number of steps is approximately:

    log2(n)

This is extremely efficient.
"""


# =============================================================================
# SECTION 8: O(n) LINEAR COMPLEXITY
# =============================================================================

def linear_search(items, target):
    """
    Linear search.

    Worst-case complexity:
        O(n)
    """

    for index, value in enumerate(items):

        if value == target:
            return index

    return -1


print("\nLINEAR SEARCH")
print("-" * 80)

print(linear_search([10, 20, 30, 40, 50], 40))


"""
Linear search may examine every element.

If there are n elements:

    worst-case operations ≈ n

Therefore:

    O(n)
"""


# =============================================================================
# SECTION 9: O(n^2) QUADRATIC COMPLEXITY
# =============================================================================

def quadratic_example(n):
    """
    Performs approximately n^2 operations.

    Complexity:
        O(n^2)
    """

    operations = 0

    for _ in range(n):

        for _ in range(n):

            operations += 1

    return operations


print("\nQUADRATIC COMPLEXITY")
print("-" * 80)

for n in [10, 20, 50, 100]:
    print(f"n = {n:3d} -> operations = {quadratic_example(n)}")


"""
If:

    n = 10

we get:

    100 operations

If:

    n = 100

we get:

    10,000 operations

If:

    n = 1,000

we get:

    1,000,000 operations

This is why quadratic algorithms can become expensive at scale.
"""


# =============================================================================
# SECTION 10: O(n^3) CUBIC COMPLEXITY
# =============================================================================

def cubic_example(n):
    """
    Performs approximately n^3 operations.

    Complexity:
        O(n^3)
    """

    operations = 0

    for _ in range(n):

        for _ in range(n):

            for _ in range(n):

                operations += 1

    return operations


print("\nCUBIC COMPLEXITY")
print("-" * 80)

for n in [5, 10, 20]:
    print(f"n = {n:2d} -> operations = {cubic_example(n)}")


"""
Cubic algorithms can become impractical much sooner than linear algorithms.

For example:

    100^3 = 1,000,000
"""


# =============================================================================
# SECTION 11: O(n log n)
# =============================================================================

"""
O(n log n) algorithms are common in efficient sorting algorithms.

Examples include conceptual implementations of:

    - Merge sort
    - Heap sort
    - Efficient comparison-based sorting

O(n log n) is generally considered efficient for large datasets.

The important idea is:

    O(n log n) grows faster than O(n)
    but much slower than O(n^2)
"""


# =============================================================================
# SECTION 12: POLYNOMIAL COMPLEXITY
# =============================================================================

"""
A polynomial-time algorithm generally has complexity:

    O(n^k)

where k is a constant.

Examples:

    O(n)
    O(n^2)
    O(n^3)
    O(n^5)

Polynomial growth can still be expensive.

For example:

    n = 1,000

n^2 = 1,000,000

n^3 = 1,000,000,000

So "polynomial" does not mean "fast".

It means the growth is fundamentally different from exponential growth.
"""


# =============================================================================
# SECTION 13: EXPONENTIAL COMPLEXITY
# =============================================================================

def count_binary_configurations(n):
    """
    Number of possible configurations of n binary variables.

    Each variable can be:

        0 or 1

    Therefore:

        total configurations = 2^n
    """

    return 2 ** n


print("\nBINARY CONFIGURATION GROWTH")
print("-" * 80)

for n in range(1, 21):

    print(
        f"{n:2d} variables -> "
        f"{count_binary_configurations(n):,} configurations"
    )


"""
This simple example explains combinatorial explosion.

If we have:

    1 binary variable  -> 2 possibilities
    2 binary variables -> 4 possibilities
    3 binary variables -> 8 possibilities

and so on.

For n variables:

    2^n

This is exponential growth.
"""


# =============================================================================
# SECTION 14: FACTORIAL COMPLEXITY
# =============================================================================

import math

print("\nFACTORIAL GROWTH")
print("-" * 80)

for n in range(1, 11):

    print(f"{n:2d}! = {math.factorial(n):,}")


"""
Factorial growth is even more aggressive.

For example:

    5!  = 120
    10! = 3,628,800
    15! = 1,307,674,368,000

Factorial growth appears naturally when we need to examine permutations.

This becomes important in problems such as the Traveling Salesperson Problem.
"""


# =============================================================================
# SECTION 15: COMPLEXITY COMPARISON
# =============================================================================

print("\nCOMPLEXITY COMPARISON")
print("-" * 80)

n = 20

complexities = {
    "O(1)": 1,
    "O(log n)": math.log2(n),
    "O(n)": n,
    "O(n log n)": n * math.log2(n),
    "O(n^2)": n ** 2,
    "O(n^3)": n ** 3,
    "O(2^n)": 2 ** n,
    "O(n!)": math.factorial(n)
}

for name, value in complexities.items():

    print(f"{name:12s} -> {value:,.0f}")


"""
For n = 20:

    n              = 20
    n^2            = 400
    n^3            = 8,000
    2^n            = 1,048,576
    n!             = 2,432,902,008,176,640,000

This illustrates why algorithmic complexity matters.
"""


# =============================================================================
# SECTION 16: SPACE COMPLEXITY
# =============================================================================

"""
Time is not the only computational resource.

Space complexity describes how much additional memory an algorithm needs.

Examples:

    O(1)
        Constant extra memory

    O(n)
        Memory grows linearly with input

    O(n^2)
        Memory grows quadratically

An algorithm may be fast but memory-intensive.

Another algorithm may use little memory but take longer to execute.

Algorithm design is therefore often a trade-off between:

    time
    memory
    accuracy
    implementation complexity
"""


# =============================================================================
# SECTION 17: WHAT IS SCALING?
# =============================================================================

"""
Scaling asks:

    What happens when the input becomes much larger?

Suppose an algorithm handles:

    1,000 records

very easily.

That does not prove it can handle:

    1,000,000,000 records

efficiently.

A central engineering principle is:

    An algorithm should scale appropriately with the size of the problem.

A poor algorithm may work perfectly during development and fail when deployed
at production scale.
"""


# =============================================================================
# SECTION 18: COMBINATORIAL EXPLOSION
# =============================================================================

"""
Combinatorial explosion occurs when the number of possibilities grows extremely
rapidly as the number of input elements increases.

For example:

    subsets of n elements = 2^n

    permutations of n elements = n!

This creates a major limitation for brute-force classical computation.
"""


def number_of_subsets(n):
    """
    Every element can either be:

        included
        excluded

    Therefore there are 2^n subsets.
    """

    return 2 ** n


def number_of_permutations(n):
    """
    Number of permutations of n unique objects.

    Formula:

        n!
    """

    return math.factorial(n)


print("\nCOMBINATORIAL EXPLOSION")
print("-" * 80)

for n in range(1, 11):

    print(
        f"n={n:2d} | "
        f"subsets={number_of_subsets(n):8,d} | "
        f"permutations={number_of_permutations(n):10,d}"
    )


# =============================================================================
# SECTION 19: BRUTE FORCE
# =============================================================================

"""
Brute force means systematically trying all possible candidates.

Advantages:

    - Simple
    - Easy to understand
    - Often easy to implement
    - Can guarantee a solution if the search space is finite and exhaustive

Disadvantages:

    - Can become extremely slow
    - Does not scale well
    - May require exponential or factorial work
"""


def brute_force_subset_sum(numbers, target):
    """
    Brute-force solution to the subset-sum problem.

    Determines whether any subset of numbers sums to target.

    Complexity:
        O(2^n)

    because there are 2^n subsets.
    """

    n = len(numbers)

    for mask in range(2 ** n):

        total = 0

        for i in range(n):

            if mask & (1 << i):

                total += numbers[i]

        if total == target:

            return True

    return False


print("\nBRUTE-FORCE SUBSET SUM")
print("-" * 80)

numbers = [3, 7, 11, 15, 20]

print(brute_force_subset_sum(numbers, 26))
print(brute_force_subset_sum(numbers, 100))


# =============================================================================
# SECTION 20: WHAT IS AN NP PROBLEM?
# =============================================================================

"""
Now we reach a fundamental concept.

NP does NOT mean:

    "Not Polynomial"

That is a common misconception.

NP traditionally means:

    Nondeterministic Polynomial time

An important practical interpretation is:

    A proposed solution to an NP problem can be verified in polynomial time.

Consider a puzzle.

Suppose someone gives us a proposed solution.

Checking the solution may be easy.

Finding that solution from scratch may be much harder.

This difference is central to complexity theory.
"""


# =============================================================================
# SECTION 21: P
# =============================================================================

"""
P is the class of decision problems that can be solved in polynomial time
by a deterministic classical computer model.

Examples include many problems involving:

    - sorting
    - searching
    - shortest paths
    - minimum spanning trees
    - basic graph algorithms

Informally:

    P = efficiently solvable problems
"""


# =============================================================================
# SECTION 22: NP
# =============================================================================

"""
NP contains decision problems for which a proposed solution can be verified
in polynomial time.

Important relationship:

    P ⊆ NP

Every problem that can be solved efficiently can also have its solution
verified efficiently.

The major unanswered question is:

    P = NP ?

or:

    P != NP ?

The general consensus among complexity theorists is that:

    P != NP

but this has not been proven.
"""


# =============================================================================
# SECTION 23: NP-COMPLETE
# =============================================================================

"""
An NP-complete problem has two important properties:

    1. It belongs to NP.
    2. Every problem in NP can be polynomially reduced to it.

NP-complete problems are therefore among the hardest problems in NP.

If someone discovered a polynomial-time algorithm for one NP-complete problem,
then every NP problem would have a polynomial-time algorithm.

That would imply:

    P = NP
"""


# =============================================================================
# SECTION 24: NP-HARD
# =============================================================================

"""
NP-hard is a broader concept.

An NP-hard problem is at least as hard as every problem in NP under the
appropriate polynomial-time reduction framework.

An NP-hard problem does NOT necessarily have to belong to NP.

Therefore:

    NP-complete = NP + NP-hard

But:

    NP-hard does not necessarily mean NP-complete.
"""


# =============================================================================
# SECTION 25: SIMPLE RELATIONSHIP
# =============================================================================

"""
A useful conceptual diagram is:

                NP-HARD
        ┌───────────────────────┐
        │                       │
        │     NP-COMPLETE       │
        │    ┌─────────────┐    │
        │    │             │    │
        │    │     NP      │    │
        │    │   ┌─────┐   │    │
        │    │   │  P  │   │    │
        │    │   └─────┘   │    │
        │    │             │    │
        │    └─────────────┘    │
        │                       │
        └───────────────────────┘

This diagram is conceptual.

The exact mathematical relationships depend on the definitions of the
complexity classes and problem types.
"""


# =============================================================================
# SECTION 26: DECISION VS OPTIMIZATION
# =============================================================================

"""
Complexity theory frequently studies decision problems.

A decision problem has a YES/NO answer.

Example:

    "Is there a route shorter than 500 km?"

Optimization version:

    "What is the shortest possible route?"

The distinction is important because many classical complexity classes are
defined using decision problems.
"""


# =============================================================================
# SECTION 27: TRAVELING SALESPERSON PROBLEM
# =============================================================================

"""
The Traveling Salesperson Problem (TSP):

Given:

    - a collection of cities
    - distances between cities

Find a route that:

    - visits every city
    - visits each city once
    - returns to the starting city
    - minimizes total distance

The optimization version is NP-hard.

The decision version:

    "Is there a tour with total distance <= K?"

is NP-complete.

A brute-force approach examines possible city orderings.

For n cities, the number of possible tours grows approximately as:

    (n - 1)!

or, after accounting for symmetry in some formulations:

    (n - 1)! / 2
"""


def tsp_brute_force(distances):
    """
    Brute-force TSP solver.

    distances:
        Dictionary mapping (city_a, city_b) to distance.

    Returns:
        Best route and best distance.

    This is only suitable for small examples.

    Complexity:
        Approximately O(n!)
    """

    from itertools import permutations

    cities = list(range(len(distances)))

    start = cities[0]

    best_distance = float("inf")
    best_route = None

    for permutation in permutations(cities[1:]):

        route = [start] + list(permutation) + [start]

        total_distance = 0

        for i in range(len(route) - 1):

            total_distance += distances[route[i]][route[i + 1]]

        if total_distance < best_distance:

            best_distance = total_distance
            best_route = route

    return best_route, best_distance


distance_matrix = [
    [0, 10, 15, 20],
    [10, 0, 35, 25],
    [15, 35, 0, 30],
    [20, 25, 30, 0]
]

route, distance = tsp_brute_force(distance_matrix)

print("\nTRAVELING SALESPERSON PROBLEM")
print("-" * 80)
print("Best route:", route)
print("Distance:", distance)


# =============================================================================
# SECTION 28: WHY TSP BECOMES DIFFICULT
# =============================================================================

print("\nTSP SEARCH SPACE")
print("-" * 80)

for n in range(4, 11):

    possible_routes = math.factorial(n - 1)

    print(
        f"{n:2d} cities -> approximately "
        f"{possible_routes:,} routes"
    )


"""
The important observation is not that TSP is impossible.

It is that the naive exact approach scales extremely poorly.

For example:

    10 cities -> 9! = 362,880

    20 cities -> 19! ≈ 1.216 × 10^17

    50 cities -> 49!

The number becomes enormous.
"""


# =============================================================================
# SECTION 29: KNAPSACK PROBLEM
# =============================================================================

"""
Knapsack Problem:

Given:

    - items
    - values
    - weights
    - maximum capacity

Choose items to maximize total value without exceeding capacity.

A brute-force algorithm examines every possible subset.

For n items:

    number of subsets = 2^n

The decision version is NP-complete under the standard formulation.
"""


def knapsack_brute_force(weights, values, capacity):
    """
    Brute-force 0/1 knapsack.

    Each item can be:

        0 = excluded
        1 = included

    Complexity:

        O(2^n)
    """

    n = len(weights)

    best_value = 0
    best_items = []

    for mask in range(2 ** n):

        total_weight = 0
        total_value = 0
        selected = []

        for i in range(n):

            if mask & (1 << i):

                total_weight += weights[i]
                total_value += values[i]
                selected.append(i)

        if total_weight <= capacity and total_value > best_value:

            best_value = total_value
            best_items = selected

    return best_items, best_value


weights = [2, 3, 4, 5]
values = [3, 4, 5, 8]
capacity = 8

items, value = knapsack_brute_force(weights, values, capacity)

print("\nKNAPSACK")
print("-" * 80)
print("Selected item indexes:", items)
print("Maximum value:", value)


# =============================================================================
# SECTION 30: SUBSET SUM
# =============================================================================

"""
Subset Sum:

Given:

    a set of integers
    a target value

Question:

    Does there exist a subset whose sum equals the target?

Example:

    [3, 7, 10, 14]

Target:

    17

Solution:

    3 + 14 = 17

The decision version is NP-complete.

Brute force requires checking up to:

    2^n

subsets.
"""


# =============================================================================
# SECTION 31: BOOLEAN SATISFIABILITY
# =============================================================================

"""
SAT stands for Boolean Satisfiability Problem.

Given a Boolean formula, determine whether there is an assignment of:

    True
    False

that makes the formula true.

Example:

    (A OR B) AND (NOT A OR C)

The SAT problem is historically important because it was the first problem
proved to be NP-complete in the famous Cook-Levin theorem.

Many practical problems can be transformed into SAT.
"""


def evaluate_boolean_formula(a, b, c):
    """
    Evaluates:

        (A OR B) AND (NOT A OR C)
    """

    return (a or b) and ((not a) or c)


print("\nSAT EXAMPLE")
print("-" * 80)

solutions = []

for a in [False, True]:

    for b in [False, True]:

        for c in [False, True]:

            if evaluate_boolean_formula(a, b, c):

                solutions.append((a, b, c))


for solution in solutions:

    print(solution)


"""
With n Boolean variables, there are:

    2^n

possible assignments.

Brute-force SAT therefore has exponential search behavior.
"""


# =============================================================================
# SECTION 32: GRAPH COLORING
# =============================================================================

"""
Graph Coloring:

Given a graph and k colors, determine whether the vertices can be colored
such that adjacent vertices have different colors.

The decision version of k-colorability is NP-complete for suitable k,
including k >= 3.

Applications include:

    - scheduling
    - frequency assignment
    - register allocation
    - resource allocation
"""


def can_color_graph(graph, colors):
    """
    Simple backtracking graph-coloring solver.

    graph:
        Dictionary:
            vertex -> list of neighboring vertices

    colors:
        Number of available colors

    Returns:
        True if a valid coloring exists.

    Backtracking may have exponential worst-case complexity.
    """

    vertices = list(graph.keys())

    assignment = {}

    def is_valid(vertex, color):

        for neighbor in graph[vertex]:

            if assignment.get(neighbor) == color:

                return False

        return True

    def backtrack(index):

        if index == len(vertices):

            return True

        vertex = vertices[index]

        for color in range(colors):

            if is_valid(vertex, color):

                assignment[vertex] = color

                if backtrack(index + 1):

                    return True

                del assignment[vertex]

        return False

    return backtrack(0)


graph = {
    "A": ["B", "C"],
    "B": ["A", "C"],
    "C": ["A", "B", "D"],
    "D": ["C"]
}

print("\nGRAPH COLORING")
print("-" * 80)
print("Can color with 3 colors:", can_color_graph(graph, 3))


# =============================================================================
# SECTION 33: HAMILTONIAN CYCLE
# =============================================================================

"""
A Hamiltonian cycle is a cycle in a graph that:

    - visits every vertex exactly once
    - returns to the starting vertex

The decision problem is NP-complete.

This is another example where the number of possible arrangements can grow
very rapidly.
"""


# =============================================================================
# SECTION 34: VERIFICATION VS SEARCH
# =============================================================================

"""
One of the deepest ideas behind NP is:

    Finding a solution can be difficult,
    while checking a proposed solution can be easy.

Example: Sudoku

Finding a completed Sudoku puzzle may require substantial search.

But if someone gives you a completed grid, checking whether it obeys the
rules is comparatively easy.

Similarly:

    TSP

Finding an optimal route may be hard.

But checking whether a given route has length <= K is easy:

    1. Follow the route.
    2. Add the distances.
    3. Compare the result with K.

This distinction is central to NP.
"""


def verify_tsp_route(route, distances, maximum_distance):
    """
    Verifies whether a proposed TSP route has total distance <= maximum_distance.
    """

    if route[0] != route[-1]:

        return False

    total = 0

    for i in range(len(route) - 1):

        total += distances[route[i]][route[i + 1]]

    return total <= maximum_distance


route = [0, 1, 3, 2, 0]

print("\nVERIFYING A TSP SOLUTION")
print("-" * 80)

print(
    verify_tsp_route(
        route,
        distance_matrix,
        100
    )
)


# =============================================================================
# SECTION 35: POLYNOMIAL-TIME REDUCTIONS
# =============================================================================

"""
A polynomial-time reduction is a way to transform one computational problem
into another efficiently.

Suppose problem A can be transformed into problem B in polynomial time.

We write conceptually:

    A <=p B

This means:

    If B can be solved efficiently,
    then A can also be solved efficiently.

Reductions are fundamental to proving that problems are NP-complete or
NP-hard.

They allow complexity theorists to compare the difficulty of problems.
"""


# =============================================================================
# SECTION 36: WHY NP-COMPLETENESS MATTERS
# =============================================================================

"""
Suppose we discover:

    Polynomial-time algorithm for one NP-complete problem

Then:

    Every problem in NP could potentially be solved in polynomial time.

Therefore:

    P = NP

This would have enormous consequences for:

    - optimization
    - scheduling
    - logistics
    - cryptography
    - artificial intelligence
    - operations research
    - automated reasoning
    - software verification
"""


# =============================================================================
# SECTION 37: DOES NP-HARD MEAN IMPOSSIBLE?
# =============================================================================

"""
NO.

NP-hard does not mean:

    "No solution exists."

It also does not mean:

    "Computers cannot solve it."

It means that there is strong theoretical evidence that no polynomial-time
algorithm is known for the general problem under standard assumptions.

Many NP-hard problems can be solved for:

    - small inputs
    - special cases
    - structured datasets
    - approximate solutions
    - heuristic methods
    - instances with useful constraints
"""


# =============================================================================
# SECTION 38: EXACT VS APPROXIMATE SOLUTIONS
# =============================================================================

"""
For difficult optimization problems, we often distinguish between:

    Exact algorithms

and:

    Approximation algorithms / heuristics

Exact algorithm:

    Guarantees the optimal solution.

Approximation:

    Produces a solution that may not be optimal but is sufficiently good.

In real-world systems, an approximate answer delivered quickly may be more
valuable than a perfect answer delivered after an impractical amount of time.
"""


# =============================================================================
# SECTION 39: GREEDY HEURISTIC
# =============================================================================

def greedy_knapsack(weights, values, capacity):
    """
    Greedy heuristic for the fractional knapsack-style strategy.

    Items are selected according to value/weight ratio.

    Important:
        This is NOT guaranteed to solve the 0/1 knapsack problem optimally.

    It demonstrates the difference between a fast heuristic and an exact
    algorithm.
    """

    items = list(range(len(weights)))

    items.sort(
        key=lambda i: values[i] / weights[i],
        reverse=True
    )

    selected = []
    total_weight = 0
    total_value = 0

    for i in items:

        if total_weight + weights[i] <= capacity:

            selected.append(i)
            total_weight += weights[i]
            total_value += values[i]

    return selected, total_value


selected, value = greedy_knapsack(
    weights,
    values,
    capacity
)

print("\nGREEDY KNAPSACK HEURISTIC")
print("-" * 80)
print("Selected:", selected)
print("Value:", value)


# =============================================================================
# SECTION 40: DYNAMIC PROGRAMMING
# =============================================================================

"""
Dynamic Programming (DP) can dramatically improve some problems that appear
exponential under naive brute-force search.

DP works particularly well when a problem has:

    1. Overlapping subproblems
    2. Optimal substructure

The important point is:

    Not every NP-hard problem becomes polynomial through dynamic programming.

Some NP-hard problems have pseudo-polynomial algorithms.

Knapsack is an important example.
"""


def knapsack_dynamic_programming(weights, values, capacity):
    """
    0/1 Knapsack using dynamic programming.

    Time complexity:

        O(n * capacity)

    Space complexity:

        O(n * capacity)

    Important:
        This is pseudo-polynomial, not polynomial in the number of bits
        required to represent the input capacity.
    """

    n = len(weights)

    dp = [
        [0] * (capacity + 1)
        for _ in range(n + 1)
    ]

    for i in range(1, n + 1):

        weight = weights[i - 1]
        value = values[i - 1]

        for c in range(capacity + 1):

            if weight <= c:

                dp[i][c] = max(
                    dp[i - 1][c],
                    value + dp[i - 1][c - weight]
                )

            else:

                dp[i][c] = dp[i - 1][c]

    return dp[n][capacity]


print("\nDYNAMIC PROGRAMMING KNAPSACK")
print("-" * 80)

print(
    "Optimal value:",
    knapsack_dynamic_programming(
        weights,
        values,
        capacity
    )
)


# =============================================================================
# SECTION 41: MEMOIZATION
# =============================================================================

"""
Memoization stores previously computed results.

Without memoization, recursive algorithms may repeatedly solve the same
subproblem.

Memoization can turn some exponential recursive algorithms into much more
efficient algorithms.

But the amount of stored state can itself consume memory.
"""


def fibonacci_naive(n):
    """
    Naive recursive Fibonacci.

    Complexity:
        Approximately exponential.
    """

    if n <= 1:

        return n

    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)


def fibonacci_memoized(n, memo=None):
    """
    Memoized Fibonacci.

    Time complexity:
        O(n)

    Space complexity:
        O(n)
    """

    if memo is None:

        memo = {}

    if n in memo:

        return memo[n]

    if n <= 1:

        return n

    memo[n] = (
        fibonacci_memoized(n - 1, memo)
        +
        fibonacci_memoized(n - 2, memo)
    )

    return memo[n]


print("\nMEMOIZATION")
print("-" * 80)

print("Naive Fibonacci:", fibonacci_naive(20))
print("Memoized Fibonacci:", fibonacci_memoized(100))


# =============================================================================
# SECTION 42: BRANCH AND BOUND
# =============================================================================

"""
Branch and Bound is an optimization technique.

Instead of exploring every possible solution:

    1. Divide the search space.
    2. Calculate bounds.
    3. Eliminate branches that cannot beat the current best solution.

This can dramatically reduce practical search.

But worst-case complexity may still be exponential.
"""


# =============================================================================
# SECTION 43: BACKTRACKING
# =============================================================================

"""
Backtracking builds a solution incrementally.

If a partial solution cannot possibly lead to a valid solution:

    stop exploring that branch.

This is useful for:

    - Sudoku
    - N-Queens
    - graph coloring
    - constraint satisfaction
    - scheduling

Backtracking does not automatically make an NP-hard problem polynomial.

It simply avoids some unnecessary search.
"""


def n_queens(n):
    """
    Solves the N-Queens problem using backtracking.

    N-Queens asks us to place N queens on an N x N chessboard so that no two
    queens attack each other.

    This demonstrates exponential-style search with pruning.
    """

    board = [-1] * n

    solutions = []

    def safe(row, col):

        for previous_row in range(row):

            previous_col = board[previous_row]

            if previous_col == col:

                return False

            if abs(previous_col - col) == abs(previous_row - row):

                return False

        return True

    def backtrack(row):

        if row == n:

            solutions.append(board.copy())

            return

        for col in range(n):

            if safe(row, col):

                board[row] = col

                backtrack(row + 1)

                board[row] = -1

    backtrack(0)

    return solutions


solutions = n_queens(8)

print("\nN-QUEENS BACKTRACKING")
print("-" * 80)
print("Number of solutions for 8 queens:", len(solutions))


# =============================================================================
# SECTION 44: WHY HARDWARE SPEED DOES NOT SOLVE EXPONENTIAL GROWTH
# =============================================================================

"""
Suppose a computer becomes:

    10 times faster.

That is an enormous engineering improvement.

But consider an exponential algorithm.

If the problem size increases from:

    n

to:

    n + 10

then:

    2^(n+10) = 1024 * 2^n

The workload has increased by a factor of 1024.

A hardware improvement of 10x is overwhelmed by the mathematical growth.

This is why algorithmic efficiency often matters more than simply buying
faster hardware.
"""


# =============================================================================
# SECTION 45: A NUMERICAL ILLUSTRATION
# =============================================================================

print("\nHARDWARE SPEED VS EXPONENTIAL GROWTH")
print("-" * 80)

for n in [20, 30, 40, 50, 60]:

    operations = 2 ** n

    print(
        f"n={n:2d} -> "
        f"2^n={operations:,}"
    )


# =============================================================================
# SECTION 46: CLASSICAL COMPUTING IS NOT "WEAK"
# =============================================================================

"""
It is important not to misunderstand these limitations.

Classical computers are extremely powerful.

They efficiently handle:

    - operating systems
    - databases
    - web servers
    - scientific simulations
    - machine learning
    - cryptography
    - graphics
    - financial systems
    - telecommunications
    - artificial intelligence

The limitation concerns certain classes of problems and the scaling behavior
of algorithms.

The problem is not:

    "Classical computers cannot compute."

The problem is:

    "Some computations scale too rapidly to remain practical."
"""


# =============================================================================
# SECTION 47: TRACTABLE VS INTRACTABLE
# =============================================================================

"""
In theoretical computer science:

TRACTABLE
---------
A problem is generally considered tractable when an algorithm exists whose
resource requirements grow reasonably with input size, commonly polynomial time.

INTRACTABLE
-----------
A problem is considered intractable when known algorithms require resources
that become impractical as the input grows.

The boundary is not always simply:

    polynomial = practical
    exponential = impossible

Because:

    - a large polynomial can be impractical
    - a small exponential can be practical
    - input structure matters
    - hardware matters
    - approximation may be acceptable
"""


# =============================================================================
# SECTION 48: WORST CASE, AVERAGE CASE, BEST CASE
# =============================================================================

"""
Algorithm analysis can examine:

    Best case
    Average case
    Worst case

Example:

Linear search:

    Best case:
        O(1)

    Worst case:
        O(n)

    Average case:
        approximately O(n)

Worst-case complexity is especially important for understanding theoretical
guarantees.
"""


# =============================================================================
# SECTION 49: BIG-O, BIG-THETA, BIG-OMEGA
# =============================================================================

"""
Big-O:

    Upper-bound style description.

Big-Omega:

    Lower-bound style description.

Big-Theta:

    Tight asymptotic bound.

For example, if an algorithm always performs proportional to n operations:

    O(n)
    Ω(n)
    Θ(n)

may all be appropriate under the corresponding formal conditions.

In introductory algorithm analysis, Big-O is commonly used to communicate
growth behavior.
"""


# =============================================================================
# SECTION 50: ASYMPTOTIC THINKING
# =============================================================================

"""
Asymptotic analysis focuses on what happens as n becomes very large.

For example:

    3n^2 + 10n + 500

is:

    O(n^2)

because the dominant growth term is n^2.

Similarly:

    1000n + 500000

is:

    O(n)

even though the constant 500000 may matter greatly for real-world performance.

Big-O deliberately abstracts away many machine-specific constants.
"""


# =============================================================================
# SECTION 51: AMORTIZED COMPLEXITY
# =============================================================================

"""
Amortized analysis studies the average cost of operations over a sequence.

For example, dynamic arrays sometimes need to resize.

Most insertions may be cheap.

Occasionally, resizing requires copying many elements.

Despite expensive individual operations, the average cost per insertion can
still be O(1) amortized for a standard dynamic-array strategy.

This illustrates why a single operation's worst case does not always describe
the total behavior of a system.
"""


# =============================================================================
# SECTION 52: PARAMETERIZED COMPLEXITY
# =============================================================================

"""
Parameterized complexity asks whether a difficult problem becomes manageable
when a particular parameter is small.

Instead of considering only:

    n

we may analyze:

    f(k) * n^c

where:

    k = a parameter
    c = constant

This can make some practically useful instances of theoretically difficult
problems manageable.

The key lesson:

    Complexity depends not only on input size,
    but potentially on the structure of the input.
"""


# =============================================================================
# SECTION 53: PSEUDO-POLYNOMIAL TIME
# =============================================================================

"""
A pseudo-polynomial algorithm has running time polynomial in the numerical
value of an input parameter, rather than polynomial in the length of its
binary representation.

Example:

    Knapsack dynamic programming:

        O(n * capacity)

If capacity is numerically large, this can still be expensive.

Suppose:

    capacity = 1,000,000

The algorithm may require millions of states.

The number 1,000,000 itself requires only about 20 bits in binary.

Therefore O(capacity) is not polynomial in the input's bit length.
"""


# =============================================================================
# SECTION 54: APPROXIMATION ALGORITHMS
# =============================================================================

"""
Approximation algorithms intentionally sacrifice guaranteed optimality for
computational efficiency.

Some NP-hard optimization problems have algorithms with provable approximation
ratios.

Example concept:

    If an algorithm is a 2-approximation for a minimization problem,

then its result is guaranteed to be no more than twice the optimum under the
algorithm's assumptions.

Approximation algorithms are important in:

    - logistics
    - network design
    - scheduling
    - resource allocation
    - facility location
"""


# =============================================================================
# SECTION 55: HEURISTICS
# =============================================================================

"""
A heuristic is a practical strategy that often produces good solutions without
necessarily providing a formal guarantee of optimality.

Examples:

    - nearest neighbor
    - local search
    - simulated annealing
    - genetic algorithms
    - greedy methods

Heuristics can be extremely useful in real systems.

Their practical quality depends heavily on the problem and the data.
"""


# =============================================================================
# SECTION 56: LOCAL SEARCH
# =============================================================================

def hill_climbing_example(values):
    """
    Simple one-dimensional hill-climbing demonstration.

    Starts from the first value and moves toward a neighboring larger value.

    This illustrates the idea of local improvement.

    It is not a general-purpose optimizer.
    """

    index = 0

    while True:

        left = values[index - 1] if index > 0 else float("-inf")
        right = (
            values[index + 1]
            if index < len(values) - 1
            else float("-inf")
        )

        if right > values[index]:

            index += 1

        elif left > values[index]:

            index -= 1

        else:

            break

    return index, values[index]


values = [1, 3, 5, 7, 6, 4, 2]

index, maximum = hill_climbing_example(values)

print("\nLOCAL SEARCH")
print("-" * 80)
print("Local maximum found at index:", index)
print("Value:", maximum)


# =============================================================================
# SECTION 57: THE COMPLEXITY OF REAL-WORLD SYSTEMS
# =============================================================================

"""
Real-world computational problems often contain several layers.

Example: logistics optimization

    Input:
        thousands of locations

    Constraints:
        delivery windows
        vehicle capacities
        traffic
        fuel
        driver schedules
        regulations

The mathematical problem may contain an NP-hard core.

Practical systems therefore combine:

    - exact algorithms
    - heuristics
    - approximation
    - dynamic programming
    - graph algorithms
    - machine learning
    - domain-specific rules
"""


# =============================================================================
# SECTION 58: COMPLEXITY IN AI
# =============================================================================

"""
AI systems also encounter computational complexity.

Examples include:

    - combinatorial optimization
    - planning
    - scheduling
    - search
    - constraint satisfaction
    - probabilistic inference
    - game playing

Modern AI often relies on strategies that avoid exhaustive search.

Examples:

    - pruning
    - heuristic search
    - learned representations
    - approximate inference
    - beam search
    - Monte Carlo methods
"""


# =============================================================================
# SECTION 59: COMPLEXITY IN CRYPTOGRAPHY
# =============================================================================

"""
Cryptography relies heavily on computational difficulty.

A cryptographic system often attempts to create a situation where:

    legitimate operation = efficient

while:

    unauthorized inversion = computationally difficult

Examples of hard mathematical problems have historically been used in
cryptographic constructions.

But cryptographic security is not simply equivalent to "NP-hard".

Many cryptographic assumptions are based on specialized mathematical problems
and computational hardness assumptions.

Therefore:

    NP-hardness != automatic cryptographic security
"""


# =============================================================================
# SECTION 60: QUANTUM COMPUTING AND CLASSICAL LIMITATIONS
# =============================================================================

"""
Quantum computing introduces a different computational model based on quantum
mechanics.

A classical bit:

    0 or 1

A qubit can exist in a quantum superposition of basis states:

    α|0> + β|1>

with:

    |α|^2 + |β|^2 = 1

Quantum algorithms can exploit:

    - superposition
    - interference
    - entanglement

to provide speedups for certain computational tasks.

Important:

    Quantum computing does NOT mean that all classical hard problems
    automatically become easy.
"""


# =============================================================================
# SECTION 61: SHOR'S ALGORITHM
# =============================================================================

"""
Shor's algorithm provides a major theoretical quantum speedup for:

    - integer factorization
    - discrete logarithm

This is important for cryptography because several widely used public-key
cryptographic systems rely on the difficulty of related mathematical problems.

A sufficiently powerful fault-tolerant quantum computer could threaten
cryptographic schemes based on these problems.
"""


# =============================================================================
# SECTION 62: GROVER'S ALGORITHM
# =============================================================================

"""
Grover's algorithm provides a quadratic speedup for unstructured search.

Classical brute-force search:

    O(N)

Quantum search:

    O(sqrt(N))

This is a significant speedup.

But note:

    sqrt(2^n) = 2^(n/2)

This is still exponential.

Therefore, Grover's algorithm does NOT turn generic exponential search into
polynomial-time search.
"""


def classical_search_space(n):
    """
    Number of candidates in an n-bit brute-force search.
    """

    return 2 ** n


def grover_style_search_space(n):
    """
    Approximate number of quantum oracle iterations represented by sqrt(2^n).

    This is only a mathematical illustration, not a quantum simulation.
    """

    return 2 ** (n / 2)


print("\nCLASSICAL VS GROVER-STYLE SEARCH SCALE")
print("-" * 80)

for n in [10, 20, 40, 80]:

    classical = classical_search_space(n)
    quantum = grover_style_search_space(n)

    print(
        f"n={n:2d} | "
        f"classical ≈ {classical:,.0f} | "
        f"quantum-style ≈ {quantum:,.0f}"
    )


# =============================================================================
# SECTION 63: QUANTUM COMPUTING DOES NOT SOLVE P VS NP
# =============================================================================

"""
A common misconception is:

    "Quantum computers will solve NP-hard problems efficiently."

This is NOT known to be true.

Quantum computing provides important speedups for certain problems.

The class of problems efficiently solvable by bounded-error quantum computers
is commonly described using BQP.

It is not known that:

    NP ⊆ BQP

or that quantum computers efficiently solve all NP-complete problems.

Therefore, quantum computing should not be viewed as a universal replacement
for classical algorithms.
"""


# =============================================================================
# SECTION 64: WHY CLASSICAL COMPUTING STILL MATTERS
# =============================================================================

"""
Even in a future with large-scale quantum computers, classical computing will
remain essential.

Quantum systems require classical systems for:

    - control
    - measurement
    - data processing
    - orchestration
    - networking
    - storage
    - user interfaces

Most realistic quantum computing architectures are expected to be hybrid:

    Classical computer
            |
            v
    Quantum processor
            |
            v
    Classical post-processing
"""


# =============================================================================
# SECTION 65: HOW ENGINEERS HANDLE HARD PROBLEMS
# =============================================================================

"""
When facing a computationally difficult problem, engineers should ask:

    1. Is the problem actually NP-hard?
    2. Is exact optimality required?
    3. Can the problem be simplified?
    4. Can the input be constrained?
    5. Are there special cases?
    6. Can dynamic programming help?
    7. Can memoization help?
    8. Can backtracking prune the search?
    9. Can branch and bound help?
    10. Can approximation be used?
    11. Can a heuristic provide a sufficiently good answer?
    12. Can the problem be decomposed?
    13. Can parallel processing help?
    14. Can a specialized solver be used?
"""


# =============================================================================
# SECTION 66: PARALLELISM
# =============================================================================

"""
Parallel computing can reduce execution time by distributing work across
multiple processors.

If work can be divided into independent pieces:

    total work / number of processors

can provide a useful speedup.

But parallelism does not magically change:

    O(2^n)

into:

    O(n)

There are limits from:

    - dependencies
    - communication
    - synchronization
    - memory bandwidth
    - sequential sections

This is related to Amdahl's Law.
"""


# =============================================================================
# SECTION 67: AMDAHL'S LAW
# =============================================================================

"""
Amdahl's Law describes the theoretical speedup of a system when only part of
the computation is parallelized.

If:

    p = fraction of work that can be parallelized
    s = 1 - p = sequential fraction
    N = number of processors

Then idealized speedup is:

    Speedup = 1 / (s + p/N)

As N becomes extremely large:

    Speedup approaches:

        1/s

Therefore even a small sequential component limits total speedup.
"""


def amdahl_speedup(parallel_fraction, processors):
    """
    Calculates idealized Amdahl's Law speedup.
    """

    sequential_fraction = 1 - parallel_fraction

    return 1 / (
        sequential_fraction
        +
        parallel_fraction / processors
    )


print("\nAMDAHL'S LAW")
print("-" * 80)

for processors in [1, 2, 4, 8, 16, 64, 256]:

    speedup = amdahl_speedup(0.95, processors)

    print(
        f"{processors:3d} processors -> "
        f"speedup ≈ {speedup:.2f}x"
    )


# =============================================================================
# SECTION 68: ENERGY AS A COMPUTATIONAL LIMIT
# =============================================================================

"""
Computation is not free.

Real systems consume energy.

As computational workloads increase, systems face:

    - power limits
    - cooling requirements
    - battery limitations
    - hardware costs
    - data-center constraints

Therefore computational complexity can become an economic and physical
engineering problem, not merely a theoretical one.
"""


# =============================================================================
# SECTION 69: MEMORY LIMITS
# =============================================================================

"""
Suppose an algorithm requires:

    O(2^n)

memory.

Even if computation were fast, the memory requirement could become impossible.

For example:

    n = 40

requires:

    2^40

states.

If each state required even a small amount of memory, the total requirement
could become enormous.

This demonstrates that both:

    time complexity
    space complexity

must be considered.
"""


# =============================================================================
# SECTION 70: TIME-SPACE TRADE-OFF
# =============================================================================

"""
Sometimes we can use additional memory to reduce computation.

Memoization is a classic example.

Without caching:

    repeated work

With caching:

    store previous results

Therefore:

    more memory
        |
        v
    less repeated computation

But this trade-off is not always available or beneficial.
"""


# =============================================================================
# SECTION 71: THE MOST IMPORTANT COMPLEXITY LESSON
# =============================================================================

"""
The central lesson of this topic is:

    Computational difficulty is often about scaling.

An algorithm may appear fast for:

    n = 10

but fail for:

    n = 1,000,000

or:

    n = 1,000,000,000

Understanding complexity allows us to predict these problems before deployment.
"""


# =============================================================================
# SECTION 72: SUMMARY TABLE
# =============================================================================

print("\nCOMPLEXITY SUMMARY")
print("-" * 80)

summary = [
    ("O(1)", "Constant", "Excellent"),
    ("O(log n)", "Logarithmic", "Excellent"),
    ("O(n)", "Linear", "Good"),
    ("O(n log n)", "Linearithmic", "Good"),
    ("O(n^2)", "Quadratic", "Can become expensive"),
    ("O(n^3)", "Cubic", "Often expensive at scale"),
    ("O(2^n)", "Exponential", "Rapidly becomes impractical"),
    ("O(n!)", "Factorial", "Extremely rapid growth")
]

for complexity, description, practical in summary:

    print(
        f"{complexity:10s} | "
        f"{description:15s} | "
        f"{practical}"
    )


# =============================================================================
# SECTION 73: FINAL KNOWLEDGE CHECK
# =============================================================================

print("\nKNOWLEDGE CHECK")
print("-" * 80)

questions = {
    1: "What does O(n) mean?",
    2: "Why does O(2^n) scale poorly?",
    3: "What is the difference between P and NP?",
    4: "What is NP-complete?",
    5: "What is NP-hard?",
    6: "Why is verification important in NP?",
    7: "Why does brute force become impractical?",
    8: "What is the Traveling Salesperson Problem?",
    9: "Why can dynamic programming help some difficult problems?",
    10: "Does quantum computing automatically solve NP-hard problems?"
}

for number, question in questions.items():

    print(f"{number}. {question}")


# =============================================================================
# FINAL SUMMARY
# =============================================================================

"""
===============================================================================
FINAL SUMMARY
===============================================================================

CLASSICAL COMPUTING
-------------------
Classical computers operate using bits and execute algorithms through
classical computational resources.

COMPUTATIONAL COMPLEXITY
------------------------
Complexity studies how computational requirements grow with input size.

IMPORTANT COMPLEXITIES
----------------------
    O(1)       Constant
    O(log n)   Logarithmic
    O(n)       Linear
    O(n log n) Linearithmic
    O(n^2)     Quadratic
    O(n^3)     Cubic
    O(2^n)     Exponential
    O(n!)      Factorial

SCALING
-------
An algorithm that works on a small dataset may become unusable when the
dataset grows.

COMBINATORIAL EXPLOSION
-----------------------
Many problems generate:

    2^n

or:

    n!

possible configurations.

This causes brute-force algorithms to become impractical.

P
-
Problems solvable in polynomial time under the standard deterministic model.

NP
--
Decision problems whose proposed solutions can be verified in polynomial time.

NP-COMPLETE
-----------
Problems that are both:

    - in NP
    - NP-hard

NP-HARD
-------
Problems at least as hard as every problem in NP under appropriate reductions.
They do not necessarily belong to NP.

IMPORTANT NP PROBLEMS
---------------------
Examples include:

    - SAT
    - 3-SAT
    - subset sum
    - graph coloring
    - Hamiltonian cycle
    - TSP decision version
    - 0/1 knapsack decision version

NP-HARD OPTIMIZATION EXAMPLES
-----------------------------
Examples include:

    - Traveling Salesperson optimization
    - many scheduling problems
    - many routing problems
    - many resource allocation problems

PRACTICAL SOLUTIONS
-------------------
When exact computation becomes expensive, engineers may use:

    - dynamic programming
    - memoization
    - backtracking
    - branch and bound
    - approximation
    - heuristics
    - greedy algorithms
    - local search
    - parallel computing
    - problem decomposition

QUANTUM COMPUTING
-----------------
Quantum algorithms can provide major speedups for certain problems.

Shor's algorithm provides important speedups for factoring and discrete
logarithms.

Grover's algorithm provides a quadratic speedup for unstructured search.

But quantum computing is NOT known to efficiently solve all NP-hard problems.

THE CENTRAL LESSON
------------------
The major limitation of classical computing is not simply that computers are
"slow".

The deeper limitation is that certain problems have solution spaces that grow
far faster than computational resources can practically handle.

Therefore:

    Better algorithms
        >
    blindly using faster hardware

is often the key to scalable computation.

===============================================================================
END OF PROGRAM
===============================================================================
"""
