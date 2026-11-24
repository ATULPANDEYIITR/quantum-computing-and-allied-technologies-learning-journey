# Quantum Kernels: Kernel Methods with Quantum Circuits

## 1. Technical Scope

Quantum kernels combine quantum feature maps with classical kernel-based machine learning.

A conventional machine learning model transforms observations into a feature representation and uses similarities between observations to construct a kernel matrix.

A quantum kernel follows the same mathematical principle, but the feature representation is encoded into a quantum state using a parameterized quantum circuit.

For an input vector \(x\), a quantum feature map prepares:

\[
|\phi(x)\rangle = U_{\phi}(x)|0\rangle^{\otimes n}
\]

where:

- \(x\) is the classical input vector.
- \(n\) is the number of qubits.
- \(U_{\phi}(x)\) is the data-dependent quantum circuit.
- \(|0\rangle^{\otimes n}\) is the initial computational basis state.

The quantum fidelity kernel is:

\[
\boxed{
K(x,z)=|\langle\phi(x)|\phi(z)\rangle|^2
}
\]

It measures the similarity between two quantum feature representations.

The resulting kernel matrix can be used with conventional machine learning algorithms, including support vector machines and kernel ridge regression.

The six deliverables implement a complete educational workflow covering quantum circuit simulation, feature encoding, kernel construction, numerical validation, classification and experiment management.

## 2. Quantum Feature Maps

### 2.1 Classical and quantum feature representations

A classical feature map may transform an observation into a higher-dimensional representation:

\[
x \rightarrow \Phi(x)
\]

A quantum feature map instead transforms the observation into a quantum state:

\[
x \rightarrow |\phi(x)\rangle
\]

The quantum state is represented by complex probability amplitudes.

For \(n\) qubits, a pure state has the representation:

\[
|\psi\rangle =
\sum_{i=0}^{2^n-1}\alpha_i|i\rangle
\]

The amplitudes satisfy:

\[
\sum_{i=0}^{2^n-1}|\alpha_i|^2=1
\]

The number of amplitudes grows exponentially with the qubit count.

The Python, JavaScript, C++17 and Java 17 implementations use dense state-vector simulation.

### 2.2 Implemented circuit architecture

The implementations use the following feature-map sequence:

1. Initialize all qubits in the zero state.
2. Apply Hadamard gates.
3. Apply data-dependent Z rotations.
4. Apply data-dependent X rotations.
5. Apply controlled-Z entangling gates.

The circuit can be represented as:

```text
|0> ── H ── RZ(2x₀) ── RX(2x₀) ── CZ ──
                                      |
|0> ── H ── RZ(2x₁) ── RX(2x₁) ──────
