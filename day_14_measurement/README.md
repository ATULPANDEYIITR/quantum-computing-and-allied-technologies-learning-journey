# Quantum measurement: observables, collapse, and probabilities

## Introduction

Quantum measurement connects the mathematical description of a quantum state with experimentally observable outcomes. A quantum state does not generally assign one predetermined classical value to every observable. Instead, the state and the chosen measurement together determine a probability distribution over possible outcomes.

Three ideas are central:

- **Observables** represent measurable quantities and are represented by Hermitian operators in the standard finite-dimensional formalism.
- **Probabilities** are calculated from the quantum state and the measurement using the Born rule.
- **State collapse**, or measurement state update, describes how the state used for subsequent predictions changes after a particular outcome is obtained.

The accompanying Python script develops these ideas computationally using small complex vectors and matrices. It begins with qubits and gradually introduces projectors, spectral decomposition, density matrices, POVMs, measurement operators, sequential measurements, uncertainty, measurement disturbance, and practical detector effects.

The implementation deliberately avoids external numerical packages. This makes the mathematical operations visible and allows the examples to be read as executable demonstrations of the underlying equations.

## Quantum states

A quantum state is the mathematical object used to predict the probabilities of measurement outcomes.

For a two-level system, a pure state can be written as

\[
|\psi\rangle =
\alpha |0\rangle + \beta |1\rangle,
\]

where \(\alpha\) and \(\beta\) are generally complex probability amplitudes.

Normalization requires

\[
|\alpha|^2 + |\beta|^2 = 1.
\]

The computational basis states are

\[
|0\rangle =
\begin{pmatrix}
1\\
0
\end{pmatrix},
\qquad
|1\rangle =
\begin{pmatrix}
0\\
1
\end{pmatrix}.
\]

The script constructs these states explicitly as complex Python lists.

A probability amplitude is not itself a probability. The Born rule converts amplitudes into probabilities through squared magnitudes.

For a computational-basis measurement,

\[
P(0)=|\alpha|^2,
\qquad
P(1)=|\beta|^2.
\]

The probabilities therefore add to one for a normalized state.

## Bra-ket notation and inner products

Quantum mechanics commonly uses Dirac notation.

A ket such as

\[
|\psi\rangle
\]

represents a state vector. Its corresponding bra is

\[
\langle\psi|.
\]

For a complex vector, the bra is obtained by taking the conjugate transpose.

The inner product

\[
\langle\phi|\psi\rangle
\]

is a complex number called an amplitude or overlap.

The script implements the inner product with complex conjugation on the first vector. This is important because ordinary real-vector dot products are insufficient for quantum states.

For normalized states, the magnitude squared

\[
|\langle\phi|\psi\rangle|^2
\]

is a probability when the measurement asks whether the system is in the state represented by \(|\phi\rangle\).

## Global phase and relative phase

Multiplying a state by a common phase,

\[
|\psi\rangle \rightarrow e^{i\theta}|\psi\rangle,
\]

does not change ordinary measurement probabilities. Such states are physically equivalent as pure-state rays.

The situation is different for a relative phase.

Consider

\[
|\psi\rangle =
\frac{|0\rangle + e^{i\phi}|1\rangle}{\sqrt{2}}.
\]

Changing \(\phi\) can change probabilities measured in the X basis even though the probabilities in the computational Z basis remain one-half and one-half.

The script demonstrates this distinction by comparing states with different relative phases.

This is a fundamental reason amplitudes must be treated as complex quantities rather than as ordinary classical probabilities.

## Observables

An observable is represented by a Hermitian operator in the standard finite-dimensional formulation.

An operator \(A\) is Hermitian when

\[
A^\dagger=A.
\]

Hermitian operators have real eigenvalues, which makes them suitable for representing physical quantities whose ideal measurement outcomes are real numbers.

The script uses the three Pauli operators:

\[
X=
\begin{pmatrix}
0&1\\
1&0
\end{pmatrix},
\]

\[
Y=
\begin{pmatrix}
0&-i\\
i&0
\end{pmatrix},
\]

and

\[
Z=
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}.
\]

These operators are particularly useful because they provide simple examples of incompatible measurements.

## Eigenvalues and eigenstates

If

\[
A|\psi\rangle=a|\psi\rangle,
\]

then \(|\psi\rangle\) is an eigenstate of \(A\), and \(a\) is its eigenvalue.

For an ideal projective measurement of \(A\), its eigenvalues are the possible measurement outcomes.

For the Z observable,

\[
Z|0\rangle=+|0\rangle,
\]

and

\[
Z|1\rangle=-|1\rangle.
\]

Consequently, measuring Z on \(|0\rangle\) produces \(+1\) with probability one, while measuring Z on \(|1\rangle\) produces \(-1\) with probability one.

An eigenstate of an observable is therefore a state with a definite outcome for that observable.

## Spectral decomposition

A Hermitian observable can be represented through its eigenspaces.

For a nondegenerate observable,

\[
A=\sum_a aP_a,
\]

where \(P_a\) is the projector onto the eigenspace corresponding to eigenvalue \(a\).

For a rank-one eigenstate \(|a\rangle\),

\[
P_a=|a\rangle\langle a|.
\]

The projectors satisfy

\[
P_a^2=P_a,
\]

and

\[
P_a^\dagger=P_a.
\]

For a complete projective measurement,

\[
\sum_a P_a=I.
\]

The script reconstructs the Pauli Z operator from its eigenvalue-projector decomposition.

## The Born rule

The Born rule connects the state to measurable probabilities.

For a pure state and projector \(P_a\),

\[
p(a)=\langle\psi|P_a|\psi\rangle.
\]

For a rank-one projector,

\[
P_a=|a\rangle\langle a|,
\]

this becomes

\[
p(a)=|\langle a|\psi\rangle|^2.
\]

For a density matrix \(\rho\), the corresponding expression is

\[
p(a)=\operatorname{Tr}(\rho P_a).
\]

The Born rule is not a rule for assigning probabilities independently of a measurement. A probability refers to a specified outcome of a specified measurement procedure.

## Expectation values

The expectation value of an observable \(A\) in a pure state is

\[
\langle A\rangle
=
\langle\psi|A|\psi\rangle.
\]

For a density matrix,

\[
\langle A\rangle
=
\operatorname{Tr}(\rho A).
\]

If the possible outcomes are \(a\) with probabilities \(p(a)\), then

\[
\langle A\rangle
=
\sum_a a\,p(a).
\]

The script calculates the expectation value both directly from the operator expression and from the probability distribution.

An expectation value is a statistical average. It does not have to be one of the possible individual measurement outcomes.

For example, an observable with outcomes \(-1\) and \(+1\) can have an expectation value of \(0.2\), even though \(0.2\) is not itself a possible outcome.

## Projective measurement

A projective measurement is described by mutually orthogonal projectors.

The projectors satisfy

\[
P_iP_j=\delta_{ij}P_i,
\]

and for a complete measurement,

\[
\sum_iP_i=I.
\]

The probability of outcome \(i\) is

\[
p_i=\langle\psi|P_i|\psi\rangle
\]

for a pure state, or

\[
p_i=\operatorname{Tr}(\rho P_i)
\]

for a density matrix.

For a rank-one projective measurement, the projectors correspond to individual basis states.

The script implements projective measurements for the X, Y, and Z bases.

## State collapse and conditional state update

Suppose a projective measurement produces outcome \(a\) represented by \(P_a\).

For a pure state, the conditional post-measurement state is

\[
|\psi_a\rangle
=
\frac{P_a|\psi\rangle}
{\sqrt{\langle\psi|P_a|\psi\rangle}},
\]

provided the outcome has nonzero probability.

This is commonly called state collapse.

The term describes the state update associated with conditioning on the observed outcome. It is essential to distinguish this mathematical state update from a claim about a particular microscopic physical mechanism. The formalism specifies how future predictions change after an outcome has been recorded.

If the initial state is

\[
|+\rangle=
\frac{|0\rangle+|1\rangle}{\sqrt2},
\]

then a Z measurement has two equally probable outcomes. If the result is \(+1\), the conditional state becomes \(|0\rangle\). If the result is \(-1\), it becomes \(|1\rangle\).

The script explicitly computes these branches.

## Eigenstate measurements

A particularly important special case occurs when the state is already an eigenstate of the measured observable.

If

\[
A|\psi\rangle=a|\psi\rangle,
\]

then the measurement produces \(a\) with probability one in the ideal projective model.

For example,

\[
Z|0\rangle=|0\rangle.
\]

Therefore,

\[
P(Z=+1)=1.
\]

An ideal projective measurement of an observable on one of its eigenstates need not change the state.

This is an important qualification to the common but overly broad statement that every measurement necessarily destroys the quantum state.

## Degenerate measurements

An observable is degenerate when multiple linearly independent states share the same eigenvalue.

Suppose an eigenvalue \(a\) corresponds to a multidimensional eigenspace. The corresponding projector \(P_a\) projects onto the entire eigenspace.

The probability is still

\[
p(a)=\langle\psi|P_a|\psi\rangle.
\]

The measurement identifies the eigenvalue but does not necessarily identify a unique vector inside the degenerate eigenspace.

The script demonstrates this using a three-dimensional state in which two basis states share the same measurement value.

Degeneracy is important because the phrase "collapse to an eigenstate" is incomplete for a degenerate measurement. The appropriate statement is that the state is updated into the relevant eigenspace according to the measurement operation.

## Lüders state update

For a projective measurement on a density matrix, the standard Lüders update for an observed outcome associated with \(P_a\) is

\[
\rho_a
=
\frac{P_a\rho P_a}
{\operatorname{Tr}(P_a\rho)}.
\]

This is the density-matrix counterpart of the pure-state projection rule.

The denominator is the probability of the observed outcome.

The numerator applies the measurement projector before normalization.

This formulation naturally handles both pure and mixed states and is especially useful for discussing degenerate projective measurements.

## Selective and nonselective measurements

A **selective measurement** retains the classical information about which outcome occurred.

If outcome \(a\) is known, the state can be conditioned on that outcome.

A **nonselective measurement** occurs when the measurement interaction happens but the outcome information is discarded.

For a projective measurement,

\[
\rho'
=
\sum_aP_a\rho P_a.
\]

The nonselective state is an average over the possible measurement branches.

The script demonstrates that a Z measurement of \(|+\rangle\), when the result is discarded, removes the off-diagonal coherence in the Z basis.

This distinction is important in quantum information because a measurement can produce classical information and quantum-state disturbance at the same time.

## Sequential measurements

Measurements can be performed one after another.

The probability of a sequence is governed by conditional probabilities.

If the first outcome has probability \(p(a)\), and the second outcome has conditional probability \(p(b|a)\), then

\[
p(a,b)=p(a)p(b|a).
\]

The important quantum feature is that \(p(b|a)\) is calculated from the state after the first measurement.

Consequently, the first measurement can change the probability distribution of the second measurement.

For example, starting with \(|0\rangle\), an X measurement prepares either \(|+\rangle\) or \(|-\rangle\). A subsequent Z measurement then has different statistics from what would have occurred had the initial X measurement not taken place.

## Measurement basis

A quantum state does not have one universal probability distribution independent of measurement choice.

The same state can give different distributions in different bases.

For \(|0\rangle\):

- Z measurement gives \(+1\) with certainty.
- X measurement gives \(+1\) and \(-1\) with equal probability.
- Y measurement also gives two possible outcomes with equal probability.

The probability therefore belongs to the combination of:

- the state,
- the measurement,
- the specified outcome.

This is why statements such as "the probability of a qubit being zero" must be interpreted relative to a particular basis or measurement.

## Commutators and compatible observables

The commutator of two operators is

\[
[A,B]=AB-BA.
\]

If

\[
[A,B]=0,
\]

the operators commute.

Commuting Hermitian operators can, under appropriate finite-dimensional conditions, be simultaneously diagonalized. They can therefore possess a common eigenbasis.

For the Pauli operators,

\[
[X,Y]=2iZ,
\]

and

\[
[X,Z]=-2iY.
\]

The nonzero commutators show that these observables are incompatible in the sense relevant to simultaneous sharp measurement.

The script calculates these commutators directly.

## Uncertainty

For an observable \(A\),

\[
(\Delta A)^2
=
\langle A^2\rangle-\langle A\rangle^2.
\]

The standard deviation is

\[
\Delta A=\sqrt{\langle A^2\rangle-\langle A\rangle^2}.
\]

The Robertson uncertainty relation is

\[
\Delta A\Delta B
\ge
\frac12
\left|
\langle[A,B]\rangle
\right|.
\]

The script evaluates the uncertainty of Pauli observables and compares the measured statistical spread with the commutator-based lower bound.

Quantum uncertainty should not be reduced to ordinary detector imprecision. A quantum state can have intrinsic statistical spread for an observable even when the measurement apparatus is ideal.

## Density matrices

A pure state can be represented by

\[
\rho=|\psi\rangle\langle\psi|.
\]

Density matrices also represent statistical mixtures.

For an ensemble of states \(\{|\psi_i\rangle\}\) with probabilities \(p_i\),

\[
\rho
=
\sum_i p_i|\psi_i\rangle\langle\psi_i|.
\]

A valid density matrix satisfies:

\[
\rho^\dagger=\rho,
\]

\[
\operatorname{Tr}(\rho)=1,
\]

and

\[
\rho\ge0.
\]

The positivity condition means that all expectation values of positive operators are nonnegative.

The script creates both pure and mixed density matrices.

## Purity

A useful quantity is the purity

\[
\operatorname{Tr}(\rho^2).
\]

For a pure state,

\[
\operatorname{Tr}(\rho^2)=1.
\]

For a genuinely mixed finite-dimensional state,

\[
\operatorname{Tr}(\rho^2)<1.
\]

For a maximally mixed qubit,

\[
\rho=\frac{I}{2},
\]

the purity is

\[
\operatorname{Tr}(\rho^2)=\frac12.
\]

The script uses this distinction to compare a pure \(|+\rangle\) state with an equal classical mixture of \(|0\rangle\) and \(|1\rangle\).

## Pure state versus mixed state

A pure state and a mixed state can sometimes produce the same statistics for one particular measurement while remaining physically distinct.

For example, an equal mixture of \(|0\rangle\) and \(|1\rangle\) produces equal Z-basis probabilities. A \(|+\rangle\) state also produces equal Z-basis probabilities.

The difference appears in other measurements. The \(|+\rangle\) state produces a deterministic X measurement, whereas the equal mixture does not.

This illustrates why complete characterization requires measurements across appropriate bases rather than relying on one measurement distribution.

## POVMs

Projective measurements are not the most general measurement description.

A generalized measurement can be represented by a positive operator-valued measure, or POVM.

A POVM consists of effects \(E_m\) satisfying

\[
E_m\ge0
\]

and

\[
\sum_mE_m=I.
\]

The probability of outcome \(m\) is

\[
p(m)=\operatorname{Tr}(\rho E_m).
\]

A POVM effect does not necessarily satisfy

\[
E_m^2=E_m.
\]

Therefore, not every generalized measurement is projective.

The script constructs a simple three-outcome qubit POVM and verifies its completeness relation.

## POVMs versus measurement operators

A POVM specifies outcome probabilities, but the POVM effects alone do not uniquely determine the post-measurement state.

Measurement operators \(M_m\) satisfy

\[
E_m=M_m^\dagger M_m.
\]

The probability of outcome \(m\) is

\[
p(m)
=
\operatorname{Tr}
(M_m\rho M_m^\dagger).
\]

The corresponding conditional state is

\[
\rho_m
=
\frac{M_m\rho M_m^\dagger}
{p(m)}.
\]

Different physical implementations can produce the same effects \(E_m\) while producing different state updates.

This distinction is important when the measurement itself is part of a larger quantum process.

## Kraus representation

Kraus operators are also used to describe general quantum operations.

A collection of operators \(M_m\) can describe measurement branches or a quantum channel.

For a trace-preserving operation,

\[
\sum_mM_m^\dagger M_m=I.
\]

For an individual measurement outcome,

\[
p_m
=
\operatorname{Tr}(M_m\rho M_m^\dagger).
\]

If the outcome is ignored, the state becomes

\[
\rho'
=
\sum_mM_m\rho M_m^\dagger.
\]

The script implements the probability calculation for measurement operators and uses projectors as a simple special case.

## Measurement disturbance

Measurement can change the state.

The disturbance is not identical to detector noise.

A measurement can be perfectly calibrated and still alter the quantum state because the measurement interaction extracts information and establishes correlations with an apparatus or environment.

For example, a Z measurement on \(|+\rangle\) removes coherence between \(|0\rangle\) and \(|1\rangle\) when the outcome is discarded.

The script compares X-basis statistics before and after a Z measurement to illustrate this effect.

## Information and disturbance

Measurement can provide information about one observable while changing the state relevant to another observable.

A Z measurement of \(|+\rangle\) provides information about Z, but the resulting state is no longer an X eigenstate.

This is connected to the noncommutativity of quantum observables.

The information-disturbance relationship is more precise than the statement that "measurement always disturbs." Some measurements can be nondisturbing with respect to particular states or particular observables.

## Weak measurement

Projective measurement is an idealized strong-measurement limit.

A weak measurement uses a weaker system-apparatus interaction. Each individual interaction can extract relatively little information while causing correspondingly smaller disturbance.

Weak measurements are useful in contexts involving continuous monitoring, indirect measurement, and weak-value experiments.

Weak does not mean that the measurement is merely inaccurate. It describes the strength of the measurement interaction and the amount of information extracted per interaction.

The script introduces the distinction conceptually rather than constructing a full continuous weak-measurement model.

## Multi-outcome measurements

Quantum measurement is not restricted to binary systems.

A d-dimensional quantum system can have a complete projective measurement with d orthonormal basis states.

The script includes a three-dimensional qutrit example using a Fourier-like measurement basis.

For a normalized state \(|\psi\rangle\) and orthonormal basis \(|\phi_k\rangle\),

\[
p_k=|\langle\phi_k|\psi\rangle|^2.
\]

The probabilities satisfy

\[
\sum_kp_k=1.
\]

The same mathematical structure applies regardless of whether there are two, three, or many possible outcomes.

## Interference and measurement probabilities

Quantum amplitudes can interfere.

For the state

\[
|\psi_\phi\rangle
=
\frac{|0\rangle+e^{i\phi}|1\rangle}{\sqrt2},
\]

the relative phase changes the X-basis measurement probability.

At \(\phi=0\), the state is \(|+\rangle\), so X=+1 is certain.

At \(\phi=\pi\), the state is \(|-\rangle\), so X=-1 is certain.

The probabilities therefore depend on the relative phase even though the computational-basis probabilities remain equal.

This is a direct computational demonstration of why quantum amplitudes contain phase information that ordinary classical probability distributions do not contain.

## Bloch-vector representation

Every qubit density matrix can be written as

\[
\rho
=
\frac12
\left(
I+r_xX+r_yY+r_zZ
\right).
\]

The vector

\[
\mathbf r=(r_x,r_y,r_z)
\]

is the Bloch vector.

Its components can be calculated through

\[
r_x=\operatorname{Tr}(\rho X),
\]

\[
r_y=\operatorname{Tr}(\rho Y),
\]

and

\[
r_z=\operatorname{Tr}(\rho Z).
\]

For pure qubit states,

\[
|\mathbf r|=1.
\]

For mixed states,

\[
|\mathbf r|<1
\]

unless the state is pure.

The maximally mixed qubit has

\[
\mathbf r=(0,0,0).
\]

The script calculates Bloch vectors for several standard states.

## Measurement of an eigenstate versus measurement of a superposition

These two cases should be distinguished carefully.

For an eigenstate of the measured observable, the result is deterministic in the ideal projective model.

For a superposition of eigenstates, multiple outcomes can occur.

For example,

\[
|+\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}
\]

is a superposition of Z eigenstates. A Z measurement therefore produces two possible results with equal probability.

The same \(|+\rangle\) state is an X eigenstate, so an X measurement gives a definite result.

The distinction depends on the observable being measured, not simply on whether the state looks like a "superposition" in some arbitrarily chosen basis.

## Statistical sampling

The Born rule gives theoretical probabilities. An experiment produces finite samples.

For a binary outcome with probability \(p\), the standard deviation of the observed frequency after \(N\) independent trials is approximately

\[
\sqrt{\frac{p(1-p)}{N}}.
\]

Therefore, statistical uncertainty decreases approximately as

\[
\frac{1}{\sqrt N}.
\]

It does not decrease as \(1/N\).

The script simulates thousands of repeated measurements and compares empirical frequencies with theoretical probabilities.

The simulation uses a fixed pseudorandom seed for reproducibility.

## Pseudorandom simulation versus physical randomness

The script uses Python's pseudorandom number generator to simulate quantum outcomes.

This is useful for educational and statistical demonstrations, but a pseudorandom generator is not a physical quantum random-number source.

A simulation can reproduce the probability distribution specified by the Born rule without reproducing every physical detail of a laboratory measurement apparatus.

For security-sensitive applications, randomness requirements must be evaluated separately. A cryptographic application may require a cryptographically secure source, while a physics simulation may prioritize reproducibility.

## Detector readout error

An ideal quantum measurement model can be separated from classical detector imperfections.

For a binary detector, define:

- false-positive rate: probability of reporting 1 when the true result is 0,
- false-negative rate: probability of reporting 0 when the true result is 1.

If the ideal probability of outcome 1 is \(p\), then the observed probability can be modeled as

\[
p_{\mathrm{obs}}
=
p(1-f_{\mathrm{negative}})
+
(1-p)f_{\mathrm{positive}}.
\]

This is a classical readout-error model.

Real measurement systems can require more detailed calibration models, including asymmetric errors, time dependence, correlated errors, drift, detector saturation, and state-dependent response.

## Measurement fidelity and calibration

A physical measurement device is not automatically identical to an ideal mathematical projector.

Experimental characterization may need to determine:

- measurement fidelity,
- readout confusion probabilities,
- calibration parameters,
- drift,
- detector response,
- coupling to the environment,
- measurement-induced state changes,
- correlated errors,
- statistical confidence intervals.

A useful computational system should therefore separate the ideal quantum model from the device model.

This separation prevents detector imperfections from being incorrectly interpreted as properties of the underlying quantum state.

## Common mistakes

### Treating amplitudes as probabilities

An amplitude can be complex and can contain phase information. The probability is generally obtained from an appropriate squared magnitude or operator expression.

### Treating expectation values as guaranteed outcomes

The expectation value is a statistical average. It does not necessarily correspond to an allowed single-shot outcome.

### Saying every measurement destroys a state

An eigenstate can remain unchanged under the corresponding ideal projective measurement.

### Treating every measurement as projective

POVMs and measurement operators provide more general descriptions.

### Assuming a POVM uniquely specifies state disturbance

POVM effects determine probabilities, but the physical measurement implementation also determines the state update.

### Ignoring degeneracy

A degenerate eigenvalue corresponds to an eigenspace, not necessarily one unique eigenvector.

### Treating uncertainty as detector imprecision

Quantum uncertainty can be intrinsic to the state and the observables involved.

### Confusing global and relative phase

Global phase does not change ordinary pure-state measurement probabilities. Relative phase can change interference and therefore measurement statistics.

### Forgetting normalization

Probability calculations assume a valid normalized state or a valid density matrix.

### Conditioning on a zero-probability outcome

The normalized conditional state is undefined when the outcome probability is zero. A software implementation should detect this instead of silently dividing by zero.

## Numerical considerations

The script uses a tolerance for floating-point comparisons.

Mathematically, probabilities and norms can be exactly zero or one. Floating-point arithmetic can produce tiny residuals such as values close to zero but not exactly zero.

For example, a computation might produce

\[
-10^{-14}
\]

where the theoretical answer is zero.

Numerical software should distinguish harmless floating-point noise from genuine violations of mathematical constraints.

The script therefore uses a small tolerance when validating:

- normalization,
- Hermiticity,
- projector identities,
- probability values,
- matrix equality.

This tolerance should be chosen according to the numerical scale and algorithm rather than treated as a universal constant.

## Computational complexity

The educational implementation stores dense matrices as nested Python lists.

For a d-dimensional state vector, basic vector operations scale approximately as

\[
O(d).
\]

A dense matrix-vector multiplication requires approximately

\[
O(d^2).
\]

Straightforward dense matrix multiplication requires approximately

\[
O(d^3).
\]

For an n-qubit system,

\[
d=2^n.
\]

Therefore, a generic state-vector simulation has exponential memory requirements in the number of qubits.

This is a major computational limitation of classical simulation.

Production implementations may require optimized numerical libraries, sparse matrices, tensor-network representations, symmetry exploitation, specialized simulators, or problem-specific approximations.

## Software design considerations

The script separates several responsibilities:

- vector and matrix operations,
- state validation,
- observable calculations,
- projective measurement,
- density-matrix calculations,
- generalized measurements,
- repeated sampling,
- experimental abstractions,
- validation tests.

This separation is useful because the physical concepts are related but not identical.

For example, a probability calculation should not implicitly perform a state update. Similarly, a theoretical probability should not be confused with a simulated finite-sample frequency.

Keeping these layers separate makes the implementation easier to test and reduces conceptual ambiguity.

## Testing and validation

The script includes internal tests covering:

- state normalization,
- Hermiticity of Pauli operators,
- Pauli operator identities,
- projector idempotence,
- Born probabilities,
- deterministic eigenstate measurements,
- expectation values,
- density-matrix trace,
- pure-state purity,
- maximally mixed-state purity,
- POVM completeness,
- global-phase invariance,
- statistical sampling behavior.

These tests are important because quantum-mechanical equations impose strong mathematical constraints.

A measurement implementation should verify that probabilities form a valid distribution and that state updates preserve the required normalization or trace properties.

## Real-world relevance

Quantum measurement is fundamental to:

- quantum computing,
- quantum communication,
- quantum cryptography,
- quantum sensing,
- spectroscopy,
- atomic and optical physics,
- condensed-matter experiments,
- quantum state tomography,
- quantum error correction,
- experimental calibration,
- quantum control.

In quantum computing, measurements convert quantum information into classical outcomes. The choice of measurement basis determines which information is extracted.

In quantum sensing, measurement statistics are used to estimate physical parameters.

In quantum communication, measurement determines how quantum information is converted into classical information and how communication protocols behave under noise or eavesdropping.

In experimental physics, measurement models connect mathematical quantum states to real detector records.

## Projective measurements, POVMs, and Kraus operators

The three descriptions have different roles.

| Formalism | Main object | Outcome probability | State update |
|---|---|---|---|
| Projective measurement | Projectors \(P_m\) | \(\operatorname{Tr}(\rho P_m)\) | \(P_m\rho P_m/p_m\) |
| POVM | Effects \(E_m\) | \(\operatorname{Tr}(\rho E_m)\) | Not fixed by effects alone |
| Measurement operators | \(M_m\) | \(\operatorname{Tr}(M_m\rho M_m^\dagger)\) | \(M_m\rho M_m^\dagger/p_m\) |

Projective measurements are a special case of generalized measurements.

The measurement-operator description is more informative about physical back-action because it specifies how each outcome transforms the state.

## Important mathematical relationships

The main relationships demonstrated by the script can be organized as follows.

### State normalization

\[
\langle\psi|\psi\rangle=1.
\]

### Projector

\[
P=|\phi\rangle\langle\phi|.
\]

### Projector probability

\[
p=\langle\psi|P|\psi\rangle.
\]

### Born rule for a density matrix

\[
p=\operatorname{Tr}(\rho P).
\]

### Expectation value

\[
\langle A\rangle
=
\langle\psi|A|\psi\rangle
\]

or

\[
\langle A\rangle
=
\operatorname{Tr}(\rho A).
\]

### Projective conditional update

\[
|\psi\rangle
\rightarrow
\frac{P|\psi\rangle}
{\sqrt{\langle\psi|P|\psi\rangle}}.
\]

### Lüders density-matrix update

\[
\rho
\rightarrow
\frac{P\rho P}
{\operatorname{Tr}(P\rho)}.
\]

### POVM probability

\[
p_m=\operatorname{Tr}(\rho E_m).
\]

### Measurement-operator probability

\[
p_m
=
\operatorname{Tr}
(M_m\rho M_m^\dagger).
\]

### Measurement-operator state update

\[
\rho_m
=
\frac{M_m\rho M_m^\dagger}{p_m}.
\]

### Nonselective projective measurement

\[
\rho'
=
\sum_mP_m\rho P_m.
\]

### Commutator

\[
[A,B]=AB-BA.
\]

### Variance

\[
(\Delta A)^2
=
\langle A^2\rangle-\langle A\rangle^2.
\]

### Robertson uncertainty relation

\[
\Delta A\Delta B
\ge
\frac12|\langle[A,B]\rangle|.
\]

## Interpretation of collapse

The word "collapse" can refer to several layers of discussion, so precise language is useful.

At the mathematical level used here, collapse means that after an observed measurement outcome, the state is updated to the conditional state associated with that outcome.

For a projective measurement,

\[
\rho_a
=
\frac{P_a\rho P_a}
{\operatorname{Tr}(P_a\rho)}.
\]

The formalism itself does not require the software implementation to assume a particular philosophical interpretation of quantum mechanics.

The computationally important fact is that the state used to calculate future probabilities is conditioned on the measurement record.

## Production considerations

A production measurement-analysis system should not rely on the educational matrix implementation for large numerical workloads.

Important engineering considerations include:

- numerically stable linear algebra,
- efficient storage,
- sparse or structured representations,
- reproducible experiment metadata,
- measurement calibration,
- uncertainty estimation,
- validation of probability distributions,
- error models,
- detector characterization,
- data integrity,
- access control,
- auditability,
- appropriate random-number generation,
- separation of simulation from physical measurement data.

For experimental systems, the measurement model should be documented alongside calibration information so that theoretical probabilities, detector outputs, and corrected estimates are not conflated.

## Scope and limitations

The script focuses primarily on finite-dimensional quantum systems, especially qubits and small matrices.

It does not attempt to provide a full treatment of:

- infinite-dimensional Hilbert spaces,
- continuous-variable measurement theory,
- relativistic quantum field theory,
- complete quantum detector modeling,
- stochastic master equations,
- continuous-time measurement,
- full quantum tomography,
- measurement-based quantum computation,
- detailed laboratory hardware,
- interpretation-specific claims about the measurement problem.

The finite-dimensional formalism nevertheless captures the core mathematical structure of observables, probabilities, projective measurements, state updates, generalized measurements, and measurement-induced disturbance.

The resulting examples provide a concrete computational foundation for understanding how quantum states become experimentally meaningful probability distributions through measurement.
