import pynusmv
import sys
from pynusmv_lower_interface.nusmv.parser import parser 
from collections import deque

from pynusmv.dd import BDD
from pynusmv.glob import prop_database

specTypes = {'LTLSPEC': parser.TOK_LTLSPEC, 'CONTEXT': parser.CONTEXT,
    'IMPLIES': parser.IMPLIES, 'IFF': parser.IFF, 'OR': parser.OR, 'XOR': parser.XOR, 'XNOR': parser.XNOR,
    'AND': parser.AND, 'NOT': parser.NOT, 'ATOM': parser.ATOM, 'NUMBER': parser.NUMBER, 'DOT': parser.DOT,

    'NEXT': parser.OP_NEXT, 'OP_GLOBAL': parser.OP_GLOBAL, 'OP_FUTURE': parser.OP_FUTURE,
    'UNTIL': parser.UNTIL,
    'EQUAL': parser.EQUAL, 'NOTEQUAL': parser.NOTEQUAL, 'LT': parser.LT, 'GT': parser.GT,
    'LE': parser.LE, 'GE': parser.GE, 'TRUE': parser.TRUEEXP, 'FALSE': parser.FALSEEXP
}

basicTypes = {parser.ATOM, parser.NUMBER, parser.TRUEEXP, parser.FALSEEXP, parser.DOT,
              parser.EQUAL, parser.NOTEQUAL, parser.LT, parser.GT, parser.LE, parser.GE}
booleanOp = {parser.AND, parser.OR, parser.XOR, parser.XNOR, parser.IMPLIES, parser.IFF}

def spec_to_bdd(model, spec):
    """
    Given a formula `spec` with no temporal operators, returns a BDD equivalent to
    the formula, that is, a BDD that contains all the states of `model` that
    satisfy `spec`
    """
    bddspec = pynusmv.mc.eval_simple_expression(model, str(spec))
    return bddspec
    
def is_boolean_formula(spec):
    """
    Given a formula `spec`, checks if the formula is a boolean combination of base
    formulas with no temporal operators. 
    """
    if spec.type in basicTypes:
        return True
    if spec.type == specTypes['NOT']:
        return is_boolean_formula(spec.car)
    if spec.type in booleanOp:
        return is_boolean_formula(spec.car) and is_boolean_formula(spec.cdr)
    return False
    
def check_GF_formula(spec):
    """
    Given a formula `spec` checks if the formula is of the form GF f, where f is a 
    boolean combination of base formulas with no temporal operators.
    Returns the formula f if `spec` is in the correct form, None otherwise 
    """
    # check if formula is of type GF f_i
    if spec.type != specTypes['OP_GLOBAL']:
        return False
    spec = spec.car
    if spec.type != specTypes['OP_FUTURE']:
        return False
    if is_boolean_formula(spec.car):
        return spec.car
    else:
        return None

def parse_react(spec):
    """
    Visit the syntactic tree of the formula `spec` to check if it is a reactive formula,
    that is wether the formula is of the form
    
                    GF f -> GF g
    
    where f and g are boolean combination of basic formulas.
    
    If `spec` is a reactive formula, the result is a pair where the first element is the 
    formula f and the second element is the formula g. If `spec` is not a reactive 
    formula, then the result is None.
    """
    # the root of a spec should be of type CONTEXT
    if spec.type != specTypes['CONTEXT']:
        return None
    # the right child of a context is the main formula
    spec = spec.cdr
    # the root of a reactive formula should be of type IMPLIES
    if spec.type != specTypes['IMPLIES']:
        return None
    # Check if lhs of the implication is a GF formula
    f_formula = check_GF_formula(spec.car)
    if f_formula == None:
        return None
    # Create the rhs of the implication is a GF formula
    g_formula = check_GF_formula(spec.cdr)
    if g_formula == None:
        return None
    return (f_formula, g_formula)

def compute_reachability(fsm):
    reach = fsm.init
    new = fsm.init

    while not new.is_false():
        new = fsm.post(new) - reach
        reach += new

    return reach

def build_loop(fsm, s, frontiers):
    has_inputs = len(fsm.bddEnc.inputsVars) > 0

    for k in range(len(frontiers)):
        if s <= frontiers[k]:
            break

    path = [ s.get_str_values() ]
    curr = s

    for i in range(k - 1, -1, -1):
        old = curr
        pred = fsm.pre(curr) * frontiers[i]
        curr = fsm.pick_one_state(pred)
        
        if has_inputs:
            inputs = fsm.get_inputs_between_states(old, curr)
            path.insert(0, fsm.pick_one_inputs(inputs).get_str_values())
        else:
            path.insert(0, {})

        path.insert(0, curr.get_str_values())
    
    # Looping input
    if has_inputs:
        inputs = fsm.get_inputs_between_states(s, s)
        path.insert(0, fsm.pick_one_inputs(inputs).get_str_values())
    else:
        path.insert(0, {})

    path.insert(0, s.get_str_values())
    return path

def build_prefix(fsm, s):
    has_inputs = len(fsm.bddEnc.inputsVars) > 0
    
    # Insert inside frontiers the regions to reach s
    # [ init ... pre_s ]
    curr = fsm.init 
    frontiers = []
    while not s <= curr:
        frontiers.append(curr)
        curr = fsm.post(curr) - curr

    path = []
    last = s
    # Construct the path traversing the frontiers in reverse
    for frontier in reversed(frontiers):
        can_reach_last = fsm.pre(last)
        # The current state is one of the states that can reach last in
        # one step
        current_state = fsm.pick_one_state(frontier * can_reach_last)
        
        if has_inputs:
            inputs = fsm.get_inputs_between_states(current_state, last)
            path.insert(0, fsm.pick_one_inputs(inputs).get_str_values())
        else:
            path.insert(0, {})

        path.insert(0, current_state.get_str_values())

        last = current_state
        
    return path

def build_counter_example(fsm, recur, pre_reach):
    r = BDD.false()
    new = fsm.post(recur)
    frontiers = [ new ]

    while not new.is_false():
        r += new
        new = fsm.post(new) * pre_reach
        new -= r
        frontiers.append(new)

    r *= recur
    
    s = fsm.pick_one_state(recur * r)
    return tuple(build_prefix(fsm, s) + build_loop(fsm, s, frontiers))

    # One (or more) of the states inside recur is a looping one
    # for s in fsm.pick_all_states(recur):
    #     r = BDD.false()
    #     new = fsm.post(s) * pre_reach
    #     frontiers = [ new ]
    #     while not new.is_false():
    #         r += new
    #         new = fsm.post(new) * pre_reach
    #         new -= r
    #         frontiers.append(new)

    #     r *= recur
    #     if s <= r:
    #         return tuple(build_prefix(fsm, s) + build_loop(fsm, s, frontiers))

    # raise ValueError("The recurrence region does not contain any loop")

def check_react_spec(spec):
    """
    Return whether the loaded SMV model satisfies or not the GR(1) formula
    `spec`, that is, whether all executions of the model satisfies `spec`
    or not. 
    """
    parsed = parse_react(spec)
    if parsed == None:
        return None

    fsm = prop_database().master.bddFsm

    f, g = parsed
    spec_f     = spec_to_bdd(fsm,  f)
    spec_not_g = spec_to_bdd(fsm, ~g)

    reach = compute_reachability(fsm)
    
    # Potential candidate for the cycle
    # □ ◊ f -> □ ◊ g
    # So the cycle contains a state that makes f true but the later ones
    # don't ever make g true
    recur = reach * spec_f * spec_not_g
    while not recur.is_false(): # Iterate con recur_i

        pre_reach = BDD.false()                 # States that can reach recur 
                                                # in >= 1 steps
        new       = fsm.pre(recur) * spec_not_g # Ensure at least one 
                                                # transition and that g is not
                                                # true

        while not new.is_false():
            pre_reach += new

            if recur <= pre_reach:
                # In recur there is for sure a path that has the following
                # properties starts from a state where f is true and g it's
                # never true
                return False, build_counter_example(
                        fsm, recur, pre_reach)

            new = (fsm.pre(new) - pre_reach) * spec_not_g

        recur *= pre_reach # recur_{i+1}

    return True, []

if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename.smv")
    sys.exit(1)

pynusmv.init.init_nusmv()
filename = sys.argv[1]
pynusmv.glob.load_from_file(filename)
pynusmv.glob.compute_model()
type_ltl = pynusmv.prop.propTypes['LTL']
for prop in pynusmv.glob.prop_database():
    spec = prop.expr
    print(spec)
    if prop.type != type_ltl:
        print("property is not LTLSPEC, skipping")
        continue
    res = check_react_spec(spec)
    if res == None:
        print('Property is not a GR(1) formula, skipping')
    if res[0] == True:
        print("Property is respected")
    elif res[0] == False:
        print("Property is not respected")
        print("Counterexample:", res[1])

pynusmv.init.deinit_nusmv()
