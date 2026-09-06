# Probability Basics: Probability Distributions and Measurement

## 1. Introduction

Probability is the mathematical framework for describing uncertainty. It provides a language for expressing how likely events are, how uncertainty changes when information becomes available, and how random quantities behave across repeated observations.

This study script develops probability from elementary ideas such as outcomes and events to probability distributions, random variables, expectation, variance, conditional probability, Bayes' theorem, simulation, measurement uncertainty, and advanced distributional concepts.

The implementation is intentionally self-contained and uses only the Python standard library. Mathematical definitions are accompanied by executable implementations so that formulas can be examined computationally.

The central progression is:

1. Experiments and sample spaces
2. Events and probability rules
3. Counting and combinatorics
4. Conditional probability
5. Independence
6. Bayes' theorem
7. Random variables
8. Probability mass functions
9. Probability density functions
10. Cumulative distribution functions
11. Expectation and moments
12. Variance and standard deviation
13. Important discrete distributions
14. Important continuous distributions
15. Joint and marginal distributions
16. Transformations
17. Sampling and simulation
18. Measurement and uncertainty
19. Statistical estimation
20. Advanced approximations and information measures

---

## 2. Experiments, Outcomes, and Sample Spaces

A **random experiment** is a process whose exact outcome cannot be known with certainty before the experiment occurs.

Examples include:

- Rolling a die
- Tossing a coin
- Selecting an item from a population
- Measuring a physical quantity
- Counting incoming requests during a time interval

An **outcome** is one possible result of an experiment.

The **sample space**, usually denoted by `S` or `Ω`, is the set of all possible outcomes.

For a standard six-sided die:

`S = {1, 2, 3, 4, 5, 6}`

An **event** is a subset of the sample space.

For example, the event of rolling an even number is:

`A = {2, 4, 6}`

The script explicitly represents sample spaces and events with Python sets. This makes set operations directly correspond to probability operations.

---

## 3. Basic Event Operations

For events `A` and `B`:

### Union

The union contains outcomes belonging to either event:

`A ∪ B`

The probability rule is:

`P(A ∪ B) = P(A) + P(B) - P(A ∩ B)`

The intersection must be subtracted because it is counted twice when the two probabilities are added.

### Intersection

The intersection contains outcomes belonging to both events:

`A ∩ B`

### Complement

The complement contains outcomes that are not in the event:

`Aᶜ`

Its probability is:

`P(Aᶜ) = 1 - P(A)`

### Mutually Exclusive Events

Two events are mutually exclusive when they cannot occur together:

`A ∩ B = ∅`

Therefore:

`P(A ∩ B) = 0`

and:

`P(A ∪ B) = P(A) + P(B)`

Mutually exclusive events should not be confused with independent events. Events that are mutually exclusive and have positive probability are not independent.

---

## 4. Probability Definitions

### Classical Probability

When elementary outcomes are equally likely:

`P(A) = Number of favorable outcomes / Number of possible outcomes`

For a fair six-sided die:

`P(even) = 3 / 6 = 0.5`

The script implements this using `probability_from_equally_likely_outcomes()`.

### Empirical Probability

Empirical probability is estimated from observed data:

`P̂(A) = Number of observed occurrences of A / Number of observations`

For example, if an event occurs 37 times in 100 trials:

`P̂(A) = 0.37`

Empirical probability is an estimate, not necessarily the exact underlying probability.

### Subjective Probability

Subjective probability represents a degree of belief based on available information. It can be useful in decision analysis and Bayesian reasoning.

The three viewpoints are different interpretations of probability rather than unrelated mathematical systems.

---

## 5. Kolmogorov Probability Axioms

A probability measure satisfies three fundamental axioms.

### Non-negativity

For every event `A`:

`P(A) >= 0`

### Normalization

The probability of the entire sample space is:

`P(S) = 1`

### Countable Additivity

For mutually exclusive events:

`P(A₁ ∪ A₂ ∪ ...) = P(A₁) + P(A₂) + ...`

The familiar rules of probability can be derived from these principles.

A probability cannot be negative or greater than one.

---

## 6. Counting Principles

Probability problems often depend on determining the number of possible outcomes.

The script covers:

- Factorials
- Permutations
- Combinations
- Enumeration with Python's `itertools`

### Factorial

For a nonnegative integer `n`:

`n! = n × (n-1) × ... × 2 × 1`

By convention:

`0! = 1`

### Permutations

When order matters:

`P(n,r) = n! / (n-r)!`

For example, selecting president and vice president from five people is an ordered selection.

### Combinations

When order does not matter:

`C(n,r) = n! / [r!(n-r)!]`

Selecting two members from a five-person group is an unordered selection.

The distinction between permutations and combinations is one of the most common sources of mistakes in elementary probability.

---

## 7. Conditional Probability

Conditional probability measures the probability of an event given that another event is known to have occurred.

The definition is:

`P(A|B) = P(A ∩ B) / P(B)`

provided:

`P(B) > 0`

The notation `P(A|B)` should be read as "probability of A given B."

Conditional probability is directional.

In general:

`P(A|B) != P(B|A)`

This distinction is essential in diagnostic testing, classification, risk analysis, and Bayesian inference.

The script raises an exception when the conditioning event has probability zero because the ordinary conditional probability formula would divide by zero.

---

## 8. Multiplication Rule

The conditional probability formula can be rearranged to obtain:

`P(A ∩ B) = P(A|B)P(B)`

Equivalently:

`P(A ∩ B) = P(B|A)P(A)`

This rule is fundamental for constructing joint probabilities.

For multiple events:

`P(A₁ ∩ A₂ ∩ ... ∩ Aₙ)`

can be decomposed into a sequence of conditional probabilities.

---

## 9. Independence

Events `A` and `B` are independent if knowledge of one does not change the probability of the other.

Mathematically:

`P(A|B) = P(A)`

when `P(B) > 0`.

An equivalent condition is:

`P(A ∩ B) = P(A)P(B)`

The script includes `independent_intersection_probability()` to demonstrate this relationship.

Independence is an assumption about the relationship between events. It should not be inferred simply because two events seem unrelated.

---

## 10. Bayes' Theorem

Bayes' theorem follows from the multiplication rule:

`P(A|B) = P(B|A)P(A) / P(B)`

In Bayesian terminology:

- `P(A)` is the prior probability.
- `P(B|A)` is the likelihood.
- `P(B)` is the evidence or marginal probability.
- `P(A|B)` is the posterior probability.

Bayes' theorem is especially important when interpreting evidence.

### Base-Rate Effect

A common mistake is to focus only on test sensitivity or likelihood while ignoring the prevalence of the underlying condition.

The script demonstrates a diagnostic-style example in which a rare condition has a highly accurate test but the probability of the condition after a positive result is still substantially affected by the low base rate.

The key principle is:

> Strong evidence does not automatically imply a high posterior probability when the prior probability is very small.

---

## 11. Law of Total Probability

Suppose `B₁, B₂, ..., Bₙ` form a partition of the sample space.

Then:

`P(A) = Σ P(A|Bᵢ)P(Bᵢ)`

This is the **law of total probability**.

It allows a probability to be decomposed into mutually exclusive cases.

For example, if a population is divided into three groups, the overall event probability can be calculated by weighting each group's conditional probability by that group's population probability.

The script implements this using `total_probability()`.

---

## 12. Law of Total Expectation

The corresponding expectation identity is:

`E[X] = Σ E[X|Bᵢ]P(Bᵢ)`

This allows a complicated expectation to be decomposed into conditional cases.

It is particularly useful in hierarchical models, mixture distributions, decision analysis, and stochastic processes.

---

# 13. Random Variables

A **random variable** is a function that maps outcomes of a random experiment to numerical values.

There are two major types.

### Discrete Random Variable

A discrete random variable takes values from a finite or countably infinite set.

Examples:

- Number of heads
- Number of customers
- Number of defective items
- Number of system failures

### Continuous Random Variable

A continuous random variable can take values over intervals of the real number line.

Examples:

- Height
- Temperature
- Waiting time
- Measurement error

The word "random variable" does not mean that the variable itself is necessarily unpredictable in every circumstance. It means that its value is determined by the outcome of a random mechanism.

---

# 14. Probability Mass Function

A discrete random variable uses a **probability mass function**, or PMF:

`p(x) = P(X=x)`

A valid PMF must satisfy:

`p(x) >= 0`

and:

`Σ p(x) = 1`

The custom `DiscreteDistribution` class implements:

- PMF evaluation
- CDF evaluation
- Expected value
- Variance
- Standard deviation
- Random sampling

For a discrete random variable:

`P(a <= X <= b)`

is calculated by summing the probabilities of all values in the interval.

---

# 15. Cumulative Distribution Function

The **cumulative distribution function**, or CDF, is:

`F(x) = P(X <= x)`

The CDF applies to both discrete and continuous variables.

Its fundamental properties include:

- `0 <= F(x) <= 1`
- It is non-decreasing.
- Its limiting value as `x` approaches negative infinity is zero.
- Its limiting value as `x` approaches positive infinity is one.

For a discrete variable, the CDF has jumps.

For a continuous variable, the CDF is generally continuous.

---

# 16. Probability Density Function

A continuous random variable is often described using a **probability density function**, or PDF.

For a continuous variable:

`P(X=x) = 0`

for any individual point `x`.

This does not mean the point has no relevance. It means probability is obtained from areas over intervals:

`P(a <= X <= b) = ∫[a,b] f(x) dx`

The density value `f(x)` is not itself a probability.

A density can even be greater than one if the distribution is concentrated over a sufficiently narrow interval. The integral of the density over the entire support must equal one.

---

# 17. Bernoulli Distribution

A Bernoulli random variable represents one binary trial.

Possible values:

`X ∈ {0,1}`

where:

`P(X=1)=p`

and:

`P(X=0)=1-p`

The mean is:

`E[X] = p`

The variance is:

`Var(X) = p(1-p)`

The `BernoulliDistribution` class implements the PMF, CDF, moments, and sampling.

The boundary cases `p=0` and `p=1` are valid. They correspond to deterministic outcomes.

---

# 18. Binomial Distribution

The binomial distribution counts the number of successes in a fixed number `n` of independent Bernoulli trials with common success probability `p`.

Notation:

`X ~ Binomial(n,p)`

PMF:

`P(X=k) = C(n,k)p^k(1-p)^(n-k)`

Mean:

`E[X] = np`

Variance:

`Var(X) = np(1-p)`

Standard deviation:

`SD(X) = sqrt(np(1-p))`

The binomial model requires important assumptions:

1. A fixed number of trials.
2. Two outcomes per trial.
3. Constant success probability.
4. Independent trials.

If sampling is performed without replacement from a finite population, the hypergeometric distribution may be more appropriate.

---

# 19. Geometric Distribution

The geometric distribution models the number of trials required to obtain the first success.

For `k = 1,2,3,...`:

`P(X=k) = (1-p)^(k-1)p`

Mean:

`E[X] = 1/p`

Variance:

`Var(X) = (1-p)/p²`

The geometric distribution has a memoryless property.

For appropriate nonnegative integers:

`P(X>s+t | X>s) = P(X>t)`

The script demonstrates this property explicitly for the exponential distribution, which is the continuous analogue of the geometric distribution.

---

# 20. Negative Binomial Distribution

The negative binomial distribution generalizes the geometric model.

Instead of asking for the number of trials until the first success, it can model the number of failures before the `r`-th success.

For `k` failures before the `r`-th success:

`P(K=k) = C(k+r-1,r-1)p^r(1-p)^k`

This model is useful when the event of interest is the accumulation of several successes rather than only the first success.

---

# 21. Hypergeometric Distribution

The hypergeometric distribution applies to sampling without replacement.

Let:

- `N` = population size
- `K` = number of successes in the population
- `n` = number of draws
- `k` = number of successes drawn

Then:

`P(X=k) = C(K,k)C(N-K,n-k) / C(N,n)`

The most important distinction from the binomial distribution is dependence.

When sampling without replacement, one draw changes the composition of the remaining population. Consequently, the trials are generally not independent.

---

# 22. Poisson Distribution

The Poisson distribution models event counts over a fixed interval when events occur under an appropriate constant-rate model.

Notation:

`X ~ Poisson(λ)`

PMF:

`P(X=k) = exp(-λ) λ^k / k!`

Mean:

`E[X] = λ`

Variance:

`Var(X) = λ`

The equality of the mean and variance is a distinctive property of the Poisson distribution.

Typical applications include:

- Event counts
- Arrival counts
- Defect counts
- Requests per interval
- Incident counts

The Poisson model should not be used merely because the data are counts. The underlying event-generation assumptions must also be reasonable.

---

# 23. Binomial Versus Poisson

The Poisson distribution can approximate a binomial distribution when:

- `n` is relatively large.
- `p` is relatively small.
- `λ = np`.

The script compares:

`Binomial(100, 0.03)`

with:

`Poisson(3)`

This illustrates why the Poisson distribution is frequently used as a computationally simpler approximation to rare-event binomial counts.

The approximation becomes less appropriate when the binomial probability is not small or when the number of trials is insufficiently large.

---

# 24. Continuous Uniform Distribution

The continuous uniform distribution assigns constant density over a bounded interval.

For `a <= x <= b`:

`f(x) = 1/(b-a)`

Mean:

`E[X] = (a+b)/2`

Variance:

`Var(X) = (b-a)²/12`

For `X ~ Uniform(0,10)`:

`P(2 <= X <= 7) = 5/10 = 0.5`

The script implements the PDF, CDF, quantile function, moments, interval probability, and sampling.

---

# 25. Exponential Distribution

The exponential distribution models continuous waiting times under an appropriate constant-rate process.

With rate `λ`:

`f(x) = λ exp(-λx), x >= 0`

CDF:

`F(x) = 1-exp(-λx)`

Mean:

`1/λ`

Variance:

`1/λ²`

The exponential distribution is memoryless.

This is unusual among continuous distributions and makes it mathematically important in stochastic-process models.

### Numerical Detail

The script uses:

`expm1()`

and:

`log1p()`

where appropriate.

These functions improve numerical accuracy when their arguments are close to zero.

---

# 26. Normal Distribution

The normal distribution is one of the most important continuous distributions.

Notation:

`X ~ Normal(μ, σ²)`

where:

- `μ` is the mean.
- `σ` is the standard deviation.
- `σ²` is the variance.

PDF:

`f(x) = [1/(σ√(2π))] exp[-(x-μ)²/(2σ²)]`

Mean:

`μ`

Variance:

`σ²`

The normal distribution is:

- Symmetric
- Unimodal
- Bell-shaped
- Completely determined by its mean and standard deviation

The script implements:

- PDF
- CDF
- Interval probability
- Standardization
- Quantiles
- Random sampling

---

# 27. Standard Normal Distribution and Z-Scores

The standard normal distribution has:

`μ = 0`

and:

`σ = 1`

A value can be standardized using:

`z = (x-μ)/σ`

The resulting z-score indicates how many standard deviations an observation lies above or below the mean.

For example, if:

`μ = 100`

`σ = 15`

and:

`x = 130`

then:

`z = (130-100)/15 = 2`

Thus the observation is two standard deviations above the mean.

Z-scores allow observations from different normal distributions to be placed on a common standardized scale.

---

# 28. Quantiles and Percentiles

A quantile identifies a value below which a specified proportion of observations lies.

For a continuous distribution, the quantile function is the inverse CDF:

`Q(p) = F⁻¹(p)`

Examples:

- `Q(0.50)` is the median.
- `Q(0.25)` is the first quartile.
- `Q(0.75)` is the third quartile.
- `Q(0.95)` is the 95th percentile.

Quantiles are particularly useful for skewed distributions because they do not depend on symmetry.

The script implements quantiles for several theoretical distributions and a simple nearest-rank sample quantile.

Different statistical systems can use different interpolation rules for sample quantiles. Therefore, two software systems may produce slightly different sample quartiles from the same finite dataset.

---

# 29. Log-Normal Distribution

A positive random variable is log-normal when its logarithm is normally distributed.

If:

`Y ~ Normal(μ, σ²)`

and:

`X = exp(Y)`

then:

`X ~ LogNormal(μ, σ²)`

The mean is:

`E[X] = exp(μ + σ²/2)`

The variance is:

`Var(X) = [exp(σ²)-1]exp(2μ+σ²)`

Log-normal distributions are useful for positive, right-skewed quantities produced by multiplicative processes.

The distinction between normal and log-normal modeling is important. A normal variable can take negative values, while a log-normal variable is strictly positive.

---

# 30. Expected Value

The expected value is the probability-weighted average of a random variable.

For a discrete random variable:

`E[X] = Σ x p(x)`

The expected value does not necessarily have to be an outcome that can actually occur.

For example, a fair six-sided die has:

`E[X] = 3.5`

even though 3.5 is not an attainable roll.

Expectation represents long-run average behavior under repeated sampling, not a guarantee about any individual observation.

---

# 31. Variance

Variance measures the average squared deviation from the mean.

Definition:

`Var(X) = E[(X-E[X])²]`

An equivalent identity is:

`Var(X) = E[X²] - E[X]²`

The second identity is often convenient computationally.

Variance has squared units.

If a measurement is in meters, its variance is in square meters.

---

# 32. Standard Deviation

Standard deviation is:

`SD(X) = sqrt(Var(X))`

It returns the measure of dispersion to the original units of the variable.

For example, if a dataset represents height in centimeters, standard deviation is also measured in centimeters.

Standard deviation is easier to interpret than variance when discussing the scale of ordinary measurement variation.

---

# 33. Population Versus Sample Variance

For a population of size `N`:

`σ² = Σ(xᵢ-μ)²/N`

For a sample of size `n`, the conventional unbiased estimator of population variance is:

`s² = Σ(xᵢ-x̄)²/(n-1)`

The use of `n-1` is called **Bessel's correction**.

The distinction matters because the sample mean is estimated from the same observations used to calculate the sample variance.

The script implements both population and sample variance to make the distinction explicit.

---

# 34. Standard Error

The standard error of the sample mean is:

`SE(x̄) = s/√n`

where:

- `s` is sample standard deviation.
- `n` is sample size.

As sample size increases, standard error decreases at a rate proportional to `1/√n`.

This is different from standard deviation.

- Standard deviation describes variation among individual observations.
- Standard error describes variation in an estimator, such as the sample mean.

---

# 35. Covariance

Covariance measures joint variation between two variables.

For random variables:

`Cov(X,Y) = E[(X-E[X])(Y-E[Y])]`

For a sample, the conventional sample covariance uses:

`1/(n-1)`

as the scaling factor.

Interpretation:

- Positive covariance indicates that the variables tend to move in the same direction.
- Negative covariance indicates opposite movement.
- Near-zero covariance indicates little linear co-movement.

Covariance depends on the units of the variables, so its numerical magnitude is often difficult to compare across datasets.

---

# 36. Correlation

Pearson correlation standardizes covariance:

`ρ(X,Y) = Cov(X,Y)/(σXσY)`

For sample data, the corresponding sample correlation is commonly denoted by `r`.

Correlation lies between:

`-1 <= r <= 1`

Interpretation:

- `r ≈ 1`: strong positive linear association
- `r ≈ -1`: strong negative linear association
- `r ≈ 0`: weak linear association

Correlation does not establish causation.

A nonlinear relationship can also have a small Pearson correlation even when the variables are strongly related in a nonlinear way.

---

# 37. Joint Distributions

When two random variables are considered simultaneously, their behavior can be described by a **joint distribution**.

For discrete variables:

`P(X=x,Y=y)`

is the joint probability.

A joint distribution must satisfy:

`Σx Σy P(X=x,Y=y) = 1`

The script represents a joint distribution using a dictionary whose keys are pairs.

---

# 38. Marginal Distributions

A marginal distribution is obtained by summing over the other variable.

For example:

`P(X=x) = Σy P(X=x,Y=y)`

Similarly:

`P(Y=y) = Σx P(X=x,Y=y)`

The script's `marginal_distribution()` function implements these operations.

Marginal distributions are useful when the joint relationship is known but interest is focused on only one variable.

---

# 39. Conditional Distributions from Joint Distributions

A conditional distribution can be derived from a joint distribution.

For example:

`P(Y=y|X=x) = P(X=x,Y=y)/P(X=x)`

The script demonstrates this normalization process.

The denominator must be nonzero because conditioning on an event of probability zero is not defined by the elementary ratio formula.

---

# 40. Independence of Random Variables

Random variables `X` and `Y` are independent when their joint distribution factors:

`P(X=x,Y=y) = P(X=x)P(Y=y)`

for all relevant values.

Independence is stronger than zero covariance.

For many distributions, two variables can have zero covariance while still being dependent.

Therefore:

`independence => zero covariance`

under ordinary finite-moment conditions, but:

`zero covariance does not generally imply independence`

---

# 41. Transformations of Random Variables

If:

`Y = g(X)`

then the distribution of `Y` can differ significantly from the distribution of `X`.

For discrete variables, probabilities associated with different `X` values must be combined when they map to the same `Y`.

The script demonstrates this using:

`Y = X²`

For example, different input values could produce the same transformed value.

For continuous transformations, Jacobian methods are often required when deriving exact transformed densities. The simple discrete implementation in the script illustrates the underlying probability-mass principle without hiding the transformation process behind a statistical library.

---

# 42. Monte Carlo Simulation

Monte Carlo methods estimate numerical quantities using random sampling.

The script estimates π using random points inside a unit square.

For a quarter-circle of radius one:

`Area = π/4`

The unit square has area:

`1`

Therefore:

`π ≈ 4 × proportion of points inside the quarter-circle`

The estimate becomes more stable as the number of samples increases.

Monte Carlo methods are useful when:

- An exact analytical calculation is difficult.
- A high-dimensional integral must be estimated.
- A complex system can be simulated but is difficult to solve symbolically.
- An event probability can be observed through repeated simulation.

---

# 43. Simulation-Based Probability Estimation

If an event occurs `K` times in `N` independent simulations, the empirical estimate is:

`P̂(A) = K/N`

The estimator becomes more stable as the number of simulations increases.

Simulation does not automatically produce an exact answer. It introduces sampling error.

A simulation estimate should therefore be interpreted as an estimate with uncertainty.

---

# 44. Law of Large Numbers

The Law of Large Numbers states, informally, that under suitable conditions, sample averages converge toward their expected values as the number of observations increases.

For a Bernoulli event with true probability `p`:

`K/N -> p`

as `N` becomes large.

The script simulates this by tracking empirical probabilities for increasing trial counts.

The Law of Large Numbers explains why empirical frequencies often become more stable with larger samples.

It does not imply that every finite sample will be close to the theoretical value.

---

# 45. Central Limit Theorem

The Central Limit Theorem is one of the central results of probability and statistics.

Under broad conditions, the standardized sample mean becomes approximately normal as sample size increases.

For independent observations with population mean `μ` and variance `σ²`:

`x̄`

has:

`E[x̄] = μ`

and:

`Var(x̄) = σ²/n`

Therefore:

`SE(x̄) = σ/√n`

The Central Limit Theorem concerns the distribution of an estimator across repeated samples. It does not claim that the original population must be normally distributed.

The script uses a deliberately skewed population and repeatedly samples from it to show how the distribution of sample means becomes more stable and approximately normal.

---

# 46. Normal Approximation to the Binomial

For sufficiently large `n` and suitable `p`, a binomial random variable can be approximated by a normal random variable:

`X ~ Binomial(n,p)`

with:

`μ = np`

and:

`σ² = np(1-p)`

The script uses a **continuity correction**.

For an integer interval:

`a <= X <= b`

the approximation uses:

`a-0.5 < Y < b+0.5`

This correction often improves the approximation because the binomial distribution is discrete while the normal distribution is continuous.

---

# 47. Entropy as a Measure of Uncertainty

Shannon entropy for a discrete distribution is:

`H(X) = -Σ p(x) log₂ p(x)`

when the logarithm is base 2.

The resulting unit is the **bit**.

For a fair binary distribution:

`H = 1 bit`

For a highly biased binary distribution, entropy is lower because the outcome is more predictable.

Entropy measures uncertainty in the probability distribution, not physical randomness itself.

A uniform distribution over a fixed number of outcomes has maximum entropy among distributions over that same finite support.

---

# 48. Measurement and Probability

Measurement is inherently connected to probability because repeated measurements can vary.

Variation can result from:

- Instrument limitations
- Environmental conditions
- Sampling variation
- Observer effects
- Process variation
- Random noise
- Model uncertainty

A measurement should therefore often be considered as an estimate rather than an exact mathematical constant.

---

# 49. Measurement Uncertainty

The script introduces a `Measurement` data structure containing:

- A measured value
- A standard uncertainty

For independent quantities, uncertainty can often be propagated through mathematical operations.

For addition or subtraction:

`u_z = sqrt(u_x² + u_y²)`

under the independent-error approximation.

For multiplication, relative uncertainty is commonly propagated approximately as:

`(u_z/|z|)² ≈ (u_x/|x|)² + (u_y/|y|)²`

The assumptions behind uncertainty propagation matter. The formulas are approximations based on local linearization and independence assumptions.

---

# 50. Uncertainty Is Not the Same as Error

These concepts should be distinguished.

### Measurement Error

Error is the difference between a measured value and a true or reference value.

### Measurement Uncertainty

Uncertainty describes incomplete knowledge about the measurement result.

A measurement can have uncertainty even when the exact error is unknown.

In practical measurement systems, the true value is often not directly observable, so uncertainty provides a quantitative description of confidence or variability around the reported result.

---

# 51. Maximum Likelihood Estimation

The script estimates the Bernoulli parameter using maximum likelihood.

Suppose observations are:

`x₁, x₂, ..., xₙ`

where each `xᵢ` is either zero or one.

The likelihood is:

`L(p) = Π p^xᵢ (1-p)^(1-xᵢ)`

The maximum likelihood estimator is:

`p̂ = number of successes / n`

The script also calculates the log-likelihood:

`log L(p) = Σ[xᵢ log(p) + (1-xᵢ)log(1-p)]`

Using logarithms is computationally important because products of many small probabilities can underflow numerically.

---

# 52. Why Log-Likelihood Is Useful

Suppose a likelihood contains hundreds or thousands of probability terms.

Direct multiplication can produce a number too small for floating-point representation.

Taking logarithms converts multiplication into addition:

`log(ab) = log(a) + log(b)`

Therefore:

`log Π pᵢ = Σ log(pᵢ)`

The location of the maximum does not change because the logarithm is strictly increasing.

This is why log-likelihoods are standard in statistical estimation and probabilistic computation.

The script handles boundary cases such as `p=0` and `p=1` explicitly.

---

# 53. Numerical Stability

Probability computations can involve very small or very large quantities.

Important practices include:

### Avoid unnecessary equality comparisons

Floating-point values should generally be compared using a tolerance.

The script uses `math.isclose()` where appropriate.

### Use stable elementary functions

For expressions such as:

`1-exp(-x)`

`math.expm1()` can provide greater accuracy when `x` is small.

For:

`log(1-x)`

`math.log1p(-x)` is often more accurate than directly computing `log(1-x)`.

### Use logarithms for products

Large likelihood products can underflow. Logarithms convert products to sums and improve numerical behavior.

### Avoid premature rounding

Probabilities and intermediate calculations should retain sufficient precision until final presentation.

---

# 54. Edge Cases

The script explicitly demonstrates several important boundary conditions.

### Probability 0

An event with probability zero is impossible under the modeled probability system.

### Probability 1

An event with probability one is certain under the modeled probability system.

### Bernoulli `p=0`

The outcome is always zero.

### Bernoulli `p=1`

The outcome is always one.

### Continuous Point Probabilities

For continuous random variables:

`P(X=x)=0`

for any individual point.

This does not imply that the PDF at that point must be zero.

### Zero Conditional Probability

`P(A|B)` is undefined under the ordinary ratio definition when:

`P(B)=0`

### Degenerate Variance

A variable that is always equal to the same constant has:

`Var(X)=0`

Its standard deviation is also zero.

Standardized scores are therefore undefined for a zero-variance variable.

---

# 55. Common Probability Mistakes

## Confusing Conditional Probabilities

`P(A|B)` and `P(B|A)` are generally different.

Bayes' theorem explains how to relate them.

## Confusing Independence and Mutual Exclusivity

Mutually exclusive events with positive probability cannot be independent.

## Using the Wrong Sampling Model

Sampling without replacement generally creates dependence and may require a hypergeometric model.

## Treating a PDF as a Probability

A density value is not a probability.

Probability is an area under the density.

## Ignoring Base Rates

Evidence must be interpreted together with prior probability.

## Assuming Correlation Implies Causation

Correlation describes association, not causal structure.

## Confusing Standard Deviation and Standard Error

Standard deviation describes variation among observations.

Standard error describes variability of an estimator.

## Rounding Too Early

Premature rounding can produce accumulated numerical error.

## Assuming Simulation Is Exact

Simulation produces an estimate and has Monte Carlo sampling error.

---

# 56. Distribution Selection

The following distinctions are central.

| Distribution | Main Use | Key Assumption or Structure |
|---|---|---|
| Bernoulli | One binary trial | One success/failure experiment |
| Binomial | Number of successes | Fixed independent trials with common `p` |
| Geometric | Trials until first success | Independent Bernoulli trials |
| Negative Binomial | Failures before `r` successes | Repeated Bernoulli trials |
| Hypergeometric | Successes without replacement | Finite population, sampling without replacement |
| Poisson | Event counts | Constant-rate count model |
| Uniform | Bounded continuous uncertainty | Constant density over an interval |
| Exponential | Waiting time | Constant-rate memoryless model |
| Normal | Symmetric continuous measurements | Bell-shaped continuous variation |
| Log-normal | Positive right-skewed quantities | Logarithm is approximately normal |

The choice of distribution should follow the data-generating mechanism rather than merely the visual appearance of the data.

---

# 57. Binomial Versus Hypergeometric

This is a particularly important comparison.

### Binomial

Use when the trials are approximately independent and the success probability remains constant.

### Hypergeometric

Use when sampling is performed without replacement from a finite population.

For example, selecting five items from a batch of twenty items without replacing each selected item changes the composition of the remaining batch.

When the population is very large relative to the sample, the dependence introduced by sampling without replacement can become small, and a binomial approximation may sometimes be reasonable.

---

# 58. Binomial Versus Poisson

The binomial distribution has:

- Fixed number of opportunities
- Two outcomes per opportunity
- Success probability `p`

The Poisson distribution has:

- A count over an interval
- A rate parameter `λ`
- No fixed maximum count

The Poisson distribution is particularly useful for rare-event counts.

The relationship:

`λ = np`

connects the Poisson approximation to the binomial model.

---

# 59. Geometric Versus Exponential

These distributions share the memoryless property.

### Geometric

Discrete:

`1, 2, 3, ...`

Counts the number of trials until a success.

### Exponential

Continuous:

`x >= 0`

Models a waiting time.

The geometric distribution is the discrete counterpart of the exponential distribution in this respect.

---

# 60. Discrete Versus Continuous Probability

| Property | Discrete | Continuous |
|---|---|---|
| Individual point probability | Can be positive | Exactly zero |
| Main function | PMF | PDF |
| Interval probability | Sum | Integral |
| CDF | Step-like | Generally continuous |
| Typical example | Number of defects | Waiting time |
| Quantiles | Inverse-style threshold | Inverse CDF |

The distinction is conceptual as well as computational.

For discrete variables:

`P(X=x)` is meaningful directly.

For continuous variables:

`P(X=x)=0`

and interval probabilities are the important quantities.

---

# 61. Expected Value Versus Median

The mean and median measure different aspects of a distribution.

The mean is sensitive to extreme observations.

The median is a quantile and is generally more robust to extreme values.

For symmetric distributions such as a normal distribution:

`mean = median`

For skewed distributions such as many log-normal distributions:

`mean != median`

This distinction becomes important when interpreting real-world measurements.

---

# 62. Variance Versus Standard Deviation

Variance is mathematically convenient because it behaves well under many algebraic operations.

Standard deviation is easier to interpret because it has the same units as the underlying variable.

For example:

- Measurement: meters
- Variance: square meters
- Standard deviation: meters

Both are important, but they serve different practical purposes.

---

# 63. Expected Value Is Not Necessarily Typical

An expected value can fall outside the set of possible individual outcomes.

For a fair die:

`E[X] = 3.5`

but no single roll equals 3.5.

Expectation represents an average over the probability distribution, not necessarily a value that will appear in an individual experiment.

---

# 64. Probability Modeling Versus Reality

A probability model is an abstraction.

For a model to be useful, assumptions must be evaluated.

Questions include:

- Are observations independent?
- Is the probability constant?
- Is the rate constant?
- Is sampling with or without replacement?
- Is the distribution stationary?
- Are measurements approximately normally distributed?
- Are outliers genuine or measurement artifacts?
- Is the sample representative?
- Are missing observations informative?

A mathematically correct calculation can still be inappropriate if the model assumptions do not describe the real process.

---

# 65. Simulation Reproducibility

The script uses `random.Random(seed)` in many simulations.

A fixed seed makes the sequence reproducible.

This is valuable for:

- Debugging
- Teaching
- Unit testing
- Comparing algorithm changes
- Reproducing experiments

A seed does not make pseudorandom numbers cryptographically secure.

Reproducibility and security are separate requirements.

---

# 66. Security Considerations for Randomness

The ordinary `random` module is appropriate for educational simulations and many non-security statistical tasks.

It should not be used for:

- Password generation
- Authentication tokens
- Session identifiers
- Cryptographic keys
- Security-sensitive secrets

Security-sensitive randomness requires a cryptographically secure source such as Python's `secrets` module.

Probability simulation and cryptographic randomness have different goals. Statistical unpredictability for a simulation is not equivalent to adversarial unpredictability.

---

# 67. Production Implementation Considerations

A teaching implementation and a production statistical library have different priorities.

A production implementation may require:

- More efficient algorithms
- Accurate tail probabilities
- Stable inverse CDF algorithms
- Vectorized computation
- High-quality random-number generators
- Parallel random streams
- Careful handling of extreme parameter values
- Numerical error analysis
- Extensive validation
- Independent verification
- Reproducibility controls
- Domain-specific diagnostics

For example, the script calculates a normal quantile using binary search because it is transparent and educational. A high-performance scientific implementation would typically use a specialized inverse-normal algorithm.

Similarly, the Poisson sampler uses a straightforward algorithm that is easy to understand but may become inefficient for large rates.

---

# 68. Testing Probability Implementations

Probability formulas are especially suitable for automated testing because many distributions have known mathematical identities.

The script contains unit tests covering:

- Classical probability
- Complements
- Union rules
- Bernoulli moments
- Binomial probabilities
- Poisson moments
- Uniform distribution
- Exponential distribution
- Normal standardization
- Measurement uncertainty
- Entropy
- Bayes' theorem

Tests help detect implementation errors such as:

- Incorrect exponents
- Missing normalization
- Off-by-one errors
- Invalid parameter handling
- Incorrect variance formulas
- Boundary-condition failures

---

# 69. Validation Rules

Probability software should validate inputs before calculations.

Important constraints include:

- Probabilities must lie in `[0,1]`.
- Distribution probabilities must sum to one.
- Standard deviations must be positive.
- Variances must be nonnegative.
- Sample sizes must be positive.
- Combinatorial parameters must satisfy their mathematical constraints.
- Hypergeometric parameters must describe a valid finite population.
- Rates such as Poisson and exponential parameters must be positive.

Explicit validation prevents invalid mathematical states from silently propagating through a program.

---

# 70. Real-World Applications

Probability distributions and measurement are used across many domains.

### Engineering

- Reliability
- Failure rates
- Measurement uncertainty
- Quality control
- Sensor noise

### Operations

- Queue arrivals
- Service times
- Capacity planning
- Demand modeling

### Finance

- Return distributions
- Risk measurement
- Portfolio uncertainty
- Scenario analysis

### Healthcare and Diagnostics

- Diagnostic testing
- Disease prevalence
- Survival and waiting times
- Measurement uncertainty

### Technology

- Request counts
- System reliability
- Error rates
- Randomized algorithms
- Capacity planning

### Manufacturing

- Defect rates
- Sampling inspection
- Process variation
- Quality control

### Data Analysis

- Sampling distributions
- Estimation
- Confidence intervals
- Hypothesis testing
- Predictive uncertainty

---

# 71. Conceptual Relationship Between Probability and Measurement

The central relationship can be represented as:

`Real process`
   
`↓`

`Random variation`

`↓`

`Observations`

`↓`

`Probability model`

`↓`

`Distribution`

`↓`

`Numerical measurements`

`↓`

`Inference and decisions`

A measurement process produces observations. Probability models describe how those observations can vary. Statistical methods then use the observed data to estimate unknown quantities and quantify uncertainty.

---

# 72. Important Mathematical Relationships

The following identities are central to the material covered in the script.

### Complement

`P(Aᶜ) = 1-P(A)`

### Union

`P(A∪B) = P(A)+P(B)-P(A∩B)`

### Conditional probability

`P(A|B) = P(A∩B)/P(B)`

### Multiplication

`P(A∩B)=P(A|B)P(B)`

### Independence

`P(A∩B)=P(A)P(B)`

### Bayes

`P(A|B)=P(B|A)P(A)/P(B)`

### Total probability

`P(A)=ΣP(A|Bᵢ)P(Bᵢ)`

### Expected value

`E[X]=Σxp(x)`

### Variance

`Var(X)=E[X²]-E[X]²`

### Standard deviation

`SD(X)=√Var(X)`

### Standard error

`SE(x̄)=s/√n`

### Z-score

`z=(x-μ)/σ`

### Pearson correlation

`ρ=Cov(X,Y)/(σXσY)`

These relationships form the mathematical foundation of the implementations in the script.

---

# 73. Script Structure

The Python file is organized progressively.

### Fundamentals

The first sections implement:

- Probability validation
- Sample spaces
- Events
- Complements
- Unions
- Intersections
- Counting

### Conditional Probability

The next layer implements:

- Conditional probability
- Independence
- Bayes' theorem
- Total probability
- Total expectation

### Discrete Distributions

The script then implements:

- Generic finite distributions
- Bernoulli
- Binomial
- Geometric
- Negative binomial
- Hypergeometric
- Poisson

### Continuous Distributions

It implements:

- Uniform
- Exponential
- Normal
- Log-normal

### Measurement and Statistics

It covers:

- Mean
- Variance
- Standard deviation
- Standard error
- Quantiles
- Covariance
- Correlation
- Measurement uncertainty

### Advanced Probability

It includes:

- Joint distributions
- Marginal distributions
- Conditional distributions
- Transformations
- Monte Carlo simulation
- Law of Large Numbers
- Central Limit Theorem
- Maximum likelihood
- Normal approximation
- Entropy

### Verification

The final portion runs automated unit tests.

---

# 74. Running the Script

The script requires a standard Python installation.

Run it from a terminal with:

    python probability_distributions_measurement.py

The program executes demonstrations sequentially and then runs the built-in test suite.

The examples are deterministic where a fixed random seed is supplied, which makes many simulation results reproducible.

---

# 75. Interpreting the Output

The script intentionally prints mathematical quantities rather than merely defining them.

Examples include:

- Exact probabilities
- Empirical probabilities
- PMFs
- CDFs
- Means
- Variances
- Standard deviations
- Quantiles
- Simulation estimates
- Approximation errors
- Measurement uncertainties
- Log-likelihood values

Comparing exact and empirical quantities is particularly useful for understanding the distinction between theoretical probability and observed frequency.

---

# 76. Important Limitations

The implementations are designed for conceptual clarity and standalone study.

They are not intended to replace specialized statistical software for high-performance or high-stakes analysis.

Important limitations include:

1. Some numerical algorithms are deliberately simple.
2. Tail probabilities can require more specialized numerical methods.
3. Quantile interpolation for empirical samples can differ among statistical conventions.
4. Measurement uncertainty propagation assumes particular mathematical conditions.
5. Monte Carlo estimates have sampling error.
6. Distribution formulas are valid only under their stated assumptions.
7. Simulation quality depends on the random-number generator and simulation design.
8. Real-world inference requires appropriate sampling and data-quality procedures.

---

# 77. Core Distinctions to Retain

Several distinctions should remain conceptually separate.

| Concept A | Concept B | Essential Difference |
|---|---|---|
| Probability | Frequency | Probability describes a model; frequency describes observed data |
| PMF | PDF | PMF assigns point probabilities; PDF describes continuous density |
| Mean | Median | Mean is an arithmetic expectation; median is a central quantile |
| Variance | Standard deviation | Variance uses squared units; SD uses original units |
| SD | Standard error | SD describes observations; SE describes estimator variability |
| Covariance | Correlation | Correlation standardizes covariance |
| Independence | Zero correlation | Independence is stronger |
| Mutual exclusivity | Independence | Mutually exclusive positive-probability events are not independent |
| Binomial | Hypergeometric | Independent trials versus sampling without replacement |
| Binomial | Poisson | Fixed trials versus event counts, with Poisson often approximating rare binomial events |
| Geometric | Exponential | Discrete trials versus continuous waiting time |
| Normal | Log-normal | Symmetric real-valued variable versus positive right-skewed variable |
| Theoretical probability | Monte Carlo estimate | Exact model quantity versus simulation-based estimate |

---

# 78. Mathematical Perspective

Probability distributions provide a structured representation of uncertainty.

A distribution can be examined through multiple layers:

`Support`

describes possible values.

`PMF/PDF`

describes probability mass or density.

`CDF`

describes accumulated probability.

`Quantile function`

maps probabilities to thresholds.

`Expectation`

describes average behavior.

`Variance`

describes dispersion.

`Higher moments`

describe additional distributional properties.

`Joint distribution`

describes multiple variables together.

`Conditional distribution`

describes behavior under information.

`Entropy`

describes uncertainty in a distribution.

These representations are related but not interchangeable.

---

# 79. Relationship Between Theory, Data, and Simulation

A complete probability analysis often involves three complementary perspectives.

### Mathematical Theory

Derive the exact probability or distribution from assumptions.

### Empirical Measurement

Collect observations and estimate quantities from data.

### Simulation

Generate artificial observations from a model to study its behavior.

For example, a fair die has theoretical probability:

`P(6)=1/6`

A finite experiment may produce:

`P̂(6)=0.17`

A simulation can independently generate thousands of die rolls and demonstrate that the empirical proportion tends toward `1/6`.

These three perspectives answer different questions and should not be conflated.

---

# 80. Final Conceptual Framework

The script develops a complete chain of reasoning:

`Uncertain experiment`

→ `Sample space`

→ `Event`

→ `Probability`

→ `Conditional probability`

→ `Random variable`

→ `Probability distribution`

→ `Expected value and variance`

→ `Sampling`

→ `Measurement`

→ `Estimation`

→ `Simulation`

→ `Uncertainty`

The most important practical principle is that probability calculations are meaningful only when the underlying model and assumptions correspond reasonably well to the process being studied. Mathematical precision and modeling validity are separate requirements, and both are necessary for reliable probabilistic analysis.
