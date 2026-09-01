#!/usr/bin/env python3
"""
Quantum Computing for Complete Beginners
=========================================

A long, beginner-friendly, terminal-based teaching program that explains:

1. What computing is
2. Classical computers and bits
3. What quantum computing is
4. Qubits
5. Superposition
6. Measurement
7. Entanglement
8. Quantum interference
9. Quantum gates
10. Quantum circuits
11. Classical vs quantum computing
12. Why quantum computers are NOT simply "faster computers"
13. Realistic and potential use cases
14. Current limitations
15. A tiny simulated quantum-style example
16. A beginner quiz and recap

The program intentionally avoids heavy mathematics. It is designed so that a
person with little or no technical background can run it and learn the ideas
through analogies, demonstrations, questions, and simple simulations.

Run:
    python quantum_computing_layman_explainer.py

No third-party packages are required.
"""

from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------

USE_PAUSE = True
FAST_MODE = False


def clear_screen() -> None:
    """Clear the terminal screen in a cross-platform way."""
    print("\033[2J\033[H", end="")


def slow_print(text: str, delay: float = 0.008) -> None:
    """Print text slowly for a presentation-like experience."""
    if FAST_MODE:
        print(text)
        return

    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def pause(message: str = "\nPress Enter to continue...") -> None:
    """Pause between lessons unless pauses are disabled."""
    if USE_PAUSE:
        input(message)


def title(text: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {text}")
    print("=" * 78)


def section(text: str) -> None:
    print("\n" + "-" * 78)
    print(f"  {text}")
    print("-" * 78)


def bullet(text: str) -> None:
    print(f"  • {text}")


def numbered(number: int, text: str) -> None:
    print(f"  {number}. {text}")


def explain_term(term: str, meaning: str) -> None:
    print(f"\n  {term.upper()}")
    print(f"  {meaning}")


def choose(prompt: str, options: Dict[str, str]) -> str:
    """Ask the user to select one of the supplied options."""
    print(f"\n{prompt}")
    for key, label in options.items():
        print(f"  [{key}] {label}")

    while True:
        answer = input("\nYour choice: ").strip().lower()
        if answer in options:
            return answer
        print("Please choose one of the displayed options.")


# ---------------------------------------------------------------------------
# Core concepts
# ---------------------------------------------------------------------------

def lesson_what_is_computing() -> None:
    title("LESSON 1 — What Is Computing?")

    slow_print(
        "Before understanding quantum computing, forget the word 'quantum' for "
        "a moment. Let's understand an ordinary computer."
    )

    section("A computer is fundamentally a machine for manipulating information")

    bullet("You give a computer information.")
    bullet("The computer follows instructions.")
    bullet("It transforms information.")
    bullet("It gives you a result.")

    print(
        """
  Imagine a recipe:

      Ingredients → Instructions → Finished meal

  A computer works in a similar conceptual way:

      Data → Instructions → Result

  For example:

      10 + 20 → computer follows addition instructions → 30
    """
    )

    explain_term(
        "Algorithm",
        "A step-by-step method for solving a problem."
    )

    explain_term(
        "Data",
        "Information that a computer stores, processes, or communicates."
    )

    explain_term(
        "Processor",
        "The hardware that performs computational operations."
    )

    pause()


def lesson_classical_bits() -> None:
    title("LESSON 2 — Classical Computers and Bits")

    slow_print(
        "A normal computer represents information using something called a bit."
    )

    section("What is a bit?")

    print(
        """
  A bit has two possible values:

                  ┌─────────────┐
                  │     BIT     │
                  └──────┬──────┘
                         │
                  ┌──────┴──────┐
                  │             │
                 0             1

  You can think of it as:

      OFF / ON
      NO  / YES
      FALSE / TRUE
      LOW / HIGH
    """
    )

    explain_term(
        "Bit",
        "The basic unit of classical digital information. It can represent 0 or 1."
    )

    section("Many bits can represent many things")

    print(
        """
  One bit:
      0 or 1

  Two bits:
      00, 01, 10, 11

  Three bits:
      000, 001, 010, 011, 100, 101, 110, 111

  Eight bits:
      256 possible combinations.

  This is how computers can encode numbers, letters, images, audio,
  instructions, and much more.
    """
    )

    pause()


def lesson_quantum_intro() -> None:
    title("LESSON 3 — So What Is Quantum Computing?")

    slow_print(
        "Quantum computing is a different way of processing information. "
        "Instead of using only classical bits, it uses quantum bits, called qubits."
    )

    print(
        """
  Classical computer:

      BIT
       │
       ├── 0
       └── 1

  Quantum computer:

      QUBIT
        │
        ├── quantum state involving 0
        ├── quantum state involving 1
        └── potentially a combination of both before measurement

  The important phrase is:

      "before measurement"

  A qubit is not simply a normal bit that is magically both 0 and 1
  in the everyday sense. Its state is described by quantum mechanics,
  using probabilities/amplitudes, and measurement produces a classical
  outcome.
    """
    )

    explain_term(
        "Qubit",
        "A quantum system used as the basic unit of quantum information."
    )

    section("Where does the quantum part come from?")

    bullet("Quantum computers exploit physical behavior described by quantum mechanics.")
    bullet("Important concepts include superposition, entanglement, and interference.")
    bullet("Quantum algorithms manipulate these properties using quantum operations.")
    bullet("When we measure a quantum system, we obtain classical information.")

    pause()


# ---------------------------------------------------------------------------
# Analogies and demonstrations
# ---------------------------------------------------------------------------

def lesson_superposition() -> None:
    title("LESSON 4 — Superposition")

    slow_print(
        "Superposition is one of the first ideas people hear about in quantum computing."
    )

    section("A beginner-friendly mental model")

    print(
        """
  Imagine a spinning coin.

        While lying flat:

             HEADS

        or

             TAILS

  While spinning, the coin has not yet settled into one visible result.

  A quantum state is much more subtle than a spinning coin, so this is only
  an analogy. But it helps explain why a qubit cannot always be described
  as simply "0" or "1" before measurement.
    """
    )

    explain_term(
        "Superposition",
        "A quantum system can be in a combination of possible states, represented "
        "by amplitudes, until measurement."
    )

    section("Important correction")

    bullet("Superposition does NOT mean a quantum computer tries every answer and automatically reads all answers.")
    bullet("Measurement gives a classical result.")
    bullet("Quantum algorithms are designed so that useful answers become more likely.")
    bullet("The advantage comes from carefully controlling amplitudes and interference.")

    section("Tiny probability demonstration")

    probabilities = [0.25, 0.75]
    outcomes = ["0", "1"]
    counts = {"0": 0, "1": 0}

    for _ in range(1000):
        r = random.random()
        if r < probabilities[0]:
            counts["0"] += 1
        else:
            counts["1"] += 1

    print(
        f"""
  Suppose a hypothetical qubit measurement has:

      P(0) = 25%
      P(1) = 75%

  After 1000 simulated measurements, we might see approximately:

      0 → {counts["0"]} times
      1 → {counts["1"]} times

  The exact numbers change each time because the process is probabilistic.
    """
    )

    pause()


def lesson_measurement() -> None:
    title("LESSON 5 — Measurement")

    slow_print(
        "Measurement is how a quantum system produces a classical result."
    )

    print(
        """
  Think of a hidden quantum state:

       QUANTUM STATE
             │
             ▼
         MEASUREMENT
             │
             ▼
       CLASSICAL RESULT

           0 or 1

  Before measurement, the state may be represented as a combination of
  possibilities.

  After measurement, you receive a definite classical outcome for that
  measurement.
    """
    )

    section("Why this matters")

    bullet("Quantum algorithms cannot simply expose every possible state to us.")
    bullet("The algorithm must manipulate the quantum state before measurement.")
    bullet("Good algorithms increase the probability of useful outcomes.")
    bullet("Repeated measurements can reveal the probability distribution.")

    pause()


def lesson_entanglement() -> None:
    title("LESSON 6 — Entanglement")

    slow_print(
        "Entanglement is another important quantum phenomenon."
    )

    print(
        """
  Imagine two quantum systems prepared in a special shared state.

       QUBIT A  ═══════════ QUBIT B
                    │
              shared quantum
                  state

  The measurement outcomes can show correlations that cannot be explained
  simply by saying that each object independently carried a pre-written
  classical answer.

  This is one reason quantum information is so different from ordinary
  information.
    """
    )

    explain_term(
        "Entanglement",
        "A quantum relationship in which the joint state of multiple systems "
        "cannot be described as independent states for each system."
    )

    section("Common misconception")

    bullet("Entanglement is NOT a faster-than-light messaging system.")
    bullet("It does not let us send ordinary information instantaneously.")
    bullet("It is a resource used by quantum protocols and algorithms.")

    pause()


def lesson_interference() -> None:
    title("LESSON 7 — Quantum Interference")

    slow_print(
        "If superposition is about combining possibilities, interference is "
        "about how those possibilities can reinforce or cancel one another."
    )

    print(
        """
  A useful analogy is waves.

      Wave A:       /\\      /\\
                   /  \\    /  \\

      Wave B:       /\\      /\\

  If waves line up, they can reinforce each other.

      constructive interference → stronger

  If they oppose each other, they can cancel.

      destructive interference → weaker

  Quantum amplitudes can behave in an analogous mathematical way.
    """
    )

    section("Why quantum algorithms care")

    bullet("An algorithm can create paths associated with many possible outcomes.")
    bullet("Interference can suppress undesirable outcomes.")
    bullet("Interference can amplify desirable outcomes.")
    bullet("This is a central part of how quantum speedups can emerge.")

    pause()


# ---------------------------------------------------------------------------
# Quantum gates and circuits
# ---------------------------------------------------------------------------

@dataclass
class QubitState:
    """Very small educational representation of a single-qubit state."""

    alpha: float = 1.0  # amplitude for |0>
    beta: float = 0.0   # amplitude for |1>

    def probabilities(self) -> Tuple[float, float]:
        p0 = self.alpha ** 2
        p1 = self.beta ** 2
        total = p0 + p1

        if total == 0:
            return 0.5, 0.5

        return p0 / total, p1 / total

    def describe(self) -> str:
        p0, p1 = self.probabilities()
        return (
            f"State ≈ {self.alpha:.3f}|0⟩ + {self.beta:.3f}|1⟩\n"
            f"Probability of measuring 0 ≈ {p0:.1%}\n"
            f"Probability of measuring 1 ≈ {p1:.1%}"
        )


def gate_hadamard(state: QubitState) -> QubitState:
    """Educational Hadamard transform for a real-valued state."""
    factor = 1 / math.sqrt(2)
    return QubitState(
        alpha=factor * (state.alpha + state.beta),
        beta=factor * (state.alpha - state.beta),
    )


def gate_x(state: QubitState) -> QubitState:
    """Educational X gate: swaps |0> and |1> amplitudes."""
    return QubitState(alpha=state.beta, beta=state.alpha)


def gate_z(state: QubitState) -> QubitState:
    """Educational Z gate: changes the phase/sign of |1>."""
    return QubitState(alpha=state.alpha, beta=-state.beta)


def lesson_quantum_gates() -> None:
    title("LESSON 8 — Quantum Gates")

    slow_print(
        "Quantum computers do not normally manipulate qubits by saying "
        "'set this qubit to 1' in the same way a classical program sets a variable."
    )

    section("Think of gates as controlled transformations")

    print(
        """
  Classical analogy:

      input → operation → output

      5 → add 3 → 8

  Quantum analogy:

      quantum state → quantum gate → new quantum state

  Gates transform the amplitudes and relationships in the quantum state.
    """
    )

    explain_term(
        "Quantum gate",
        "A reversible mathematical operation that changes a quantum state."
    )

    section("Three famous beginner gates")

    print(
        """
  X gate
  -------
  Roughly analogous to a NOT operation for a computational basis state:

      |0⟩ → |1⟩
      |1⟩ → |0⟩


  H gate (Hadamard)
  -----------------
  Creates useful superpositions.

      |0⟩ → approximately equal combination of |0⟩ and |1⟩


  Z gate
  -------
  Changes the phase/sign relationship of components of the state.
  This becomes important when interference is used.
    """
    )

    state = QubitState()
    print("\n  Starting state:")
    print("  " + state.describe().replace("\n", "\n  "))

    state = gate_hadamard(state)
    print("\n  After H gate:")
    print("  " + state.describe().replace("\n", "\n  "))

    state = gate_z(state)
    print("\n  After Z gate:")
    print("  " + state.describe().replace("\n", "\n  "))

    state = gate_x(state)
    print("\n  After X gate:")
    print("  " + state.describe().replace("\n", "\n  "))

    pause()


def lesson_quantum_circuit() -> None:
    title("LESSON 9 — Quantum Circuits")

    slow_print(
        "A quantum circuit is a sequence of operations performed on qubits."
    )

    print(
        """
  A very simplified picture:

      q0: ──H────X────M──
                 │
      q1: ───────●────M──

      H = Hadamard gate
      X = X gate
      ● = part of a controlled operation
      M = measurement

  The exact meaning of the circuit depends on the gates and the quantum
  state being processed.

  You can think of a circuit as a recipe:

      Prepare → Transform → Interact → Transform → Measure
    """
    )

    explain_term(
        "Quantum circuit",
        "A structured sequence of quantum operations applied to qubits."
    )

    section("Why circuit depth matters")

    bullet("Real quantum hardware is noisy.")
    bullet("Quantum states can lose useful information through decoherence.")
    bullet("More operations can create more opportunities for errors.")
    bullet("Therefore, practical algorithms care about gate count, circuit depth, and hardware connectivity.")

    pause()


# ---------------------------------------------------------------------------
# Classical vs quantum comparison
# ---------------------------------------------------------------------------

def classical_vs_quantum_table() -> None:
    title("LESSON 10 — Classical vs Quantum Computing")

    rows = [
        ("Basic information unit", "Bit", "Qubit"),
        ("Typical basis states", "0 or 1", "Quantum state involving |0⟩ and |1⟩"),
        ("Main physical framework", "Classical physics / electronics", "Quantum mechanics"),
        ("Core operations", "Logic and arithmetic operations", "Quantum gates / circuits"),
        ("Measurement", "Reads classical state", "Produces a classical outcome from a quantum state"),
        ("Special phenomena", "No quantum entanglement required", "Superposition, entanglement, interference"),
        ("Hardware examples", "CPUs, GPUs, microcontrollers", "Superconducting circuits, trapped ions, photonic systems, etc."),
        ("Noise tolerance", "Modern digital systems are highly robust", "Quantum systems are generally sensitive to noise"),
        ("Best general use", "Everyday computing", "Specific problems where quantum algorithms can offer advantages"),
    ]

    headers = ("Category", "Classical", "Quantum")
    widths = (25, 24, 28)

    print()
    print("  " + " | ".join(
        headers[i].ljust(widths[i]) for i in range(3)
    ))
    print("  " + "-+-".join("-" * w for w in widths))

    for category, classical, quantum in rows:
        print(
            "  "
            + " | ".join(
                [
                    category.ljust(widths[0]),
                    classical.ljust(widths[1]),
                    quantum.ljust(widths[2]),
                ]
            )
        )

    print(
        """
  Key takeaway:

  Quantum computers are not replacements for ordinary computers in general.

  A future computing environment is more likely to look like:

      Classical computers
             +
      GPUs / accelerators
             +
      Quantum processors
             +
      Specialized hardware

  Each type handles the tasks it is good at.
    """
    )

    pause()


# ---------------------------------------------------------------------------
# Quantum advantage and misconceptions
# ---------------------------------------------------------------------------

def lesson_not_magic() -> None:
    title("LESSON 11 — Quantum Computers Are Not Magic")

    section("Myth 1: 'A quantum computer is faster at everything.'")

    print(
        """
  FALSE.

  Quantum computers are expected to provide advantages for particular
  problem classes and algorithms.

  For many ordinary tasks, a classical computer remains the practical choice.
    """
    )

    section("Myth 2: 'A quantum computer tries every answer simultaneously and reads them all.'")

    print(
        """
  MISLEADING.

  Quantum states can contain amplitudes associated with many basis states,
  but measurement does not return every state.

  The algorithm must use interference to increase the chance of obtaining
  useful results.
    """
    )

    section("Myth 3: 'More qubits automatically means a better computer.'")

    print(
        """
  NOT NECESSARILY.

  Useful quantum computing depends on more than qubit count:

      qubit quality
      gate fidelity
      connectivity
      coherence
      error rates
      error correction
      circuit depth
      software and algorithms
      ability to scale the system
    """
    )

    section("Myth 4: 'Quantum computers will replace laptops.'")

    print(
        """
  Not in the foreseeable general sense.

  A laptop is excellent for browsing, documents, software development,
  media, databases, and thousands of everyday tasks.

  Quantum processors are specialized computational resources.
    """
    )

    pause()


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------

def use_case_cryptography() -> None:
    section("1. Cryptography and cybersecurity")

    print(
        """
  Some quantum algorithms have major implications for public-key
  cryptography.

  The most famous example is Shor's algorithm, which can efficiently solve
  certain mathematical problems that underpin widely used public-key
  cryptographic systems when run on a sufficiently large, fault-tolerant
  quantum computer.

  This is why organizations are preparing for post-quantum cryptography.

  Important:
      The existence of today's quantum hardware does NOT mean that all
      current encryption can suddenly be broken.
    """
    )


def use_case_chemistry() -> None:
    section("2. Chemistry and molecular simulation")

    print(
        """
  Nature itself is quantum mechanical.

  Molecules involve quantum behavior, so quantum computers are being studied
  as potential tools for simulating molecular and material systems.

  Potential applications include:

      • drug discovery research
      • catalyst design
      • battery materials
      • superconducting materials
      • chemical reactions
      • energy technologies

  The long-term promise is not 'the quantum computer knows every molecule.'
  The goal is to simulate useful quantum systems more naturally than a
  classical machine can in some cases.
    """
    )


def use_case_optimization() -> None:
    section("3. Optimization")

    print(
        """
  Optimization means finding a good solution among many possible choices.

  Examples:

      • delivery routes
      • scheduling
      • portfolio construction
      • supply chains
      • manufacturing
      • resource allocation

  Quantum optimization methods are actively researched, but this area needs
  careful benchmarking. A quantum approach is not automatically better than
  the best classical optimization method.
    """
    )


def use_case_machine_learning() -> None:
    section("4. Machine learning")

    print(
        """
  Quantum machine learning explores whether quantum circuits can help with
  selected learning tasks.

  Possible research areas include:

      • quantum-enhanced feature representations
      • variational quantum algorithms
      • quantum kernels
      • hybrid quantum-classical models

  Today, most practical machine learning is overwhelmingly classical and
  uses CPUs, GPUs, and specialized accelerators.
    """
    )


def use_case_finance() -> None:
    section("5. Finance")

    print(
        """
  Finance has mathematical problems involving optimization, simulation,
  and risk.

  Researchers investigate quantum approaches for:

      • portfolio optimization
      • option pricing
      • risk analysis
      • Monte Carlo acceleration

  These are promising research areas, not a claim that quantum computers
  currently outperform classical finance infrastructure broadly.
    """
    )


def use_case_search() -> None:
    section("6. Search and structured problem solving")

    print(
        """
  Grover's algorithm provides a famous example of a quantum speedup for
  unstructured search.

  In simplified terms:

      classical search → roughly proportional to N checks
      Grover-style search → roughly proportional to √N quantum iterations

  This is a quadratic speedup, not 'infinite speed.'

  The algorithm also requires a suitable quantum implementation of the
  problem and a way to verify the answer.
    """
    )


def use_case_science() -> None:
    section("7. Scientific computing")

    print(
        """
  Quantum computing is being investigated across physics, materials
  science, chemistry, and other scientific fields.

  The broad idea is:

      difficult quantum system
               ↓
      encode relevant information
               ↓
      manipulate with quantum operations
               ↓
      measure useful quantities

  The difficult part is building a reliable quantum simulation that gives
  a meaningful advantage over classical techniques.
    """
    )


def lesson_use_cases() -> None:
    title("LESSON 12 — Where Could Quantum Computing Be Used?")

    slow_print(
        "Quantum computing is most exciting when the structure of a problem "
        "matches what quantum algorithms can exploit."
    )

    use_case_cryptography()
    use_case_chemistry()
    use_case_optimization()
    use_case_machine_learning()
    use_case_finance()
    use_case_search()
    use_case_science()

    pause()


# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------

def lesson_limitations() -> None:
    title("LESSON 13 — Why Don't We Use Quantum Computers Everywhere Yet?")

    section("1. Quantum states are fragile")

    bullet("Environmental noise can disturb quantum information.")
    bullet("Interactions with the environment can cause decoherence.")
    bullet("Hardware needs careful engineering and control.")

    section("2. Error correction is difficult")

    bullet("Quantum errors are different from ordinary bit flips.")
    bullet("Useful fault-tolerant quantum computing requires substantial overhead.")
    bullet("Building reliable logical qubits from noisy physical qubits is a major engineering challenge.")

    section("3. Hardware is specialized")

    bullet("Different platforms use different physical technologies.")
    bullet("Many systems require sophisticated control electronics and/or extreme environments.")
    bullet("Scaling while maintaining quality is difficult.")

    section("4. Algorithms are specialized")

    bullet("Only certain problems are expected to benefit significantly.")
    bullet("Finding a quantum formulation of a real-world problem can be hard.")
    bullet("Classical algorithms continue to improve.")

    section("5. Data loading can matter")

    print(
        """
  A quantum algorithm may have a beautiful theoretical speedup, but if the
  real workflow requires expensive conversion of a huge classical dataset
  into a quantum state, the practical benefit may disappear.

  Therefore:

      theoretical speedup ≠ automatic real-world speedup
    """
    )

    pause()


# ---------------------------------------------------------------------------
# Tiny simulations
# ---------------------------------------------------------------------------

def simulate_measurements(probability_one: float, shots: int = 1000) -> Tuple[int, int]:
    """Simulate repeated measurement of a single qubit."""
    ones = 0
    zeros = 0

    for _ in range(shots):
        if random.random() < probability_one:
            ones += 1
        else:
            zeros += 1

    return zeros, ones


def lesson_probability_simulation() -> None:
    title("LESSON 14 — Hands-On Simulation: Repeated Measurements")

    print(
        """
  We will simulate a hypothetical qubit where:

      P(0) = 50%
      P(1) = 50%

  We are NOT building a real quantum computer here.

  We are simply using ordinary Python randomness to understand what repeated
  quantum measurements can look like statistically.
    """
    )

    shots = 1000
    zeros, ones = simulate_measurements(0.50, shots)

    print(f"\n  Number of simulated measurements: {shots}")
    print(f"  Result 0: {zeros}")
    print(f"  Result 1: {ones}")
    print(f"  Observed P(0): {zeros / shots:.1%}")
    print(f"  Observed P(1): {ones / shots:.1%}")

    print(
        """
  You should expect the numbers to be close to 50/50, but not exactly equal.

  This is similar to repeatedly flipping a fair coin. Randomness at the
  individual level can produce stable probabilities at the aggregate level.
    """
    )

    pause()


def lesson_bit_count() -> None:
    title("LESSON 15 — Why Qubits Get People Excited")

    print(
        """
  The number of basis states represented by n qubits is:

                         2^n

  Examples:

      1 qubit  → 2 basis states
      2 qubits → 4 basis states
      3 qubits → 8 basis states
      10 qubits → 1,024 basis states
      20 qubits → 1,048,576 basis states
      30 qubits → 1,073,741,824 basis states

  This exponential growth is one reason quantum systems can represent very
  large mathematical state spaces.

  BUT:

      "2^n possible basis states"
                does NOT mean
      "we get 2^n classical answers for free."

  Measurement and algorithm design are crucial.
    """
    )

    print("\n  Let's calculate 2^n for some values:")

    for n in range(1, 21):
        print(f"      {n:2d} qubits → {2 ** n:>12,} basis states")

    pause()


# ---------------------------------------------------------------------------
# Interactive analogy game
# ---------------------------------------------------------------------------

def lesson_analogy_game() -> None:
    title("LESSON 16 — Think Like a Quantum Computing Student")

    questions = [
        (
            "Which is the basic information unit of a classical digital computer?",
            ["Qubit", "Bit", "Photon", "Quantum gate"],
            1,
        ),
        (
            "Which is a quantum phenomenon used in quantum computing?",
            ["Superposition", "Spreadsheeting", "Pixel compression", "File indexing"],
            0,
        ),
        (
            "What happens when a qubit is measured?",
            [
                "It produces a classical outcome according to the quantum measurement rules",
                "It reveals every possible state at once",
                "It automatically becomes a faster CPU",
                "It sends information faster than light",
            ],
            0,
        ),
        (
            "Does more qubits automatically mean a better quantum computer?",
            ["Yes, always", "No", "Only for laptops", "Only for databases"],
            1,
        ),
        (
            "Which field is strongly connected to potential quantum simulation?",
            ["Chemistry", "Word processing", "Photo editing", "Keyboard design"],
            0,
        ),
    ]

    score = 0

    for number, (question, choices, correct) in enumerate(questions, start=1):
        print(f"\nQuestion {number}: {question}")

        for i, choice in enumerate(choices, start=1):
            print(f"  {i}. {choice}")

        while True:
            try:
                answer = int(input("Your answer: "))
                if 1 <= answer <= len(choices):
                    break
            except ValueError:
                pass
            print("Enter a valid option number.")

        if answer - 1 == correct:
            print("  ✓ Correct!")
            score += 1
        else:
            print(f"  ✗ Not quite. Correct answer: {choices[correct]}")

    print(f"\n  Final score: {score}/{len(questions)}")

    if score == len(questions):
        print("  Excellent. You have the core mental model.")
    elif score >= 3:
        print("  Good foundation. Review the lessons you found difficult.")
    else:
        print("  That's okay. Quantum computing takes time. Re-run the lessons and try again.")

    pause()


# ---------------------------------------------------------------------------
# Glossary
# ---------------------------------------------------------------------------

def lesson_glossary() -> None:
    title("LESSON 17 — Quantum Computing Glossary")

    terms = [
        ("Bit", "Classical information unit with two values, conventionally 0 or 1."),
        ("Qubit", "Quantum information unit represented by a quantum state."),
        ("Superposition", "A combination of basis states represented by quantum amplitudes."),
        ("Measurement", "Process that produces a classical outcome from a quantum state."),
        ("Entanglement", "A non-classical correlation represented by a joint quantum state."),
        ("Interference", "Combination of amplitudes that can reinforce or cancel outcomes."),
        ("Quantum gate", "A reversible operation that transforms quantum states."),
        ("Quantum circuit", "A sequence of quantum gates and measurements."),
        ("Coherence", "Maintenance of quantum phase relationships needed for computation."),
        ("Decoherence", "Loss of quantum coherence through interaction with the environment."),
        ("Noise", "Unwanted effects that disturb quantum computation."),
        ("Quantum algorithm", "An algorithm designed to exploit quantum computational principles."),
        ("Logical qubit", "An error-corrected qubit encoded using multiple physical qubits."),
        ("Fault tolerance", "A design approach intended to allow computation despite physical errors."),
        ("Quantum advantage", "A useful performance advantage over classical approaches for a defined task."),
        ("NISQ", "Noisy Intermediate-Scale Quantum; a term used for a class of pre-fault-tolerant quantum systems."),
    ]

    for term, definition in terms:
        print(f"\n  {term}")
        print(f"      {definition}")

    pause()


# ---------------------------------------------------------------------------
# Learning roadmap
# ---------------------------------------------------------------------------

def lesson_next_steps() -> None:
    title("LESSON 18 — What Should You Learn Next?")

    print(
        """
  If this program made sense, you are ready to move from "What is it?"
  toward "How does it actually work?"

  Suggested path:

      STEP 1
      Mathematics foundations
          ↓
      Complex numbers, vectors, matrices, probability

      STEP 2
      Quantum mechanics foundations
          ↓
      States, observables, measurement, operators

      STEP 3
      Quantum information
          ↓
      Qubits, Bloch sphere, density matrices

      STEP 4
      Quantum gates and circuits
          ↓
      X, Y, Z, H, S, T, CNOT, controlled gates

      STEP 5
      Algorithms
          ↓
      Deutsch-Jozsa
      Bernstein-Vazirani
      Grover
      Quantum Fourier Transform
      Shor
      Variational algorithms

      STEP 6
      Hardware
          ↓
      Superconducting
      Trapped-ion
      Photonic
      Neutral-atom
      Spin-based approaches

      STEP 7
      Error correction
          ↓
      Physical vs logical qubits
      Stabilizer codes
      Surface codes
      Fault tolerance

      STEP 8
      Programming
          ↓
      Build circuits with a quantum SDK
      Simulate circuits
      Run on cloud-accessible quantum hardware

      STEP 9
      Applications
          ↓
      Chemistry
      Optimization
      Cryptography
      Machine learning
      Scientific simulation
    """
    )

    pause()


# ---------------------------------------------------------------------------
# Final recap
# ---------------------------------------------------------------------------

def final_recap() -> None:
    title("FINAL RECAP — Explain Quantum Computing in 60 Seconds")

    print(
        """
  If someone asks you "What is quantum computing?", you can now say:

  "Quantum computing is a form of computation that uses quantum-mechanical
  systems to process information. Its basic unit is the qubit. Unlike a
  classical bit, a qubit is described by a quantum state that can involve
  a combination of basis states. Quantum algorithms use operations such as
  superposition, entanglement, and interference to solve certain problems
  in ways that can offer advantages over classical algorithms. Quantum
  computers are not faster for every task, and today's machines are limited
  by noise, error correction, hardware scaling, and the need for suitable
  algorithms."

  The three ideas to remember:

      1. Qubit
         Quantum information unit.

      2. Superposition
         Quantum states can be combinations of basis states.

      3. Interference
         Quantum amplitudes can reinforce useful outcomes and suppress others.

  And the most important practical idea:

      Quantum computing is a specialized form of computing,
      not a universal replacement for classical computers.
    """
    )

    print("\n  Congratulations — you completed the beginner lesson.")
    print("  Run the program again whenever you want to review the concepts.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

LESSONS: List[Tuple[str, Callable[[], None]]] = [
    ("What is computing?", lesson_what_is_computing),
    ("Classical computers and bits", lesson_classical_bits),
    ("What is quantum computing?", lesson_quantum_intro),
    ("Superposition", lesson_superposition),
    ("Measurement", lesson_measurement),
    ("Entanglement", lesson_entanglement),
    ("Quantum interference", lesson_interference),
    ("Quantum gates", lesson_quantum_gates),
    ("Quantum circuits", lesson_quantum_circuit),
    ("Classical vs quantum comparison", classical_vs_quantum_table),
    ("Quantum computers are not magic", lesson_not_magic),
    ("Quantum computing use cases", lesson_use_cases),
    ("Current limitations", lesson_limitations),
    ("Measurement simulation", lesson_probability_simulation),
    ("Why qubits get people excited", lesson_bit_count),
    ("Beginner quiz", lesson_analogy_game),
    ("Glossary", lesson_glossary),
    ("What to learn next", lesson_next_steps),
]


def print_banner() -> None:
    clear_screen()
    print(
        r"""
   ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗████████╗██╗   ██╗███╗   ███╗
  ██╔═══██╗██║   ██║██╔══██╗████╗  ██║╚══██╔══╝██║   ██║████╗ ████║
  ██║   ██║██║   ██║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██║▄▄ ██║██║   ██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║   ██║   ╚═██████╔╝██║ ╚═╝ ██║
   ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝

              QUANTUM COMPUTING — COMPLETE BEGINNER EXPLAINER

                  From bits → qubits → algorithms → use cases
        """
    )


def main_menu() -> None:
    global USE_PAUSE, FAST_MODE

    while True:
        print_banner()

        print("\n  MENU")
        print("  ----")
        print("  [1] Start complete beginner course")
        print("  [2] Browse individual lessons")
        print("  [3] Run the hands-on simulations")
        print("  [4] Take the beginner quiz")
        print("  [5] Show the glossary")
        print("  [6] Show the learning roadmap")
        print("  [7] Toggle fast mode")
        print("  [8] Toggle pauses")
        print("  [0] Exit")

        choice = input("\n  Select: ").strip()

        if choice == "1":
            for _, lesson in LESSONS:
                lesson()
            final_recap()

        elif choice == "2":
            clear_screen()
            print_banner()
            for i, (name, _) in enumerate(LESSONS, start=1):
                print(f"  [{i:02d}] {name}")

            print("  [0] Back")

            while True:
                raw = input("\n  Lesson number: ").strip()
                if raw == "0":
                    break

                try:
                    index = int(raw) - 1
                    if 0 <= index < len(LESSONS):
                        LESSONS[index][1]()
                        break
                except ValueError:
                    pass

                print("  Please enter a valid lesson number.")

        elif choice == "3":
            lesson_probability_simulation()
            lesson_bit_count()
            lesson_quantum_gates()

        elif choice == "4":
            lesson_analogy_game()

        elif choice == "5":
            lesson_glossary()

        elif choice == "6":
            lesson_next_steps()

        elif choice == "7":
            FAST_MODE = not FAST_MODE
            print(f"\n  Fast mode: {'ON' if FAST_MODE else 'OFF'}")
            time.sleep(1)

        elif choice == "8":
            USE_PAUSE = not USE_PAUSE
            print(f"\n  Pauses: {'ON' if USE_PAUSE else 'OFF'}")
            time.sleep(1)

        elif choice == "0":
            print("\n  Goodbye. Keep learning quantum computing! 🚀")
            break

        else:
            print("\n  Invalid choice.")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n  Program interrupted. Goodbye!")
        sys.exit(0)

