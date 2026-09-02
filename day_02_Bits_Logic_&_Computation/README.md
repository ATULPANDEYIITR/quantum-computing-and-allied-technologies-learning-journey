# Bits, Logic & Computation

## 1. Bits

A bit is a binary digit. It has two possible values:

* `0`
* `1`

A bit is an abstract representation. The values `0` and `1` may correspond to physical states such as low and high voltage, off and on, or false and true, but these physical meanings are implementation-dependent.

The important idea is that a bit has two possible states.

Binary is a base-2 number system. Each position represents a power of 2.

For example:

```text
1011
```

means:

```text
1 × 2³ + 0 × 2² + 1 × 2¹ + 1 × 2⁰
= 8 + 0 + 2 + 1
= 11
```

For `n` bits, the number of possible combinations is:

```text
2ⁿ
```

Therefore:

```text
1 bit  → 2 combinations
2 bits → 4 combinations
3 bits → 8 combinations
4 bits → 16 combinations
8 bits → 256 combinations
```

An 8-bit quantity is commonly called a byte.

The same bit pattern can have different meanings depending on its interpretation. A sequence of bits can represent an integer, character, address, instruction, part of an image, or another type of data. The bits themselves do not contain an inherent interpretation.

---

## 2. Boolean Values

Boolean logic works with two logical values:

```text
True
False
```

These correspond naturally to:

```text
1
0
```

A Boolean variable therefore behaves like a one-bit logical value.

For example:

```text
A = True
B = False
```

Boolean expressions combine these values using logical operations.

---

## 3. Logic Gates

A logic gate is a computational building block that takes binary inputs and produces a binary output.

The main gates are:

* NOT
* AND
* OR
* NAND
* NOR
* XOR
* XNOR

A truth table describes the behavior of a gate by listing every possible input combination and its output.

---

## 4. NOT Gate

The NOT gate has one input and reverses it.

```text
NOT 0 = 1
NOT 1 = 0
```

It is also called an inverter.

In Boolean notation:

```text
A'
```

or:

```text
NOT(A)
```

---

## 5. AND Gate

AND produces `1` only when all inputs are `1`.

For two inputs:

```text
A B | AND
---------
0 0 |  0
0 1 |  0
1 0 |  0
1 1 |  1
```

The Boolean form is:

```text
A · B
```

AND is useful when several conditions must simultaneously be satisfied.

For example:

```text
enabled AND valid
```

is true only when both conditions are true.

---

## 6. OR Gate

OR produces `1` when at least one input is `1`.

```text
A B | OR
--------
0 0 | 0
0 1 | 1
1 0 | 1
1 1 | 1
```

In Boolean notation:

```text
A + B
```

The `+` here means Boolean OR, not ordinary arithmetic addition.

---

## 7. NAND Gate

NAND means NOT-AND.

```text
NAND(A, B) = NOT(A AND B)
```

Its truth table is:

```text
A B | NAND
---------
0 0 |  1
0 1 |  1
1 0 |  1
1 1 |  0
```

NAND is important because it is functionally complete.

---

## 8. NOR Gate

NOR means NOT-OR.

```text
NOR(A, B) = NOT(A OR B)
```

Its truth table is:

```text
A B | NOR
--------
0 0 |  1
0 1 |  0
1 0 |  0
1 1 |  0
```

NOR is also functionally complete.

---

## 9. XOR Gate

XOR means exclusive OR.

For two inputs, XOR produces `1` when the inputs are different.

```text
A B | XOR
---------
0 0 |  0
0 1 |  1
1 0 |  1
1 1 |  0
```

A useful Boolean expression for XOR is:

```text
A'B + AB'
```

XOR is important in addition, parity, comparison, bit manipulation, and many digital algorithms.

---

## 10. XNOR Gate

XNOR is the complement of XOR.

It produces `1` when the inputs are equal.

```text
A B | XNOR
----------
0 0 |  1
0 1 |  0
1 0 |  0
1 1 |  1
```

XNOR is therefore naturally useful as an equality detector.

---

## 11. Truth Tables

A truth table completely specifies a Boolean function for a given number of inputs.

For `n` Boolean inputs, there are:

```text
2ⁿ
```

possible input combinations.

For example:

```text
2 inputs → 4 rows
3 inputs → 8 rows
4 inputs → 16 rows
```

A truth table is useful for defining, checking, and comparing Boolean functions.

---

## 12. Boolean Algebra

Boolean algebra provides mathematical rules for manipulating logical expressions.

The basic operations are:

```text
AND
OR
NOT
```

Important Boolean laws include identity, domination, complement, idempotent, commutative, associative, distributive, absorption, and De Morgan's laws.

Boolean algebra allows an expression to be changed into an equivalent form without changing its output.

---

## 13. Identity Laws

The identity laws are:

```text
A AND 1 = A
A OR 0  = A
```

The identity value does not change the original Boolean value.

---

## 14. Domination Laws

The domination laws are:

```text
A AND 0 = 0
A OR 1  = 1
```

A single dominating value determines the result.

---

## 15. Idempotent Laws

The idempotent laws are:

```text
A AND A = A
A OR A  = A
```

Repeating the same Boolean variable does not change the result.

---

## 16. Double Negation

Double negation gives the original value:

```text
NOT(NOT(A)) = A
```

Therefore:

```text
A = 0 → NOT(A) = 1 → NOT(NOT(A)) = 0
A = 1 → NOT(A) = 0 → NOT(NOT(A)) = 1
```

---

## 17. Complement Laws

The complement laws are:

```text
A AND NOT(A) = 0
A OR NOT(A)  = 1
```

A value and its complement can never both be true, while one of them must always be true.

---

## 18. Commutative Laws

The commutative laws are:

```text
A AND B = B AND A
A OR B  = B OR A
```

Changing the order of the operands does not change the result.

---

## 19. Associative Laws

The associative laws are:

```text
(A AND B) AND C = A AND (B AND C)

(A OR B) OR C = A OR (B OR C)
```

The grouping can change without changing the result.

---

## 20. Distributive Laws

Boolean algebra has two important distributive laws:

```text
A AND (B OR C)
=
(A AND B) OR (A AND C)
```

and:

```text
A OR (B AND C)
=
(A OR B) AND (A OR C)
```

The second relationship is especially important because Boolean algebra does not behave exactly like ordinary arithmetic.

---

## 21. De Morgan's Laws

De Morgan's laws are fundamental Boolean transformations.

The first is:

```text
NOT(A AND B)
=
NOT(A) OR NOT(B)
```

The second is:

```text
NOT(A OR B)
=
NOT(A) AND NOT(B)
```

These laws are useful for simplifying expressions and converting between different circuit implementations.

---

## 22. Absorption Laws

The absorption laws are:

```text
A + AB = A
```

and:

```text
A(A + B) = A
```

They allow redundant portions of expressions to be removed.

For example:

```text
A + AB
```

can simply become:

```text
A
```

---

## 23. Consensus Theorem

An important Boolean identity is:

```text
AB + A'C + BC
=
AB + A'C
```

The `BC` term can be redundant.

This demonstrates that Boolean expressions can contain terms that are unnecessary for the final logical function.

---

## 24. Minterms

A minterm is a product term containing every variable once, either complemented or uncomplemented.

For two variables, the possible minterms are:

```text
A'B'
A'B
AB'
AB
```

Each minterm corresponds to exactly one truth-table row.

Minterms are especially useful for constructing canonical Sum-of-Products expressions.

---

## 25. Maxterms

A maxterm is a sum term containing every variable once.

Maxterms are associated with the rows of a truth table where the function has an output of `0`.

Minterms are generally used to describe the `1` rows, while maxterms are generally used to describe the `0` rows.

---

## 26. Sum of Products

A Sum-of-Products, or SOP, expression consists of OR-connected product terms.

For example:

```text
A'B + AB'
```

is an SOP expression.

It is also the Boolean representation of XOR.

The individual terms use AND, while the terms themselves are combined with OR.

---

## 27. Product of Sums

A Product-of-Sums, or POS, expression consists of AND-connected sum terms.

For example:

```text
(A + B)(A' + B')
```

contains OR expressions inside the parentheses and combines them using AND.

---

## 28. Functional Completeness

A set of gates is functionally complete when every Boolean function can be constructed using that set.

NAND is functionally complete.

NOR is also functionally complete.

Using only NAND gates, the basic operations can be constructed as:

```text
NOT(A) = NAND(A, A)
```

```text
A AND B = NAND(NAND(A, B), NAND(A, B))
```

```text
A OR B = NAND(NAND(A, A), NAND(B, B))
```

This means an entire digital logic system can theoretically be constructed using only NAND gates.

The same principle applies to NOR.

---

## 29. Boolean Expressions as Circuits

Consider:

```text
F = (A AND B) OR NOT(C)
```

The expression can be decomposed into intermediate signals:

```text
X1 = A AND B
X2 = NOT(C)
F  = X1 OR X2
```

This corresponds directly to a circuit containing an AND gate, a NOT gate, and an OR gate.

A Boolean expression and a gate-level circuit are two different representations of the same logical computation.

---

## 30. Combinational Logic

A combinational circuit is one where the current output depends on the current inputs.

Conceptually:

```text
Output = f(Current Inputs)
```

Examples include:

* adders
* multiplexers
* decoders
* encoders
* comparators
* arithmetic logic functions

Combinational logic does not require stored previous state to determine its current output.

---

## 31. Half Adder

A half adder adds two one-bit values.

Inputs:

```text
A
B
```

Outputs:

```text
Sum
Carry
```

The equations are:

```text
Sum = A XOR B
Carry = A AND B
```

For:

```text
1 + 1
```

the result is:

```text
10
```

Therefore:

```text
Sum = 0
Carry = 1
```

---

## 32. Full Adder

A full adder adds three one-bit values:

```text
A
B
Carry-in
```

It produces:

```text
Sum
Carry-out
```

A full adder can be constructed from two half adders and an OR gate.

The first half adder adds `A` and `B`.

The second half adder adds the first sum to the carry-in.

The two carry outputs are combined with OR.

---

## 33. Multi-Bit Addition

Multi-bit addition can be constructed by chaining full adders.

The carry from one bit position becomes the carry-in for the next bit position.

For example:

```text
   1011
 + 0110
 -------
  10001
```

The calculation begins at the least significant bit and propagates carries toward the most significant bit.

---

## 34. Two's Complement

Two's complement is widely used to represent signed integers.

To calculate the two's complement of a fixed-width binary value:

1. Invert every bit.
2. Add 1.

For example, using 8 bits:

```text
+5:

00000101
```

Invert:

```text
11111010
```

Add 1:

```text
11111011
```

Therefore `11111011` represents `-5` in 8-bit two's complement.

---

## 35. Signed and Unsigned Interpretation

The same bit pattern can have different numerical meanings.

For an unsigned `n`-bit value:

```text
0 through 2ⁿ - 1
```

For an `n`-bit two's complement signed value:

```text
-2ⁿ⁻¹ through 2ⁿ⁻¹ - 1
```

For 8 bits:

```text
Unsigned: 0 to 255
Signed:   -128 to 127
```

Therefore a bit pattern cannot be interpreted correctly without knowing the representation being used.

---

## 36. Overflow

Overflow occurs when the result of an operation cannot be represented using the available number of bits.

For an 8-bit unsigned value:

```text
255 + 1
```

produces:

```text
1 00000000
```

If only eight bits are retained:

```text
00000000
```

The extra ninth bit is the carry out.

Signed overflow has different detection rules because the signed interpretation uses two's complement.

---

## 37. Multiplexer

A multiplexer, or MUX, selects one input from several inputs.

A 2-to-1 multiplexer has:

```text
D0
D1
Select
```

Its Boolean equation is:

```text
Y = (NOT(S) AND D0) OR (S AND D1)
```

When:

```text
S = 0
```

the output is:

```text
D0
```

When:

```text
S = 1
```

the output is:

```text
D1
```

Multiplexers are important for selecting data paths inside digital systems.

---

## 38. Demultiplexer

A demultiplexer performs the reverse conceptual operation.

For a 1-to-2 demultiplexer:

```text
Output0 = Data AND NOT(Select)
Output1 = Data AND Select
```

Only the selected output receives the input.

---

## 39. Decoder

A decoder converts an `n`-bit input into one of `2ⁿ` possible output lines.

A 2-to-4 decoder has:

```text
2 inputs
4 outputs
```

For every valid two-bit input, one corresponding output is active.

Decoders are useful in:

* address selection
* instruction decoding
* control logic
* hardware selection

---

## 40. Encoder

An encoder performs a conceptual reverse operation.

A 4-to-2 encoder can represent one active input using two binary output bits:

```text
Input 0 → 00
Input 1 → 01
Input 2 → 10
Input 3 → 11
```

A priority encoder is used when multiple inputs may be active and the system needs to determine which input receives priority.

---

## 41. Comparator

A one-bit comparator can determine:

```text
A > B
A = B
A < B
```

The equations are:

```text
A > B = A AND NOT(B)

A < B = NOT(A) AND B

A = B = XNOR(A, B)
```

For multi-bit values, equality can be determined by checking every corresponding pair of bits with XNOR and then ANDing all the equality results.

---

## 42. Bitwise Operations

Programming languages provide operations that work directly on the individual bits of integer values.

Common operations include:

```text
&   bitwise AND
|   bitwise OR
^   bitwise XOR
~   bitwise complement
<<  left shift
>>  right shift
```

For example:

```text
1010
AND
1100
----
1000
```

Bitwise operations are useful in low-level programming, hardware control, networking, binary protocols, flags, and compact data representations.

---

## 43. Bit Masks

A bit mask is used to select or manipulate particular bits.

Suppose:

```text
value = 10110110
mask  = 00000100
```

Then:

```text
value AND mask
```

checks whether the selected bit is set.

Bit masks are common in:

* CPU registers
* permissions
* device control
* configuration flags
* networking
* binary protocols

---

## 44. Setting, Clearing, and Toggling Bits

To set a bit:

```text
value OR mask
```

To clear a bit:

```text
value AND NOT(mask)
```

To toggle a bit:

```text
value XOR mask
```

XOR is especially useful for toggling because:

```text
A XOR 0 = A
A XOR 1 = NOT(A)
```

---

## 45. Bit Shifts

A left shift moves bits toward the left:

```text
x << n
```

For non-negative integers, a left shift by `n` corresponds to multiplication by:

```text
2ⁿ
```

A right shift:

```text
x >> n
```

moves bits toward the right.

For non-negative integers, this corresponds to integer division by:

```text
2ⁿ
```

Bit shifts are heavily used in low-level computation.

---

## 46. XOR and Parity

XOR can be applied repeatedly to a collection of bits:

```text
b1 XOR b2 XOR b3 XOR ...
```

The result is `1` when the number of `1` bits is odd and `0` when the number of `1` bits is even.

This property is useful for parity calculations and simple error detection.

---

## 47. XOR and Bit Differences

XOR identifies positions where two bit patterns differ.

For example:

```text
101101
100001
------
001100
```

The `1`s in the XOR result identify the positions where the original patterns were different.

Counting those positions gives the Hamming distance between two equal-length bit strings.

---

## 48. XOR Reversibility

XOR has the property:

```text
A XOR B XOR B = A
```

because:

```text
B XOR B = 0
```

and:

```text
A XOR 0 = A
```

Therefore if:

```text
C = A XOR B
```

then:

```text
A = C XOR B
```

and:

```text
B = C XOR A
```

This is an important algebraic property of XOR.

---

## 49. Boolean Functions

A Boolean function maps Boolean inputs to a Boolean output.

For `n` input variables:

```text
f : {0,1}ⁿ → {0,1}
```

There are:

```text
2^(2ⁿ)
```

different Boolean functions of `n` variables.

For one variable:

```text
2² = 4
```

Boolean functions exist.

For two variables:

```text
2⁴ = 16
```

Boolean functions exist.

For three variables:

```text
2⁸ = 256
```

Boolean functions exist.

The number increases extremely rapidly as the number of variables increases.

---

## 50. Boolean Functions as Lookup Tables

A Boolean function can be represented as a table.

For `n` input bits, there are:

```text
2ⁿ
```

possible inputs.

Each input maps to either:

```text
0
```

or:

```text
1
```

This makes a truth table equivalent to a finite lookup table.

This viewpoint connects Boolean functions with decoders, lookup structures, ROM-like structures, and programmable logic.

---

## 51. Circuit Depth

A Boolean circuit can contain multiple levels of gates.

For example:

```text
inputs
  ↓
AND
  ↓
NOT
  ↓
OR
  ↓
output
```

The number of logical stages between an input and an output contributes to circuit depth.

In real hardware, deeper circuits can have greater propagation delay.

Two circuits can therefore implement the same Boolean function while having different timing and physical characteristics.

---

## 52. Propagation Delay

Real hardware does not respond instantaneously.

When an input changes, the resulting output changes after a finite amount of time.

This is propagation delay.

If a signal travels through several gates, the total delay depends on the characteristics of those gates and the path through the circuit.

A truth table describes logical behavior, not the complete physical timing behavior.

---

## 53. Hazards and Glitches

Different paths through a circuit can have different propagation delays.

When input values change, signals traveling through those paths may arrive at different times.

This can cause a temporary incorrect output called a glitch.

Therefore:

```text
Boolean equivalence
```

does not automatically imply:

```text
identical transient behavior
```

in physical hardware.

---

## 54. Fan-In and Fan-Out

Fan-in refers to the number of inputs accepted by a gate.

For example:

```text
two-input AND → fan-in = 2
```

Fan-out refers to the number of gate inputs driven by an output.

Real hardware has physical limitations on both fan-in and fan-out.

The abstract Boolean model generally ignores many of these physical constraints.

---

## 55. Active-High and Active-Low Signals

A signal can be defined as active-high or active-low.

For an active-high signal:

```text
1 = asserted
0 = inactive
```

For an active-low signal:

```text
0 = asserted
1 = inactive
```

This demonstrates again that the physical binary level and logical meaning are separate concepts.

---

## 56. Transistors and Logic Gates

A transistor can be used as a controllable electronic switch.

Large collections of transistors form digital circuits.

Logic gates are abstractions over transistor-level implementations.

At the Boolean level, the designer reasons about:

```text
inputs
outputs
truth tables
Boolean expressions
gates
```

without needing to track individual transistor behavior.

This is an example of abstraction.

---

## 57. Abstraction in Computing

Digital computing can be understood through multiple layers:

```text
transistors
    ↓
logic gates
    ↓
Boolean expressions
    ↓
digital circuits
    ↓
arithmetic/control units
    ↓
processor
    ↓
machine instructions
    ↓
programming languages
    ↓
applications
```

Each layer hides implementation details from the layer above it.

Boolean logic provides an important mathematical foundation between transistor-level electronics and higher-level digital computation.

---

## 58. Control Logic

Boolean logic is used to control operations.

For example:

```text
enable = valid AND ready AND NOT(reset)
```

This means the system is enabled only when:

```text
valid = 1
ready = 1
reset = 0
```

Boolean logic is therefore used for decisions such as:

* whether an operation should execute
* whether a register should be enabled
* whether a memory location should be selected
* whether an instruction is valid
* whether a control signal should be activated

---

## 59. Arithmetic Logic Unit

An Arithmetic Logic Unit, or ALU, performs arithmetic and logical operations.

Typical operations include:

* addition
* subtraction
* AND
* OR
* XOR
* comparison
* shifts

The ALU itself is built from lower-level digital logic.

The processor's control system determines which operation should be performed and which operands should be used.

---

## 60. Registers and State

A register stores a collection of bits.

An `n`-bit register contains `n` bits of state.

Registers can hold:

* operands
* addresses
* intermediate results
* instruction information
* processor state

Boolean logic controls operations such as loading, clearing, selecting, and updating register contents.

---

## 61. Combinational Logic and Sequential Logic

Combinational logic depends on current inputs:

```text
Output = f(Current Inputs)
```

Sequential logic also depends on stored state:

```text
Next State = f(Current State, Inputs)
```

Memory elements such as latches, flip-flops, and registers allow a digital system to remember information.

This distinction is fundamental:

```text
Combinational logic → no stored state required
Sequential logic    → depends on stored state
```

---

## 62. State Representation

If a system has `n` state bits, it can represent:

```text
2ⁿ
```

different states.

For example, three bits can represent:

```text
000
001
010
011
100
101
110
111
```

Finite-state machines use such binary state representations together with Boolean next-state and output logic.

---

## 63. Memory Addressing

Memory addresses are represented using bits.

With `n` address bits, there are:

```text
2ⁿ
```

possible address values.

Boolean decoding logic can determine which memory location or hardware device corresponds to a particular address.

This connects Boolean logic directly with computer memory systems.

---

## 64. Instruction Decoding

Machine instructions are represented using bit patterns.

An instruction may contain an opcode and other fields.

Control logic examines the opcode and generates signals corresponding to the requested operation.

For example:

```text
101
```

could represent one particular instruction according to an architecture's instruction-set specification.

Instruction decoding is therefore another practical application of Boolean computation.

---

## 65. CPU Flags

Processors often maintain flags such as:

* zero
* carry
* overflow
* negative/sign
* comparison conditions

For example, a zero flag can be generated by checking whether every bit of a result is zero.

For result bits:

```text
R0, R1, R2, ..., Rn
```

the zero condition can be expressed conceptually as:

```text
zero = NOT(R0 OR R1 OR R2 OR ... OR Rn)
```

If every result bit is zero, the zero flag is `1`.

---

## 66. Multi-Bit Equality

Two binary values are equal when every corresponding pair of bits is equal.

For each pair:

```text
XNOR(Ai, Bi)
```

checks equality.

Then all equality results are combined with AND:

```text
equal =
XNOR(A0,B0)
AND XNOR(A1,B1)
AND ...
AND XNOR(An,Bn)
```

This provides a direct Boolean construction of a multi-bit equality comparator.

---

## 67. Bit Width

Bit width affects the number of values that can be represented and the size of many digital datapaths.

Common widths include:

```text
8-bit
16-bit
32-bit
64-bit
```

The width influences:

* integer ranges
* register size
* arithmetic operations
* datapath size
* address representation
* storage requirements

The meaning of a value always depends on its representation and interpretation.

---

## 68. Endianness

When a value occupies multiple bytes, the order in which those bytes are stored can differ.

Two major conventions are:

```text
big-endian
little-endian
```

Endianness concerns byte ordering within multi-byte representations.

It is distinct from Boolean logic itself, but it becomes relevant when interpreting groups of bits stored in computer memory.

---

## 69. Logic Optimization

Two different circuits can implement the same Boolean function.

One may use:

* more gates
* more levels
* more wiring
* more physical area

while another may implement the same function more efficiently.

Logic optimization can target:

* gate count
* area
* power
* delay
* wiring complexity

Methods include:

* Boolean algebra
* Karnaugh maps
* Quine-McCluskey minimization
* logic synthesis
* technology mapping

---

## 70. Karnaugh Maps

A Karnaugh map is a graphical method for simplifying Boolean functions.

The cells are arranged so that adjacent cells differ in only one variable.

Groups of adjacent `1`s can be used to simplify SOP expressions.

Groups of adjacent `0`s can be used to simplify POS expressions.

Karnaugh maps are particularly useful for relatively small Boolean functions.

---

## 71. Don't-Care Conditions

Some input combinations may never occur in a real system, or the output may not matter for those combinations.

Such cases can be treated as don't-care conditions.

During optimization, a don't-care can be treated as either `0` or `1` if doing so produces a simpler implementation.

This can reduce circuit complexity.

---

## 72. Boolean Logic and Error Detection

Boolean operations can be used for simple error detection.

Parity is a common example.

A parity calculation can use XOR across a collection of bits.

If the number of `1`s is odd, the XOR result is `1`.

If the number of `1`s is even, the XOR result is `0`.

A parity bit can therefore be added to transmitted data to help detect certain errors.

Parity has limitations and does not detect every possible error pattern.

---

## 73. Boolean Logic and Programming

Programming languages use Boolean expressions extensively.

For example:

```python
if user_is_valid and account_is_active:
    ...
```

The logical structure is similar to:

```text
user_is_valid
        \
         AND → allow
        /
account_is_active
```

At the language level, Boolean operations are part of programming semantics.

At the hardware level, digital logic performs the underlying computation.

The two levels should not be treated as literally identical implementations, because compilers and processors introduce several abstraction layers between them.

---

## 74. Short-Circuit Evaluation

Mathematical Boolean logic defines the result of an expression.

Programming languages may also define evaluation strategies.

For example, Python can use short-circuit evaluation:

```python
False and expensive_operation()
```

The second expression does not need to be evaluated because the result is already known.

This is a programming-language execution behavior and should not be confused with the abstract truth table of the AND function.

---

## 75. Boolean Logic and Data Representation

A bit pattern has no universal meaning.

For example:

```text
01000001
```

can represent:

```text
65
```

as an unsigned binary integer.

It can also represent:

```text
0x41
```

in hexadecimal.

Under an appropriate character encoding, it can represent:

```text
A
```

It could also be part of:

* an instruction
* an address
* an image
* compressed data
* a network packet

The representation is the bit pattern. The meaning is supplied by the interpretation.

---

## 76. Boolean Logic and Computation

The fundamental computational chain can be viewed as:

```text
Bit
 ↓
Boolean value
 ↓
Logic operation
 ↓
Logic gate
 ↓
Boolean expression
 ↓
Combinational circuit
 ↓
Arithmetic/control circuit
 ↓
Datapath and state
 ↓
Processor
 ↓
Computer
```

A simple gate performs a small logical transformation.

Multiple gates can be composed into larger functions.

Larger functions can be combined into circuits.

Circuits can implement arithmetic, control, comparison, selection, decoding, and state-related operations.

This compositional structure is what allows extremely complex digital systems to be constructed from relatively simple binary primitives.

---

## 77. Core Relationships

The most important relationships represented in the study material are:

```text
1 bit
→ 2 possible states
```

```text
n bits
→ 2ⁿ possible combinations
```

```text
n Boolean inputs
→ 2ⁿ truth-table rows
```

```text
n Boolean inputs
→ 2^(2ⁿ) possible Boolean functions
```

```text
XOR
→ difference detection
→ parity
→ sum bit in binary addition
```

```text
AND
→ simultaneous conditions
→ carry generation
→ masking
```

```text
OR
→ alternative conditions
→ combining logical conditions
```

```text
NOT
→ inversion
```

```text
XNOR
→ equality detection
```

```text
NAND
→ functionally complete logic
```

```text
NOR
→ functionally complete logic
```

```text
Boolean expression
↔
logic circuit
```

```text
Combinational logic
→ current inputs determine current outputs
```

```text
Sequential logic
→ current inputs + stored state determine future behavior
```

The mathematical Boolean model provides a precise way to describe the logical behavior of digital computation, while gates and circuits provide the structural mechanisms through which those Boolean functions can be implemented.

```
```

