# Variables, Algebraic Expressions and Linear Equations
# Mathematical Foundations for Quantum Computing

print("==============================================")
print("DAY 02: ALGEBRA FOR QUANTUM COMPUTING")
print("Variables, Expressions and Linear Equations")
print("==============================================\n")


# ==============================================
# 1. VARIABLES
# ==============================================

print("1. VARIABLES\n")

x = 10
y = 5

print("Value of x =", x)
print("Value of y =", y)


# ==============================================
# 2. ALGEBRAIC EXPRESSIONS
# ==============================================

print("\n2. ALGEBRAIC EXPRESSIONS\n")

# Expression: x + y
addition_expression = x + y
print("x + y =", addition_expression)

# Expression: x - y
subtraction_expression = x - y
print("x - y =", subtraction_expression)

# Expression: 2x + 3y
expression_1 = 2 * x + 3 * y
print("2x + 3y =", expression_1)

# Expression: x² + y²
expression_2 = x ** 2 + y ** 2
print("x² + y² =", expression_2)

# Expression: (x + y)²
expression_3 = (x + y) ** 2
print("(x + y)² =", expression_3)


# ==============================================
# 3. LINEAR EQUATION
# ==============================================

print("\n3. LINEAR EQUATIONS\n")

# Equation:
# ax + b = 0
#
# Solving for x:
# x = -b / a

a = 2
b = -8

solution = -b / a

print("Linear Equation:")
print(f"{a}x + ({b}) = 0")

print("Solution for x =", solution)


# ==============================================
# 4. SOLVING ANOTHER LINEAR EQUATION
# ==============================================

print("\n4. SOLVING ANOTHER LINEAR EQUATION\n")

# Equation:
# 5x + 10 = 0

a = 5
b = 10

x_solution = -b / a

print(f"{a}x + {b} = 0")
print("Value of x =", x_solution)


# ==============================================
# 5. VERIFYING THE SOLUTION
# ==============================================

print("\n5. VERIFYING THE LINEAR EQUATION\n")

# Substitute the solution into:
# 5x + 10 = 0

verification = a * x_solution + b

print("Substituting x =", x_solution)
print(f"{a}({x_solution}) + {b} =", verification)

if verification == 0:
    print("The solution is correct.")
else:
    print("The solution needs verification.")


# ==============================================
# 6. USER INPUT AND LINEAR EQUATION
# ==============================================

print("\n6. SOLVE YOUR OWN LINEAR EQUATION\n")

print("Equation Format: ax + b = 0")

a = float(input("Enter the value of a: "))
b = float(input("Enter the value of b: "))

if a != 0:
    x = -b / a

    print("\nEquation:")
    print(f"{a}x + ({b}) = 0")

    print("Solution:")
    print("x =", x)

else:
    print("\nThe coefficient 'a' cannot be zero for a linear equation of the form ax + b = 0.")


# ==============================================
# DAY 02 COMPLETED
# ==============================================

print("\n==============================================")
print("DAY 02 ALGEBRA COMPLETED")
print("Variables, Expressions and Linear Equations")
print("==============================================")
