# How the uncertainty intervals work

*From positive counts to a range for the underlying probability*

### 1. The data and the unknown probability

We observe k positives in n valid trials. The observed proportion is k/n. We want to describe uncertainty about p, the underlying probability of a positive result.

Assuming independent trials with the same probability p, the count of positives has a binomial distribution:

$$
k\mid p,n\sim\mathrm{Binomial}(n,p),\qquad \widehat{p}=\frac{k}{n}.
$$

The count follows the binomial model. The beta distribution below describes our uncertainty about p after seeing the count.

### 2. The prior and posterior

The project starts with the Jeffreys prior. Updating it with k positives and n-k negatives gives the posterior:

$$
p\sim\mathrm{Beta}\!\left(\frac{1}{2},\frac{1}{2}\right),
$$

$$
p\mid k,n\sim\mathrm{Beta}\!\left(k+\frac{1}{2},\ n-k+\frac{1}{2}\right).
$$

So k and n determine the posterior once we have chosen the prior. A different prior would generally give a different posterior.

### 3. Choosing the 95% interval

Let f(p | k,n) denote the posterior density. We choose lower and upper bounds L and U so that each tail contains 2.5% probability:

$$
\int_0^L f(p\mid k,n)\,dp=0.025,\qquad\int_U^1 f(p\mid k,n)\,dp=0.025.
$$

This leaves 95% of the area between the bounds and 5% outside them:

$$
\int_L^U f(p\mid k,n)\,dp=0.95,\qquad 0.025+0.025=0.05.
$$

The integrand f is the height of the density curve. The integral is the area under it and gives a probability. Here, 0.05 is the combined area outside the interval.

## Equal probability, not equal distance

*Why the two sides of an error bar can have different lengths*

Our bounds balance probability in the two tails. They are generally not equally far from 0.5, from k/n, or from the posterior mean. A skewed posterior gives asymmetric error bars.

If F is the posterior cumulative distribution function, the bounds are its 2.5th and 97.5th percentiles:

$$
F(x)=\int_0^x f(p\mid k,n)\,dp,\qquad L=F^{-1}(0.025),\quad U=F^{-1}(0.975).
$$

### A numerical example

For 1 positive in 25 trials, the observed rate is 4%. The posterior is Beta(1.5, 24.5), and the 95% interval is approximately 0.44% to 17.21%.

![Beta posterior with 95% probability between the bounds and 2.5% in each tail.](<uncertainty illustration.png>)

*The graph shows p from 0 to 0.45 to make the shape visible; the full possible range is 0 to 1.*

### If you wanted bounds equally far from 0.5

That would be a different interval rule: set the bounds to 0.5-d and 0.5+d, then solve for d to enclose 95% probability.

$$
L=\frac{1}{2}-d,\quad U=\frac{1}{2}+d,\quad\int_{1/2-d}^{1/2+d}f(p\mid k,n)\,dp=0.95.
$$

This agrees with our equal-tailed rule when the posterior is symmetric about 0.5, which here occurs when k=n/2.

### What this uncertainty includes

Under the sampling and prior assumptions, the interval contains 95% of the posterior probability for p. It describes finite sample uncertainty conditional on the saved labels; it does not include judge errors or changes in prompts or providers. For the group outcome, n counts valid groups.

Implementation: [uncertainties.py](<../Multi Character PoC/uncertainties.py>) uses `beta.ppf([0.025, 0.975], k + 0.5, n - k + 0.5)`. The plotted point is the observed rate `k/n`.

## Walking through the question

*Our conversation, condensed and lightly edited for readability*

### Your first question

I understand that we observe n independent yes/no trials, each with probability p of yes. The number k of yeses follows a binomial distribution, and we observe the proportion k/n. But what is the uncertainty about? Is the question: "For our given result, how likely is the result we saw?" That feels wrong.

### The distinction

Your understanding of the binomial model is right. The important distinction is that we want uncertainty about the underlying probability p, given the result we observed.

The binomial model asks: "Suppose I knew p. How likely would I be to observe k positives in n trials?"

For example, suppose we observed 1 positive in 25 trials. If p = 0.04, seeing 1 positive would be quite plausible. If p = 0.50, seeing only 1 positive would be very unusual. The observed result therefore gives us evidence for some values of p over others.

Our scientific question runs in the other direction: "Having observed 1 positive in 25 trials, what values of p remain plausible, and how much uncertainty do we have about them?"

We know exactly what happened in our sample. What we do not know is the probability that generated those outcomes.

The observed proportion k/n comes from the same data; it is not additional evidence to combine with the binomial. It gives a natural estimate of p, but does not by itself tell us how precise that estimate is. Both 1/25 and 100/2500 give 4%, but the larger sample gives much more information.

### Your observation

"I see, the question is what values of p remain plausible. That is interesting."

### Thinking of p as a slider

Imagine a slider for p running from 0 to 1. At each position, ask: "If this were the true value of p, how likely would our observed count have been?"

Some positions make the observation unsurprising; others make it extremely surprising. As we vary p while keeping the observed data fixed, we get a curve called the likelihood. For the binomial model, it peaks at the observed proportion k/n. Nearby values can also explain the observation well, so the peak alone does not capture our uncertainty.

The likelihood measures how well each proposed p explains the data. It is not yet a probability distribution for p. Combining it with a prior and applying Bayes' rule gives the posterior distribution for p. In our calculation, that posterior is the beta distribution described above.
