"""
Probability Basics: Probability Distributions and Measurement
==============================================================

A self-contained study script covering probability from absolute beginner
through advanced level, with executable demonstrations of:

1. Experiments, outcomes, sample spaces, and events
2. Classical, empirical, and subjective probability
3. Probability axioms and basic rules
4. Counting principles and combinatorics
5. Conditional probability and independence
6. Bayes' theorem
7. Random variables and probability mass functions
8. Discrete probability distributions
9. Continuous random variables and probability density functions
10. Cumulative distribution functions
11. Expectation, variance, standard deviation, covariance, and correlation
12. Bernoulli, Binomial, Geometric, Negative Binomial, Hypergeometric,
    Poisson, Uniform, Exponential, Normal, and related distributions
13. Joint, marginal, and conditional distributions
14. Law of total probability and law of total expectation
15. Transformations of random variables
16. Quantiles and percentile measurement
17. Standardization and z-scores
18. Sampling and Monte Carlo simulation
19. Law of Large Numbers and Central Limit Theorem demonstrations
20. Confidence intervals and measurement uncertainty
21. Maximum likelihood estimation
22. Simulation-based probability estimation
23. Numerical stability and implementation considerations
24. Edge cases, common mistakes, validation, and tests

Only the Python standard library is used.

Run:
    python probability_distributions_measurement.py
"""

from __future__ import annotations

import math
import random
import statistics
import unittest
from collections import Counter
from dataclasses import dataclass
from itertools import combinations, permutations, product
from typing import Callable, Iterable, Optional, Sequence


# ============================================================================
# SECTION 1: GENERAL DISPLAY AND VALIDATION UTILITIES
# ============================================================================

def section(title: str) -> None:
    """Print a visually distinct section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    """Print a subsection heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def approximately_equal(a: float, b: float, tolerance: float = 1e-9) -> bool:
    """Compare floating-point values using an absolute/relative tolerance."""
    return math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)


def validate_probability(probability: float, name: str = "probability") -> None:
    """
    Validate a probability.

    A probability must lie in the closed interval [0, 1].
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")


def validate_positive(value: float, name: str = "value") -> None:
    """Validate a strictly positive numeric parameter."""
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0.")


def validate_nonnegative(value: float, name: str = "value") -> None:
    """Validate a nonnegative numeric parameter."""
    if value < 0:
        raise ValueError(f"{name} must be nonnegative.")


# ============================================================================
# SECTION 2: FUNDAMENTAL PROBABILITY CONCEPTS
# ============================================================================

def probability_from_equally_likely_outcomes(
    favorable_outcomes: int,
    total_outcomes: int,
) -> float:
    """
    Classical probability:

        P(A) = number of favorable outcomes / total number of outcomes

    This formula is appropriate when the elementary outcomes are equally
    likely.
    """
    if total_outcomes <= 0:
        raise ValueError("total_outcomes must be positive.")
    if favorable_outcomes < 0 or favorable_outcomes > total_outcomes:
        raise ValueError("favorable_outcomes must be between 0 and total_outcomes.")
    return favorable_outcomes / total_outcomes


def empirical_probability(successes: int, trials: int) -> float:
    """
    Estimate probability from observed data:

        estimated P(A) = successes / trials
    """
    if trials <= 0:
        raise ValueError("trials must be positive.")
    if not 0 <= successes <= trials:
        raise ValueError("successes must be between 0 and trials.")
    return successes / trials


def event_complement(probability: float) -> float:
    """P(A^c) = 1 - P(A)."""
    validate_probability(probability)
    return 1.0 - probability


def event_union_probability(
    probability_a: float,
    probability_b: float,
    probability_intersection: float,
) -> float:
    """
    General addition rule:

        P(A union B) = P(A) + P(B) - P(A intersection B)
    """
    for value, name in [
        (probability_a, "probability_a"),
        (probability_b, "probability_b"),
        (probability_intersection, "probability_intersection"),
    ]:
        validate_probability(value, name)

    result = probability_a + probability_b - probability_intersection

    if not 0.0 <= result <= 1.0:
        raise ValueError("The supplied probabilities are inconsistent.")

    return result


def independent_intersection_probability(
    probability_a: float,
    probability_b: float,
) -> float:
    """
    For independent events:

        P(A intersection B) = P(A) * P(B)
    """
    validate_probability(probability_a, "probability_a")
    validate_probability(probability_b, "probability_b")
    return probability_a * probability_b


# ============================================================================
# SECTION 3: SAMPLE SPACES AND EVENTS
# ============================================================================

def dice_sample_space() -> set[int]:
    """Return the sample space for one standard six-sided die."""
    return set(range(1, 7))


def event_even_die() -> set[int]:
    """Event that a standard die produces an even number."""
    return {2, 4, 6}


def event_greater_than_four() -> set[int]:
    """Event that a standard die produces a value greater than four."""
    return {5, 6}


def event_intersection(event_a: set, event_b: set) -> set:
    """A intersection B."""
    return event_a & event_b


def event_union(event_a: set, event_b: set) -> set:
    """A union B."""
    return event_a | event_b


def event_complement_set(sample_space: set, event: set) -> set:
    """A^c relative to a specified sample space."""
    if not event.issubset(sample_space):
        raise ValueError("Event must be a subset of the sample space.")
    return sample_space - event


# ============================================================================
# SECTION 4: COUNTING AND COMBINATORICS
# ============================================================================

def factorial(n: int) -> int:
    """Compute n! for a nonnegative integer."""
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer.")
    return math.factorial(n)


def permutations_count(n: int, r: int) -> int:
    """
    Number of ordered selections:

        P(n, r) = n! / (n-r)!
    """
    if not isinstance(n, int) or not isinstance(r, int):
        raise TypeError("n and r must be integers.")
    if n < 0 or r < 0 or r > n:
        raise ValueError("Require n >= r >= 0.")
    return math.perm(n, r)


def combinations_count(n: int, r: int) -> int:
    """
    Number of unordered selections:

        C(n, r) = n! / [r!(n-r)!]
    """
    if not isinstance(n, int) or not isinstance(r, int):
        raise TypeError("n and r must be integers.")
    if n < 0 or r < 0 or r > n:
        raise ValueError("Require n >= r >= 0.")
    return math.comb(n, r)


def probability_exactly_k_successes(
    n: int,
    k: int,
    p: float,
) -> float:
    """
    Binomial probability:

        P(X=k) = C(n,k) p^k (1-p)^(n-k)
    """
    if n < 0 or k < 0 or k > n:
        raise ValueError("Require n >= k >= 0.")
    validate_probability(p, "p")

    return (
        combinations_count(n, k)
        * (p ** k)
        * ((1.0 - p) ** (n - k))
    )


# ============================================================================
# SECTION 5: CONDITIONAL PROBABILITY AND BAYES' THEOREM
# ============================================================================

def conditional_probability(
    probability_intersection: float,
    probability_condition: float,
) -> float:
    """
    Conditional probability:

        P(A | B) = P(A intersection B) / P(B)

    The condition must have nonzero probability.
    """
    validate_probability(probability_intersection, "probability_intersection")
    validate_probability(probability_condition, "probability_condition")

    if probability_condition == 0:
        raise ZeroDivisionError("Conditional probability is undefined when P(B)=0.")

    result = probability_intersection / probability_condition

    if not 0.0 <= result <= 1.0:
        raise ValueError("The supplied probabilities are inconsistent.")

    return result


def bayes_theorem(
    prior: float,
    likelihood: float,
    evidence_probability: float,
) -> float:
    """
    Bayes' theorem:

        P(H | E) = P(E | H) P(H) / P(E)

    where:
        H = hypothesis
        E = observed evidence
    """
    validate_probability(prior, "prior")
    validate_probability(likelihood, "likelihood")
    validate_probability(evidence_probability, "evidence_probability")

    if evidence_probability == 0:
        raise ZeroDivisionError("Posterior is undefined when P(E)=0.")

    posterior = likelihood * prior / evidence_probability

    if not 0.0 <= posterior <= 1.0:
        raise ValueError("Supplied probabilities are inconsistent.")

    return posterior


def bayes_from_two_hypotheses(
    prior_h1: float,
    likelihood_e_given_h1: float,
    likelihood_e_given_h2: float,
) -> float:
    """
    Two-hypothesis Bayes calculation.

    P(H1|E) =
        P(E|H1)P(H1)
        ------------------------------
        P(E|H1)P(H1) + P(E|H2)P(H2)
    """
    validate_probability(prior_h1, "prior_h1")
    validate_probability(likelihood_e_given_h1, "likelihood_e_given_h1")
    validate_probability(likelihood_e_given_h2, "likelihood_e_given_h2")

    prior_h2 = 1.0 - prior_h1

    denominator = (
        likelihood_e_given_h1 * prior_h1
        + likelihood_e_given_h2 * prior_h2
    )

    if denominator == 0:
        raise ZeroDivisionError("Evidence has probability zero.")

    return likelihood_e_given_h1 * prior_h1 / denominator


# ============================================================================
# SECTION 6: DISCRETE RANDOM VARIABLES
# ============================================================================

@dataclass(frozen=True)
class DiscreteDistribution:
    """
    Finite discrete probability distribution.

    outcomes:
        Possible values of the random variable.

    probabilities:
        Corresponding probabilities.

    A valid distribution requires:
        p(x) >= 0
        sum p(x) = 1
    """

    outcomes: tuple[float, ...]
    probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.outcomes) != len(self.probabilities):
            raise ValueError("Outcomes and probabilities must have equal length.")

        if len(self.outcomes) == 0:
            raise ValueError("Distribution cannot be empty.")

        if any(p < 0 for p in self.probabilities):
            raise ValueError("Probabilities cannot be negative.")

        total = sum(self.probabilities)

        if not math.isclose(total, 1.0, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("Probabilities must sum to 1.")

    def pmf(self, value: float) -> float:
        """Return P(X=value)."""
        return sum(
            probability
            for outcome, probability in zip(self.outcomes, self.probabilities)
            if outcome == value
        )

    def cdf(self, value: float) -> float:
        """Return P(X <= value)."""
        return sum(
            probability
            for outcome, probability in zip(self.outcomes, self.probabilities)
            if outcome <= value
        )

    def mean(self) -> float:
        """E[X] = sum x p(x)."""
        return sum(
            outcome * probability
            for outcome, probability in zip(self.outcomes, self.probabilities)
        )

    def variance(self) -> float:
        """Var(X) = E[X^2] - E[X]^2."""
        mean = self.mean()
        second_moment = sum(
            outcome ** 2 * probability
            for outcome, probability in zip(self.outcomes, self.probabilities)
        )
        return max(0.0, second_moment - mean ** 2)

    def standard_deviation(self) -> float:
        """sqrt(Var(X))."""
        return math.sqrt(self.variance())

    def sample(self, rng: Optional[random.Random] = None) -> float:
        """Draw one observation according to the PMF."""
        generator = rng or random
        return generator.choices(
            self.outcomes,
            weights=self.probabilities,
            k=1,
        )[0]


# ============================================================================
# SECTION 7: BERNOULLI DISTRIBUTION
# ============================================================================

class BernoulliDistribution:
    """
    Bernoulli random variable.

    X = 1 with probability p
    X = 0 with probability 1-p

    Mean:
        E[X] = p

    Variance:
        Var(X) = p(1-p)
    """

    def __init__(self, p: float) -> None:
        validate_probability(p, "p")
        self.p = p

    def pmf(self, x: int) -> float:
        if x == 1:
            return self.p
        if x == 0:
            return 1.0 - self.p
        return 0.0

    def cdf(self, x: float) -> float:
        if x < 0:
            return 0.0
        if x < 1:
            return 1.0 - self.p
        return 1.0

    def mean(self) -> float:
        return self.p

    def variance(self) -> float:
        return self.p * (1.0 - self.p)

    def sample(self, rng: Optional[random.Random] = None) -> int:
        generator = rng or random
        return int(generator.random() < self.p)


# ============================================================================
# SECTION 8: BINOMIAL DISTRIBUTION
# ============================================================================

class BinomialDistribution:
    """
    Binomial distribution.

    X counts successes in n independent Bernoulli trials.

    PMF:
        P(X=k) = C(n,k)p^k(1-p)^(n-k)

    Mean:
        np

    Variance:
        np(1-p)
    """

    def __init__(self, n: int, p: float) -> None:
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be a nonnegative integer.")
        validate_probability(p, "p")
        self.n = n
        self.p = p

    def pmf(self, k: int) -> float:
        if not isinstance(k, int) or k < 0 or k > self.n:
            return 0.0
        return probability_exactly_k_successes(self.n, k, self.p)

    def cdf(self, k: int) -> float:
        if k < 0:
            return 0.0
        if k >= self.n:
            return 1.0
        return sum(self.pmf(i) for i in range(k + 1))

    def mean(self) -> float:
        return self.n * self.p

    def variance(self) -> float:
        return self.n * self.p * (1.0 - self.p)

    def standard_deviation(self) -> float:
        return math.sqrt(self.variance())

    def sample(self, rng: Optional[random.Random] = None) -> int:
        generator = rng or random
        return sum(generator.random() < self.p for _ in range(self.n))


# ============================================================================
# SECTION 9: GEOMETRIC DISTRIBUTION
# ============================================================================

class GeometricDistribution:
    """
    Geometric distribution counting trials until the first success.

    Support:
        k = 1, 2, 3, ...

    PMF:
        P(X=k) = (1-p)^(k-1)p

    Mean:
        1/p

    Variance:
        (1-p)/p^2
    """

    def __init__(self, p: float) -> None:
        validate_probability(p, "p")
        if p == 0:
            raise ValueError("Geometric p must be greater than zero.")
        self.p = p

    def pmf(self, k: int) -> float:
        if not isinstance(k, int) or k < 1:
            return 0.0
        return ((1.0 - self.p) ** (k - 1)) * self.p

    def cdf(self, k: int) -> float:
        if k < 1:
            return 0.0
        return 1.0 - (1.0 - self.p) ** k

    def mean(self) -> float:
        return 1.0 / self.p

    def variance(self) -> float:
        return (1.0 - self.p) / (self.p ** 2)

    def sample(self, rng: Optional[random.Random] = None) -> int:
        generator = rng or random
        trials = 1
        while generator.random() >= self.p:
            trials += 1
        return trials


# ============================================================================
# SECTION 10: NEGATIVE BINOMIAL DISTRIBUTION
# ============================================================================

def negative_binomial_pmf(
    failures_before_r_successes: int,
    r_successes: int,
    p: float,
) -> float:
    """
    Probability of exactly k failures before the r-th success.

        P(K=k) = C(k+r-1, r-1) p^r (1-p)^k
    """
    if not isinstance(failures_before_r_successes, int):
        raise TypeError("Number of failures must be an integer.")
    if failures_before_r_successes < 0:
        return 0.0
    if not isinstance(r_successes, int) or r_successes <= 0:
        raise ValueError("r_successes must be a positive integer.")
    validate_probability(p, "p")
    if p == 0:
        return 0.0

    k = failures_before_r_successes
    return (
        combinations_count(k + r_successes - 1, r_successes - 1)
        * (p ** r_successes)
        * ((1.0 - p) ** k)
    )


# ============================================================================
# SECTION 11: HYPERGEOMETRIC DISTRIBUTION
# ============================================================================

def hypergeometric_pmf(
    population_size: int,
    successes_in_population: int,
    draws: int,
    successes_drawn: int,
) -> float:
    """
    Hypergeometric probability for sampling without replacement.

        P(X=k) =
            C(K,k) C(N-K,n-k)
            ------------------
                 C(N,n)

    N = population size
    K = successes in population
    n = number drawn
    k = successes drawn
    """
    N = population_size
    K = successes_in_population
    n = draws
    k = successes_drawn

    if any(not isinstance(value, int) for value in [N, K, n, k]):
        raise TypeError("All hypergeometric parameters must be integers.")

    if N <= 0 or not 0 <= K <= N or not 0 <= n <= N:
        raise ValueError("Require N>0, 0<=K<=N, and 0<=n<=N.")

    lower = max(0, n - (N - K))
    upper = min(n, K)

    if k < lower or k > upper:
        return 0.0

    return (
        combinations_count(K, k)
        * combinations_count(N - K, n - k)
        / combinations_count(N, n)
    )


# ============================================================================
# SECTION 12: POISSON DISTRIBUTION
# ============================================================================

class PoissonDistribution:
    """
    Poisson distribution for event counts over a fixed interval.

    PMF:
        P(X=k) = exp(-lambda) lambda^k / k!

    Mean:
        lambda

    Variance:
        lambda
    """

    def __init__(self, rate: float) -> None:
        validate_positive(rate, "rate")
        self.rate = rate

    def pmf(self, k: int) -> float:
        if not isinstance(k, int) or k < 0:
            return 0.0

        # Use log-space internally for better numerical behavior at larger
        # parameter values.
        log_probability = (
            -self.rate
            + k * math.log(self.rate)
            - math.lgamma(k + 1)
        )
        return math.exp(log_probability)

    def cdf(self, k: int) -> float:
        if k < 0:
            return 0.0
        return min(1.0, sum(self.pmf(i) for i in range(k + 1)))

    def mean(self) -> float:
        return self.rate

    def variance(self) -> float:
        return self.rate

    def sample(self, rng: Optional[random.Random] = None) -> int:
        """
        Knuth's algorithm for Poisson simulation.

        This implementation is simple and useful pedagogically, though it is
        not the fastest method for very large rates.
        """
        generator = rng or random
        threshold = math.exp(-self.rate)
        product_value = 1.0
        count = 0

        while product_value > threshold:
            product_value *= generator.random()
            count += 1

        return count - 1


# ============================================================================
# SECTION 13: CONTINUOUS RANDOM VARIABLES
# ============================================================================

class ContinuousDistribution:
    """
    Base interface for continuous distributions.

    Continuous distributions assign probability to intervals rather than
    individual points. For a continuous variable X:

        P(X = x) = 0

    while:

        P(a <= X <= b) = integral_a^b f(x) dx
    """

    def pdf(self, x: float) -> float:
        raise NotImplementedError

    def cdf(self, x: float) -> float:
        raise NotImplementedError

    def mean(self) -> float:
        raise NotImplementedError

    def variance(self) -> float:
        raise NotImplementedError

    def quantile(self, probability: float) -> float:
        raise NotImplementedError

    def interval_probability(self, lower: float, upper: float) -> float:
        if lower > upper:
            raise ValueError("lower must not exceed upper.")
        return self.cdf(upper) - self.cdf(lower)


# ============================================================================
# SECTION 14: CONTINUOUS UNIFORM DISTRIBUTION
# ============================================================================

class UniformDistribution(ContinuousDistribution):
    """
    Continuous Uniform(a,b).

    PDF:
        f(x) = 1/(b-a), a <= x <= b

    Mean:
        (a+b)/2

    Variance:
        (b-a)^2 / 12
    """

    def __init__(self, lower: float, upper: float) -> None:
        if lower >= upper:
            raise ValueError("Require lower < upper.")
        self.lower = lower
        self.upper = upper

    def pdf(self, x: float) -> float:
        if self.lower <= x <= self.upper:
            return 1.0 / (self.upper - self.lower)
        return 0.0

    def cdf(self, x: float) -> float:
        if x < self.lower:
            return 0.0
        if x >= self.upper:
            return 1.0
        return (x - self.lower) / (self.upper - self.lower)

    def mean(self) -> float:
        return (self.lower + self.upper) / 2.0

    def variance(self) -> float:
        return (self.upper - self.lower) ** 2 / 12.0

    def quantile(self, probability: float) -> float:
        validate_probability(probability, "probability")
        return self.lower + probability * (self.upper - self.lower)

    def sample(self, rng: Optional[random.Random] = None) -> float:
        generator = rng or random
        return generator.uniform(self.lower, self.upper)


# ============================================================================
# SECTION 15: EXPONENTIAL DISTRIBUTION
# ============================================================================

class ExponentialDistribution(ContinuousDistribution):
    """
    Exponential(rate=lambda).

    PDF:
        f(x) = lambda exp(-lambda x), x >= 0

    CDF:
        F(x) = 1 - exp(-lambda x)

    Mean:
        1/lambda

    Variance:
        1/lambda^2

    The exponential distribution has the memoryless property.
    """

    def __init__(self, rate: float) -> None:
        validate_positive(rate, "rate")
        self.rate = rate

    def pdf(self, x: float) -> float:
        if x < 0:
            return 0.0
        return self.rate * math.exp(-self.rate * x)

    def cdf(self, x: float) -> float:
        if x < 0:
            return 0.0
        return -math.expm1(-self.rate * x)

    def mean(self) -> float:
        return 1.0 / self.rate

    def variance(self) -> float:
        return 1.0 / (self.rate ** 2)

    def quantile(self, probability: float) -> float:
        validate_probability(probability, "probability")
        if probability == 1.0:
            return math.inf
        if probability == 0.0:
            return 0.0

        # -log(1-p)/lambda is computed using log1p for numerical stability.
        return -math.log1p(-probability) / self.rate

    def sample(self, rng: Optional[random.Random] = None) -> float:
        generator = rng or random
        u = generator.random()
        while u == 0.0:
            u = generator.random()
        return -math.log(u) / self.rate


# ============================================================================
# SECTION 16: NORMAL DISTRIBUTION
# ============================================================================

class NormalDistribution(ContinuousDistribution):
    """
    Normal(mu, sigma^2).

    PDF:
        f(x) =
            1
            ---------------- exp[-(x-mu)^2/(2 sigma^2)]
            sigma sqrt(2 pi)

    Mean:
        mu

    Variance:
        sigma^2

    The standard normal is N(0,1).
    """

    def __init__(self, mean: float = 0.0, standard_deviation: float = 1.0) -> None:
        validate_positive(standard_deviation, "standard_deviation")
        self.mu = mean
        self.sigma = standard_deviation

    def pdf(self, x: float) -> float:
        standardized = (x - self.mu) / self.sigma
        return (
            math.exp(-0.5 * standardized ** 2)
            / (self.sigma * math.sqrt(2.0 * math.pi))
        )

    def cdf(self, x: float) -> float:
        standardized = (x - self.mu) / (self.sigma * math.sqrt(2.0))
        return 0.5 * (1.0 + math.erf(standardized))

    def mean(self) -> float:
        return self.mu

    def variance(self) -> float:
        return self.sigma ** 2

    def standardize(self, x: float) -> float:
        """Convert an observation to a z-score."""
        return (x - self.mu) / self.sigma

    def quantile(self, probability: float) -> float:
        """
        Numerical inverse CDF using binary search.

        A production statistics package would normally provide a specialized
        inverse-normal implementation. Binary search is used here because it
        is transparent and requires only the standard library.
        """
        validate_probability(probability, "probability")

        if probability == 0.0:
            return -math.inf
        if probability == 1.0:
            return math.inf

        lower = self.mu - 12.0 * self.sigma
        upper = self.mu + 12.0 * self.sigma

        for _ in range(100):
            midpoint = (lower + upper) / 2.0
            if self.cdf(midpoint) < probability:
                lower = midpoint
            else:
                upper = midpoint

        return (lower + upper) / 2.0

    def sample(self, rng: Optional[random.Random] = None) -> float:
        generator = rng or random
        return generator.gauss(self.mu, self.sigma)


# ============================================================================
# SECTION 17: LOG-NORMAL DISTRIBUTION
# ============================================================================

class LogNormalDistribution(ContinuousDistribution):
    """
    Log-normal distribution.

    If Y ~ Normal(mu, sigma^2), then:

        X = exp(Y)

    follows a log-normal distribution.

    Mean:
        exp(mu + sigma^2/2)

    Variance:
        [exp(sigma^2)-1] exp(2mu + sigma^2)
    """

    def __init__(self, log_mean: float = 0.0, log_standard_deviation: float = 1.0):
        validate_positive(log_standard_deviation, "log_standard_deviation")
        self.log_mean = log_mean
        self.log_sigma = log_standard_deviation

    def pdf(self, x: float) -> float:
        if x <= 0:
            return 0.0

        z = (math.log(x) - self.log_mean) / self.log_sigma

        return (
            math.exp(-0.5 * z ** 2)
            / (x * self.log_sigma * math.sqrt(2.0 * math.pi))
        )

    def cdf(self, x: float) -> float:
        if x <= 0:
            return 0.0

        z = (math.log(x) - self.log_mean) / (
            self.log_sigma * math.sqrt(2.0)
        )
        return 0.5 * (1.0 + math.erf(z))

    def mean(self) -> float:
        return math.exp(
            self.log_mean + (self.log_sigma ** 2) / 2.0
        )

    def variance(self) -> float:
        sigma_squared = self.log_sigma ** 2
        return (
            (math.exp(sigma_squared) - 1.0)
            * math.exp(2.0 * self.log_mean + sigma_squared)
        )

    def quantile(self, probability: float) -> float:
        validate_probability(probability, "probability")

        if probability == 0:
            return 0.0
        if probability == 1:
            return math.inf

        normal = NormalDistribution(
            self.log_mean,
            self.log_sigma,
        )
        return math.exp(normal.quantile(probability))

    def sample(self, rng: Optional[random.Random] = None) -> float:
        generator = rng or random
        return math.exp(generator.gauss(self.log_mean, self.log_sigma))


# ============================================================================
# SECTION 18: DISTRIBUTION MEASURES
# ============================================================================

def expected_value(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """Compute E[X] for a finite discrete distribution."""
    if len(values) != len(probabilities):
        raise ValueError("Values and probabilities must have equal length.")

    if any(p < 0 for p in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    total_probability = sum(probabilities)
    if not math.isclose(total_probability, 1.0, abs_tol=1e-12):
        raise ValueError("Probabilities must sum to 1.")

    return sum(x * p for x, p in zip(values, probabilities))


def variance_from_distribution(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """Compute Var(X) from a finite PMF."""
    mean = expected_value(values, probabilities)
    second_moment = expected_value(
        [x ** 2 for x in values],
        probabilities,
    )
    return max(0.0, second_moment - mean ** 2)


def covariance(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> float:
    """
    Sample covariance with denominator n-1.

    This measures how two observed variables vary together.
    """
    if len(x_values) != len(y_values):
        raise ValueError("Samples must have equal lengths.")
    if len(x_values) < 2:
        raise ValueError("At least two observations are required.")

    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)

    return sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    ) / (len(x_values) - 1)


def correlation(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> float:
    """
    Pearson correlation:

        corr(X,Y) = Cov(X,Y) / (sd(X) sd(Y))
    """
    if len(x_values) != len(y_values):
        raise ValueError("Samples must have equal lengths.")

    covariance_value = covariance(x_values, y_values)
    x_sd = statistics.stdev(x_values)
    y_sd = statistics.stdev(y_values)

    if x_sd == 0 or y_sd == 0:
        raise ZeroDivisionError(
            "Correlation is undefined when a variable has zero variance."
        )

    return covariance_value / (x_sd * y_sd)


# ============================================================================
# SECTION 19: POPULATION AND SAMPLE MEASUREMENT
# ============================================================================

def population_mean(values: Sequence[float]) -> float:
    """Arithmetic mean of an entire population."""
    if not values:
        raise ValueError("At least one observation is required.")
    return sum(values) / len(values)


def population_variance(values: Sequence[float]) -> float:
    """Variance using denominator N."""
    if not values:
        raise ValueError("At least one observation is required.")

    mean = population_mean(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def sample_variance(values: Sequence[float]) -> float:
    """Unbiased sample variance using denominator n-1."""
    if len(values) < 2:
        raise ValueError("At least two observations are required.")

    mean = statistics.mean(values)
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


def standard_error_of_mean(
    sample_standard_deviation: float,
    sample_size: int,
) -> float:
    """
    Standard error of the sample mean:

        SE = s / sqrt(n)
    """
    validate_positive(sample_standard_deviation, "sample_standard_deviation")
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    return sample_standard_deviation / math.sqrt(sample_size)


def z_score(
    observation: float,
    mean: float,
    standard_deviation: float,
) -> float:
    """Calculate how many standard deviations an observation is from the mean."""
    validate_positive(standard_deviation, "standard_deviation")
    return (observation - mean) / standard_deviation


# ============================================================================
# SECTION 20: QUANTILES AND MEDIAN
# ============================================================================

def quantile_nearest_rank(
    values: Sequence[float],
    probability: float,
) -> float:
    """
    Simple nearest-rank quantile definition.

    This implementation is intentionally explicit because several software
    systems use different interpolation conventions for sample quantiles.
    """
    if not values:
        raise ValueError("At least one value is required.")
    validate_probability(probability, "probability")

    sorted_values = sorted(values)

    if probability == 0:
        return sorted_values[0]

    rank = math.ceil(probability * len(sorted_values))
    return sorted_values[rank - 1]


def five_number_summary(values: Sequence[float]) -> dict[str, float]:
    """Return minimum, Q1, median, Q3, and maximum."""
    if not values:
        raise ValueError("At least one value is required.")

    return {
        "minimum": min(values),
        "Q1": quantile_nearest_rank(values, 0.25),
        "median": quantile_nearest_rank(values, 0.50),
        "Q3": quantile_nearest_rank(values, 0.75),
        "maximum": max(values),
    }


# ============================================================================
# SECTION 21: JOINT AND MARGINAL DISTRIBUTIONS
# ============================================================================

def joint_distribution_table() -> dict[tuple[str, int], float]:
    """
    Example joint distribution:

        Gender-like category: A/B
        Score category:       0/1

    The labels are intentionally generic because the mathematics is what
    matters.

    Returns:
        P(A,0), P(A,1), P(B,0), P(B,1)
    """
    return {
        ("A", 0): 0.20,
        ("A", 1): 0.30,
        ("B", 0): 0.10,
        ("B", 1): 0.40,
    }


def marginal_distribution(
    joint: dict[tuple[str, int], float],
    dimension: int,
) -> dict:
    """
    Compute a marginal distribution by summing over the other variable.

    dimension=0 -> first variable
    dimension=1 -> second variable
    """
    if dimension not in (0, 1):
        raise ValueError("dimension must be 0 or 1.")

    result: dict = {}

    for key, probability in joint.items():
        marginal_key = key[dimension]
        result[marginal_key] = result.get(marginal_key, 0.0) + probability

    return result


def joint_probability_independence_check(
    joint: dict[tuple, float],
) -> dict[tuple, bool]:
    """
    Check whether each joint cell satisfies:

        P(X=x,Y=y) = P(X=x)P(Y=y)

    Small floating-point differences are tolerated.
    """
    first_marginal = marginal_distribution(joint, 0)
    second_marginal = marginal_distribution(joint, 1)

    result = {}

    for (x, y), probability in joint.items():
        expected = first_marginal[x] * second_marginal[y]
        result[(x, y)] = math.isclose(
            probability,
            expected,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )

    return result


# ============================================================================
# SECTION 22: LAW OF TOTAL PROBABILITY AND EXPECTATION
# ============================================================================

def total_probability(
    conditional_probabilities: Sequence[float],
    partition_probabilities: Sequence[float],
) -> float:
    """
    Law of total probability:

        P(A) = sum P(A|B_i) P(B_i)

    where the B_i form a valid partition.
    """
    if len(conditional_probabilities) != len(partition_probabilities):
        raise ValueError("Sequences must have equal lengths.")

    if not math.isclose(sum(partition_probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("Partition probabilities must sum to 1.")

    for value in conditional_probabilities:
        validate_probability(value, "conditional probability")

    for value in partition_probabilities:
        validate_probability(value, "partition probability")

    return sum(
        conditional * partition
        for conditional, partition
        in zip(conditional_probabilities, partition_probabilities)
    )


def total_expectation(
    conditional_means: Sequence[float],
    partition_probabilities: Sequence[float],
) -> float:
    """
    Law of total expectation:

        E[X] = sum E[X|B_i] P(B_i)
    """
    if len(conditional_means) != len(partition_probabilities):
        raise ValueError("Sequences must have equal lengths.")

    if not math.isclose(sum(partition_probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("Partition probabilities must sum to 1.")

    return sum(
        mean * probability
        for mean, probability
        in zip(conditional_means, partition_probabilities)
    )


# ============================================================================
# SECTION 23: TRANSFORMATIONS OF RANDOM VARIABLES
# ============================================================================

def transform_discrete_distribution(
    distribution: DiscreteDistribution,
    transformation: Callable[[float], float],
) -> DiscreteDistribution:
    """
    Transform X into Y=g(X).

    If multiple X values map to the same Y value, their probabilities must
    be combined.
    """
    combined: dict[float, float] = {}

    for x, probability in zip(
        distribution.outcomes,
        distribution.probabilities,
    ):
        y = transformation(x)
        combined[y] = combined.get(y, 0.0) + probability

    outcomes = tuple(sorted(combined))
    probabilities = tuple(combined[y] for y in outcomes)

    return DiscreteDistribution(outcomes, probabilities)


# ============================================================================
# SECTION 24: MONTE CARLO SIMULATION
# ============================================================================

def monte_carlo_pi(
    number_of_samples: int,
    seed: Optional[int] = 42,
) -> float:
    """
    Estimate pi using random points in a unit square.

    A point (x,y) lies inside the quarter-circle when:

        x^2 + y^2 <= 1

    The quarter-circle area is pi/4, so:

        pi approximately 4 * proportion_inside
    """
    if number_of_samples <= 0:
        raise ValueError("number_of_samples must be positive.")

    rng = random.Random(seed)
    inside = 0

    for _ in range(number_of_samples):
        x = rng.random()
        y = rng.random()

        if x * x + y * y <= 1.0:
            inside += 1

    return 4.0 * inside / number_of_samples


def estimate_probability_by_simulation(
    experiment: Callable[[random.Random], bool],
    number_of_trials: int,
    seed: Optional[int] = 42,
) -> float:
    """Estimate P(event) from repeated simulated experiments."""
    if number_of_trials <= 0:
        raise ValueError("number_of_trials must be positive.")

    rng = random.Random(seed)
    successes = sum(experiment(rng) for _ in range(number_of_trials))
    return successes / number_of_trials


# ============================================================================
# SECTION 25: SAMPLING FROM A CUSTOM DISCRETE DISTRIBUTION
# ============================================================================

def sample_distribution(
    distribution: DiscreteDistribution,
    sample_size: int,
    seed: Optional[int] = 42,
) -> list[float]:
    """Generate repeated observations from a finite PMF."""
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    rng = random.Random(seed)
    return [distribution.sample(rng) for _ in range(sample_size)]


def empirical_distribution(
    samples: Sequence[float],
) -> dict[float, float]:
    """Convert observed samples into relative frequencies."""
    if not samples:
        raise ValueError("At least one sample is required.")

    counts = Counter(samples)
    total = len(samples)

    return {
        value: count / total
        for value, count in sorted(counts.items())
    }


# ============================================================================
# SECTION 26: CENTRAL LIMIT THEOREM DEMONSTRATION
# ============================================================================

def central_limit_theorem_simulation(
    population: Sequence[float],
    sample_size: int,
    number_of_samples: int,
    seed: Optional[int] = 42,
) -> tuple[list[float], float, float]:
    """
    Draw repeated samples and return their sample means.

    The Central Limit Theorem states that, under broad conditions, the
    distribution of sample means becomes approximately normal as sample size
    increases, even when the original population is not normal.
    """
    if not population:
        raise ValueError("Population cannot be empty.")
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")
    if number_of_samples <= 0:
        raise ValueError("number_of_samples must be positive.")

    rng = random.Random(seed)
    means = []

    for _ in range(number_of_samples):
        sample = rng.choices(population, k=sample_size)
        means.append(statistics.mean(sample))

    return means, statistics.mean(means), statistics.stdev(means)


# ============================================================================
# SECTION 27: LAW OF LARGE NUMBERS DEMONSTRATION
# ============================================================================

def running_empirical_probability(
    probability: float,
    trial_counts: Sequence[int],
    seed: Optional[int] = 42,
) -> dict[int, float]:
    """
    Show how empirical probability tends to stabilize as trial count grows.

    This illustrates the Law of Large Numbers.
    """
    validate_probability(probability, "probability")

    if not trial_counts:
        raise ValueError("trial_counts cannot be empty.")

    if any(n <= 0 for n in trial_counts):
        raise ValueError("All trial counts must be positive.")

    rng = random.Random(seed)
    maximum_trials = max(trial_counts)

    successes = 0
    results = {}

    requested = set(trial_counts)

    for trial in range(1, maximum_trials + 1):
        if rng.random() < probability:
            successes += 1

        if trial in requested:
            results[trial] = successes / trial

    return results


# ============================================================================
# SECTION 28: MEASUREMENT ERROR AND UNCERTAINTY
# ============================================================================

@dataclass(frozen=True)
class Measurement:
    """
    A measured value with an estimated standard uncertainty.

    If independent measurements are added:

        z = x + y

    then:

        u_z = sqrt(u_x^2 + u_y^2)

    For a difference, the same variance propagation applies when errors are
    independent.
    """

    value: float
    standard_uncertainty: float

    def __post_init__(self) -> None:
        validate_nonnegative(
            self.standard_uncertainty,
            "standard_uncertainty",
        )


def combine_independent_uncertainties(
    uncertainties: Sequence[float],
) -> float:
    """
    Root-sum-of-squares combination:

        u_combined = sqrt(sum(u_i^2))
    """
    if not uncertainties:
        raise ValueError("At least one uncertainty is required.")

    for uncertainty in uncertainties:
        validate_nonnegative(uncertainty, "uncertainty")

    return math.sqrt(sum(u ** 2 for u in uncertainties))


def add_measurements(
    first: Measurement,
    second: Measurement,
) -> Measurement:
    """Add independent measurements and propagate uncertainty."""
    value = first.value + second.value
    uncertainty = combine_independent_uncertainties(
        [first.standard_uncertainty, second.standard_uncertainty]
    )
    return Measurement(value, uncertainty)


def multiply_measurements(
    first: Measurement,
    second: Measurement,
) -> Measurement:
    """
    Multiply independent measurements.

    For nonzero values, approximate relative uncertainty propagation:

        (u_z / |z|)^2 =
            (u_x / |x|)^2 +
            (u_y / |y|)^2
    """
    if first.value == 0 or second.value == 0:
        raise ValueError(
            "This relative-uncertainty implementation requires nonzero values."
        )

    value = first.value * second.value

    relative_uncertainty = math.sqrt(
        (first.standard_uncertainty / abs(first.value)) ** 2
        + (second.standard_uncertainty / abs(second.value)) ** 2
    )

    return Measurement(
        value,
        abs(value) * relative_uncertainty,
    )


# ============================================================================
# SECTION 29: MAXIMUM LIKELIHOOD ESTIMATION FOR BERNOULLI DATA
# ============================================================================

def bernoulli_mle(observations: Sequence[int]) -> float:
    """
    Maximum likelihood estimator for Bernoulli parameter p.

    Given observations x_1,...,x_n:

        p_hat = number of successes / n
    """
    if not observations:
        raise ValueError("At least one observation is required.")

    if any(observation not in (0, 1) for observation in observations):
        raise ValueError("Bernoulli observations must be 0 or 1.")

    return sum(observations) / len(observations)


def bernoulli_log_likelihood(
    observations: Sequence[int],
    p: float,
) -> float:
    """
    Bernoulli log-likelihood:

        log L(p)
        = sum [x log(p) + (1-x)log(1-p)]

    Boundary cases p=0 and p=1 are handled explicitly.
    """
    validate_probability(p, "p")

    if any(x not in (0, 1) for x in observations):
        raise ValueError("Observations must contain only 0 and 1.")

    if not observations:
        raise ValueError("At least one observation is required.")

    successes = sum(observations)
    failures = len(observations) - successes

    if p == 0:
        return 0.0 if successes == 0 else -math.inf

    if p == 1:
        return 0.0 if failures == 0 else -math.inf

    return successes * math.log(p) + failures * math.log1p(-p)


# ============================================================================
# SECTION 30: NORMAL APPROXIMATION TO BINOMIAL
# ============================================================================

def normal_approximation_binomial_probability(
    n: int,
    p: float,
    lower: int,
    upper: int,
) -> float:
    """
    Approximate P(lower <= X <= upper) for X~Binomial(n,p)
    using a continuity-corrected normal distribution.

    Mean:
        np

    Standard deviation:
        sqrt(np(1-p))

    Continuity correction:
        P(a <= X <= b)
        approximately
        P(a-0.5 < Y < b+0.5)
    """
    if n <= 0:
        raise ValueError("n must be positive.")
    validate_probability(p, "p")

    if not 0 <= lower <= upper <= n:
        raise ValueError("Require 0 <= lower <= upper <= n.")

    mean = n * p
    standard_deviation = math.sqrt(n * p * (1.0 - p))

    if standard_deviation == 0:
        return 1.0 if lower <= mean <= upper else 0.0

    normal = NormalDistribution(mean, standard_deviation)

    return normal.cdf(upper + 0.5) - normal.cdf(lower - 0.5)


# ============================================================================
# SECTION 31: CONDITIONAL DISTRIBUTION FROM A JOINT TABLE
# ============================================================================

def conditional_from_joint(
    joint: dict[tuple, float],
    fixed_dimension: int,
    fixed_value,
    target_dimension: int,
) -> dict:
    """
    Derive a conditional distribution from a joint distribution.

    Example:
        P(Y=y | X=x)

    by selecting all cells with X=x and normalizing their probabilities.
    """
    if fixed_dimension == target_dimension:
        raise ValueError("Fixed and target dimensions must differ.")

    if fixed_dimension not in (0, 1) or target_dimension not in (0, 1):
        raise ValueError("Dimensions must be 0 or 1.")

    selected = {
        key[target_dimension]: probability
        for key, probability in joint.items()
        if key[fixed_dimension] == fixed_value
    }

    denominator = sum(selected.values())

    if denominator == 0:
        raise ZeroDivisionError("Condition has zero probability.")

    return {
        value: probability / denominator
        for value, probability in selected.items()
    }


# ============================================================================
# SECTION 32: ENTROPY AS A MEASURE OF UNCERTAINTY
# ============================================================================

def shannon_entropy(probabilities: Sequence[float], base: float = 2.0) -> float:
    """
    Shannon entropy:

        H(X) = -sum p(x) log_base(p(x))

    With base 2, entropy is measured in bits.

    Terms with p=0 contribute zero by convention because:
        lim p->0+ p log(p) = 0
    """
    if base <= 0 or math.isclose(base, 1.0):
        raise ValueError("Logarithm base must be positive and not equal to 1.")

    if any(p < 0 for p in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    if not math.isclose(sum(probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("Probabilities must sum to 1.")

    entropy = 0.0

    for p in probabilities:
        if p > 0:
            entropy -= p * math.log(p, base)

    return entropy


# ============================================================================
# SECTION 33: DISTRIBUTION COMPARISONS
# ============================================================================

def compare_binomial_and_poisson(
    n: int,
    p: float,
    maximum_k: int,
) -> list[tuple[int, float, float]]:
    """
    Compare a Binomial(n,p) PMF with a Poisson(lambda=np) PMF.

    The Poisson approximation is generally useful when n is large and p is
    small, with lambda=np of moderate size.
    """
    if n <= 0:
        raise ValueError("n must be positive.")
    validate_probability(p, "p")
    if maximum_k < 0:
        raise ValueError("maximum_k must be nonnegative.")

    binomial = BinomialDistribution(n, p)
    poisson = PoissonDistribution(n * p)

    return [
        (k, binomial.pmf(k), poisson.pmf(k))
        for k in range(maximum_k + 1)
    ]


# ============================================================================
# SECTION 34: SAMPLE OUTPUT HELPERS
# ============================================================================

def print_distribution_table(
    distribution: DiscreteDistribution,
) -> None:
    """Print a finite PMF in a readable table."""
    print("Value       Probability       CDF")
    print("-" * 38)

    cumulative = 0.0

    for value, probability in sorted(
        zip(distribution.outcomes, distribution.probabilities)
    ):
        cumulative += probability
        print(f"{value:<11} {probability:<17.6f} {cumulative:.6f}")


def print_dictionary(dictionary: dict) -> None:
    """Print dictionary values consistently."""
    for key, value in dictionary.items():
        print(f"{key}: {value}")


# ============================================================================
# SECTION 35: TESTS
# ============================================================================

class ProbabilityTests(unittest.TestCase):
    """Unit tests for core probability calculations."""

    def test_classical_probability(self) -> None:
        self.assertAlmostEqual(
            probability_from_equally_likely_outcomes(3, 6),
            0.5,
        )

    def test_complement(self) -> None:
        self.assertAlmostEqual(event_complement(0.7), 0.3)

    def test_union(self) -> None:
        self.assertAlmostEqual(
            event_union_probability(0.5, 0.4, 0.2),
            0.7,
        )

    def test_binomial(self) -> None:
        distribution = BinomialDistribution(4, 0.5)
        self.assertAlmostEqual(distribution.pmf(2), 0.375)

    def test_bernoulli_moments(self) -> None:
        distribution = BernoulliDistribution(0.25)
        self.assertAlmostEqual(distribution.mean(), 0.25)
        self.assertAlmostEqual(distribution.variance(), 0.1875)

    def test_poisson_moments(self) -> None:
        distribution = PoissonDistribution(4.0)
        self.assertAlmostEqual(distribution.mean(), 4.0)
        self.assertAlmostEqual(distribution.variance(), 4.0)

    def test_uniform(self) -> None:
        distribution = UniformDistribution(0.0, 10.0)
        self.assertAlmostEqual(distribution.mean(), 5.0)
        self.assertAlmostEqual(distribution.variance(), 100.0 / 12.0)
        self.assertAlmostEqual(distribution.interval_probability(2, 7), 0.5)

    def test_exponential(self) -> None:
        distribution = ExponentialDistribution(2.0)
        self.assertAlmostEqual(distribution.mean(), 0.5)
        self.assertAlmostEqual(distribution.variance(), 0.25)

    def test_normal_standardization(self) -> None:
        distribution = NormalDistribution(100.0, 15.0)
        self.assertAlmostEqual(distribution.standardize(130.0), 2.0)

    def test_measurement_uncertainty(self) -> None:
        result = combine_independent_uncertainties([3.0, 4.0])
        self.assertAlmostEqual(result, 5.0)

    def test_entropy(self) -> None:
        entropy = shannon_entropy([0.5, 0.5])
        self.assertAlmostEqual(entropy, 1.0)

    def test_bayes(self) -> None:
        posterior = bayes_from_two_hypotheses(0.01, 0.95, 0.05)
        self.assertAlmostEqual(
            posterior,
            0.01 * 0.95 / (0.01 * 0.95 + 0.99 * 0.05),
        )


def run_tests() -> None:
    """Run all built-in unit tests."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProbabilityTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)


# ============================================================================
# SECTION 36: BEGINNER EXAMPLES
# ============================================================================

def demonstrate_beginner_probability() -> None:
    section("1. Probability Fundamentals")

    sample_space = dice_sample_space()
    even = event_even_die()

    print("Sample space for one die:", sorted(sample_space))
    print("Even-number event:", sorted(even))

    probability_even = probability_from_equally_likely_outcomes(
        favorable_outcomes=len(even),
        total_outcomes=len(sample_space),
    )

    print("P(even) =", probability_even)
    print("P(not even) =", event_complement(probability_even))

    subsection("Union, intersection, and complement")

    greater_than_four = event_greater_than_four()
    intersection = event_intersection(even, greater_than_four)
    union = event_union(even, greater_than_four)
    complement = event_complement_set(sample_space, even)

    print("A = even:", sorted(even))
    print("B = greater than four:", sorted(greater_than_four))
    print("A intersection B:", sorted(intersection))
    print("A union B:", sorted(union))
    print("A complement:", sorted(complement))


# ============================================================================
# SECTION 37: COUNTING EXAMPLES
# ============================================================================

def demonstrate_counting() -> None:
    section("2. Counting and Combinatorics")

    print("5! =", factorial(5))
    print("Permutations P(5,2) =", permutations_count(5, 2))
    print("Combinations C(5,2) =", combinations_count(5, 2))

    # Choosing two people from five is different from arranging two people:
    # order matters for permutations but not for combinations.
    people = ["A", "B", "C", "D", "E"]

    print("Example combinations:", list(combinations(people, 2)))
    print("Example permutations:", list(permutations(people, 2))[:10])


# ============================================================================
# SECTION 38: CONDITIONAL PROBABILITY EXAMPLES
# ============================================================================

def demonstrate_conditional_probability() -> None:
    section("3. Conditional Probability and Bayes' Theorem")

    # Suppose 30% of observations satisfy both A and B and 60% satisfy B.
    # Then P(A|B)=P(A intersection B)/P(B).
    conditional = conditional_probability(0.30, 0.60)
    print("P(A|B) =", conditional)

    subsection("Independence")

    independent_probability = independent_intersection_probability(
        0.4,
        0.5,
    )
    print("If A and B are independent, P(A and B) =", independent_probability)

    subsection("Bayes theorem: diagnostic-style example")

    # Suppose a condition has prevalence 1%.
    # A test is positive for 95% of affected cases and 5% of unaffected cases.
    prevalence = 0.01
    sensitivity = 0.95
    false_positive_rate = 0.05

    posterior = bayes_from_two_hypotheses(
        prior_h1=prevalence,
        likelihood_e_given_h1=sensitivity,
        likelihood_e_given_h2=false_positive_rate,
    )

    print("P(condition | positive test) =", posterior)
    print(
        "Percentage:",
        f"{posterior * 100:.2f}%"
    )


# ============================================================================
# SECTION 39: DISCRETE DISTRIBUTION EXAMPLES
# ============================================================================

def demonstrate_discrete_distributions() -> None:
    section("4. Discrete Probability Distributions")

    subsection("A custom discrete distribution")

    distribution = DiscreteDistribution(
        outcomes=(1, 2, 3, 4),
        probabilities=(0.1, 0.2, 0.3, 0.4),
    )

    print_distribution_table(distribution)
    print("E[X] =", distribution.mean())
    print("Var(X) =", distribution.variance())
    print("SD(X) =", distribution.standard_deviation())

    subsection("Bernoulli")

    bernoulli = BernoulliDistribution(0.7)
    print("P(X=1) =", bernoulli.pmf(1))
    print("E[X] =", bernoulli.mean())
    print("Var(X) =", bernoulli.variance())

    subsection("Binomial")

    binomial = BinomialDistribution(10, 0.4)

    print("P(X=4) =", binomial.pmf(4))
    print("P(X<=4) =", binomial.cdf(4))
    print("E[X] =", binomial.mean())
    print("Var(X) =", binomial.variance())

    subsection("Geometric")

    geometric = GeometricDistribution(0.25)
    print("P(first success on trial 4) =", geometric.pmf(4))
    print("P(success by trial 4) =", geometric.cdf(4))
    print("E[X] =", geometric.mean())

    subsection("Negative binomial")

    print(
        "P(3 failures before the 2nd success) =",
        negative_binomial_pmf(3, 2, 0.4),
    )

    subsection("Hypergeometric")

    # A population contains 20 items, 6 of which are marked as successes.
    # Five items are sampled without replacement.
    print(
        "P(exactly 2 marked items in sample) =",
        hypergeometric_pmf(20, 6, 5, 2),
    )

    subsection("Poisson")

    poisson = PoissonDistribution(3.0)
    print("P(X=2) =", poisson.pmf(2))
    print("P(X<=2) =", poisson.cdf(2))
    print("Mean =", poisson.mean())
    print("Variance =", poisson.variance())


# ============================================================================
# SECTION 40: CONTINUOUS DISTRIBUTION EXAMPLES
# ============================================================================

def demonstrate_continuous_distributions() -> None:
    section("5. Continuous Probability Distributions")

    subsection("Continuous uniform")

    uniform = UniformDistribution(0, 10)
    print("PDF at 5 =", uniform.pdf(5))
    print("P(2 <= X <= 7) =", uniform.interval_probability(2, 7))
    print("Median =", uniform.quantile(0.5))

    subsection("Exponential")

    exponential = ExponentialDistribution(0.5)
    print("PDF at 2 =", exponential.pdf(2))
    print("P(X<=2) =", exponential.cdf(2))
    print("P(X>2) =", 1.0 - exponential.cdf(2))
    print("Mean =", exponential.mean())

    # Memorylessness:
    # P(X > s+t | X>s) = P(X>t)
    s = 3.0
    t = 2.0

    conditional_survival = (
        1.0 - exponential.cdf(s + t)
    ) / (
        1.0 - exponential.cdf(s)
    )

    unconditional_survival = 1.0 - exponential.cdf(t)

    print("Exponential memoryless check:")
    print("Conditional survival =", conditional_survival)
    print("Unconditional survival =", unconditional_survival)

    subsection("Normal distribution")

    normal = NormalDistribution(100, 15)

    print("PDF at 100 =", normal.pdf(100))
    print("P(X <= 130) =", normal.cdf(130))
    print("P(85 <= X <= 115) =", normal.interval_probability(85, 115))
    print("z-score of 130 =", normal.standardize(130))
    print("95th percentile =", normal.quantile(0.95))

    subsection("Log-normal distribution")

    log_normal = LogNormalDistribution(2.0, 0.5)
    print("Mean =", log_normal.mean())
    print("Variance =", log_normal.variance())
    print("P(X<=10) =", log_normal.cdf(10))


# ============================================================================
# SECTION 41: MEASUREMENT STATISTICS
# ============================================================================

def demonstrate_measurement_statistics() -> None:
    section("6. Measurement: Mean, Variance, Standard Deviation, and Quantiles")

    measurements = [10, 12, 11, 13, 9, 15, 10, 12]

    print("Observations:", measurements)
    print("Population mean:", population_mean(measurements))
    print("Population variance:", population_variance(measurements))
    print("Sample variance:", sample_variance(measurements))
    print("Sample standard deviation:", statistics.stdev(measurements))
    print("Standard error:", standard_error_of_mean(
        statistics.stdev(measurements),
        len(measurements),
    ))

    print("Five-number summary:")
    print_dictionary(five_number_summary(measurements))

    print("z-score of 15:", z_score(
        15,
        population_mean(measurements),
        statistics.stdev(measurements),
    ))


# ============================================================================
# SECTION 42: COVARIANCE AND CORRELATION
# ============================================================================

def demonstrate_covariance_correlation() -> None:
    section("7. Covariance and Correlation")

    x = [1, 2, 3, 4, 5]
    y = [2, 4, 5, 8, 10]

    print("X:", x)
    print("Y:", y)
    print("Covariance:", covariance(x, y))
    print("Pearson correlation:", correlation(x, y))

    print(
        "\nImportant distinction:"
        "\nCorrelation measures linear association."
        "\nCorrelation does not by itself prove causation."
        "\nA nonlinear relationship can have weak Pearson correlation."
    )


# ============================================================================
# SECTION 43: JOINT DISTRIBUTION EXAMPLES
# ============================================================================

def demonstrate_joint_distributions() -> None:
    section("8. Joint, Marginal, and Conditional Distributions")

    joint = joint_distribution_table()

    print("Joint distribution:")
    print_dictionary(joint)

    first = marginal_distribution(joint, 0)
    second = marginal_distribution(joint, 1)

    print("\nFirst-variable marginal:")
    print_dictionary(first)

    print("\nSecond-variable marginal:")
    print_dictionary(second)

    print("\nConditional distribution of second variable given first='A':")
    conditional = conditional_from_joint(
        joint,
        fixed_dimension=0,
        fixed_value="A",
        target_dimension=1,
    )
    print_dictionary(conditional)

    print("\nIndependence checks by cell:")
    print_dictionary(joint_probability_independence_check(joint))


# ============================================================================
# SECTION 44: TOTAL PROBABILITY AND EXPECTATION
# ============================================================================

def demonstrate_total_probability() -> None:
    section("9. Law of Total Probability and Total Expectation")

    conditional_success_rates = [0.9, 0.6, 0.2]
    group_probabilities = [0.2, 0.5, 0.3]

    overall_probability = total_probability(
        conditional_success_rates,
        group_probabilities,
    )

    print("Overall event probability:", overall_probability)

    conditional_means = [10, 20, 50]

    overall_mean = total_expectation(
        conditional_means,
        group_probabilities,
    )

    print("Overall expected value:", overall_mean)


# ============================================================================
# SECTION 45: TRANSFORMATIONS
# ============================================================================

def demonstrate_transformations() -> None:
    section("10. Transformations of Random Variables")

    original = DiscreteDistribution(
        outcomes=(1, 2, 3, 4),
        probabilities=(0.25, 0.25, 0.25, 0.25),
    )

    squared = transform_discrete_distribution(
        original,
        lambda x: x ** 2,
    )

    print("Original distribution:")
    print_distribution_table(original)

    print("\nDistribution of Y=X^2:")
    print_distribution_table(squared)


# ============================================================================
# SECTION 46: MONTE CARLO
# ============================================================================

def demonstrate_monte_carlo() -> None:
    section("11. Monte Carlo Simulation")

    for samples in [1_000, 10_000, 100_000]:
        estimate = monte_carlo_pi(samples, seed=42)
        error = abs(estimate - math.pi)

        print(
            f"samples={samples:>7}, "
            f"estimated pi={estimate:.6f}, "
            f"absolute error={error:.6f}"
        )

    subsection("Estimating an event probability")

    # Probability that two independent dice sum to at least 10.
    def sum_at_least_ten(rng: random.Random) -> bool:
        return rng.randint(1, 6) + rng.randint(1, 6) >= 10

    estimate = estimate_probability_by_simulation(
        sum_at_least_ten,
        100_000,
        seed=42,
    )

    exact = 6 / 36

    print("Simulated P(sum >= 10):", estimate)
    print("Exact P(sum >= 10):", exact)


# ============================================================================
# SECTION 47: LAW OF LARGE NUMBERS
# ============================================================================

def demonstrate_law_of_large_numbers() -> None:
    section("12. Law of Large Numbers")

    true_probability = 0.3
    requested_trials = [10, 100, 1_000, 10_000, 100_000]

    results = running_empirical_probability(
        true_probability,
        requested_trials,
        seed=42,
    )

    print("True probability:", true_probability)

    for trials, estimate in results.items():
        print(
            f"Trials={trials:>7}, "
            f"empirical probability={estimate:.6f}, "
            f"error={estimate - true_probability:+.6f}"
        )


# ============================================================================
# SECTION 48: CENTRAL LIMIT THEOREM
# ============================================================================

def demonstrate_central_limit_theorem() -> None:
    section("13. Central Limit Theorem")

    # A deliberately skewed discrete population.
    population = [1, 1, 1, 2, 2, 3, 5, 8, 13, 21]

    population_mean_value = statistics.mean(population)
    population_sd = statistics.pstdev(population)

    print("Population mean:", population_mean_value)
    print("Population standard deviation:", population_sd)

    for sample_size in [2, 10, 30]:
        means, mean_of_means, sd_of_means = central_limit_theorem_simulation(
            population,
            sample_size,
            5_000,
            seed=42,
        )

        theoretical_se = population_sd / math.sqrt(sample_size)

        print(
            f"\nSample size={sample_size}"
            f"\nMean of sample means={mean_of_means:.4f}"
            f"\nObserved SD of sample means={sd_of_means:.4f}"
            f"\nTheoretical SE={theoretical_se:.4f}"
            f"\nFirst five sample means={means[:5]}"
        )


# ============================================================================
# SECTION 49: MEASUREMENT UNCERTAINTY
# ============================================================================

def demonstrate_measurement_uncertainty() -> None:
    section("14. Measurement Uncertainty")

    length = Measurement(20.0, 0.3)
    correction = Measurement(2.0, 0.2)

    total = add_measurements(length, correction)

    print("First measurement:", length)
    print("Second measurement:", correction)
    print("Sum:", total)

    mass = Measurement(50.0, 0.5)
    volume = Measurement(10.0, 0.2)

    density = multiply_measurements(
        mass,
        Measurement(1.0 / volume.value, volume.standard_uncertainty / volume.value ** 2),
    )

    print("Illustrative propagated product/inverse calculation:")
    print("Result:", density)


# ============================================================================
# SECTION 50: MAXIMUM LIKELIHOOD
# ============================================================================

def demonstrate_mle() -> None:
    section("15. Maximum Likelihood Estimation")

    observations = [
        1, 0, 1, 1, 0,
        1, 1, 0, 1, 1,
    ]

    estimate = bernoulli_mle(observations)

    print("Observations:", observations)
    print("Bernoulli MLE for p:", estimate)
    print("Log-likelihood at MLE:", bernoulli_log_likelihood(
        observations,
        estimate,
    ))

    print("\nLog-likelihood comparison:")

    for candidate in [0.2, 0.4, 0.6, 0.8]:
        likelihood = bernoulli_log_likelihood(
            observations,
            candidate,
        )
        print(f"p={candidate:.1f}: log-likelihood={likelihood:.6f}")


# ============================================================================
# SECTION 51: NORMAL APPROXIMATION
# ============================================================================

def demonstrate_normal_approximation() -> None:
    section("16. Normal Approximation to Binomial")

    n = 100
    p = 0.5
    lower = 45
    upper = 55

    exact = sum(
        BinomialDistribution(n, p).pmf(k)
        for k in range(lower, upper + 1)
    )

    approximation = normal_approximation_binomial_probability(
        n,
        p,
        lower,
        upper,
    )

    print("Exact binomial probability:", exact)
    print("Normal approximation:", approximation)
    print("Absolute approximation error:", abs(exact - approximation))


# ============================================================================
# SECTION 52: ENTROPY
# ============================================================================

def demonstrate_entropy() -> None:
    section("17. Entropy as a Measure of Uncertainty")

    fair_coin = [0.5, 0.5]
    biased_coin = [0.9, 0.1]
    fair_die = [1 / 6] * 6

    print("Fair binary entropy:", shannon_entropy(fair_coin), "bits")
    print("Biased binary entropy:", shannon_entropy(biased_coin), "bits")
    print("Fair six-outcome entropy:", shannon_entropy(fair_die), "bits")


# ============================================================================
# SECTION 53: BINOMIAL VS POISSON
# ============================================================================

def demonstrate_binomial_poisson_comparison() -> None:
    section("18. Binomial and Poisson Comparison")

    comparisons = compare_binomial_and_poisson(
        n=100,
        p=0.03,
        maximum_k=7,
    )

    print("k       Binomial       Poisson(lambda=3)")
    print("-" * 45)

    for k, binomial_probability, poisson_probability in comparisons:
        print(
            f"{k:<7}"
            f"{binomial_probability:<15.8f}"
            f"{poisson_probability:.8f}"
        )


# ============================================================================
# SECTION 54: EMPIRICAL VS THEORETICAL DISTRIBUTION
# ============================================================================

def demonstrate_empirical_distribution() -> None:
    section("19. Empirical Versus Theoretical Probability")

    theoretical = DiscreteDistribution(
        outcomes=(1, 2, 3, 4, 5, 6),
        probabilities=(1 / 6,) * 6,
    )

    samples = sample_distribution(
        theoretical,
        sample_size=20_000,
        seed=42,
    )

    empirical = empirical_distribution(samples)

    print("Value     Theoretical     Empirical")
    print("-" * 40)

    for value in theoretical.outcomes:
        print(
            f"{value:<10}"
            f"{theoretical.pmf(value):<15.6f}"
            f"{empirical.get(value, 0.0):.6f}"
        )


# ============================================================================
# SECTION 55: EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    section("20. Edge Cases and Exceptions")

    subsection("Impossible and certain events")

    print("P(impossible event) =", 0.0)
    print("P(certain event) =", 1.0)

    subsection("Bernoulli boundaries")

    for p in [0.0, 1.0]:
        distribution = BernoulliDistribution(p)
        print(
            f"p={p}: "
            f"P(X=0)={distribution.pmf(0)}, "
            f"P(X=1)={distribution.pmf(1)}"
        )

    subsection("Normal extreme quantiles")

    normal = NormalDistribution(0, 1)
    print("Q(0) =", normal.quantile(0))
    print("Q(0.5) =", normal.quantile(0.5))
    print("Q(1) =", normal.quantile(1))

    subsection("Invalid probability")

    try:
        validate_probability(1.5)
    except ValueError as error:
        print("Caught expected error:", error)

    subsection("Conditional probability with zero denominator")

    try:
        conditional_probability(0.0, 0.0)
    except ZeroDivisionError as error:
        print("Caught expected error:", error)

    subsection("Zero-probability points in continuous distributions")

    exponential = ExponentialDistribution(1.0)

    print(
        "For a continuous distribution, P(X=2) is exactly 0 "
        "even though PDF(2) is positive."
    )
    print("Exponential PDF(2) =", exponential.pdf(2))
    print("Probability of the point X=2 =", 0.0)


# ============================================================================
# SECTION 56: COMMON MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    section("21. Common Probability Mistakes")

    examples = [
        (
            "Confusing P(A|B) with P(B|A)",
            "Conditional probability is directional; these probabilities "
            "are generally different.",
        ),
        (
            "Assuming correlation means causation",
            "Association alone does not establish a causal mechanism.",
        ),
        (
            "Using binomial when trials are dependent",
            "The standard binomial model assumes independent trials with "
            "a constant success probability.",
        ),
        (
            "Using hypergeometric when sampling is with replacement",
            "Hypergeometric models sampling without replacement.",
        ),
        (
            "Treating a PDF value as a probability",
            "For continuous variables, probabilities come from areas under "
            "the density over intervals.",
        ),
        (
            "Using population SD when sample SD is required",
            "Population and sample variance use different denominators.",
        ),
        (
            "Ignoring base rates in diagnostic reasoning",
            "Bayes' theorem combines prior probability with evidence.",
        ),
        (
            "Rounding probabilities too early",
            "Premature rounding can accumulate numerical error.",
        ),
    ]

    for mistake, explanation in examples:
        print(f"\n{mistake}")
        print(f"  {explanation}")


# ============================================================================
# SECTION 57: DISTRIBUTION SELECTION
# ============================================================================

def demonstrate_distribution_selection() -> None:
    section("22. Choosing an Appropriate Distribution")

    choices = {
        "Bernoulli": "One binary trial: success/failure.",
        "Binomial": "Number of successes in a fixed number of independent Bernoulli trials.",
        "Geometric": "Number of trials until the first success.",
        "Negative Binomial": "Number of failures until a specified number of successes.",
        "Hypergeometric": "Success count when sampling without replacement.",
        "Poisson": "Count of events over a fixed interval under a constant-rate model.",
        "Uniform": "Continuous values equally likely over a bounded interval.",
        "Exponential": "Waiting time between Poisson-process events.",
        "Normal": "Continuous measurements with approximately symmetric bell-shaped variation.",
        "Log-normal": "Positive, right-skewed measurements whose logarithm is approximately normal.",
    }

    for distribution_name, use_case in choices.items():
        print(f"{distribution_name:<18} -> {use_case}")


# ============================================================================
# SECTION 58: PRODUCTION AND SECURITY CONSIDERATIONS
# ============================================================================

def demonstrate_implementation_considerations() -> None:
    section("23. Implementation, Numerical, and Security Considerations")

    print(
        "Numerical considerations:\n"
        "1. Floating-point values should not normally be compared with ==.\n"
        "2. log1p and expm1 improve accuracy for small arguments.\n"
        "3. Log-likelihoods avoid underflow when multiplying many probabilities.\n"
        "4. Large combinatorial quantities should use exact integer arithmetic "
        "or logarithmic formulations where appropriate.\n"
        "5. Tail probabilities may require specialized numerical algorithms "
        "in production statistical systems."
    )

    print(
        "\nRandomness considerations:\n"
        "1. random.Random is suitable for educational simulations.\n"
        "2. A fixed seed makes demonstrations reproducible.\n"
        "3. Pseudorandom simulation should not be treated as cryptographic "
        "randomness.\n"
        "4. Security-sensitive tokens, keys, and secrets require a "
        "cryptographically secure random generator such as secrets."
    )

    print(
        "\nModel considerations:\n"
        "1. A mathematically correct formula can still produce a misleading "
        "result when the underlying model is inappropriate.\n"
        "2. Probability estimates depend on assumptions about the data-generating "
        "process.\n"
        "3. Independence, stationarity, constant rates, and sampling design "
        "must be examined rather than assumed."
    )


# ============================================================================
# SECTION 59: FULL STUDY PROGRAM
# ============================================================================

def run_all_demonstrations() -> None:
    """Execute the complete educational progression."""
    demonstrate_beginner_probability()
    demonstrate_counting()
    demonstrate_conditional_probability()
    demonstrate_discrete_distributions()
    demonstrate_continuous_distributions()
    demonstrate_measurement_statistics()
    demonstrate_covariance_correlation()
    demonstrate_joint_distributions()
    demonstrate_total_probability()
    demonstrate_transformations()
    demonstrate_monte_carlo()
    demonstrate_law_of_large_numbers()
    demonstrate_central_limit_theorem()
    demonstrate_measurement_uncertainty()
    demonstrate_mle()
    demonstrate_normal_approximation()
    demonstrate_entropy()
    demonstrate_binomial_poisson_comparison()
    demonstrate_empirical_distribution()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    demonstrate_distribution_selection()
    demonstrate_implementation_considerations()


# ============================================================================
# SECTION 60: MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """
    Main execution entry point.

    The script first runs educational demonstrations and then executes its
    unit tests so that the implemented formulas are checked automatically.
    """
    print("Probability Basics: Probability Distributions and Measurement")
    print("Standard-library-only educational implementation")

    run_all_demonstrations()

    section("24. Automated Verification")
    run_tests()
    print("All built-in tests passed.")


if __name__ == "__main__":
    main()
