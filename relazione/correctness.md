# Symbolic Loop Finding

<!-- 1. obiettivo: trovare un controesemptio per la formula; 
il controesempio è una trace con un ciclo dove f è valida una volta e g mai.
- insieme di tutti gli stati ragg
- tra quali di questi stati f valida e g non valida: stati da cui può partire il ciclo; (precisare che anche se il loop parte prima del "nodo" troviamo lo stesso ciclo anche partendo da lì, ma ci arriviamo in maniera diversa)
- main loop:
    - recur = potential candidates for the cycle
    - pre reach = tutti gli stati che in n >= 1 passi possono raggiungere recur
    - new = sono tutti gli stati che stiamo analizzando ora (la pre in cui g non è valida)
    - 
--> 

The goal of this algorithm is to find an execution for which a given formula in the form of *□ ◊ f -> □ ◊ g* doesn't hold. To do that it's enough to find a loop with at least one state in which *f* holds and *g* never holds.

The algorithm proceeds in two main phases:

1. the algorithm finds the states belonging to the cycle;
2. the algorithm builds the counterexample execution trace, and it has two subphases:
    1. the algorithm builds a loop execution;
    2. the algorithm builds a linear execution leading to the previously built loop.

## 0. Computing the reachable region

The algorithm will always need to ignore all the non-reachable states, therefore as first thing it computes the set of reachable states with the function `compute_reachability`. The algorithm will always stay in the reachable set.

## 1. Checking for correctness of the model

The goal is to find a cycle that invalidates the formula *□ ◊ f -> □ ◊ g*. As showed before, to do that, finding a cycle where g never holds and f holds at least once it's sufficient. Therefore, the algorithm attempts to find a cycle like that.

Note that a cycle like that always contains at least one state where *f* is true and *g* is false. We will refer to this kind of states as **knots**, since we will use a node such that as the join point with the trace from the initial state.

The variable `recur` will always contain the knots, i.e. the possible starting points of the cycle. When `recur` becomes empty then there are no possible cycle and the formula holds.

In this cycle's body, we consider two regions:

- `pre_reach`, which represents all the state that can reach `recur` in a finite number of steps greater than 0;
- `new`, which represents all the states that might be part of the cycle, i.e. the ones reachable in a finite positive number of steps.

Then, we have an inner cycle that updates `pre_reach`: each iteration, it computes every time a region of states which can reach the `new` region in a single step; then it ignores the old ones and adds only the new ones to the `pre_reach` set. Of course, the algorithm takes only the ones where *g* doesn't hold.

Note that this process ensures that `pre_reach` represents a region where there could be a loop within *k* steps, where *k* is the number of iterations. Thus, when all the knots in `recur` are also in `pre_reach`, it's sure that there is at least one state that leads to a cycle in `recur`. The algorithm will now find that state with the function `build_counter_example` (phase 2).

The inner cycle ends when there are no more new states to visit and `recur` never turns out to be a subset of `pre_reach`. This means that there are some states that don't lead the execution into a cycle. We get rid of those states with an intersection with `pre_reach`, i.e. we keep only the knots that might lead to a cycle, then we start again the outer cycle.

The outer cycle runs until there are no more possible candidates for a cycle (the algorithm keep reducing the `recur` region if it doesn't find any valid knot).

## 2. Counter example

Given `recur` and `pre_reach` correctly defined as in (1), the function
`build_counter_examples` finds one of the *knots* that is not satisfying the
condition set by the reactivity formula, that for sure it exists given the condition
of (1).

### 2.1 Finding a *knot*

Within this part we will follow the steps of the execution from all the possible knots. In this context, we define the following invariants after *k* iteration:

- `r` is the region of states that are reachable from `recur` in *k+1* steps and may have a cycle;
- `new` is the region of states that are reachable from the `new` of the previous iteration in a single step;
- both `r` and `new` only contains states where *g* is false;
- `r` intersected with `new` is always empty (there are no duplicates in new - therwise, we would never notice that we'd reach a fix point).

The invariants over `r` are ensured because it is built inductively starting from an
empty region and every time adding to it their successors (obviously only the ones that
keep the property *g* false, this is done by always taking the intersection with
`pre_reach`) until we reach a fix point (i.e. we don't find any new state to insert in 
`r`). It's important to note that every time we save the new frontier (i.e. the
new nodes that we can reach at every new step) in the list `frontiers` (this will
be used later).

At the end of the loop, `r` will contain all the states reachable from `recur` in a finite positive number of steps. Since there is at least one cycle (as guaranteed by the correctness of step (1)), `r` must contain at least one state that is also in `recur` (the knot of the cycle). We then pick one such state (if there are more we can choose any of those), and we will call it `knot` going on.

### 2.2 Constructing the self loop

We construct the self loop starting from `knot` using the `frontiers`, we assume
their correctness from (2.1) in the function `build_loop`:

We find the smallest index `k` in which we can find `knot`, it for sure exists
given the condition imposed in (2.1) and we build a path from `knot` going backwards
(range k ... 0) following the frontiers, picking any of the state between them and 
one of the input necessary to perform that transition (if present) storing if
every time it inside the list `path`.
By inductive construction is clear that at the end of the iteration inside
`path` is present a sequence of state and inputs starting from `knot` and going back to itself.

### 2.3 Reaching the self loop

From (2.1) we know that `knot` is a member of `recur` and from (1) we know that
`recur` is a subset of `reach`. Therefore, `knot` is for sure a reachable state, thus we can
construct a sequence starting from one of the initial state to `knot` in
`build_prefix`.

We perform a Dijkstra-like path finding to find a sequence of regions from the
region of the initial states to reach `knot`. Inductively we construct the list
`frontiers` where we store the sequence of regions that reach the state `knot`,
every one is a distance +1 transition from the preceding one. We know that the
construction terminates since as we said before `knot` is a reachable state.

By iterating `frontier` backwards we extract one of the states and the
input necessary to go from a frontier and his predecessor and insert them inside
the path, it's clear from the construction of `frontiers` that is always present
such state and input, and at the end of iteration path contains the path from
one of the initial states to `knot`.
