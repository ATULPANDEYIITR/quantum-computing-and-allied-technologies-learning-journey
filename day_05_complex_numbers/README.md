# Complex Numbers: Complex Arithmetic and Quantum Amplitudes

## 1. Introduction

Complex numbers extend the real-number system by introducing the imaginary unit.

The imaginary unit is traditionally written as \(i\), where

\[
i^2=-1.
\]

Python represents the imaginary unit using `j`. Therefore, the mathematical number

\[
3+4i
\]

is written in Python as `3 + 4j`.

A complex number has the general form

\[
z=a+bi,
\]

where \(a\) is the real component and \(b\) is the imaginary component.

Complex numbers are important in mathematics, physics, engineering, signal processing, control systems, electrical engineering, Fourier analysis, and quantum mechanics.

The accompanying Python script develops the subject from basic arithmetic through polar and exponential representations, complex roots, numerical precision, quantum amplitudes, qubit states, quantum gates, interference, tensor products, entanglement, and measurement.

---

## 2. Fundamental Terminology

### 2.1 Complex Number

A complex number is a number of the form

\[
z=a+bi.
\]

The value \(a\) is called the real part and \(b\) is called the imaginary part.

### 2.2 Real Part

The real part of

\[
z=a+bi
\]

is

\[
\operatorname{Re}(z)=a.
\]

In Python:

`z.real`

### 2.3 Imaginary Part

The imaginary part is

\[
\operatorname{Im}(z)=b.
\]

In Python:

`z.imag`

### 2.4 Imaginary Unit

The imaginary unit satisfies

\[
i^2=-1.
\]

Python uses `1j` to represent it.

### 2.5 Complex Conjugate

The conjugate of

\[
z=a+bi
\]

is

\[
\overline z=a-bi.
\]

### 2.6 Modulus

The modulus, or magnitude, is

\[
|z|=\sqrt{a^2+b^2}.
\]

### 2.7 Argument

The argument is the angle associated with a nonzero complex number in the complex plane.

It is commonly written as

\[
\arg(z).
\]

Python's `cmath.phase()` returns the principal phase.

---

## 3. Creating Complex Numbers in Python

Python provides two common approaches.

A complex literal can be written as:

`z = 3 + 4j`

A complex number can also be constructed using:

`z = complex(3, 4)`

Both represent the same complex value.

A purely real complex value can be represented using:

`complex(8, 0)`

A purely imaginary value can be represented using:

`complex(0, 8)`

Python uses `j` rather than the mathematical notation `i`.

---

## 4. Complex Arithmetic

Complex numbers support normal arithmetic operations.

The script demonstrates:

- Addition
- Subtraction
- Multiplication
- Division
- Exponentiation

### 4.1 Addition

For

\[
z_1=a+bi
\]

and

\[
z_2=c+di,
\]

addition gives

\[
z_1+z_2=(a+c)+(b+d)i.
\]

The real components are added separately from the imaginary components.

### 4.2 Subtraction

\[
z_1-z_2=(a-c)+(b-d)i.
\]

### 4.3 Multiplication

Multiplication follows ordinary algebra together with

\[
i^2=-1.
\]

Therefore,

\[
(a+bi)(c+di)
\]

becomes

\[
ac+adi+bci+bd i^2.
\]

Since \(i^2=-1\),

\[
(a+bi)(c+di)
=
(ac-bd)+(ad+bc)i.
\]

The Python script calculates multiplication directly and also reconstructs the result from the mathematical formula.

### 4.4 Division

Complex division uses the conjugate of the denominator.

For

\[
\frac{a+bi}{c+di},
\]

multiplying numerator and denominator by

\[
c-di
\]

produces a real denominator.

The denominator becomes

\[
(c+di)(c-di)=c^2+d^2.
\]

Python performs complex division directly with `/`.

Division by zero remains invalid and produces `ZeroDivisionError`.

---

## 5. Complex Conjugates

For

\[
z=a+bi,
\]

the conjugate is

\[
\overline z=a-bi.
\]

For example,

\[
\overline{3+4i}=3-4i.
\]

An important identity is

\[
z\overline z=|z|^2.
\]

For

\[
z=3+4i,
\]

we obtain

\[
(3+4i)(3-4i)
=
9-12i+12i-16i^2.
\]

Since \(i^2=-1\),

\[
z\overline z=25.
\]

The script verifies this identity numerically.

---

## 6. The Complex Plane

A complex number can be represented geometrically.

For

\[
z=a+bi,
\]

the real part \(a\) determines the horizontal coordinate and the imaginary part \(b\) determines the vertical coordinate.

The resulting two-dimensional representation is called the complex plane or Argand plane.

Complex arithmetic therefore has geometric interpretations.

Addition corresponds to vector addition.

Subtraction corresponds to displacement.

The modulus corresponds to distance from the origin.

The argument corresponds to angular position.

Multiplication combines scaling and rotation.

---

## 7. Modulus

The modulus of

\[
z=a+bi
\]

is

\[
|z|=\sqrt{a^2+b^2}.
\]

This is exactly the Euclidean distance from the origin to the corresponding point in the complex plane.

For

\[
z=3+4i,
\]

the modulus is

\[
|z|
=
\sqrt{3^2+4^2}
=
5.
\]

Python calculates it with:

`abs(z)`

The script also calculates the modulus manually to demonstrate the underlying formula.

The distance between two complex numbers \(z_1\) and \(z_2\) is

\[
|z_2-z_1|.
\]

---

## 8. Argument and Phase

For a nonzero complex number

\[
z=a+bi,
\]

the argument is the angle between the positive real axis and the vector representing \(z\).

The principal argument is commonly restricted to

\[
(-\pi,\pi].
\]

Python provides this value using:

`cmath.phase(z)`

Angles differing by integer multiples of \(2\pi\) describe the same direction.

Therefore,

\[
\theta,
\theta+2\pi,
\theta-2\pi
\]

represent equivalent directions.

This becomes especially important when working with complex logarithms and phase differences.

---

## 9. Polar Form

A complex number can be represented using magnitude and phase.

If

\[
r=|z|
\]

and

\[
\theta=\arg(z),
\]

then

\[
z=r(\cos\theta+i\sin\theta).
\]

This is called polar form.

For example,

\[
1+i
\]

has magnitude

\[
\sqrt2
\]

and phase

\[
\frac{\pi}{4}.
\]

Therefore,

\[
1+i
=
\sqrt2
\left(
\cos\frac{\pi}{4}
+i\sin\frac{\pi}{4}
\right).
\]

Polar form is particularly useful for multiplication, division, powers, roots, and rotations.

---

## 10. Exponential Form

Euler's formula states

\[
e^{i\theta}
=
\cos\theta+i\sin\theta.
\]

Therefore, the polar representation can also be written as

\[
z=re^{i\theta}.
\]

This is called exponential form.

Multiplication becomes especially simple.

If

\[
z_1=r_1e^{i\theta_1}
\]

and

\[
z_2=r_2e^{i\theta_2},
\]

then

\[
z_1z_2
=
r_1r_2e^{i(\theta_1+\theta_2)}.
\]

Thus, multiplication has two geometric effects:

1. Magnitudes are multiplied.
2. Phases are added.

For division,

\[
\frac{z_1}{z_2}
=
\frac{r_1}{r_2}
e^{i(\theta_1-\theta_2)}.
\]

---

## 11. Euler's Formula and Euler's Identity

Euler's formula is

\[
e^{i\theta}
=
\cos\theta+i\sin\theta.
\]

Taking

\[
\theta=\pi
\]

gives

\[
e^{i\pi}=-1.
\]

Therefore,

\[
e^{i\pi}+1=0.
\]

The Python script evaluates this expression numerically.

Because floating-point arithmetic is approximate, the result may contain a very small numerical error instead of being represented as an exact zero.

---

## 12. Powers of Complex Numbers

For

\[
z=re^{i\theta},
\]

raising \(z\) to an integer power gives

\[
z^n=r^ne^{in\theta}.
\]

This follows from De Moivre's theorem.

In trigonometric form,

\[
[r(\cos\theta+i\sin\theta)]^n
=
r^n
[\cos(n\theta)+i\sin(n\theta)].
\]

The script computes the power directly using Python and independently using De Moivre's theorem.

This provides a numerical verification of the mathematical relationship.

---

## 13. Complex Roots

Complex numbers make root calculations more general.

For a nonzero complex number

\[
z=re^{i\theta},
\]

the \(n\)-th roots are

\[
r^{1/n}
e^{i(\theta+2\pi k)/n},
\]

where

\[
k=0,1,\ldots,n-1.
\]

Therefore, a nonzero complex number has \(n\) distinct \(n\)-th roots.

The script implements a general `complex_nth_roots()` function.

Each calculated root is raised to the appropriate power to verify the result.

For the zero number, every root is zero, although the mathematical treatment of multiplicity differs from the nonzero case.

---

## 14. Complex Exponential Function

Python's `cmath` module provides mathematical functions for complex values.

The script demonstrates:

`cmath.exp(z)`

which evaluates the complex exponential.

Complex exponentials are fundamental in:

- Differential equations
- Fourier analysis
- Signal processing
- Electrical engineering
- Wave mechanics
- Quantum mechanics
- Control systems

The exponential representation is particularly valuable because it combines oscillatory behavior and magnitude into one expression.

---

## 15. Complex Logarithms

For

\[
z=re^{i\theta},
\]

the complex logarithm can be written as

\[
\log z
=
\ln r+i(\theta+2\pi k),
\]

where \(k\) is an integer.

Consequently, the complex logarithm is mathematically multivalued.

A programming library must select a branch.

Python's `cmath.log()` returns the principal branch.

The script explicitly constructs multiple logarithm branches by changing the integer \(k\).

This is an important distinction between complex mathematics and a single numerical return value.

---

## 16. Complex Square Roots

Complex square roots exist even when the corresponding real square root does not.

For example,

\[
\sqrt{-1}=i.
\]

Python's `cmath.sqrt()` handles negative and general complex inputs.

The square root of a nonzero complex number has two mathematical values that differ by sign.

A numerical library generally returns one principal square root.

---

## 17. Complex Trigonometric Functions

The trigonometric functions extend naturally to complex arguments.

The script demonstrates:

- `cmath.sin()`
- `cmath.cos()`
- `cmath.tan()`

Complex trigonometric functions are closely connected with exponential functions.

For example,

\[
\sin z
=
\frac{e^{iz}-e^{-iz}}{2i}.
\]

This connection is important in mathematical physics, signal analysis, and differential equations.

---

## 18. Complex Multiplication as Rotation

Multiplication by

\[
e^{i\theta}
\]

rotates a complex number counterclockwise by \(\theta\) radians.

Suppose

\[
z=re^{i\phi}.
\]

Then

\[
ze^{i\theta}
=
re^{i(\phi+\theta)}.
\]

The magnitude remains \(r\), while the phase changes.

The script defines a reusable `rotate()` function to demonstrate this behavior.

This is one of the clearest geometric interpretations of complex multiplication.

---

# Quantum Amplitudes

## 19. Complex Numbers in Quantum Mechanics

Quantum mechanics uses complex amplitudes to describe quantum states.

A quantum amplitude is not itself a probability.

If an outcome has amplitude

\[
\alpha,
\]

the corresponding probability is

\[
|\alpha|^2.
\]

This distinction is fundamental.

An amplitude may be complex, negative, or have a nontrivial phase.

A probability must be real and nonnegative.

---

## 20. Single-Qubit State

A single qubit can be represented as

\[
|\psi\rangle
=
\alpha|0\rangle+\beta|1\rangle.
\]

Here:

- \(\alpha\) is the amplitude of \(|0\rangle\).
- \(\beta\) is the amplitude of \(|1\rangle\).

A valid normalized state satisfies

\[
|\alpha|^2+|\beta|^2=1.
\]

The Python script represents this structure with the `QubitState` class.

---

## 21. Qubit State Normalization

Normalization is necessary because measurement probabilities must add to one.

For

\[
|\psi\rangle
=
\alpha|0\rangle+\beta|1\rangle,
\]

the normalization condition is

\[
|\alpha|^2+|\beta|^2=1.
\]

For a general vector \(v\),

\[
\|v\|
=
\sqrt{\sum_i|v_i|^2}.
\]

The normalized vector is

\[
\frac{v}{\|v\|}.
\]

The zero vector cannot be normalized because its norm is zero.

The script detects this situation and raises an exception rather than producing an invalid state.

---

## 22. Measurement Probabilities

For

\[
|\psi\rangle
=
\alpha|0\rangle+\beta|1\rangle,
\]

measurement in the computational basis produces:

\[
P(0)=|\alpha|^2
\]

and

\[
P(1)=|\beta|^2.
\]

The total probability satisfies

\[
P(0)+P(1)=1.
\]

For the state

\[
\frac{1}{\sqrt2}|0\rangle
+
\frac{i}{\sqrt2}|1\rangle,
\]

the probabilities are

\[
P(0)=\frac12
\]

and

\[
P(1)=\frac12.
\]

The factor \(i\) affects phase but not the individual probability.

---

## 23. Magnitude and Phase of an Amplitude

Every nonzero complex amplitude can be represented as

\[
\alpha=re^{i\theta}.
\]

Here:

- \(r\) is the magnitude.
- \(\theta\) is the phase.

The probability is

\[
|\alpha|^2=r^2.
\]

The phase is not directly visible in the probability of that isolated amplitude.

It becomes important when amplitudes are combined.

---

## 24. Global Phase

A global phase multiplies every component of a quantum state by the same phase factor.

For example,

\[
|\psi'\rangle
=
e^{i\gamma}|\psi\rangle.
\]

The measurement probabilities remain unchanged because

\[
|e^{i\gamma}\alpha|^2
=
|\alpha|^2.
\]

Thus states that differ only by a global phase have identical measurement probabilities for ordinary projective measurements.

The script demonstrates this property by applying a common complex phase to the amplitudes of a qubit.

---

## 25. Relative Phase

Relative phase is different from global phase.

Consider

\[
|\psi_1\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}
\]

and

\[
|\psi_2\rangle
=
\frac{|0\rangle-|1\rangle}{\sqrt2}.
\]

Both produce equal computational-basis probabilities.

Yet the two states are not physically equivalent because their relative phase differs.

The difference becomes observable through later quantum operations and interference.

Therefore, retaining only the magnitudes of amplitudes is insufficient for representing a quantum state.

---

# Quantum Linear Algebra

## 26. State Vectors

The computational-basis states of a qubit can be represented as

\[
|0\rangle
=
\begin{bmatrix}
1\\
0
\end{bmatrix}
\]

and

\[
|1\rangle
=
\begin{bmatrix}
0\\
1
\end{bmatrix}.
\]

A general qubit is

\[
|\psi\rangle
=
\begin{bmatrix}
\alpha\\
\beta
\end{bmatrix}.
\]

The components are complex amplitudes.

The script represents these vectors using ordinary Python lists.

---

## 27. Inner Product

For complex vectors, the inner product requires conjugation of the first vector.

The inner product is

\[
\langle a|b\rangle
=
\sum_i\overline{a_i}b_i.
\]

The conjugation is essential.

For the computational basis,

\[
\langle0|0\rangle=1,
\]

\[
\langle1|1\rangle=1,
\]

and

\[
\langle0|1\rangle=0.
\]

The last equation expresses orthogonality.

The script implements `inner_product()` and explicitly conjugates the first vector.

---

## 28. Vector Norm

The norm of a complex vector is

\[
\|v\|
=
\sqrt{\langle v|v\rangle}.
\]

Because

\[
\langle v|v\rangle
=
\sum_i|v_i|^2,
\]

the squared norm is always nonnegative.

A quantum state is normalized when

\[
\langle\psi|\psi\rangle=1.
\]

The script provides functions for calculating and enforcing normalization.

---

## 29. Quantum Gates

Quantum gates can be represented by matrices.

If \(U\) is a gate and \(|\psi\rangle\) is a state, the transformed state is

\[
|\psi'\rangle
=
U|\psi\rangle.
\]

For a closed quantum system, valid reversible quantum transformations are represented by unitary matrices.

The unitarity condition is

\[
U^\dagger U=I.
\]

Here \(U^\dagger\) denotes the conjugate transpose.

---

## 30. Conjugate Transpose

For a complex matrix \(A\), the conjugate transpose is written

\[
A^\dagger.
\]

It is obtained by transposing the matrix and then taking the complex conjugate of every element.

Equivalently,

\[
(A^\dagger)_{ij}
=
\overline{A_{ji}}.
\]

The script implements this operation with `matrix_conjugate_transpose()`.

---

## 31. Unitary Matrices

A matrix \(U\) is unitary when

\[
U^\dagger U=I.
\]

Unitary matrices preserve:

- Vector norms
- Inner products
- Orthogonality
- Total probability

This makes them appropriate for representing reversible quantum transformations.

The script implements `is_unitary()` and verifies several standard quantum gates.

---

## 32. Hadamard Gate

The Hadamard gate is

\[
H=
\frac{1}{\sqrt2}
\begin{bmatrix}
1&1\\
1&-1
\end{bmatrix}.
\]

Applied to \(|0\rangle\),

\[
H|0\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}.
\]

This produces equal probabilities:

\[
P(0)=\frac12
\]

and

\[
P(1)=\frac12.
\]

Applying the Hadamard gate twice gives

\[
H^2=I.
\]

The script demonstrates both properties.

---

## 33. Pauli Gates

The Pauli matrices are

\[
X=
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix},
\]

\[
Y=
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix},
\]

and

\[
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}.
\]

All three are unitary.

They are also Hermitian.

The \(Y\) gate demonstrates explicitly that complex-valued matrix elements occur naturally in quantum transformations.

---

## 34. Phase Gates

The script demonstrates the phase gates \(S\) and \(T\).

The \(S\) gate is

\[
S=
\begin{bmatrix}
1&0\\
0&i
\end{bmatrix}.
\]

The \(T\) gate is

\[
T=
\begin{bmatrix}
1&0\\
0&e^{i\pi/4}
\end{bmatrix}.
\]

These gates change the phase of the \(|1\rangle\) component while preserving its magnitude.

Although such a phase change may leave immediate computational-basis probabilities unchanged, it can alter the result of later interference.

---

# Bloch Sphere

## 35. Bloch-Sphere Parameterization

A pure single-qubit state can be represented, up to global phase, as

\[
|\psi\rangle
=
\cos\frac{\theta}{2}|0\rangle
+
e^{i\phi}
\sin\frac{\theta}{2}|1\rangle.
\]

The angle \(\theta\) determines the polar position.

The angle \(\phi\) determines the azimuthal position.

Important cases include:

\[
\theta=0
\]

for the north pole corresponding to \(|0\rangle\), and

\[
\theta=\pi
\]

for the south pole corresponding to \(|1\rangle\), up to global phase.

When

\[
\theta=\frac{\pi}{2},
\]

the state lies on the equator.

The script implements this parameterization with `qubit_from_bloch_angles()`.

---

# Multi-Qubit States

## 36. Tensor Products

When independent quantum systems are combined, their state spaces are combined using the tensor product.

For two vectors,

\[
a=[a_0,a_1]
\]

and

\[
b=[b_0,b_1],
\]

their tensor product is

\[
a\otimes b
=
[
a_0b_0,
a_0b_1,
a_1b_0,
a_1b_1
].
\]

Two qubits therefore have four computational-basis states:

\[
|00\rangle,
|01\rangle,
|10\rangle,
|11\rangle.
\]

The script implements a general `tensor_product()` function.

---

## 37. Two-Qubit States

A general two-qubit state can be written as

\[
|\psi\rangle
=
a|00\rangle
+b|01\rangle
+c|10\rangle
+d|11\rangle.
\]

Normalization requires

\[
|a|^2+|b|^2+|c|^2+|d|^2=1.
\]

The computational-basis measurement probabilities are

\[
P(00)=|a|^2,
\]

\[
P(01)=|b|^2,
\]

\[
P(10)=|c|^2,
\]

and

\[
P(11)=|d|^2.
\]

---

## 38. Exponential Growth of the State Space

An \(n\)-qubit system has

\[
2^n
\]

computational-basis states.

Therefore, a general state-vector representation requires \(2^n\) complex amplitudes.

Examples:

| Number of qubits | Number of amplitudes |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

This exponential growth is one of the major challenges in classically simulating general quantum systems.

---

## 39. Bell States

Bell states are maximally entangled two-qubit states.

One Bell state is

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}.
\]

Its amplitude vector is

\[
\begin{bmatrix}
1/\sqrt2\\
0\\
0\\
1/\sqrt2
\end{bmatrix}.
\]

The probabilities are

\[
P(00)=\frac12,
\]

\[
P(01)=0,
\]

\[
P(10)=0,
\]

and

\[
P(11)=\frac12.
\]

The state is normalized, but it cannot be expressed as a tensor product of two independent single-qubit states.

---

## 40. Product States and Entanglement

A two-qubit product state can be expressed as

\[
|\psi_A\rangle\otimes|\psi_B\rangle.
\]

For a pure two-qubit state with amplitudes

\[
[a,b,c,d],
\]

the state is separable if

\[
ad-bc=0.
\]

This condition follows from the determinant of the corresponding two-by-two amplitude matrix.

The script implements this criterion using `is_product_state_two_qubit()`.

The criterion is intended for pure two-qubit states and should not be generalized blindly to arbitrary mixed states.

---

# Quantum Interference

## 41. Adding Amplitudes

Suppose two alternatives have amplitudes \(A\) and \(B\).

The combined amplitude is

\[
A+B.
\]

The probability is

\[
|A+B|^2.
\]

Expanding gives

\[
|A+B|^2
=
|A|^2+|B|^2
+
2\operatorname{Re}(A\overline B).
\]

The final term is the interference term.

This is why quantum probabilities cannot generally be calculated by adding independent probabilities before accounting for amplitudes.

---

## 42. Constructive Interference

If two amplitudes have the same phase, they reinforce each other.

For example,

\[
A=\frac1{\sqrt2}
\]

and

\[
B=\frac1{\sqrt2}.
\]

Then

\[
A+B=\sqrt2.
\]

The magnitude is larger than either individual amplitude.

---

## 43. Destructive Interference

If two amplitudes have opposite phases,

\[
A=\frac1{\sqrt2}
\]

and

\[
B=-\frac1{\sqrt2},
\]

then

\[
A+B=0.
\]

The corresponding probability is zero.

This is destructive interference.

---

## 44. Relative Phase and Interference

Suppose

\[
A=r
\]

and

\[
B=re^{i\phi}.
\]

Then

\[
A+B=r(1+e^{i\phi}).
\]

Changing \(\phi\) changes the magnitude of the combined amplitude.

Important cases include:

- \(\phi=0\): constructive interference.
- \(\phi=\pi\): destructive interference.
- Intermediate phases: partial interference.

The script evaluates several phase values and calculates the resulting probabilities.

---

# Quantum Measurement

## 45. Measurement Simulation

For amplitudes

\[
\alpha_0,\alpha_1,\ldots,\alpha_{n-1},
\]

the corresponding computational-basis probabilities are

\[
p_i=|\alpha_i|^2.
\]

The script converts amplitudes into probabilities and uses a random-number generator to simulate measurement outcomes.

For a normalized state,

\[
\sum_i p_i=1.
\]

Repeated measurements should produce empirical frequencies that approach the theoretical probabilities.

The frequencies are not expected to match the theoretical probabilities exactly in a finite experiment.

---

## 46. Randomness and Reproducibility

The script uses a fixed random seed for its demonstration.

This makes the pseudo-random sequence reproducible.

A fixed seed is useful for:

- Debugging
- Testing
- Educational demonstrations
- Regression testing

It should not be confused with physical quantum randomness.

The random-number generator is only simulating the sampling process classically.

---

# Observables

## 47. Hermitian Matrices

A matrix \(M\) is Hermitian when

\[
M^\dagger=M.
\]

Hermitian matrices are important because quantum observables are represented by Hermitian operators.

The Pauli matrices \(X\), \(Y\), and \(Z\) are Hermitian.

The script provides `is_hermitian()` to verify this property.

---

## 48. Expectation Value

For a normalized state \(|\psi\rangle\) and observable \(M\), the expectation value is

\[
\langle M\rangle
=
\langle\psi|M|\psi\rangle.
\]

The script implements this calculation using matrix-vector multiplication and the complex inner product.

For a Hermitian observable, the exact expectation value is real.

Floating-point calculations may produce an extremely small imaginary component because of numerical rounding.

---

# Numerical Considerations

## 49. Floating-Point Precision

Complex arithmetic performed with Python floating-point components is approximate.

Mathematically,

\[
e^{i\pi}=-1.
\]

A numerical calculation may instead produce a result extremely close to \(-1\), with a tiny imaginary component.

For this reason, independent floating-point calculations should generally be compared using tolerances.

The script defines `complex_is_close()` for this purpose.

---

## 50. Absolute and Relative Tolerance

An absolute tolerance is useful when values are expected to be near zero.

A relative tolerance is useful when values can have different scales.

The comparison function in the script considers both.

This is preferable to relying exclusively on exact equality for scientific numerical computations.

---

## 51. Phase of Zero

The mathematical phase of zero is undefined.

Although Python's `cmath.phase(0j)` returns a numerical value according to its library convention, that does not mean zero has a mathematically defined argument.

The script therefore provides `safe_phase()` and explicitly rejects zero.

This illustrates an important implementation principle: numerical library behavior and mathematical definitions are not always identical at edge cases.

---

## 52. Zero-Vector Normalization

The zero vector has norm

\[
0.
\]

Normalization requires division by the norm.

Therefore,

\[
\frac{0}{\|0\|}
\]

is undefined.

The script detects this condition and raises `ValueError`.

Silently returning an invalid normalized state would be an implementation error.

---

## 53. Probability Validation

A valid probability distribution satisfies

\[
p_i\geq0
\]

for every \(i\), and

\[
\sum_i p_i=1.
\]

The script checks these conditions with numerical tolerance.

This validation prevents an invalid amplitude vector from being used as a measurement distribution.

---

# Performance Considerations

## 54. State-Vector Scaling

For \(n\) qubits, a general state vector contains

\[
2^n
\]

complex amplitudes.

The state-space therefore grows exponentially.

A single qubit requires two amplitudes.

Two qubits require four.

Twenty qubits require over one million.

Thirty qubits require more than one billion.

This growth affects both memory requirements and computational cost.

---

## 55. Dense Versus Sparse Representation

A dense representation stores every amplitude, including zeros.

A sparse representation stores only nonzero amplitudes.

For example, a sparse state can be represented as a dictionary mapping basis-state indices to amplitudes.

This can be efficient when a state genuinely contains many zeros.

Sparse representations are not universally superior. Quantum operations can quickly make a state dense, at which point dictionary-based storage may become inefficient.

---

## 56. Matrix-Vector Complexity

The straightforward multiplication of a dense \(n\times n\) matrix by an \(n\)-element vector has approximately

\[
O(n^2)
\]

time complexity.

Basic dense matrix multiplication has approximately

\[
O(n^3)
\]

time complexity.

The implementations in the script use direct Python loops for transparency.

They are educational implementations rather than optimized numerical kernels.

---

# Common Mistakes

## 57. Using `i` Instead of `j`

Mathematical notation commonly uses \(i\), but Python uses `j`.

Correct Python syntax is:

`z = 2 + 3j`

Writing `2 + 3i` does not represent a Python complex literal.

---

## 58. Treating Amplitudes as Probabilities

An amplitude may be complex.

A probability is obtained from its squared magnitude.

The correct transformation is

\[
P=|\alpha|^2.
\]

It is incorrect to treat the complex amplitude itself as a probability.

---

## 59. Forgetting Complex Conjugation

For complex vectors, the inner product requires conjugation of the first vector.

The correct formula is

\[
\langle a|b\rangle
=
\sum_i\overline{a_i}b_i.
\]

Simply multiplying corresponding components without conjugation produces a different mathematical operation.

---

## 60. Ignoring Relative Phase

Two quantum states can have identical computational-basis probabilities while differing in relative phase.

Those states can later produce different interference patterns.

Therefore, quantum-state representations must retain complex amplitudes rather than storing only their magnitudes.

---

## 61. Assuming Every Matrix Is a Quantum Gate

A matrix is not automatically a valid quantum gate.

For a closed-system quantum transformation, the matrix must be unitary.

The condition is

\[
U^\dagger U=I.
\]

The script explicitly verifies unitarity before applying a gate.

---

## 62. Exact Floating-Point Comparisons

Expressions involving floating-point complex numbers should generally not be tested with exact equality when their values come from numerical calculations.

For example, a theoretically zero result may be represented by a tiny value such as \(10^{-16}\).

Tolerance-based comparison is more reliable.

---

## 63. Ignoring Dimension Mismatches

Matrix-vector multiplication requires compatible dimensions.

Similarly, matrix multiplication requires the number of columns of the first matrix to equal the number of rows of the second.

The script validates these conditions and raises exceptions for incompatible inputs.

---

# Important Comparisons

## 64. Real Numbers Versus Complex Numbers

| Property | Real Numbers | Complex Numbers |
|---|---|---|
| General form | \(a\) | \(a+bi\) |
| Dimensions for geometric representation | One | Two |
| Imaginary component | Zero | May be nonzero |
| Conjugate | Same value | Imaginary sign changes |
| Phase | Not generally defined | Defined for nonzero values |
| Square root of negative number | Not real | Complex solution exists |

---

## 65. Magnitude Versus Phase

For

\[
z=re^{i\theta},
\]

\(r\) is the magnitude and \(\theta\) is the phase.

Magnitude describes size.

Phase describes angular position.

Both are required to fully characterize a nonzero complex number.

---

## 66. Amplitude Versus Probability

An amplitude is a complex quantity.

A probability is a real nonnegative quantity.

The relationship is

\[
P=|\alpha|^2.
\]

The phase of an individual amplitude does not change its own probability, but relative phase can affect interference when amplitudes are combined.

---

## 67. Global Phase Versus Relative Phase

Global phase affects all amplitudes equally:

\[
|\psi\rangle
\rightarrow
e^{i\gamma}|\psi\rangle.
\]

It does not change measurement probabilities.

Relative phase describes the difference between the phases of different components.

Relative phase can affect interference and is therefore physically significant.

---

## 68. Unitary Versus Hermitian

A unitary matrix satisfies

\[
U^\dagger U=I.
\]

A Hermitian matrix satisfies

\[
H^\dagger=H.
\]

Unitary matrices describe reversible quantum transformations.

Hermitian matrices represent quantum observables.

A matrix can have both properties. The Pauli matrices are examples.

---

# Real-World Applications

## 69. Electrical Engineering

Complex numbers are widely used in alternating-current circuit analysis.

They allow magnitude and phase relationships to be represented together.

Complex impedance provides a compact mathematical representation of resistive and reactive behavior.

---

## 70. Signal Processing

Complex numbers are fundamental to frequency-domain analysis.

Applications include:

- Fourier transforms
- Digital signal processing
- Filtering
- Modulation
- Spectral analysis
- Frequency response

Complex exponentials provide an efficient mathematical representation of sinusoidal signals.

---

## 71. Control Systems

Complex numbers are used to represent poles and zeros of transfer functions.

The location of poles in the complex plane provides information about system stability and oscillatory behavior.

Real parts are associated with exponential growth or decay, while imaginary parts are associated with oscillatory frequency.

---

## 72. Wave Mechanics

Complex exponentials provide a natural representation for oscillatory phenomena.

They allow amplitude and phase to be manipulated algebraically and appear throughout mathematical descriptions of waves.

---

## 73. Quantum Computing

Complex numbers form part of the mathematical foundation of quantum information.

They appear in:

- Quantum-state amplitudes
- State vectors
- Quantum gates
- Unitary matrices
- Inner products
- Measurement probabilities
- Interference
- Phase transformations
- Tensor products
- Entanglement
- Expectation values

The script demonstrates these relationships directly using Python's built-in complex-number support.

---

# Implementation Considerations

## 74. Standard Library Usage

The script uses Python's standard library.

The primary modules are:

- `cmath` for complex mathematical functions.
- `math` for real-valued mathematical operations.
- `random` for measurement sampling.
- `dataclasses` for the qubit state representation.
- `typing` for type annotations.

No external package is required.

---

## 75. Reusable Functions

The script contains reusable implementations for:

- Complex numerical comparison
- Complex roots
- Complex rotation
- Polynomial evaluation
- Inner products
- Vector normalization
- Matrix-vector multiplication
- Matrix multiplication
- Conjugate transpose
- Unitary testing
- Hermitian testing
- Tensor products
- Measurement simulation
- Probability validation
- Product-state testing

These functions demonstrate how mathematical definitions can be translated directly into executable algorithms.

---

## 76. Class-Based State Representation

The `QubitState` class groups related operations around a single-qubit state.

It provides methods for:

- Norm calculation
- Normalization checks
- State normalization
- Measurement probabilities
- Global-phase removal

This design keeps the mathematical representation and its associated operations together.

---

## 77. Error Handling

The script raises exceptions when mathematical or structural preconditions are violated.

Examples include:

- Division by zero
- Invalid root degree
- Zero-vector normalization
- Undefined phase of zero
- Matrix dimension mismatch
- Invalid probability distributions
- Non-unitary gate application
- Invalid state dimensions

Explicit error handling is preferable to silently producing invalid mathematical results.

---

# Advanced Mathematical Relationships

## 78. Complex Multiplication and Geometry

Complex multiplication combines scaling and rotation.

For

\[
z_1=r_1e^{i\theta_1}
\]

and

\[
z_2=r_2e^{i\theta_2},
\]

their product is

\[
z_1z_2
=
r_1r_2e^{i(\theta_1+\theta_2)}.
\]

This provides an elegant connection between algebra and geometry.

---

## 79. Complex Numbers and Inner-Product Spaces

The complex inner product requires conjugation.

For a vector \(v\),

\[
\langle v|v\rangle
=
\sum_i|v_i|^2.
\]

This produces a nonnegative real quantity and therefore gives a meaningful notion of vector length.

This mathematical structure is essential for quantum state spaces.

---

## 80. Complex Numbers and Unitary Transformations

If \(U\) is unitary, then

\[
U^\dagger U=I.
\]

For a state \(|\psi\rangle\),

\[
\|U|\psi\rangle\|^2
=
\langle\psi|U^\dagger U|\psi\rangle.
\]

Therefore,

\[
\|U|\psi\rangle\|^2
=
\langle\psi|\psi\rangle.
\]

The norm is preserved.

This is why unitary transformations preserve total probability.

---

## 81. Complex Numbers and Interference

Complex amplitudes can add constructively or destructively.

The probability

\[
|A+B|^2
\]

contains the cross term

\[
2\operatorname{Re}(A\overline B).
\]

The cross term depends on relative phase.

Therefore, complex phase is essential for describing interference.

---

## 82. Complex Numbers and Entanglement

A multi-qubit state is represented by a vector of complex amplitudes.

The tensor product describes independent combinations of quantum systems.

Some states cannot be expressed as products of independent subsystem states.

Such states are entangled.

The Bell-state example demonstrates this distinction.

---

# Numerical Reliability

## 83. Numerical Conditioning

A mathematically valid formula may still be numerically unstable.

Potential problems include:

- Cancellation between nearly equal values
- Overflow
- Underflow
- Accumulated rounding error
- Ill-conditioned matrix operations
- Unstable root calculations

Numerical implementations should therefore consider both mathematical correctness and numerical stability.

---

## 84. Tolerance Selection

Tolerance should depend on the scale and purpose of the computation.

A tolerance that is too small may incorrectly reject mathematically equivalent floating-point values.

A tolerance that is too large may hide genuine numerical errors.

The script uses both relative and absolute tolerance to provide a balanced comparison.

---

# Key Mathematical Formulas

## 85. Complex Number

\[
z=a+bi
\]

## 86. Conjugate

\[
\overline z=a-bi
\]

## 87. Modulus

\[
|z|=\sqrt{a^2+b^2}
\]

## 88. Modulus Identity

\[
|z|^2=z\overline z
\]

## 89. Polar Form

\[
z=r(\cos\theta+i\sin\theta)
\]

## 90. Exponential Form

\[
z=re^{i\theta}
\]

## 91. Euler's Formula

\[
e^{i\theta}
=
\cos\theta+i\sin\theta
\]

## 92. De Moivre's Theorem

\[
(re^{i\theta})^n
=
r^ne^{in\theta}
\]

## 93. Quantum-State Normalization

\[
\sum_i|\alpha_i|^2=1
\]

## 94. Measurement Probability

\[
P(i)=|\alpha_i|^2
\]

## 95. Complex Inner Product

\[
\langle a|b\rangle
=
\sum_i\overline{a_i}b_i
\]

## 96. Unitary Condition

\[
U^\dagger U=I
\]

## 97. Hermitian Condition

\[
H^\dagger=H
\]

## 98. Expectation Value

\[
\langle M\rangle
=
\langle\psi|M|\psi\rangle
\]

## 99. Bloch-Sphere Qubit

\[
|\psi\rangle
=
\cos\frac{\theta}{2}|0\rangle
+
e^{i\phi}
\sin\frac{\theta}{2}|1\rangle
\]

## 100. Tensor-Product Dimension

For \(n\) qubits,

\[
\dim(\mathcal H)=2^n.
\]

---

# Python Reference

## 101. Basic Complex Operations

The most important Python operations demonstrated in the script are:

`z = 3 + 4j`

`complex(3, 4)`

`z.real`

`z.imag`

`z.conjugate()`

`abs(z)`

`cmath.phase(z)`

`cmath.exp(z)`

`cmath.log(z)`

`cmath.sqrt(z)`

`cmath.sin(z)`

`cmath.cos(z)`

`cmath.tan(z)`

Complex arithmetic uses the normal operators:

`+`

`-`

`*`

`/`

`**`

---

# Practical Interpretation

## 102. Why Complex Numbers Are More Than an Extension of Real Numbers

Complex numbers provide a unified way to represent magnitude and phase.

A number such as

\[
re^{i\theta}
\]

simultaneously describes:

- A magnitude \(r\)
- A direction or phase \(\theta\)

This makes complex numbers particularly effective for oscillatory systems and transformations involving rotations.

---

## 103. Why Complex Amplitudes Matter

Quantum mechanics requires amplitudes that can interfere.

If amplitudes were replaced by probabilities before combining alternatives, the phase information required for interference would be lost.

Complex amplitudes preserve both magnitude and phase until the measurement probability is calculated.

The transition from amplitude to probability is therefore:

\[
\alpha
\rightarrow
|\alpha|^2.
\]

This distinction is one of the central concepts connecting complex arithmetic with quantum amplitudes.

---

## 104. Relationship Between the Script's Sections

The script progresses from elementary complex arithmetic to increasingly structured mathematical objects.

The progression is:

1. Complex numbers
2. Real and imaginary parts
3. Arithmetic
4. Conjugation
5. Magnitude
6. Phase
7. Polar representation
8. Exponential representation
9. Powers and roots
10. Complex functions
11. Geometry
12. Complex vectors
13. Quantum amplitudes
14. Qubit states
15. Inner products
16. Quantum gates
17. Unitary matrices
18. Bloch-sphere representation
19. Tensor products
20. Multi-qubit states
21. Entanglement
22. Measurement
23. Interference
24. Observables
25. Numerical validation
26. Testing

Each stage builds on the mathematical structures introduced earlier.

---

# Production and Reliability Considerations

## 105. Input Validation

Production numerical software should validate all externally supplied values.

Important checks include:

- Correct numeric types
- Finite values when required
- Nonzero denominators
- Compatible dimensions
- Valid probability ranges
- Correct probability normalization
- Valid state-vector dimensions
- Valid matrix dimensions
- Unitarity when a matrix is intended to be a quantum gate

---

## 106. Numerical Testing

Numerical software should test mathematical invariants.

Examples include:

\[
|z|^2=z\overline z
\]

\[
U^\dagger U=I
\]

\[
\sum_i|\alpha_i|^2=1
\]

and

\[
\|U|\psi\rangle\|
=
\||\psi\rangle\|.
\]

The Python script converts these relationships into executable tests.

---

## 107. Educational Versus High-Performance Implementation

The script intentionally uses basic Python lists and loops.

This makes the mathematical operations visible and easy to inspect.

For large numerical workloads, specialized numerical libraries and optimized linear-algebra routines would normally be required.

The simple implementations are therefore best interpreted as transparent reference implementations rather than high-performance computational kernels.

---

# Complete Conceptual Reference

## 108. Complex Arithmetic

Complex arithmetic extends ordinary arithmetic by treating the imaginary unit as a number satisfying

\[
i^2=-1.
\]

The resulting number system is closed under addition, subtraction, multiplication, division by nonzero values, and polynomial equations.

---

## 109. Complex Geometry

Every complex number can be interpreted as a point or vector in two dimensions.

Its modulus gives distance from the origin.

Its argument gives angular direction.

Multiplication corresponds to combining scale and rotation.

---

## 110. Complex Analysis Concepts Demonstrated

The script introduces several concepts associated with complex analysis:

- Complex exponentials
- Complex logarithms
- Branches of logarithms
- Complex square roots
- Complex trigonometric functions
- Polar representation
- Arguments
- Roots of complex numbers

These concepts show why complex arithmetic is richer than ordinary real arithmetic.

---

## 111. Quantum-Amplitude Concepts Demonstrated

The script also demonstrates:

- Complex amplitudes
- Normalized states
- Measurement probabilities
- Global phase
- Relative phase
- Superposition
- Interference
- Inner products
- Unitary transformations
- Hermitian observables
- Expectation values
- Tensor products
- Multi-qubit state vectors
- Bell states
- Entanglement
- Measurement simulation

The central relationship is that complex amplitudes determine probabilities through squared magnitude while their relative phases influence interference.

---

# Final Technical Reference

## 112. Core Python Expressions

Complex construction:

`z = a + bj`

Complex constructor:

`z = complex(a, b)`

Real component:

`z.real`

Imaginary component:

`z.imag`

Conjugate:

`z.conjugate()`

Magnitude:

`abs(z)`

Phase:

`cmath.phase(z)`

Exponential:

`cmath.exp(z)`

Logarithm:

`cmath.log(z)`

Square root:

`cmath.sqrt(z)`

Sine:

`cmath.sin(z)`

Cosine:

`cmath.cos(z)`

Tangent:

`cmath.tan(z)`

---

## 113. Core Quantum Expressions

Single-qubit state:

\[
|\psi\rangle
=
\alpha|0\rangle+\beta|1\rangle
\]

Normalization:

\[
|\alpha|^2+|\beta|^2=1
\]

Measurement:

\[
P(0)=|\alpha|^2
\]

\[
P(1)=|\beta|^2
\]

Inner product:

\[
\langle\phi|\psi\rangle
=
\sum_i\overline{\phi_i}\psi_i
\]

Quantum transformation:

\[
|\psi'\rangle=U|\psi\rangle
\]

Unitarity:

\[
U^\dagger U=I
\]

Expectation value:

\[
\langle M\rangle
=
\langle\psi|M|\psi\rangle
\]

Two-qubit state:

\[
|\psi\rangle
=
a|00\rangle+b|01\rangle+c|10\rangle+d|11\rangle
\]

Two-qubit normalization:

\[
|a|^2+|b|^2+|c|^2+|d|^2=1
\]

Bell state:

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}
\]

---

## 114. Conceptual Distinctions to Retain

The most important technical distinctions demonstrated by the script are:

- A complex number is not the same thing as a real number.
- An amplitude is not the same thing as a probability.
- Magnitude is not the same thing as phase.
- Global phase is not the same thing as relative phase.
- A unitary matrix is not the same thing as a Hermitian matrix.
- A product state is not the same thing as an entangled state.
- A principal complex logarithm is not the same thing as the full multivalued logarithm.
- Numerical equality is not always the same thing as exact mathematical equality.
- A mathematical convention used by a numerical library does not necessarily define the mathematical value of an edge case.

These distinctions form the conceptual foundation for using complex arithmetic correctly in both general numerical computing and quantum-amplitude calculations.
