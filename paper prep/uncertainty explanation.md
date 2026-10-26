# What are we uncertain about?

*A step-by-step explanation incorporating our discussion*

### 1. We observe outcomes, and estimate a probability

We perform $n$ independent yes/no trials, each with the same unknown probability $p$ of yes. Before observing them, the number of yeses is a random count $K$. Afterwards, we have a particular observed count $k$.

$$
K\mid p,n\sim\mathrm{Binomial}(n,p),\qquad \widehat p=\frac{k}{n}.
$$

The symbol $\widehat p$ ("p-hat") is the observed proportion and an estimate of $p$. We observe $k$ and $n$; we have not observed $p$ itself. The proportion is calculated from the same data, so it is not extra evidence to combine with them.

### 2. What is the question we are trying to answer?

> Your question: "For our given result, how likely is the result we saw?"

The binomial model answers a forward question: "Suppose I knew $p$. How likely would I be to observe $k$ positives in $n$ trials?"

Our scientific question runs in the other direction: "Having observed $k$ positives in $n$ trials, what values of $p$ remain plausible, and how much uncertainty do we have about them?"

We know what happened in our sample. We are uncertain about the underlying probability that generated those outcomes.

For example, 1 positive in 25 trials would be quite plausible if $p=0.04$, but very unusual if $p=0.50$. The observation therefore gives us evidence for some values of $p$ over others.

### 3. Hold the data fixed and move a slider for p

Imagine moving $p$ from 0 to 1. At every position, ask how likely our fixed observed count would have been. The resulting curve is the likelihood, denoted $\mathcal{L}(p)$:

$$
\mathcal{L}(p)=\Pr(K=k\mid p,n)=\binom{n}{k}p^k(1-p)^{n-k}.
$$

For the binomial model, this curve peaks at $\widehat p=k/n$. Nearby values can also explain the observation well. The likelihood is not yet a probability distribution over $p$.

The estimate alone does not express precision: both 1/25 and 100/2500 give 4%, but the larger sample gives much more information about $p$.

## From likelihood to a beta posterior

*The data, a prior, and Bayes' theorem*

### 4. The missing ingredient is a prior

We have the data $k,n$ and the binomial likelihood. The additional ingredient is a prior: a probability distribution for $p$ specified before using these observations. The estimate $\widehat p$ is a summary of the data, not a substitute for this prior.

Bayes' theorem combines these ingredients to give the posterior: our updated probability distribution for $p$ after observing the data.

$$
\mathrm{posterior}\ \propto\ \mathrm{likelihood}\times\mathrm{prior}.
$$

The symbol $\propto$ means "proportional to." Multiply the likelihood by the prior density, then scale the resulting curve so that its total area is 1.

Writing $\pi(p)$ for the prior density, the full formula is:

$$
\pi(p\mid k,n)=\frac{\mathcal{L}(p)\,\pi(p)}{\int_0^1\mathcal{L}(q)\,\pi(q)\,dq}.
$$

The denominator is the total area before scaling. The symbol $q$ is just an integration variable that runs over the possible probabilities; it is not another unknown parameter in our experiment.

### 5. Why a beta distribution appears

The beta family describes distributions on the probability range from 0 to 1. Its two positive shape parameters are often called $\alpha$ and $\beta$. If the prior is beta, updating it with a binomial likelihood produces another beta distribution:

$$
p\sim\mathrm{Beta}(\alpha,\beta)\quad\Longrightarrow\quad p\mid k,n\sim\mathrm{Beta}(\alpha+k,\,\beta+n-k).
$$

The first parameter gains the $k$ positives; the second gains the $n-k$ negatives. The prior and posterior belong to the same distribution family, with different parameter values.

### 6. The prior used in this project

We use the Jeffreys prior, which sets $\alpha=\beta=1/2$:

$$
p\sim\mathrm{Beta}\!\left(\frac{1}{2},\frac{1}{2}\right),
$$

$$
p\mid k,n\sim\mathrm{Beta}\!\left(k+\frac{1}{2},\,n-k+\frac{1}{2}\right).
$$

So $k$ and $n$ determine our posterior once this prior has been chosen. It is uncertainty about $p$ that follows this beta distribution. The count of positives follows the binomial model.

## Choosing the uncertainty bounds

*From the posterior curve to a 95% credible interval*

### 7. Density is a height; probability is an area

Call the posterior density $f(p\mid k,n)$. This is the same posterior written as $\pi(p\mid k,n)$ on the previous page; the letter is simply a label. Its total area over the possible range is 1:

$$
\int_0^1 f(p\mid k,n)\,dp=1.
$$

The integrand $f(p\mid k,n)$ is the height of the curve. Integrating it over an interval gives the probability assigned to that interval. We choose bounds using areas, rather than setting the curve's height to 0.05.

### 8. Put 2.5% in each tail

For our 95% equal-tailed credible interval, choose the lower bound $L$ and upper bound $U$ so that 2.5% of the posterior probability lies below $L$ and 2.5% lies above $U$:

$$
\int_0^L f(p\mid k,n)\,dp=0.025,\qquad \int_U^1 f(p\mid k,n)\,dp=0.025.
$$

That leaves 95% between the bounds. The 0.05 is the total probability outside the interval, split equally between the two tails:

$$
\int_L^U f(p\mid k,n)\,dp=0.95,\qquad 0.025+0.025=0.05.
$$

### 9. Equal probability does not mean equal distance

The bounds balance the areas in the tails. They generally are not equally far from 0.5, from $\widehat p$, or from the posterior mean. A skewed posterior gives asymmetric error bars.

If you wanted bounds equally far from the centre of the range $[0,1]$, you would impose the following different rule and solve for $d$:

$$
L=\frac{1}{2}-d,\quad U=\frac{1}{2}+d,\quad \int_{1/2-d}^{1/2+d} f(p\mid k,n)\,dp=0.95.
$$

That is not the rule the project uses. The two rules agree when the posterior is symmetric about 0.5, which here occurs when $k=n/2$.

### 10. How the computer finds our bounds

Let $F(x)$ be the cumulative posterior probability up to $x$. Our bounds are the values at which it reaches 0.025 and 0.975:

$$
F(x)=\int_0^x f(p\mid k,n)\,dp,\qquad L=F^{-1}(0.025),\quad U=F^{-1}(0.975).
$$

Here $F^{-1}$ means the inverse cumulative distribution function: supply a probability, and it returns the corresponding value of $p$.

## A worked example

*One positive in 25 trials*

The data are $k=1$ and $n=25$. The observed proportion is 4%. Using our Jeffreys prior gives:

$$
\widehat p=\frac{1}{25}=0.04,\qquad p\mid k,n\sim\mathrm{Beta}(1.5,24.5).
$$

The 2.5th and 97.5th percentiles of that posterior give:

$$
L\approx 0.00435,\qquad U\approx 0.17213.
$$

Thus, our estimate is 4%, and our 95% equal-tailed credible interval is approximately 0.44% to 17.21%.

![Posterior density with 95% probability between L and U and 2.5% in each tail.](<uncertainty illustration.png>)

*The graph shows p from 0 to 0.45 to make the shape visible; the full possible range is 0 to 1. The dotted blue line marks the observed proportion.*

### 11. Read the shaded areas

The blue area between $L$ and $U$ contains 95% of the posterior probability. Each orange tail contains 2.5%. Notice how different the distances from the observed 4% to the two bounds are.

The interval therefore expresses which values of the underlying $p$ remain plausible under our model and prior. It is not a probability assigned to the result that already happened, and it is not a prediction interval for the count in a new set of trials.

### 12. What this uncertainty includes

This describes finite sample uncertainty conditional on the saved labels and the independent, common-probability trial model. It does not include judge errors or changes in prompts or providers. For the multi-agent group outcome, $n$ counts valid groups, not individual agents.

Implementation: [uncertainties.py](<../Multi Character PoC/uncertainties.py>) computes `beta.ppf([0.025, 0.975], k + 0.5, n - k + 0.5)`. The reported point estimate is `k/n`.
