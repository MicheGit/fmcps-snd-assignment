# Symbolic Loop Finding

This algorithm's goal is to find an execution such that a given formula in the form of *□ ◊ f -> □ ◊ g* doesn't hold. For this purpose, it's enough to find a loop with at least one state in which *f* holds and *g* never holds.

The algorithm proceeds in two main phases:

1. the algorithm finds the region with the states that may belong to the cycle;
2. the algorithm builds the counterexample execution trace; in turn it has two subphases:
    1. the algorithm builds a loop execution;
    2. the algorithm builds a linear execution leading to the such loop.

## 0. Computing the reachable region

The algorithm will always need to ignore all the non-reachable states, therefore as first thing it computes the set of reachable states with the function `compute_reachability`. The algorithm will always stay in the reachable set.

<p align="center">
  <img src="/relazione/img/reach_def.svg"
       alt="Reachablity of the model">
</p>

## 1. Checking for correctness of the model

<p align="center">
  <img src="/relazione/img/correctness_verification.svg"
       alt="Correctnes of the model">
</p>

The goal is to find a cycle that invalidates the formula *□ ◊ f -> □ ◊ g*. As showed before, it will be enough to find a cycle where *g* never holds and *f* holds at least in one state. We will find the states where *f* holds and *g* doesn't as **knots**; we will use a node of them as the join point with the trace from the initial state.

The variable `recur` will always represent the possible starting points of the cycle (the knots). When `recur` becomes empty then there are no possible cycle and the formula holds. In the outer loop's body, we consider two regions:

- `pre_reach`, which represents all the state that can reach `recur` in a finite number of steps greater than 0;
- `new`, which represents all the states that might be part of the cycle, i.e. the ones reachable in a finite positive number of steps.

Then, we have an inner cycle that updates `pre_reach`: each iteration, it computes a region of states which can reach the `new` region in a single step; then it ignores the old ones and adds only the new ones to the `pre_reach` set. Of course, the algorithm takes only the ones where *g* doesn't hold.

Note that this process ensures that `pre_reach` represents a region where there could be a loop within *k* steps, where *k* is the number of iterations. Thus, when all the knots in `recur` are also in `pre_reach`, it's sure that there is at least one state that leads to a cycle in `recur`. The algorithm will now find that state with the function `build_counter_example` (phase 2).

The inner cycle ends when there are no more new states to visit and `recur` never turns out to be a subset of `pre_reach`. This means that there are some states that don't lead the execution into a cycle. We get rid of those states with an intersection with `pre_reach`, i.e. we keep only the knots that might lead to a cycle, then we start again the outer cycle.

The outer cycle runs until there are no more possible candidates for a cycle (the algorithm keep reducing the `recur` region if it doesn't find any valid knot).



## 2. Counter example

Given `recur` and `pre_reach` correctly defined as in (1), the function
`build_counter_examples` finds one of the *knots* that is not satisfying the
condition set by the reactivity formula, that for sure it exists given the condition
of (1).

### 2.1 Finding a *knot*

<p align="center">
  <img src="/relazione/img/knot_research.svg"
       alt="Knot searching">
</p>

The algorithm checks each element inside the `recur` until it finds the one that starts the loop. The algorithm computes the executions starting from each of those states, always staying in `pre_reach`, until it finds one that goes back to the start.

We define the following invariants after *k* iterations of the inner loop:

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

At the end of the loop, `r` will contain all the states reachable from `recur` in a finite positive number of steps. Since there is at least one cycle (as guaranteed by the correctness of step (1)), `r` must contain at least one state that is also in `recur` (the knot of the cycle). We then pick one such state (if there are more we can choose any of those), and we will refer to this chosen knot with the `s` variable going on.

### 2.2 Building the self loop

<p align="center">
  <img src="/relazione/img/loop_building.svg"
       alt="CE loop building">
</p>


We build the self loop starting from `s`, following the path throug the `frontiers` list; we assume their correctness as a post-condition of the function `build_loop` (2.1).

We find the smallest index `k` in which we can find `s`, by (2.1) it exists for sure. Then we build the loop starting from `s` travelling withing the `k` leading elements of `frontiers`.

In this function, we define the following invariants after *n* iterations:

- `path` represents all the possible paths ending in the knot `s` in *k* steps;
- `curr` is the last state put in `path`.

The algorith builds the path following the frontiers backwards (range *k - 1, ..., 0*), picking a state between them (it doesn't matter which state, but it must be one in the *pre-*region of the last `curr`) and 
one of the inputs necessary to perform the transition (if present) storing it inside the list `path`. 

After the last iteration, `path` represents a full path ending in `s` and starting from a state in the first `frontiers` region (by inductive construction), which we recall, being the states reachable from `recur` in a single step. After that, the algorithm computes the last "pre" transition, adding the input state (if needed) and the knot state.

Therefore it's clear that at the end of the function
`path` holds a sequence of states and inputs starting from `s` going back to `s`.

### 2.3 Reaching the self loop

<p align="center">
  <img src="/relazione/img/prefix_building.svg"
       alt="CE prefix building">
</p>

From (2.1) we know that `s` is a member of `recur` and from (1) we know that
`recur` is a subset of `reach`. Therefore, `s` is for sure a reachable state, thus we can
build a sequence starting from one of the initial states to `s` in
`build_prefix`.

We perform a Dijkstra-like algorithm to find a sequence of regions from the
region of the initial states reaching `s`. Inductively we construct the list
`frontiers` where we store the sequence of regions that might reach the state `s`,
each one step of transition farther from the preceding one. We know that the
construction terminates since, as we said before, `s` is a reachable state.

While iterating `frontier` backwards, we extract one of the states and the
input necessary to go from a frontier and his predecessor and insert them inside
the path, it's clear from the construction of `frontiers` that there are always
such state and input. At the end of the iteration, path contains the path from
one of the initial states to `s`.
