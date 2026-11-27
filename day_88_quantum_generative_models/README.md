# Quantum Generative Models: Quantum Generative Learning

## 1. Introduction

Quantum generative models use quantum circuits and quantum probability distributions to learn the statistical structure of data and generate new samples.

Classical generative models approximate a target probability distribution using parameterized mathematical functions. Quantum generative models use quantum states, unitary transformations, and measurement outcomes to construct probability distributions.

A quantum generative model typically contains:

1. A quantum state initialization mechanism.
2. A parameterized quantum circuit.
3. An entanglement structure.
4. A measurement process.
5. A probability distribution derived from measurement outcomes.
6. An optimization procedure that adjusts circuit parameters.
7. An evaluation mechanism for comparing generated and target distributions.

The five implementations develop these concepts from statevector simulation to experiment management and relational data governance.

## 2. Mathematical Foundations

### 2.1 Quantum states

An n-qubit system has a computational basis containing \(2^n\) basis states.

A pure quantum state is represented as:

\[
|\psi\rangle =
\sum_{x=0}^{2^n-1}\alpha_x|x\rangle
\]

Where:

- \(n\) is the number of qubits.
- \(|x\rangle\) is a computational basis state.
- \(\alpha_x\) is a complex probability amplitude.

The amplitudes satisfy the normalization condition:

\[
\sum_{x=0}^{2^n-1}|\alpha_x|^2=1
\]

The probability of observing outcome \(x\) is given by the Born rule:

\[
P(x)=|\alpha_x|^2
\]

A measurement converts a quantum state into a classical outcome. Repeated measurements produce empirical frequency estimates of the underlying quantum probability distribution.

### 2.2 Unitary transformations

Quantum circuits transform an initial state through unitary operators.

\[
|\psi_{\theta}\rangle=U(\theta)|0\rangle^{\otimes n}
\]

Here, \(U(\theta)\) represents a parameterized quantum circuit and \(\theta\) denotes its trainable parameters.

Unitary transformations preserve quantum-state normalization.

The implementations use rotation gates and controlled-NOT operations to construct a small parameterized circuit.

### 2.3 Rotation around the Y-axis

The Y-axis rotation gate is:

\[
R_y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

It changes the amplitudes associated with the selected qubit.

The rotation angle is a trainable parameter. Optimizing these angles changes the probability distribution produced by the circuit.

### 2.4 Entanglement

Entanglement describes quantum correlations that cannot generally be represented as independent quantum states of individual subsystems.

The controlled-NOT gate performs a conditional bit flip:

\[
|a,b\rangle\rightarrow|a,a\oplus b\rangle
\]

The first qubit is the control and the second is the target.

Entangling gates allow quantum generative models to represent correlations between variables.

The implemented circuit uses a chain of CNOT gates connecting adjacent qubits.

## 3. Quantum Generative Learning

### 3.1 Quantum Born machines

A quantum Born machine represents a probability distribution using the squared magnitudes of quantum-state amplitudes.

\[
P_{\theta}(x)=
|\langle x|U(\theta)|0\rangle^{\otimes n}|^2
\]

This is known as a Born probability model.

The model learns parameters that make its generated distribution approximate a target distribution.

The principal distinction from a conventional classical generative model is the use of quantum amplitudes and measurement probabilities as the distribution-generating mechanism.

### 3.2 Training objective

The implementations use Kullback-Leibler divergence.

\[
D_{KL}(P\|Q)=
\sum_x P(x)\log\frac{P(x)}{Q(x)}
\]

Where:

- \(P(x)\) is the target probability.
- \(Q(x)\) is the generated probability.
- \(D_{KL}\) measures the difference between the distributions.

A lower divergence indicates a closer approximation under this objective.

The implementation assigns zero contribution to target outcomes with zero probability and applies a small numerical floor to generated probabilities.

KL divergence is asymmetric:

\[
D_{KL}(P\|Q)\neq D_{KL}(Q\|P)
\]

Consequently, selecting the direction of divergence is an important modeling decision.

### 3.3 SPSA optimization

Simultaneous Perturbation Stochastic Approximation (SPSA) estimates gradients using two perturbed objective evaluations.

For parameter vector \(\theta\), generate a random perturbation vector:

\[
\Delta_k=
(\Delta_{k,1},\ldots,\Delta_{k,d})
\]

Each component is independently selected from:

\[
\Delta_{k,i}\in\{-1,+1\}
\]

Evaluate:

\[
L_+=L(\theta_k+c_k\Delta_k)
\]

\[
L_-=L(\theta_k-c_k\Delta_k)
\]

The approximate gradient is:

\[
\hat{g}_{k,i}=
\frac{L_+-L_-}{2c_k\Delta_{k,i}}
\]

Update the parameters:

\[
\theta_{k+1}=\theta_k-a_k\hat{g}_k
\]

The learning-rate and perturbation schedules decrease over time.

SPSA is useful when evaluating an objective is expensive because it requires two objective evaluations per iteration regardless of parameter count.

It is a stochastic approximation, not an exact gradient calculation.

## 4. Quantum Circuit Architecture

The Python, JavaScript, C++17, and Java 17 implementations use the same two-layer architecture.

```text
Initial state |00>
       |
       v
RY(theta0) on qubit 0
RY(theta1) on qubit 1
       |
       v
CNOT(0 -> 1)
       |
       v
RY(theta2) on qubit 0
RY(theta3) on qubit 1
       |
       v
Measurement
       |
       v
Born probability distribution
       |
       v
Generated binary samples
