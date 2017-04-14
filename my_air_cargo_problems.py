from functools import partial
from itertools import product

from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import Node, Problem
from aimacode.utils import expr
from lp_utils import FluentState, decode_state, encode_state
from my_planning_graph import PlanningGraph


class AirCargoProblem(Problem):
    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem
        :param planes: list of str
            planes in the problem
        :param airports: list of str
            airports in the problem
        :param initial: FluentState object
            positive and negative literal fluents (as expr) describing initial state
        :param goal: list of expr
            literal fluents required for goal test
        """
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal)
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        '''
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        '''

        def load_actions():
            '''Create all concrete Load actions and return a list

            :return: list of Action objects
            '''

            def load_action(cargo, plane, airport):
                """Return a load action given a cargo, plane and airport."""
                precond_pos = [
                    expr('At({}, {})'.format(cargo, airport)),
                    expr('At({}, {})'.format(plane, airport)),
                ]
                precond_neg = []
                effect_add = [expr('In({}, {})'.format(cargo, plane))]
                effect_rem = [expr('At({}, {})'.format(cargo, airport))]
                action = expr('Load({}, {}, {})'.format(cargo, plane, airport))

                return Action(action, [precond_pos, precond_neg], [effect_add, effect_rem])

            groups = product(self.cargos, self.planes, self.airports)

            return [load_action(c, p, a) for c, p, a in groups]

        def unload_actions():
            '''Create all concrete Unload actions and return a list

            :return: list of Action objects
            '''

            def unload_action(cargo, plane, airport):
                """Return an unload action given a cargo, plane and airport."""
                precond_pos = [
                    expr('In({}, {})'.format(cargo, plane)),
                    expr('At({}, {})'.format(plane, airport)),
                ]
                precond_neg = []
                effect_add = [expr('At({}, {})'.format(cargo, airport))]
                effect_rem = [expr('In({}, {})'.format(cargo, plane))]
                action = expr('Unload({}, {}, {})'.format(cargo, plane, airport))

                return Action(action, [precond_pos, precond_neg], [effect_add, effect_rem])

            groups = product(self.cargos, self.planes, self.airports)

            return [unload_action(c, p, a) for c, p, a in groups]

        def fly_actions():
            '''Create all concrete Fly actions and return a list

            :return: list of Action objects
            '''
            flys = []

            for fr in self.airports:
                for to in self.airports:
                    if fr != to:
                        for p in self.planes:
                            precond_pos = [
                                expr("At({}, {})".format(p, fr)),
                            ]
                            precond_neg = []
                            effect_add = [expr("At({}, {})".format(p, to))]
                            effect_rem = [expr("At({}, {})".format(p, fr))]
                            fly = Action(
                                expr("Fly({}, {}, {})".format(p, fr, to)), [precond_pos, precond_neg],
                                [effect_add, effect_rem])
                            flys.append(fly)

            return flys

        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """

        def is_possible(clauses, action):
            """Return True if an action is possible given a set of clauses.
            * all positive preconditions must be included in clauses (subset)
            * all negative preconditions must be excluded from clauses (disjoint)"""
            return set(action.precond_pos).issubset(clauses) and \
                   set(action.precond_neg).isdisjoint(clauses)

        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        is_possible_given_clauses = partial(is_possible, set(kb.clauses))

        return list(filter(is_possible_given_clauses, self.actions_list))

    def result(self, state: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).

        :param state: state entering node
        :param action: Action applied
        :return: resulting state after action
        """
        # retrieve preconditions and action effects
        fluent = decode_state(state, self.state_map)
        positives, negatives = set(fluent.pos), set(fluent.neg)
        additions, substractions = set(action.effect_add), set(action.effect_rem)

        # apply add/remove effects on current state
        P = (positives - substractions) | additions
        N = (negatives - additions) | substractions

        return encode_state(FluentState(P, N), self.state_map)

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached

        :param state: str representing state
        :return: bool
        """
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                return False
        return True

    def h_1(self, node: Node):
        # note that this is not a true heuristic
        h_const = 1
        return h_const

    def h_pg_levelsum(self, node: Node):
        '''
        This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        '''
        # requires implemented PlanningGraph class
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        return pg_levelsum

    def h_ignore_preconditions(self, node: Node):
        '''
        This heuristic estimates the minimum number of actions that must be
        carried out from the current state in order to satisfy all of the goal
        conditions by ignoring the preconditions required for an action to be
        executed.
        '''

        def is_absent(clauses, goal):
            """Return True if a goal is absent given a set of clauses."""
            return goal not in clauses

        kb = PropKB()
        kb.tell(decode_state(node.state, self.state_map).pos_sentence())
        is_absent_given_clauses = partial(is_absent, set(kb.clauses))

        return len(list(filter(is_absent_given_clauses, self.goal)))


def air_cargo_p1() -> AirCargoProblem:
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']
    pos = [
        expr('At(C1, SFO)'),
        expr('At(C2, JFK)'),
        expr('At(P1, SFO)'),
        expr('At(P2, JFK)'),
    ]
    neg = [
        expr('At(C2, SFO)'),
        expr('In(C2, P1)'),
        expr('In(C2, P2)'),
        expr('At(C1, JFK)'),
        expr('In(C1, P1)'),
        expr('In(C1, P2)'),
        expr('At(P1, JFK)'),
        expr('At(P2, SFO)'),
    ]
    init = FluentState(pos, neg)
    goal = [
        expr('At(C1, JFK)'),
        expr('At(C2, SFO)'),
    ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    # entities

    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['JFK', 'SFO', 'ATL']

    # initial state

    pos = [
        # planes / airports
        expr('At(P1, SFO)'),
        expr('At(P2, JFK)'),
        expr('At(P3, ATL)'),
        # cargos / airports
        expr('At(C1, SFO)'),
        expr('At(C2, JFK)'),
        expr('At(C3, ATL)'),
    ]

    neg = [
        # planes / airports
        expr('At(P1, JFK)'),
        expr('At(P1, ATL)'),
        expr('At(P2, SFO)'),
        expr('At(P2, ATL)'),
        expr('At(P3, SFO)'),
        expr('At(P3, JFK)'),
        # cargos / airports
        expr('At(C1, JFK)'),
        expr('At(C1, ATL)'),
        expr('At(C2, SFO)'),
        expr('At(C2, ATL)'),
        expr('At(C3, SFO)'),
        expr('At(C3, JFK)'),
        # cargos / planes
        expr('In(C1, P1)'),
        expr('In(C1, P2)'),
        expr('In(C1, P3)'),
        expr('In(C2, P1)'),
        expr('In(C2, P2)'),
        expr('In(C2, P3)'),
        expr('In(C3, P1)'),
        expr('In(C3, P2)'),
        expr('In(C3, P3)'),
    ]

    init = FluentState(pos, neg)

    # goal state

    goal = [
        expr('At(C1, JFK)'),
        expr('At(C2, SFO)'),
        expr('At(C3, SFO)'),
    ]

    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p3() -> AirCargoProblem:
    # entities

    planes = ['P1', 'P2']
    cargos = ['C1', 'C2', 'C3', 'C4']
    airports = ['JFK', 'SFO', 'ATL', 'ORD']

    # initial state

    pos = [
        # planes / airports
        expr('At(P1, SFO)'),
        expr('At(P2, JFK)'),
        # cargos / airports
        expr('At(C1, SFO)'),
        expr('At(C2, JFK)'),
        expr('At(C3, ATL)'),
        expr('At(C4, ORD)'),
    ]

    neg = [
        # planes/ airports
        expr('At(P1, JFK)'),
        expr('At(P1, ATL)'),
        expr('At(P1, ORD)'),
        expr('At(P2, SFO)'),
        expr('At(P2, ATL)'),
        expr('At(P2, ORD)'),
        # cargos / airports
        expr('At(C1, JFK)'),
        expr('At(C1, ATL)'),
        expr('At(C1, ORD)'),
        expr('At(C2, SFO)'),
        expr('At(C2, ATL)'),
        expr('At(C2, ORD)'),
        expr('At(C3, JFK)'),
        expr('At(C3, ORD)'),
        expr('At(C3, SFO)'),
        expr('At(C4, SFO)'),
        expr('At(C4, JFK)'),
        expr('At(C4, ATL)'),
        # cargos / planes
        expr('In(C1, P1)'),
        expr('In(C1, P2)'),
        expr('In(C2, P1)'),
        expr('In(C2, P2)'),
        expr('In(C3, P1)'),
        expr('In(C3, P2)'),
        expr('In(C4, P1)'),
        expr('In(C4, P2)'),
    ]

    init = FluentState(pos, neg)

    # goal state

    goal = [
        expr('At(C1, JFK)'),
        expr('At(C2, SFO)'),
        expr('At(C3, JFK)'),
        expr('At(C4, SFO)'),
    ]

    return AirCargoProblem(cargos, planes, airports, init, goal)
