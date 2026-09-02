```python
"""
BITS, LOGIC & COMPUTATION
=========================

Topic:
    Bits, Logic Gates, Boolean Computation

Purpose:
    This script is a self-contained study program for understanding how
    digital computation is built from bits, Boolean logic, logic gates,
    Boolean algebra, truth tables, combinational logic, sequential ideas,
    arithmetic circuits, multiplexers, decoders, encoders, and the connection
    between Boolean computation and real computer systems.

The script is intentionally written as an educational program rather than
as a collection of disconnected definitions.

It uses Python to model the ideas being studied. The Python language itself
is not the subject. Python is used as a convenient laboratory for observing
Boolean computation.

No external packages are required.
"""

# =============================================================================
# 1. WHAT IS A BIT?
# =============================================================================

print("=" * 80)
print("BITS, LOGIC & COMPUTATION")
print("=" * 80)

print("""
A bit is the smallest conventional unit of digital information.

A bit has two possible values:

    0
    1

The word bit comes from "binary digit".

A bit does not inherently mean:
    0 volts or 1 volt
    false or true
    off or on
    low or high
    no or yes

Those are interpretations.

At the abstract level, a bit is simply a variable whose domain contains
two possible states.
""")

bit_values = [0, 1]

print("Possible bit values:", bit_values)

for bit in bit_values:
    print("Bit:", bit)


# =============================================================================
# 2. BINARY
# =============================================================================

print("\n" + "=" * 80)
print("BINARY REPRESENTATION")
print("=" * 80)

print("""
Computers use binary because digital electronic systems can reliably
distinguish between two broad physical states.

Binary is a base-2 number system.

Decimal uses ten symbols:

    0 1 2 3 4 5 6 7 8 9

Binary uses two symbols:

    0 1

Binary positional notation works like decimal positional notation, except
the powers are powers of 2 rather than powers of 10.

For example:

    1011

means:

    1*2^3 + 0*2^2 + 1*2^1 + 1*2^0

which is:

    8 + 0 + 2 + 1
    = 11
""")


def binary_to_decimal(binary_string):
    """Convert a binary string to a decimal integer."""
    value = 0

    for character in binary_string:
        if character not in "01":
            raise ValueError("A binary number can contain only 0 and 1.")

        value = value * 2 + int(character)

    return value


examples = ["0", "1", "10", "11", "100", "101", "1010", "1011", "1111"]

for value in examples:
    print(value, "=", binary_to_decimal(value))


def decimal_to_binary(number):
    """Convert a non-negative decimal integer to binary."""
    if number < 0:
        raise ValueError("This function expects a non-negative integer.")

    if number == 0:
        return "0"

    result = ""

    while number > 0:
        remainder = number % 2
        result = str(remainder) + result
        number //= 2

    return result


for number in range(16):
    print(number, "=", decimal_to_binary(number))


# =============================================================================
# 3. BITS AS INFORMATION CAPACITY
# =============================================================================

print("\n" + "=" * 80)
print("INFORMATION CAPACITY OF BITS")
print("=" * 80)

print("""
One bit can represent:

    2^1 = 2

different combinations.

Two bits can represent:

    2^2 = 4

different combinations.

Three bits:

    2^3 = 8

Four bits:

    2^4 = 16

In general, n bits can represent:

    2^n

different combinations.

This is one of the most important relationships in digital computation.
""")


def number_of_combinations(number_of_bits):
    return 2 ** number_of_bits


for n in range(1, 9):
    print(
        f"{n} bit(s): "
        f"{number_of_combinations(n)} possible combinations"
    )


# =============================================================================
# 4. BITS, BYTES, AND WORDS
# =============================================================================

print("\n" + "=" * 80)
print("BITS, BYTES, AND WORDS")
print("=" * 80)

print("""
A byte conventionally contains 8 bits.

Therefore:

    1 byte = 8 bits

An 8-bit quantity has:

    2^8 = 256

possible patterns.

These patterns can be:

    00000000
    00000001
    00000010
    ...
    11111111

When interpreted as an unsigned integer, these correspond to:

    0 through 255

A processor may work with larger word sizes such as 16, 32, 64 bits,
or other widths depending on the architecture.
""")


def unsigned_range(bits):
    return 0, (2 ** bits) - 1


for bits in [8, 16, 32, 64]:
    minimum, maximum = unsigned_range(bits)
    print(f"{bits}-bit unsigned range: {minimum} to {maximum}")


# =============================================================================
# 5. BOOLEAN VARIABLES
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN VARIABLES")
print("=" * 80)

print("""
Boolean logic deals with two logical values:

    True
    False

These correspond naturally to:

    1
    0

A Boolean variable can therefore be thought of as a one-bit logical value.

For example:

    A = True
    B = False

Boolean expressions combine Boolean values according to defined rules.
""")

A = True
B = False

print("A =", A)
print("B =", B)
print("A AND B =", A and B)
print("A OR B  =", A or B)
print("NOT A   =", not A)


# =============================================================================
# 6. LOGIC GATES
# =============================================================================

print("\n" + "=" * 80)
print("LOGIC GATES")
print("=" * 80)

print("""
A logic gate is an abstract computational element that takes one or more
binary inputs and produces a binary output.

The fundamental gates studied here are:

    NOT
    AND
    OR
    NAND
    NOR
    XOR
    XNOR

The behavior of a gate can be described with a truth table.

A truth table lists every possible input combination and the corresponding
output.
""")


# =============================================================================
# 7. NOT GATE
# =============================================================================

print("\n" + "-" * 80)
print("NOT GATE")
print("-" * 80)

print("""
The NOT gate has one input and one output.

It reverses the input.

    NOT 0 = 1
    NOT 1 = 0
""")

for x in [False, True]:
    print(f"NOT {int(x)} = {int(not x)}")


# =============================================================================
# 8. AND GATE
# =============================================================================

print("\n" + "-" * 80)
print("AND GATE")
print("-" * 80)

print("""
The AND gate produces 1 only when every input is 1.

For two inputs:

    A AND B

the output is 1 only for:

    A = 1
    B = 1
""")

print("A B | AND")
print("----+----")

for a in [False, True]:
    for b in [False, True]:
        print(int(a), int(b), "|", int(a and b))


# =============================================================================
# 9. OR GATE
# =============================================================================

print("\n" + "-" * 80)
print("OR GATE")
print("-" * 80)

print("""
The OR gate produces 1 when at least one input is 1.

For two inputs:

    A OR B

the only input combination producing 0 is:

    A = 0
    B = 0
""")

print("A B | OR")
print("----+---")

for a in [False, True]:
    for b in [False, True]:
        print(int(a), int(b), "|", int(a or b))


# =============================================================================
# 10. NAND GATE
# =============================================================================

print("\n" + "-" * 80)
print("NAND GATE")
print("-" * 80)

print("""
NAND means:

    NOT AND

Therefore:

    NAND(A, B) = NOT(A AND B)

The NAND output is 0 only when both inputs are 1.
""")

for a in [False, True]:
    for b in [False, True]:
        output = not (a and b)
        print(int(a), int(b), "|", int(output))


# =============================================================================
# 11. NOR GATE
# =============================================================================

print("\n" + "-" * 80)
print("NOR GATE")
print("-" * 80)

print("""
NOR means:

    NOT OR

Therefore:

    NOR(A, B) = NOT(A OR B)

The NOR output is 1 only when both inputs are 0.
""")

for a in [False, True]:
    for b in [False, True]:
        output = not (a or b)
        print(int(a), int(b), "|", int(output))


# =============================================================================
# 12. XOR GATE
# =============================================================================

print("\n" + "-" * 80)
print("XOR GATE")
print("-" * 80)

print("""
XOR means exclusive OR.

For two inputs, XOR produces 1 when the inputs are different.

Therefore:

    0 XOR 0 = 0
    0 XOR 1 = 1
    1 XOR 0 = 1
    1 XOR 1 = 0

XOR can be written as:

    A XOR B

or:

    A ⊕ B
""")

for a in [False, True]:
    for b in [False, True]:
        output = a != b
        print(int(a), int(b), "|", int(output))


# =============================================================================
# 13. XNOR GATE
# =============================================================================

print("\n" + "-" * 80)
print("XNOR GATE")
print("-" * 80)

print("""
XNOR is the complement of XOR.

It produces 1 when both inputs are equal.

    0 XNOR 0 = 1
    0 XNOR 1 = 0
    1 XNOR 0 = 0
    1 XNOR 1 = 1
""")

for a in [False, True]:
    for b in [False, True]:
        output = a == b
        print(int(a), int(b), "|", int(output))


# =============================================================================
# 14. GENERIC GATE FUNCTIONS
# =============================================================================

print("\n" + "=" * 80)
print("GATE FUNCTIONS")
print("=" * 80)


def NOT(x):
    return not x


def AND(a, b):
    return a and b


def OR(a, b):
    return a or b


def NAND(a, b):
    return NOT(AND(a, b))


def NOR(a, b):
    return NOT(OR(a, b))


def XOR(a, b):
    return a != b


def XNOR(a, b):
    return a == b


print("NAND(True, True) =", NAND(True, True))
print("NOR(False, False) =", NOR(False, False))
print("XOR(True, False) =", XOR(True, False))
print("XNOR(True, True) =", XNOR(True, True))


# =============================================================================
# 15. TRUTH TABLE GENERATION
# =============================================================================

print("\n" + "=" * 80)
print("GENERATING TRUTH TABLES")
print("=" * 80)

print("""
Truth tables become particularly important when Boolean expressions contain
several variables.

For n Boolean variables there are:

    2^n

possible input combinations.
""")


def truth_table_two_inputs(operation):
    print("A B | Output")
    print("----+-------")

    for a in [False, True]:
        for b in [False, True]:
            result = operation(a, b)
            print(f"{int(a)} {int(b)} | {int(result)}")


truth_table_two_inputs(AND)


# =============================================================================
# 16. BOOLEAN ALGEBRA
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN ALGEBRA")
print("=" * 80)

print("""
Boolean algebra is an algebraic system used to reason about Boolean
variables and logical expressions.

Important notation:

    AND:  A · B
    OR:   A + B
    NOT:  A'

The symbols are not ordinary arithmetic operations.

For example:

    A + B

means Boolean OR, not integer addition.

Likewise:

    A · B

means Boolean AND.

Boolean algebra allows logical expressions to be transformed while
preserving their logical meaning.
""")


# =============================================================================
# 17. IDENTITY LAWS
# =============================================================================

print("\n" + "-" * 80)
print("IDENTITY LAWS")
print("-" * 80)

print("""
Identity laws:

    A AND 1 = A
    A OR 0  = A

In symbolic form:

    A · 1 = A
    A + 0 = A
""")

for a in [False, True]:
    print(
        int(a),
        int(a and True),
        int(a or False)
    )


# =============================================================================
# 18. NULL / DOMINATION LAWS
# =============================================================================

print("\n" + "-" * 80)
print("DOMINATION LAWS")
print("-" * 80)

print("""
Domination laws:

    A AND 0 = 0
    A OR 1  = 1
""")

for a in [False, True]:
    print(
        int(a),
        "A AND 0 =", int(a and False),
        "| A OR 1 =", int(a or True)
    )


# =============================================================================
# 19. IDEMPOTENT LAWS
# =============================================================================

print("\n" + "-" * 80)
print("IDEMPOTENT LAWS")
print("-" * 80)

print("""
Idempotent laws:

    A AND A = A
    A OR A  = A
""")

for a in [False, True]:
    print(
        int(a),
        int(a and a),
        int(a or a)
    )


# =============================================================================
# 20. DOUBLE NEGATION
# =============================================================================

print("\n" + "-" * 80)
print("DOUBLE NEGATION")
print("-" * 80)

print("""
Double negation:

    NOT(NOT(A)) = A
""")

for a in [False, True]:
    print(
        int(a),
        "->",
        int(NOT(NOT(a)))
    )


# =============================================================================
# 21. COMPLEMENT LAWS
# =============================================================================

print("\n" + "-" * 80)
print("COMPLEMENT LAWS")
print("-" * 80)

print("""
Complement laws:

    A AND NOT A = 0
    A OR NOT A  = 1
""")

for a in [False, True]:
    print(
        int(a),
        "AND complement =",
        int(a and not a),
        "| OR complement =",
        int(a or not a)
    )


# =============================================================================
# 22. COMMUTATIVE LAWS
# =============================================================================

print("\n" + "-" * 80)
print("COMMUTATIVE LAWS")
print("-" * 80)

print("""
Commutative laws:

    A AND B = B AND A
    A OR B  = B OR A

The order of operands does not affect the result.
""")

for a in [False, True]:
    for b in [False, True]:
        assert AND(a, b) == AND(b, a)
        assert OR(a, b) == OR(b, a)


# =============================================================================
# 23. ASSOCIATIVE LAWS
# =============================================================================

print("\n" + "-" * 80)
print("ASSOCIATIVE LAWS")
print("-" * 80)

print("""
Associative laws:

    (A AND B) AND C = A AND (B AND C)
    (A OR B) OR C   = A OR (B OR C)
""")

for a in [False, True]:
    for b in [False, True]:
        for c in [False, True]:
            assert (a and b) and c == a and (b and c)
            assert (a or b) or c == a or (b or c)


# =============================================================================
# 24. DISTRIBUTIVE LAWS
# =============================================================================

print("\n" + "-" * 80)
print("DISTRIBUTIVE LAWS")
print("-" * 80)

print("""
Boolean algebra has two useful distributive laws:

    A AND (B OR C)
        =
    (A AND B) OR (A AND C)

and:

    A OR (B AND C)
        =
    (A OR B) AND (A OR C)

The second form is different from ordinary arithmetic intuition.
""")

for a in [False, True]:
    for b in [False, True]:
        for c in [False, True]:

            left_1 = a and (b or c)
            right_1 = (a and b) or (a and c)

            left_2 = a or (b and c)
            right_2 = (a or b) and (a or c)

            assert left_1 == right_1
            assert left_2 == right_2


# =============================================================================
# 25. DE MORGAN'S LAWS
# =============================================================================

print("\n" + "-" * 80)
print("DE MORGAN'S LAWS")
print("-" * 80)

print("""
De Morgan's laws are fundamental Boolean transformations.

First law:

    NOT(A AND B)
        =
    NOT(A) OR NOT(B)

Second law:

    NOT(A OR B)
        =
    NOT(A) AND NOT(B)

These laws are important when transforming circuits, simplifying expressions,
and converting between different gate structures.
""")

for a in [False, True]:
    for b in [False, True]:

        assert NOT(AND(a, b)) == OR(NOT(a), NOT(b))
        assert NOT(OR(a, b)) == AND(NOT(a), NOT(b))


# =============================================================================
# 26. BOOLEAN EXPRESSION EVALUATION
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN EXPRESSION EVALUATION")
print("=" * 80)

print("""
Consider:

    F = (A AND B) OR NOT(C)

The expression can be evaluated in stages:

    1. Evaluate A AND B.
    2. Evaluate NOT(C).
    3. OR the two intermediate results.

This staged evaluation is exactly the type of structure represented by
a combinational logic circuit.
""")


def expression_f(a, b, c):
    first = AND(a, b)
    second = NOT(c)
    result = OR(first, second)

    return result


for a in [False, True]:
    for b in [False, True]:
        for c in [False, True]:
            print(
                f"A={int(a)} B={int(b)} C={int(c)} "
                f"F={int(expression_f(a, b, c))}"
            )


# =============================================================================
# 27. MINTERMS
# =============================================================================

print("\n" + "=" * 80)
print("MINTERMS")
print("=" * 80)

print("""
A minterm is a product term containing every variable exactly once,
either complemented or uncomplemented.

For variables A and B:

    A'B'
    A'B
    AB'
    AB

Each minterm corresponds to exactly one row of a two-variable truth table.

For example:

    AB

is 1 only when:

    A = 1
    B = 1

Minterms are useful when converting truth tables into Boolean expressions.
""")


def minterm(a, b, required_a, required_b):
    return (
        (a == required_a)
        and
        (b == required_b)
    )


print("Minterm for A=1, B=0:")

for a in [False, True]:
    for b in [False, True]:
        print(
            int(a),
            int(b),
            "->",
            int(minterm(a, b, True, False))
        )


# =============================================================================
# 28. MAXTERMS
# =============================================================================

print("\n" + "=" * 80)
print("MAXTERMS")
print("=" * 80)

print("""
A maxterm is a sum term containing every variable exactly once.

Maxterms are associated with rows where a Boolean function evaluates to 0.

For two variables, examples include expressions such as:

    A + B
    A + B'
    A' + B
    A' + B'

Minterms are commonly associated with the 1 rows of a truth table.

Maxterms are commonly associated with the 0 rows.
""")


# =============================================================================
# 29. SUM OF PRODUCTS
# =============================================================================

print("\n" + "=" * 80)
print("SUM OF PRODUCTS")
print("=" * 80)

print("""
A Sum of Products, or SOP, expression consists of OR-connected product
terms.

Example:

    F = A'B + AB'

This is the Boolean expression for XOR.

Each product term is formed using AND.

The product terms are then combined using OR.
""")

for a in [False, True]:
    for b in [False, True]:

        sop = (NOT(a) and b) or (a and NOT(b))
        print(
            f"A={int(a)} B={int(b)} XOR={int(sop)}"
        )


# =============================================================================
# 30. PRODUCT OF SUMS
# =============================================================================

print("\n" + "=" * 80)
print("PRODUCT OF SUMS")
print("=" * 80)

print("""
A Product of Sums, or POS, expression consists of AND-connected sum terms.

Example:

    F = (A + B)(A' + B')

The individual parenthesized terms are OR operations.
The terms themselves are then ANDed.
""")


# =============================================================================
# 31. CANONICAL BOOLEAN REPRESENTATION
# =============================================================================

print("\n" + "=" * 80)
print("CANONICAL REPRESENTATION")
print("=" * 80)

print("""
A Boolean function can be represented systematically from its truth table.

For SOP:

    Identify every row where F = 1.
    Construct the corresponding minterm.
    OR all of those minterms.

For POS:

    Identify every row where F = 0.
    Construct the corresponding maxterm.
    AND all of those maxterms.

This provides a mechanical way to move from a truth table to a Boolean
expression.
""")


# =============================================================================
# 32. FUNCTIONAL COMPLETENESS
# =============================================================================

print("\n" + "=" * 80)
print("FUNCTIONAL COMPLETENESS")
print("=" * 80)

print("""
A set of gates is functionally complete if every Boolean function can be
constructed using only gates from that set.

NAND is functionally complete.

NOR is also functionally complete.

This means that NOT, AND, and OR can all be constructed from NAND alone,
and similarly from NOR alone.

For NAND:

    NOT(A) = NAND(A, A)

    A AND B = NAND(NAND(A, B), NAND(A, B))

    A OR B = NAND(NAND(A, A), NAND(B, B))
""")


def NAND_NOT(a):
    return NAND(a, a)


def NAND_AND(a, b):
    temporary = NAND(a, b)
    return NAND(temporary, temporary)


def NAND_OR(a, b):
    return NAND(NAND(a, a), NAND(b, b))


for a in [False, True]:
    assert NAND_NOT(a) == NOT(a)

for a in [False, True]:
    for b in [False, True]:
        assert NAND_AND(a, b) == AND(a, b)
        assert NAND_OR(a, b) == OR(a, b)


# =============================================================================
# 33. NOR AS A UNIVERSAL GATE
# =============================================================================

print("\n" + "-" * 80)
print("NOR AS A UNIVERSAL GATE")
print("-" * 80)

print("""
NOR can also implement the basic operations.

NOT:

    NOT(A) = NOR(A, A)

OR:

    A OR B = NOR(NOR(A, B), NOR(A, B))

AND:

    A AND B = NOR(NOR(A, A), NOR(B, B))
""")


def NOR_NOT(a):
    return NOR(a, a)


def NOR_OR(a, b):
    temporary = NOR(a, b)
    return NOR(temporary, temporary)


def NOR_AND(a, b):
    return NOR(NOR(a, a), NOR(b, b))


for a in [False, True]:
    assert NOR_NOT(a) == NOT(a)

for a in [False, True]:
    for b in [False, True]:
        assert NOR_OR(a, b) == OR(a, b)
        assert NOR_AND(a, b) == AND(a, b)


# =============================================================================
# 34. HALF ADDER
# =============================================================================

print("\n" + "=" * 80)
print("HALF ADDER")
print("=" * 80)

print("""
A half adder adds two one-bit binary numbers.

Inputs:

    A
    B

Outputs:

    Sum
    Carry

The equations are:

    Sum   = A XOR B
    Carry = A AND B

Example:

    1 + 1 = binary 10

Therefore:

    Sum   = 0
    Carry = 1
""")


def half_adder(a, b):
    sum_bit = XOR(a, b)
    carry = AND(a, b)

    return sum_bit, carry


for a in [False, True]:
    for b in [False, True]:
        s, c = half_adder(a, b)

        print(
            f"A={int(a)} B={int(b)} "
            f"Sum={int(s)} Carry={int(c)}"
        )


# =============================================================================
# 35. FULL ADDER
# =============================================================================

print("\n" + "=" * 80)
print("FULL ADDER")
print("=" * 80)

print("""
A full adder adds three one-bit values:

    A
    B
    Carry-in

It produces:

    Sum
    Carry-out

A common construction uses two half adders and an OR gate.

First half adder:

    A + B

Second half adder:

    first_sum + Carry_in

Carry-out is the OR of the two carry values.
""")


def full_adder(a, b, carry_in):

    first_sum, first_carry = half_adder(a, b)

    final_sum, second_carry = half_adder(
        first_sum,
        carry_in
    )

    carry_out = OR(
        first_carry,
        second_carry
    )

    return final_sum, carry_out


for a in [False, True]:
    for b in [False, True]:
        for carry_in in [False, True]:

            s, carry = full_adder(a, b, carry_in)

            print(
                f"A={int(a)} "
                f"B={int(b)} "
                f"Cin={int(carry_in)} "
                f"Sum={int(s)} "
                f"Cout={int(carry)}"
            )


# =============================================================================
# 36. MULTI-BIT ADDITION
# =============================================================================

print("\n" + "=" * 80)
print("MULTI-BIT BINARY ADDITION")
print("=" * 80)

print("""
A multi-bit binary adder can be constructed by chaining full adders.

The carry generated by one bit position becomes the carry-in for the next
bit position.

For example:

        1011
      + 0110
      ------
       10001

The addition proceeds from the least significant bit toward the most
significant bit.
""")


def add_binary_strings(a, b):
    """
    Add two non-negative binary strings using full-adder logic.
    """

    max_length = max(len(a), len(b))

    a = a.zfill(max_length)
    b = b.zfill(max_length)

    carry = False
    result = []

    for i in range(max_length - 1, -1, -1):

        bit_a = a[i] == "1"
        bit_b = b[i] == "1"

        sum_bit, carry = full_adder(
            bit_a,
            bit_b,
            carry
        )

        result.append("1" if sum_bit else "0")

    if carry:
        result.append("1")

    return "".join(reversed(result))


print("1011 + 0110 =", add_binary_strings("1011", "0110"))


# =============================================================================
# 37. SUBTRACTION AND TWO'S COMPLEMENT
# =============================================================================

print("\n" + "=" * 80)
print("SUBTRACTION AND TWO'S COMPLEMENT")
print("=" * 80)

print("""
Binary subtraction can be implemented using addition and two's complement.

For a fixed-width binary number:

    1. Invert every bit.
    2. Add 1.

This produces the two's complement representation of the negative value.

For example, using 8 bits:

    +5
    00000101

Invert:

    11111010

Add 1:

    11111011

Therefore 11111011 represents -5 in 8-bit two's complement.
""")


def twos_complement(bits):
    inverted = "".join(
        "1" if bit == "0" else "0"
        for bit in bits
    )

    result = add_binary_strings(
        inverted,
        "1".zfill(len(bits))
    )

    return result[-len(bits):]


print("Two's complement of 00000101:")
print(twos_complement("00000101"))


# =============================================================================
# 38. SIGNED VS UNSIGNED
# =============================================================================

print("\n" + "=" * 80)
print("SIGNED AND UNSIGNED BINARY")
print("=" * 80)

print("""
An n-bit pattern does not have one universal numerical meaning.

For unsigned interpretation:

    n bits represent:

    0 through 2^n - 1

For two's complement signed interpretation:

    -2^(n-1) through 2^(n-1)-1

For 8 bits:

Unsigned:

    0 through 255

Signed:

    -128 through 127

The same physical bit pattern can therefore have different interpretations.
""")


def unsigned_value(bits):
    return binary_to_decimal(bits)


def signed_twos_complement_value(bits):
    value = binary_to_decimal(bits)

    if bits[0] == "1":
        value -= 2 ** len(bits)

    return value


for bits in [
    "00000000",
    "00000101",
    "01111111",
    "10000000",
    "11111111"
]:

    print(
        bits,
        "unsigned =", unsigned_value(bits),
        "signed =", signed_twos_complement_value(bits)
    )


# =============================================================================
# 39. OVERFLOW
# =============================================================================

print("\n" + "=" * 80)
print("OVERFLOW")
print("=" * 80)

print("""
Overflow occurs when the result cannot be represented within the available
number of bits.

For unsigned 8-bit arithmetic:

    maximum = 255

Therefore:

    255 + 1

produces:

    1 00000000

If only eight bits are retained:

    00000000

The ninth bit is the carry out and is discarded in fixed-width arithmetic.

Signed overflow has a different interpretation and must be detected according
to signed arithmetic rules.
""")


# =============================================================================
# 40. MULTIPLEXER
# =============================================================================

print("\n" + "=" * 80)
print("MULTIPLEXER")
print("=" * 80)

print("""
A multiplexer, or MUX, selects one input from multiple inputs and forwards
the selected input to the output.

A 2-to-1 multiplexer has:

    D0
    D1
    S

where S is the select signal.

Its equation is:

    Y = NOT(S) AND D0
        OR
        S AND D1

When:

    S = 0

the output is:

    Y = D0

When:

    S = 1

the output is:

    Y = D1
""")


def mux_2_to_1(d0, d1, select):
    return OR(
        AND(NOT(select), d0),
        AND(select, d1)
    )


for select in [False, True]:
    print(
        "D0=0 D1=1",
        "S=", int(select),
        "Y=", int(mux_2_to_1(False, True, select))
    )


# =============================================================================
# 41. DEMULTIPLEXER CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("DEMULTIPLEXER")
print("=" * 80)

print("""
A demultiplexer performs the reverse conceptual operation.

One input is routed toward one of several outputs according to selection
signals.

For a 1-to-2 demultiplexer:

    output0 = input AND NOT(select)
    output1 = input AND select

Only the selected output receives the input value.
""")


def demux_1_to_2(data, select):
    output0 = AND(data, NOT(select))
    output1 = AND(data, select)

    return output0, output1


for select in [False, True]:
    print(
        "select =", int(select),
        "outputs =",
        tuple(int(x) for x in demux_1_to_2(True, select))
    )


# =============================================================================
# 42. DECODER
# =============================================================================

print("\n" + "=" * 80)
print("DECODER")
print("=" * 80)

print("""
A decoder converts an n-bit input into one of 2^n output lines.

A 2-to-4 decoder has:

    2 inputs
    4 outputs

Only one output is active for each valid input combination.

This is useful in address selection, instruction decoding, control logic,
and many digital systems.
""")


def decoder_2_to_4(a, b):

    return [
        AND(NOT(a), NOT(b)),
        AND(NOT(a), b),
        AND(a, NOT(b)),
        AND(a, b)
    ]


for a in [False, True]:
    for b in [False, True]:

        outputs = decoder_2_to_4(a, b)

        print(
            f"{int(a)}{int(b)} ->",
            "".join(str(int(x)) for x in outputs)
        )


# =============================================================================
# 43. ENCODER
# =============================================================================

print("\n" + "=" * 80)
print("ENCODER")
print("=" * 80)

print("""
An encoder performs a conceptual reverse operation.

For a 4-to-2 encoder, one active input is represented using a two-bit
binary code.

For example:

    input 0 -> 00
    input 1 -> 01
    input 2 -> 10
    input 3 -> 11

Real systems may use priority encoders when more than one input can be
active.
""")


def encoder_4_to_2(active_index):
    if active_index not in [0, 1, 2, 3]:
        raise ValueError("Active index must be between 0 and 3.")

    return decimal_to_binary(active_index).zfill(2)


for index in range(4):
    print(index, "->", encoder_4_to_2(index))


# =============================================================================
# 44. COMBINATIONAL LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("COMBINATIONAL LOGIC")
print("=" * 80)

print("""
A combinational circuit is a digital circuit where the current output is
determined by the current inputs.

Conceptually:

    Output = f(Current Inputs)

Examples include:

    adders
    multiplexers
    decoders
    encoders
    comparators
    arithmetic logic functions

There is no need for the circuit to remember a previous input in order to
determine its current output.
""")


# =============================================================================
# 45. COMPARATORS
# =============================================================================

print("\n" + "=" * 80)
print("ONE-BIT COMPARATOR")
print("=" * 80)

print("""
A one-bit comparator can determine:

    A > B
    A = B
    A < B

For Boolean inputs:

    A > B is true only for A=1, B=0
    A < B is true only for A=0, B=1
    A = B is equivalent to XNOR
""")


def compare_bits(a, b):

    greater = AND(a, NOT(b))
    equal = XNOR(a, b)
    less = AND(NOT(a), b)

    return greater, equal, less


for a in [False, True]:
    for b in [False, True]:

        greater, equal, less = compare_bits(a, b)

        print(
            f"A={int(a)} B={int(b)} "
            f"A>B={int(greater)} "
            f"A=B={int(equal)} "
            f"A<B={int(less)}"
        )


# =============================================================================
# 46. BOOLEAN COMPUTATION AS A CIRCUIT
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN COMPUTATION AS A CIRCUIT")
print("=" * 80)

print("""
Consider:

    F = (A AND B) OR (C AND NOT(D))

This can be interpreted as a circuit.

Stage 1:

    X1 = A AND B

Stage 2:

    X2 = NOT(D)

Stage 3:

    X3 = C AND X2

Stage 4:

    F = X1 OR X3

The Boolean expression and the gate-level circuit describe the same
computation at different abstraction levels.
""")


def circuit(a, b, c, d):

    x1 = AND(a, b)
    x2 = NOT(d)
    x3 = AND(c, x2)
    output = OR(x1, x3)

    return output


for a in [False, True]:
    for b in [False, True]:
        for c in [False, True]:
            for d in [False, True]:

                result = circuit(a, b, c, d)

                print(
                    f"{int(a)}{int(b)}{int(c)}{int(d)}"
                    f" -> {int(result)}"
                )


# =============================================================================
# 47. CIRCUIT DEPTH
# =============================================================================

print("\n" + "=" * 80)
print("CIRCUIT DEPTH")
print("=" * 80)

print("""
A Boolean expression may require several layers of logical operations.

For example:

    A
     \
      AND ----\
    B          OR ---- F
    C          /
     \        /
      AND ---/
       ^
       |
      NOT(D)

The number of logical stages between an input and an output affects the
propagation time in a physical implementation.

This introduces the distinction between:

    logical correctness
    physical timing

Two circuits may compute the same Boolean function while having different
depth, gate counts, wiring requirements, or timing characteristics.
""")


# =============================================================================
# 48. PROPAGATION DELAY
# =============================================================================

print("\n" + "=" * 80)
print("PROPAGATION DELAY")
print("=" * 80)

print("""
In real hardware, a gate does not respond infinitely quickly.

When an input changes, the output changes after a small delay.

This is called propagation delay.

For a conceptual circuit:

    input -> gate -> gate -> gate -> output

the signal may have to pass through several stages.

More gate levels can increase the maximum propagation delay.

Digital logic therefore has both a logical dimension and a physical
implementation dimension.
""")


# =============================================================================
# 49. HAZARDS AND GLITCHES
# =============================================================================

print("\n" + "=" * 80)
print("HAZARDS AND GLITCHES")
print("=" * 80)

print("""
A Boolean expression describes stable logical behavior.

A real circuit has propagation delays.

If different paths through a circuit have different delays, a transition
can temporarily produce an unwanted output value.

This transient behavior is commonly called a glitch.

For example, two logically equivalent signals may not physically arrive at
an output at exactly the same time.

This matters in real digital circuit design, especially when signals are
used as control signals or clocks.
""")


# =============================================================================
# 50. LOGICAL EQUIVALENCE
# =============================================================================

print("\n" + "=" * 80)
print("LOGICAL EQUIVALENCE")
print("=" * 80)

print("""
Two Boolean expressions are logically equivalent if they produce the same
output for every possible combination of their inputs.

For example:

    NOT(A AND B)

and:

    NOT(A) OR NOT(B)

are equivalent by De Morgan's law.

We can verify this computationally.
""")


def equivalent_two_input(function1, function2):

    for a in [False, True]:
        for b in [False, True]:

            if function1(a, b) != function2(a, b):
                return False

    return True


print(
    equivalent_two_input(
        lambda a, b: NOT(AND(a, b)),
        lambda a, b: OR(NOT(a), NOT(b))
    )
)


# =============================================================================
# 51. EXHAUSTIVE BOOLEAN VERIFICATION
# =============================================================================

print("\n" + "=" * 80)
print("EXHAUSTIVE VERIFICATION")
print("=" * 80)

print("""
For a small number of Boolean variables, every possible input combination
can be tested.

For n variables:

    number of combinations = 2^n

This makes exhaustive verification practical for many small Boolean
functions.

For example, a three-variable expression requires only:

    2^3 = 8

tests.

A four-variable expression requires:

    2^4 = 16

tests.

A ten-variable expression requires:

    2^10 = 1024

tests.

The number grows exponentially with the number of variables.
""")


def all_boolean_inputs(number_of_variables):
    total = 2 ** number_of_variables

    for value in range(total):

        bits = decimal_to_binary(value).zfill(
            number_of_variables
        )

        yield tuple(bit == "1" for bit in bits)


for inputs in all_boolean_inputs(3):
    print(
        "".join(str(int(x)) for x in inputs)
    )


# =============================================================================
# 52. BOOLEAN FUNCTION
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN FUNCTIONS")
print("=" * 80)

print("""
A Boolean function maps Boolean inputs to a Boolean output.

For n input variables:

    f : {0,1}^n -> {0,1}

There are:

    2^(2^n)

possible Boolean functions of n variables.

For one variable:

    2^(2^1) = 4

possible Boolean functions.

For two variables:

    2^(2^2) = 16

possible Boolean functions.

For three variables:

    2^(2^3) = 256

possible Boolean functions.

The number grows extremely quickly.
""")


def number_of_boolean_functions(number_of_variables):
    return 2 ** (2 ** number_of_variables)


for n in range(1, 5):
    print(
        n,
        "input variable(s):",
        number_of_boolean_functions(n),
        "possible Boolean functions"
    )


# =============================================================================
# 53. BITWISE OPERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("BITWISE OPERATIONS")
print("=" * 80)

print("""
Programming languages expose Boolean-like operations directly on integer
bit patterns.

For Python integers:

    &   bitwise AND
    |   bitwise OR
    ^   bitwise XOR
    ~   bitwise complement
    <<  left shift
    >>  right shift

These operate on the binary representation of integer values.

Example:

    1010
AND 1100
--------
    1000
""")

x = 0b1010
y = 0b1100

print("x       =", bin(x))
print("y       =", bin(y))
print("x & y   =", bin(x & y))
print("x | y   =", bin(x | y))
print("x ^ y   =", bin(x ^ y))


# =============================================================================
# 54. BIT MASKS
# =============================================================================

print("\n" + "=" * 80)
print("BIT MASKS")
print("=" * 80)

print("""
A bit mask is a value used to select, inspect, set, clear, or toggle
particular bits.

Suppose:

    value = 10110110

and:

    mask = 00000100

Then:

    value AND mask

checks the third bit from the right.

Bit masks are common in:

    permissions
    CPU registers
    device control
    networking
    binary protocols
    compact data structures
    configuration flags
""")


value = 0b10110110
mask = 0b00000100

print("value =", bin(value))
print("mask  =", bin(mask))
print("value & mask =", bin(value & mask))

if value & mask:
    print("Selected bit is set.")
else:
    print("Selected bit is clear.")


# =============================================================================
# 55. SETTING, CLEARING, TOGGLING BITS
# =============================================================================

print("\n" + "=" * 80)
print("SETTING, CLEARING, AND TOGGLING BITS")
print("=" * 80)

print("""
To set a bit:

    value OR mask

To clear a bit:

    value AND NOT(mask)

To toggle a bit:

    value XOR mask
""")

value = 0b1000
bit_position = 1
mask = 1 << bit_position

set_value = value | mask
clear_value = value & ~mask
toggle_value = value ^ mask

print("Original :", bin(value))
print("Set      :", bin(set_value))
print("Clear    :", bin(clear_value))
print("Toggle   :", bin(toggle_value))


# =============================================================================
# 56. SHIFT OPERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("BIT SHIFTS")
print("=" * 80)

print("""
Left shift:

    x << n

moves the bit pattern to the left by n positions.

For non-negative integers, a left shift by n is equivalent to multiplying
by:

    2^n

A right shift:

    x >> n

moves bits toward the right.

For non-negative integers, this is equivalent to integer division by:

    2^n
""")


number = 13

print("13 binary:", bin(number))
print("13 << 1:", number << 1, bin(number << 1))
print("13 << 2:", number << 2, bin(number << 2))
print("13 >> 1:", number >> 1, bin(number >> 1))


# =============================================================================
# 57. XOR AS A TOGGLE OPERATION
# =============================================================================

print("\n" + "=" * 80)
print("XOR AS A TOGGLE")
print("=" * 80)

print("""
XOR has a useful property:

    A XOR 0 = A
    A XOR 1 = NOT(A)

Therefore XOR can be used to toggle selected bits.

If a mask contains:

    1

at a position, the corresponding bit changes.

If the mask contains:

    0

the corresponding bit remains unchanged.
""")

original = 0b1010
toggle_mask = 0b0011

print("Original:", bin(original))
print("Mask    :", bin(toggle_mask))
print("Result  :", bin(original ^ toggle_mask))


# =============================================================================
# 58. PARITY
# =============================================================================

print("\n" + "=" * 80)
print("PARITY AND XOR")
print("=" * 80)

print("""
XOR can be used to calculate parity.

For a collection of bits:

    parity = b1 XOR b2 XOR b3 XOR ...

The result is:

    1

when the number of 1 bits is odd.

The result is:

    0

when the number of 1 bits is even.

This property is useful in error detection.
""")


def xor_reduce(bits):
    result = False

    for bit in bits:
        result = XOR(result, bit)

    return result


samples = [
    [False, False, False],
    [True, False, False],
    [True, True, False],
    [True, True, True]
]

for sample in samples:
    print(
        [int(x) for x in sample],
        "parity =",
        int(xor_reduce(sample))
    )


# =============================================================================
# 59. Hamming-style BIT DIFFERENCE
# =============================================================================

print("\n" + "=" * 80)
print("BIT DIFFERENCE")
print("=" * 80)

print("""
XOR also identifies positions where two bit patterns differ.

If:

    A XOR B

is calculated, a resulting 1 means that the corresponding bits are
different.

Counting those 1s gives the Hamming distance between two equal-length
binary strings.
""")


def hamming_distance(a, b):

    if len(a) != len(b):
        raise ValueError("Binary strings must have equal length.")

    return sum(
        bit_a != bit_b
        for bit_a, bit_b in zip(a, b)
    )


print(
    "101101 vs 100001:",
    hamming_distance("101101", "100001")
)


# =============================================================================
# 60. LOGIC VS ARITHMETIC
# =============================================================================

print("\n" + "=" * 80)
print("LOGIC VS ARITHMETIC")
print("=" * 80)

print("""
Boolean operations and arithmetic operations are related but different.

Boolean OR:

    1 OR 1 = 1

Arithmetic addition:

    1 + 1 = 2

At the bit level, addition requires multiple outputs:

    1 + 1 = 10

The lower bit is the sum and the higher bit is the carry.

This distinction is fundamental.

A logic gate does not automatically mean arithmetic addition.

Arithmetic circuits are constructed from logic gates.
""")


# =============================================================================
# 61. LOGIC AS THE FOUNDATION OF COMPUTATION
# =============================================================================

print("\n" + "=" * 80)
print("LOGIC AS THE FOUNDATION OF COMPUTATION")
print("=" * 80)

print("""
A digital computer can be viewed as a hierarchy.

At the physical level:

    transistors

are used to construct:

    logic gates

which construct:

    combinational and sequential circuits

which construct:

    arithmetic units
    registers
    control logic
    memory structures

which form:

    processors and digital systems

At a higher abstraction level, these systems execute:

    instructions
    programs
    algorithms

The layers are different descriptions of related computational mechanisms.
""")


# =============================================================================
# 62. TRANSISTORS AND LOGIC GATES
# =============================================================================

print("\n" + "=" * 80)
print("TRANSISTORS AND LOGIC GATES")
print("=" * 80)

print("""
A transistor is an electronic device that can be used as a controllable
switch.

Modern digital circuits use enormous numbers of transistors to implement
logic.

A logic gate is therefore an abstraction over lower-level transistor
behavior.

For example, CMOS implementations use complementary networks of MOSFETs
to implement Boolean functions.

At the logic-design level, we usually reason about:

    inputs
    outputs
    truth tables
    Boolean expressions
    gates

without tracking individual electron movements.
""")


# =============================================================================
# 63. ABSTRACTION
# =============================================================================

print("\n" + "=" * 80)
print("ABSTRACTION IN DIGITAL COMPUTATION")
print("=" * 80)

print("""
One of the central ideas in computer engineering is abstraction.

At one level:

    transistor behavior

At another:

    gates

At another:

    Boolean expressions

At another:

    circuits

At another:

    CPU components

At another:

    machine instructions

At another:

    programming languages

At another:

    applications

Each layer hides many implementation details from the layer above it.

Boolean logic is important because it provides a precise mathematical
language for a major part of the digital hardware underneath software.
""")


# =============================================================================
# 64. CONTROL LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN LOGIC IN CONTROL")
print("=" * 80)

print("""
Boolean logic is not restricted to arithmetic.

A system may need to decide:

    Should this operation execute?

    Is this instruction valid?

    Is this register enabled?

    Should this memory location be selected?

    Is an interrupt active?

    Is a condition satisfied?

These decisions can be expressed as Boolean conditions.

For example:

    enable = valid AND ready AND NOT(reset)

Such expressions become control logic in digital hardware.
""")


def control_signal(valid, ready, reset):
    return AND(
        AND(valid, ready),
        NOT(reset)
    )


for valid in [False, True]:
    for ready in [False, True]:
        for reset in [False, True]:

            print(
                f"valid={int(valid)} "
                f"ready={int(ready)} "
                f"reset={int(reset)} "
                f"enable={int(control_signal(valid, ready, reset))}"
            )


# =============================================================================
# 65. BOOLEAN LOGIC AND CONDITIONS
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN LOGIC AND PROGRAM CONDITIONS")
print("=" * 80)

print("""
Programming languages use Boolean expressions constantly.

For example:

    if user_is_valid and account_is_active:
        allow_access()

The condition is conceptually a Boolean circuit:

    user_is_valid
            \
             AND ---- allow_access
            /
    account_is_active

Programming language syntax provides a high-level representation of logical
operations that ultimately correspond to computations performed by hardware.
""")


# =============================================================================
# 66. SHORT-CIRCUITING AND PURE BOOLEAN LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("SHORT-CIRCUITING")
print("=" * 80)

print("""
There is an important distinction between mathematical Boolean evaluation
and programming-language evaluation.

Mathematically:

    A AND B

defines a Boolean result.

A programming language may use short-circuit evaluation.

For example, in Python:

    False and expensive_operation()

does not need to evaluate the second operand because the result is already
known to be False.

This is an execution optimization or language semantic behavior.

It should not be confused with the abstract truth table of the AND function.
""")


# =============================================================================
# 67. TRUTH TABLE FOR XOR AND ADDITION
# =============================================================================

print("\n" + "=" * 80)
print("XOR AND BINARY ADDITION")
print("=" * 80)

print("""
For one-bit addition:

    A + B

the Sum bit is:

    A XOR B

and the Carry bit is:

    A AND B

This explains why XOR appears naturally in arithmetic circuits.
""")

print("A B | Sum Carry")
print("----+---------")

for a in [False, True]:
    for b in [False, True]:

        s, c = half_adder(a, b)

        print(
            int(a),
            int(b),
            "|",
            int(s),
            "   ",
            int(c)
        )


# =============================================================================
# 68. ALU CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("ARITHMETIC LOGIC UNIT")
print("=" * 80)

print("""
An Arithmetic Logic Unit, or ALU, performs arithmetic and logical
operations.

Conceptually, an ALU may support operations such as:

    addition
    subtraction
    AND
    OR
    XOR
    comparison
    shifts

The ALU itself is built from lower-level digital logic.

A processor's instruction may cause control logic to select:

    which operands are used
    which operation is performed
    where the result goes
""")


def simple_alu(a, b, operation):

    if operation == "AND":
        return AND(a, b)

    if operation == "OR":
        return OR(a, b)

    if operation == "XOR":
        return XOR(a, b)

    if operation == "NAND":
        return NAND(a, b)

    raise ValueError("Unsupported operation")


for operation in ["AND", "OR", "XOR", "NAND"]:

    print(
        operation,
        "with A=1 B=0 ->",
        int(simple_alu(True, False, operation))
    )


# =============================================================================
# 69. COMBINATIONAL CIRCUIT DESIGN PROCESS
# =============================================================================

print("\n" + "=" * 80)
print("DESIGNING A COMBINATIONAL CIRCUIT")
print("=" * 80)

print("""
A typical Boolean circuit design process can be described as:

    1. Define the problem.
    2. Identify inputs.
    3. Identify outputs.
    4. Define the desired behavior.
    5. Construct a truth table.
    6. Derive a Boolean expression.
    7. Simplify the expression.
    8. Implement the expression using gates.
    9. Verify all input combinations.
   10. Consider implementation cost and timing.

The exact engineering workflow can be more elaborate, but this sequence
captures the central logical reasoning process.
""")


# =============================================================================
# 70. EXAMPLE CIRCUIT DESIGN
# =============================================================================

print("\n" + "=" * 80)
print("EXAMPLE: TWO-INPUT ALARM")
print("=" * 80)

print("""
Suppose an alarm should activate when:

    the door is open

AND:

    the system is armed.

Inputs:

    door_open
    system_armed

Output:

    alarm

Boolean expression:

    alarm = door_open AND system_armed
""")


def alarm_logic(door_open, system_armed):
    return AND(
        door_open,
        system_armed
    )


for door_open in [False, True]:
    for system_armed in [False, True]:

        print(
            f"door={int(door_open)} "
            f"armed={int(system_armed)} "
            f"alarm={int(alarm_logic(door_open, system_armed))}"
        )


# =============================================================================
# 71. EXAMPLE WITH PRIORITY
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN PRIORITY")
print("=" * 80)

print("""
Boolean expressions can model priority conditions.

Suppose a system should activate when:

    emergency = 1

or when:

    normal_request = 1

provided that the system is enabled.

One possible expression is:

    output = enabled AND (emergency OR normal_request)
""")


def request_logic(enabled, emergency, normal_request):

    return AND(
        enabled,
        OR(emergency, normal_request)
    )


for emergency in [False, True]:
    result = request_logic(
        enabled=True,
        emergency=emergency,
        normal_request=False
    )

    print(
        "emergency=",
        int(emergency),
        "output=",
        int(result)
    )


# =============================================================================
# 72. CANONICAL XOR
# =============================================================================

print("\n" + "=" * 80)
print("XOR AS A CANONICAL SOP")
print("=" * 80)

print("""
For two variables:

    XOR = A'B + AB'

The first term represents:

    A=0, B=1

The second term represents:

    A=1, B=0

Therefore the expression produces 1 exactly when the inputs differ.
""")


def xor_sop(a, b):

    term1 = AND(NOT(a), b)
    term2 = AND(a, NOT(b))

    return OR(term1, term2)


for a in [False, True]:
    for b in [False, True]:

        assert xor_sop(a, b) == XOR(a, b)


# =============================================================================
# 73. XOR IDENTITIES
# =============================================================================

print("\n" + "=" * 80)
print("XOR IDENTITIES")
print("=" * 80)

print("""
Useful XOR properties include:

    A XOR 0 = A

    A XOR 1 = NOT(A)

    A XOR A = 0

    A XOR NOT(A) = 1

XOR is commutative:

    A XOR B = B XOR A

XOR is associative:

    (A XOR B) XOR C
        =
    A XOR (B XOR C)

These properties make XOR useful for parity, checksums, toggling,
comparisons, and arithmetic circuits.
""")


# =============================================================================
# 74. XNOR AS EQUALITY
# =============================================================================

print("\n" + "=" * 80)
print("XNOR AS EQUALITY")
print("=" * 80)

print("""
For single bits:

    XNOR(A, B)

is true exactly when:

    A == B

Therefore XNOR naturally functions as a one-bit equality detector.
""")


for a in [False, True]:
    for b in [False, True]:

        assert XNOR(a, b) == (a == b)


# =============================================================================
# 75. BOOLEAN SIMPLIFICATION BY EXHAUSTION
# =============================================================================

print("\n" + "=" * 80)
print("CHECKING A BOOLEAN SIMPLIFICATION")
print("=" * 80)

print("""
Consider:

    A + AB

Boolean algebra simplifies this to:

    A

because:

    A + AB
    = A(1 + B)
    = A

We can verify the equivalence for every possible input.
""")


def expression_original(a, b):
    return OR(
        a,
        AND(a, b)
    )


def expression_simplified(a, b):
    return a


for a in [False, True]:
    for b in [False, True]:

        print(
            int(a),
            int(b),
            "original=",
            int(expression_original(a, b)),
            "simplified=",
            int(expression_simplified(a, b))
        )

        assert expression_original(a, b) == expression_simplified(a, b)


# =============================================================================
# 76. ABSORPTION LAWS
# =============================================================================

print("\n" + "=" * 80)
print("ABSORPTION LAWS")
print("=" * 80)

print("""
Two important absorption laws are:

    A + AB = A

and:

    A(A + B) = A

These laws are useful for simplifying circuits and removing unnecessary
logic.
""")


for a in [False, True]:
    for b in [False, True]:

        assert OR(a, AND(a, b)) == a
        assert AND(a, OR(a, b)) == a


# =============================================================================
# 77. CONSENSUS THEOREM
# =============================================================================

print("\n" + "=" * 80)
print("CONSENSUS THEOREM")
print("-" * 80)

print("""
A useful Boolean identity is:

    AB + A'C + BC
        =
    AB + A'C

The term:

    BC

is the consensus term and can be redundant for the Boolean function.

This illustrates an important point:

A term can appear necessary when an expression is viewed syntactically,
while being unnecessary when the complete Boolean behavior is considered.
""")


def consensus_original(a, b, c):
    return (
        (a and b)
        or
        ((not a) and c)
        or
        (b and c)
    )


def consensus_simplified(a, b, c):
    return (
        (a and b)
        or
        ((not a) and c)
    )


for inputs in all_boolean_inputs(3):

    a, b, c = inputs

    assert (
        consensus_original(a, b, c)
        ==
        consensus_simplified(a, b, c)
    )


# =============================================================================
# 78. GATE COUNT AND CIRCUIT COST
# =============================================================================

print("\n" + "=" * 80)
print("GATE COUNT AND CIRCUIT COST")
print("=" * 80)

print("""
Two Boolean expressions can implement the same function but require
different hardware.

Possible implementation concerns include:

    number of gates
    number of inputs per gate
    circuit depth
    wiring complexity
    propagation delay
    physical area
    power consumption

Therefore Boolean simplification is not merely mathematical decoration.

It can correspond to real implementation improvements.
""")


# =============================================================================
# 79. FAN-IN AND FAN-OUT
# =============================================================================

print("\n" + "=" * 80)
print("FAN-IN AND FAN-OUT")
print("=" * 80)

print("""
Fan-in refers to the number of inputs a gate accepts.

For example:

    a two-input AND gate

has fan-in of 2.

A four-input AND gate has fan-in of 4.

Fan-out refers to how many gate inputs are driven by a particular output.

Real hardware places physical limits on fan-in and fan-out.

The abstract Boolean model does not always expose these limitations.
""")


# =============================================================================
# 80. ACTIVE-HIGH AND ACTIVE-LOW SIGNALS
# =============================================================================

print("\n" + "=" * 80)
print("ACTIVE-HIGH AND ACTIVE-LOW")
print("=" * 80)

print("""
A signal's logical meaning is separate from its electrical representation.

An active-high signal is considered asserted when it is 1.

An active-low signal is considered asserted when it is 0.

Active-low signals are often represented using notation such as:

    RESET_N
    ENABLE_B

or with an inversion marker in hardware diagrams.

Therefore:

    physical 0

does not necessarily mean:

    logical false

The meaning depends on the signal convention.
""")


# =============================================================================
# 81. POSITIVE AND NEGATIVE LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("LOGIC POLARITY")
print("=" * 80)

print("""
Digital logic has a distinction between signal level and logical meaning.

In positive logic:

    higher signal level represents logical 1.

In negative logic:

    the interpretation can be reversed.

This reinforces an important principle:

    Boolean value
        !=
    physical voltage

Boolean logic is an abstraction over the physical implementation.
""")


# =============================================================================
# 82. NOISE MARGIN CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("NOISE AND DIGITAL STATES")
print("=" * 80)

print("""
Real digital systems operate with physical voltages and currents.

A digital input does not necessarily require one mathematically exact
voltage.

Instead, hardware specifications define ranges corresponding to acceptable
logic levels.

This provides tolerance against electrical noise.

The abstract Boolean model reduces all of this physical behavior to:

    0
    1

The reduction is useful because it allows digital systems to be reasoned
about mathematically.
""")


# =============================================================================
# 83. BOOLEAN LOGIC AND MEMORY
# =============================================================================

print("\n" + "=" * 80)
print("LOGIC AND MEMORY")
print("=" * 80)

print("""
Combinational logic depends only on current inputs.

Memory requires a system to retain state.

Conceptually:

    next_state = f(current_state, inputs)

and:

    output = g(current_state, inputs)

This introduces sequential logic.

Elements such as:

    latches
    flip-flops
    registers

allow digital systems to maintain state.

The Boolean logic studied in this script forms the foundation of the
logic used inside these larger structures.
""")


# =============================================================================
# 84. STATE AS BITS
# =============================================================================

print("\n" + "=" * 80)
print("STATE REPRESENTATION")
print("=" * 80)

print("""
A system with n state bits can represent up to:

    2^n

distinct states.

For example, three bits can represent eight states:

    000
    001
    010
    011
    100
    101
    110
    111

A state machine can use such bit patterns to represent modes or stages
of operation.
""")


# =============================================================================
# 85. FINITE STATE MACHINE CONNECTION
# =============================================================================

print("\n" + "=" * 80)
print("FINITE STATE MACHINE CONNECTION")
print("=" * 80)

print("""
A finite state machine can be described using:

    current state
    inputs
    next-state logic
    output logic

The next state is determined by Boolean computation.

For example:

    next_state = f(state_bits, input_bits)

The physical system may use flip-flops to store the current state and
combinational logic to calculate the next state.
""")


# =============================================================================
# 86. BOOLEAN LOGIC AND MEMORY ADDRESSING
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN LOGIC AND ADDRESSING")
print("=" * 80)

print("""
A memory address is represented using bits.

If an address contains n bits, it can identify up to:

    2^n

distinct address values.

Address decoding uses Boolean logic to determine which memory location
or hardware device corresponds to a particular address.
""")


# =============================================================================
# 87. BIT WIDTH
# =============================================================================

print("\n" + "=" * 80)
print("BIT WIDTH")
print("=" * 80)

print("""
Bit width determines how many binary positions are available.

Examples:

    4-bit
    8-bit
    16-bit
    32-bit
    64-bit

Bit width affects:

    representable integer ranges
    precision for fixed-width integer values
    address space
    register size
    datapath width
    arithmetic behavior

A wider datapath does not automatically mean that every computation is
better. It changes the set of values and operations that can be represented
directly.
""")


# =============================================================================
# 88. END-TO-END COMPUTATION EXAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("END-TO-END BOOLEAN COMPUTATION")
print("=" * 80)

print("""
Consider a small control system.

Inputs:

    A = request
    B = permission
    C = emergency_stop

Desired behavior:

    output = request AND permission AND NOT(emergency_stop)

The computation can be decomposed:

    X1 = request AND permission
    X2 = NOT(emergency_stop)
    output = X1 AND X2

The same logic can be described at several levels:

    Boolean equation
    truth table
    gate network
    transistor implementation

The mathematical function remains the same while the representation changes.
""")


def access_control(request, permission, emergency_stop):

    x1 = AND(request, permission)
    x2 = NOT(emergency_stop)

    return AND(x1, x2)


for inputs in all_boolean_inputs(3):

    request, permission, emergency_stop = inputs

    print(
        f"request={int(request)} "
        f"permission={int(permission)} "
        f"stop={int(emergency_stop)} "
        f"output={int(access_control(request, permission, emergency_stop))}"
    )


# =============================================================================
# 89. BOOLEAN FUNCTION ENUMERATION
# =============================================================================

print("\n" + "=" * 80)
print("ENUMERATING TWO-INPUT BOOLEAN FUNCTIONS")
print("=" * 80)

print("""
A two-input Boolean function has four truth-table rows.

Each row can independently have output 0 or 1.

Therefore:

    2^4 = 16

different two-input Boolean functions exist.

The familiar gates are only a small subset of these functions.
""")


def truth_table_code(function):

    bits = []

    for a in [False, True]:
        for b in [False, True]:
            bits.append(
                "1" if function(a, b) else "0"
            )

    return "".join(bits)


named_functions = {
    "AND": AND,
    "OR": OR,
    "NAND": NAND,
    "NOR": NOR,
    "XOR": XOR,
    "XNOR": XNOR,
}

for name, function in named_functions.items():
    print(
        f"{name:5} -> {truth_table_code(function)}"
    )


# =============================================================================
# 90. CONSTANT BOOLEAN FUNCTIONS
# =============================================================================

print("\n" + "=" * 80)
print("CONSTANT BOOLEAN FUNCTIONS")
print("=" * 80)

print("""
Two of the possible Boolean functions are constant:

    F = 0

and:

    F = 1

They ignore their inputs and always produce the same result.

This is another reminder that a Boolean function is defined by its complete
mapping from input combinations to output values.
""")


def constant_zero(a, b):
    return False


def constant_one(a, b):
    return True


print("Constant zero:", truth_table_code(constant_zero))
print("Constant one :", truth_table_code(constant_one))


# =============================================================================
# 91. BOOLEAN FUNCTION AS A LOOKUP TABLE
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN FUNCTION AS A LOOKUP TABLE")
print("=" * 80)

print("""
A Boolean function can be represented by a lookup table.

For n input bits, the input acts as an index into:

    2^n

possible entries.

Each entry contains the corresponding output bit.

This viewpoint connects Boolean functions to:

    truth tables
    lookup tables
    ROM-like structures
    decoders
    programmable logic
""")


def lookup_boolean_function(table, inputs):

    index = 0

    for bit in inputs:
        index = index * 2 + int(bit)

    return table[index]


table = [False, True, True, False]

for inputs in all_boolean_inputs(2):

    print(
        "".join(str(int(x)) for x in inputs),
        "->",
        int(lookup_boolean_function(table, inputs))
    )


# =============================================================================
# 92. HARDWARE DESCRIPTION PERSPECTIVE
# =============================================================================

print("\n" + "=" * 80)
print("HARDWARE DESCRIPTION")
print("=" * 80)

print("""
Boolean expressions are closely related to hardware-description concepts.

A hardware designer may specify:

    signals
    combinational expressions
    registers
    clocks
    state transitions

Hardware description languages such as Verilog and VHDL provide formal
ways of describing digital systems.

The Boolean level remains important because many hardware descriptions
ultimately describe logic operations and state behavior.
""")


# =============================================================================
# 93. LOGIC OPTIMIZATION
# =============================================================================

print("\n" + "=" * 80)
print("LOGIC OPTIMIZATION")
print("=" * 80)

print("""
Logic optimization attempts to implement the same Boolean function using
a more efficient circuit.

Possible objectives include:

    fewer gates
    smaller area
    lower power
    shorter delay
    simpler wiring

Optimization may involve:

    Boolean algebra
    Karnaugh maps
    Quine-McCluskey minimization
    logic synthesis
    technology mapping

For small functions, algebraic manipulation can be enough.
For larger functions, automated synthesis methods become important.
""")


# =============================================================================
# 94. KARNAUGH MAP CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("KARNAUGH MAP CONCEPT")
print("=" * 80)

print("""
A Karnaugh map is a graphical method for simplifying Boolean expressions.

It arranges truth-table values so that adjacent cells differ in only one
variable.

Groups of adjacent 1s can be combined to produce simplified SOP expressions.

Groups of adjacent 0s can similarly be used for POS simplification.

Karnaugh maps are particularly useful for small numbers of variables.
""")


# =============================================================================
# 95. DON'T-CARE CONDITIONS
# =============================================================================

print("\n" + "=" * 80)
print("DON'T-CARE CONDITIONS")
print("=" * 80)

print("""
Some digital systems contain input combinations that never occur or whose
output does not matter.

Such cases can be marked as don't-care conditions.

A don't-care condition may be treated as either 0 or 1 during optimization,
depending on which choice produces a simpler circuit.

This can significantly reduce logic complexity.
""")


# =============================================================================
# 96. BOOLEAN LOGIC AND ERROR DETECTION
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN LOGIC AND ERROR DETECTION")
print("=" * 80)

print("""
XOR-based parity demonstrates how Boolean computation can detect certain
errors.

Suppose a system sends:

    1011001

A parity bit can be added so that the total number of 1s has a chosen parity.

If one bit changes during transmission, the parity may change.

Parity is not a complete error-correction mechanism. It is a simple error
detection technique with specific limitations.
""")


# =============================================================================
# 97. CHECKING PARITY
# =============================================================================

print("\n" + "=" * 80)
print("PARITY CHECK")
print("=" * 80)


def even_parity_bit(bits):

    return xor_reduce(bits)


data = [
    True,
    False,
    True,
    True,
    False
]

parity_bit = even_parity_bit(data)

print(
    "Data:",
    "".join(str(int(x)) for x in data)
)

print(
    "Parity bit:",
    int(parity_bit)
)

print(
    "Combined parity:",
    int(xor_reduce(data + [parity_bit]))
)


# =============================================================================
# 98. BOOLEAN LOGIC AND CRYPTOGRAPHIC STRUCTURES
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN OPERATIONS IN COMPUTING")
print("=" * 80)

print("""
XOR, AND, OR, NOT, and bitwise operations appear throughout computer
systems.

XOR is especially important in many low-level algorithms and digital
structures because it is reversible with respect to one operand:

    A XOR B XOR B = A

Bitwise Boolean operations are also used in:

    checksums
    hash constructions
    error detection
    instruction processing
    bit-level algorithms
    digital communication

The presence of XOR in these areas comes from its algebraic properties,
not from XOR being a replacement for every other form of logic.
""")


# =============================================================================
# 99. REVERSIBILITY OF XOR
# =============================================================================

print("\n" + "=" * 80)
print("XOR REVERSIBILITY")
print("=" * 80)

print("""
The identity:

    A XOR B XOR B = A

follows because:

    B XOR B = 0

and:

    A XOR 0 = A

This property means that if:

    C = A XOR B

then:

    A = C XOR B

and:

    B = C XOR A

This is an important algebraic property of XOR.
""")


for a in [False, True]:
    for b in [False, True]:

        c = XOR(a, b)

        assert XOR(c, b) == a
        assert XOR(c, a) == b


# =============================================================================
# 100. LOGIC GATE COMPOSITION
# =============================================================================

print("\n" + "=" * 80)
print("COMPOSITION OF LOGIC")
print("=" * 80)

print("""
A complex Boolean circuit is simply a composition of simpler functions.

For example:

    F = (A AND B) OR (C XOR D)

can be constructed by:

    AND gate
    XOR gate
    OR gate

The output of the first gates becomes input to the final gate.

This compositional structure is one reason digital logic scales to very
large systems.
""")


def composed_logic(a, b, c, d):

    left = AND(a, b)
    right = XOR(c, d)

    return OR(left, right)


for inputs in all_boolean_inputs(4):

    a, b, c, d = inputs

    print(
        "".join(str(int(x)) for x in inputs),
        "->",
        int(composed_logic(a, b, c, d))
    )


# =============================================================================
# 101. BOOLEAN LOGIC AND COMPUTABILITY
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN LOGIC AND COMPUTATION")
print("=" * 80)

print("""
Boolean logic is powerful enough to express arbitrary finite Boolean
functions.

With universal gates such as NAND, arbitrary Boolean computations can be
constructed from one fundamental gate type.

This gives Boolean logic an important role in the theory and engineering
of computation.

At the hardware level, complex computations are ultimately constructed from
large networks of simple operations.
""")


# =============================================================================
# 102. SEPARATING VALUE FROM REPRESENTATION
# =============================================================================

print("\n" + "=" * 80)
print("VALUE VS REPRESENTATION")
print("=" * 80)

print("""
A sequence of bits does not inherently identify what it means.

For example:

    01000001

can be interpreted as:

    decimal 65
    hexadecimal 0x41
    an ASCII character such as 'A'
    part of an instruction
    part of an address
    part of an image
    part of a compressed data stream

The bits are the representation.

The interpretation comes from a specification or context.

This is one of the most important conceptual distinctions in computing.
""")


pattern = "01000001"

print("Binary:", pattern)
print("Decimal:", binary_to_decimal(pattern))
print("Hexadecimal:", hex(binary_to_decimal(pattern)))
print("ASCII interpretation:", chr(binary_to_decimal(pattern)))


# =============================================================================
# 103. ENDIANNESS
# =============================================================================

print("\n" + "=" * 80)
print("BIT GROUPS AND BYTE ORDER")
print("=" * 80)

print("""
When multiple bytes represent a larger value, the ordering of bytes matters.

Two common conventions are:

    big-endian
    little-endian

For example, the four-byte hexadecimal value:

    12 34 56 78

may be stored in different memory byte orders.

Endianness concerns the ordering of bytes in multi-byte representations.
It is separate from the basic definition of a Boolean value.
""")


# =============================================================================
# 104. LOGICAL CORRECTNESS VS IMPLEMENTATION
# =============================================================================

print("\n" + "=" * 80)
print("LOGICAL CORRECTNESS VS IMPLEMENTATION")
print("=" * 80)

print("""
A Boolean expression answers:

    What output should occur for each input?

Circuit engineering also asks:

    How quickly?
    With how many gates?
    With what power consumption?
    With what physical constraints?
    With what timing behavior?
    With what noise tolerance?

Therefore Boolean correctness is necessary but is not the entire hardware
engineering problem.
""")


# =============================================================================
# 105. COMPLETE TWO-INPUT GATE TEST
# =============================================================================

print("\n" + "=" * 80)
print("COMPLETE TWO-INPUT GATE TEST")
print("=" * 80)


def verify_gate(name, function, expected):

    actual = []

    for a in [False, True]:
        for b in [False, True]:

            actual.append(
                int(function(a, b))
            )

    passed = actual == expected

    print(
        f"{name:5} "
        f"expected={expected} "
        f"actual={actual} "
        f"PASS={passed}"
    )


verify_gate("AND", AND, [0, 0, 0, 1])
verify_gate("OR", OR, [0, 1, 1, 1])
verify_gate("NAND", NAND, [1, 1, 1, 0])
verify_gate("NOR", NOR, [1, 0, 0, 0])
verify_gate("XOR", XOR, [0, 1, 1, 0])
verify_gate("XNOR", XNOR, [1, 0, 0, 1])


# =============================================================================
# 106. COMMON LOGICAL MISTAKES
# =============================================================================

print("\n" + "=" * 80)
print("COMMON LOGICAL MISTAKES")
print("=" * 80)

print("""
Mistake 1:
Treating Boolean OR as ordinary arithmetic addition.

Mistake 2:
Assuming every integer has a unique meaning independent of bit width.

Mistake 3:
Confusing XOR with OR.

Mistake 4:
Forgetting that NOT changes 0 to 1 and 1 to 0.

Mistake 5:
Assuming a physical voltage is inherently a Boolean value.

Mistake 6:
Ignoring operator precedence when reading expressions.

Mistake 7:
Assuming logically equivalent circuits necessarily have identical timing
or physical cost.

Mistake 8:
Assuming a truth table describes physical propagation behavior. It describes
the logical function, not the complete electrical timing behavior.

Mistake 9:
Assuming the same bit pattern has one universal interpretation.

Mistake 10:
Confusing a Boolean function with the particular circuit used to implement it.
""")


# =============================================================================
# 107. OPERATOR PRECEDENCE
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN OPERATOR PRECEDENCE")
print("=" * 80)

print("""
A conventional Boolean expression commonly gives NOT higher precedence
than AND, and AND higher precedence than OR.

Thus:

    A OR B AND C

is normally interpreted as:

    A OR (B AND C)

and:

    NOT A AND B

as:

    (NOT A) AND B

Parentheses should be used whenever they improve clarity.
""")


# =============================================================================
# 108. BOOLEAN EXPRESSION TREE
# =============================================================================

print("\n" + "=" * 80)
print("EXPRESSION TREE")
print("=" * 80)

print("""
A Boolean expression can be viewed as a tree.

For:

    (A AND B) OR NOT(C)

the root is OR.

Its left child is:

    AND(A, B)

Its right child is:

    NOT(C)

The leaves are:

    A
    B
    C

This is conceptually similar to an expression tree used in compiler
construction.
""")


def expression_tree_example(a, b, c):

    left_subtree = AND(a, b)
    right_subtree = NOT(c)

    return OR(
        left_subtree,
        right_subtree
    )


# =============================================================================
# 109. CIRCUIT AS DATAFLOW
# =============================================================================

print("\n" + "=" * 80)
print("CIRCUIT AS DATAFLOW")
print("=" * 80)

print("""
A combinational circuit can be viewed as a directed dataflow graph.

Each gate receives signals and produces another signal.

For example:

    A ----\
           AND ---- X ----\
    B ----/                OR ---- F
                          /
    C ----\              /
           NOT ---- Y ---/
    D ----/

Intermediate values X and Y are wires carrying Boolean values.

This representation is useful for understanding hardware synthesis and
digital design.
""")


# =============================================================================
# 110. BOOLEAN LOGIC AND CPU FLAGS
# =============================================================================

print("\n" + "=" * 80)
print("BOOLEAN LOGIC AND CPU FLAGS")
print("=" * 80)

print("""
Processors commonly maintain condition information such as:

    zero
    carry
    overflow
    negative/sign
    comparison results

These flags are generated and consumed by digital logic.

For example, a zero flag can be conceptually generated by NOR-ing all bits
of a result:

    zero = NOT(bit0 OR bit1 OR ... OR bitN)

If every result bit is 0, the zero flag becomes 1.
""")


def zero_flag(bits):

    result = False

    for bit in bits:
        result = OR(result, bit)

    return NOT(result)


for bits in [
    [False, False, False, False],
    [False, False, True, False],
    [True, False, False, False]
]:

    print(
        "".join(str(int(x)) for x in bits),
        "zero flag =",
        int(zero_flag(bits))
    )


# =============================================================================
# 111. MULTI-BIT EQUALITY
# =============================================================================

print("\n" + "=" * 80)
print("MULTI-BIT EQUALITY")
print("=" * 80)

print("""
Two n-bit values are equal if every corresponding bit is equal.

For each pair:

    XNOR(Ai, Bi)

produces 1 when the pair is equal.

The entire values are equal when all pairwise equality results are 1.

Therefore:

    equality =
        XNOR(A0,B0)
        AND XNOR(A1,B1)
        AND ...
        AND XNOR(An,Bn)
""")


def binary_equal(a, b):

    if len(a) != len(b):
        return False

    equal = True

    for bit_a, bit_b in zip(a, b):
        equal = AND(
            equal,
            XNOR(
                bit_a == "1",
                bit_b == "1"
            )
        )

    return equal


print(binary_equal("101101", "101101"))
print(binary_equal("101101", "100101"))


# =============================================================================
# 112. MULTI-BIT ZERO DETECTION
# =============================================================================

print("\n" + "=" * 80)
print("MULTI-BIT ZERO DETECTION")
print("=" * 80)

print("""
A multi-bit value is zero if every bit is zero.

This can be implemented conceptually as:

    zero = NOT(OR(all bits))

This is the same idea used in a processor zero-detection circuit.
""")


# =============================================================================
# 113. BOOLEAN LOGIC AND INSTRUCTION DECODING
# =============================================================================

print("\n" + "=" * 80)
print("INSTRUCTION DECODING")
print("=" * 80)

print("""
Machine instructions are represented as bit patterns.

Control logic can inspect particular fields and determine which operation
is being requested.

For example, if an opcode is:

    101

a decoder can activate the control signal associated with that operation.

The decoder is itself a Boolean circuit.
""")


def opcode_is_add(opcode):
    return opcode == "101"


for opcode in ["000", "001", "101", "111"]:
    print(
        opcode,
        "ADD=",
        int(opcode_is_add(opcode))
    )


# =============================================================================
# 114. BOOLEAN LOGIC AND REGISTERS
# =============================================================================

print("\n" + "=" * 80)
print("REGISTERS")
print("=" * 80)

print("""
A register stores a group of bits.

An n-bit register contains n storage elements.

Registers are used for:

    operands
    addresses
    instruction information
    intermediate results
    processor state

Boolean logic controls operations such as:

    load
    clear
    enable
    select
    update
""")


# =============================================================================
# 115. ENABLE LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("ENABLE LOGIC")
print("=" * 80)

print("""
Suppose a register should accept a new value only when enable is 1.

At a conceptual level:

    next_value = enable ? new_value : old_value

This selection can be implemented using multiplexing logic.

For each bit:

    next_bit =
        MUX(old_bit, new_bit, enable)

Thus a multi-bit register update can be built from one multiplexer per bit,
combined with storage elements.
""")


def enabled_update(old_bit, new_bit, enable):
    return mux_2_to_1(
        old_bit,
        new_bit,
        enable
    )


for enable in [False, True]:

    print(
        "enable=",
        int(enable),
        "result=",
        int(enabled_update(False, True, enable))
    )


# =============================================================================
# 116. BOOLEAN LOGIC AND COMPUTATIONAL UNIVERSALITY
# =============================================================================

print("\n" + "=" * 80)
print("COMPUTATIONAL UNIVERSALITY")
print("=" * 80)

print("""
Universal computation is a broader concept than Boolean logic alone.

Boolean circuits can represent arbitrary finite Boolean transformations.

When combined with mechanisms for:

    state
    memory
    sequencing
    instruction interpretation

digital logic can form general-purpose computers.

The important idea is not that every computer operation is literally one
simple gate, but that complex computation can be built compositionally from
simple logical primitives.
""")


# =============================================================================
# 117. FINAL INTERNAL CONSISTENCY TESTS
# =============================================================================

print("\n" + "=" * 80)
print("CONSISTENCY TESTS")
print("=" * 80)

print("Testing fundamental Boolean identities...")


for a in [False, True]:
    for b in [False, True]:
        for c in [False, True]:

            # Identity
            assert AND(a, True) == a
            assert OR(a, False) == a

            # Domination
            assert AND(a, False) is False
            assert OR(a, True) is True

            # Complement
            assert AND(a, NOT(a)) is False
            assert OR(a, NOT(a)) is True

            # De Morgan
            assert NOT(AND(a, b)) == OR(NOT(a), NOT(b))
            assert NOT(OR(a, b)) == AND(NOT(a), NOT(b))

            # Distributivity
            assert (
                AND(a, OR(b, c))
                ==
                OR(AND(a, b), AND(a, c))
            )

            assert (
                OR(a, AND(b, c))
                ==
                AND(OR(a, b), OR(a, c))
            )

            # XOR identities
            assert XOR(a, False) == a
            assert XOR(a, True) == NOT(a)
            assert XOR(a, a) is False

            # XNOR
            assert XNOR(a, b) == (a == b)


print("All Boolean identity tests passed.")


# =============================================================================
# 118. FINAL COMPUTATIONAL MODEL
# =============================================================================

print("\n" + "=" * 80)
print("COMPUTATIONAL MODEL")
print("=" * 80)

print("""
The complete conceptual chain can now be represented as:

    BIT
      |
      v
    BOOLEAN VALUE
      |
      v
    LOGIC OPERATION
      |
      v
    LOGIC GATE
      |
      v
    BOOLEAN EXPRESSION
      |
      v
    COMBINATIONAL CIRCUIT
      |
      +----------------------+
      |                      |
      v                      v
   ARITHMETIC             CONTROL
   CIRCUITS                LOGIC
      |                      |
      +----------+-----------+
                 |
                 v
              DATAPATH
                 |
                 v
              PROCESSOR
                 |
                 v
              COMPUTER

A bit is the basic binary state.

Boolean logic defines how binary values can be combined.

Logic gates provide physical or logical building blocks for those
operations.

Boolean expressions describe combinations of those operations.

Circuits implement the expressions.

Larger digital components are constructed by composing circuits.

This is the central relationship between bits, logic, and computation.
""")


print("\n" + "=" * 80)
print("END OF PROGRAM")
print("=" * 80)
```

