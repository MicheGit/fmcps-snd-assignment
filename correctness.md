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

## 1. Finding the cycle

The goal is to find a cycle that invalidates the formula *□ ◊ f -> □ ◊ g*. As showed before, to do that, finding a cycle where g never holds and f holds at least once it's sufficient. Therefore, the algorithm attempts to find a cycle like that.

Note that a cycle like that always contains at least one state where *f* is true and *g* is false. We will refer to this kind of states as **knots**, since we will use a node such that as the join point with the trace from the initial state.

The variable `recur` will always contain the knots, i.e. the possible starting points of the cycle. When `recur` becomes empty then there are no possible cycle and the formula holds. 

In this cycle's body, we consider two regions:

- `pre_reach`, which represents all the state that can reach `recur` in a finite number of steps greater than 0;
- `new`, which represents all the states that might be part of the cycle, i.e. the ones reachable in a finite positive number of steps.

Then, we have an inner cycle that updates `pre_reach` accordingly, adding every time the new ones. When `recur` is a subset of `pre_reach` it means that 