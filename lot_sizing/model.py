"""Module responsible for modelling the lot sizing problem mathematically."""

from itertools import product

from ortools.linear_solver import pywraplp

from lot_sizing.input import Input


class MipModel:
    """Models the lot sizing problem via mixed integer programming."""

    def __init__(self, prob_input: Input, solver: pywraplp):
        self.prob_input = prob_input
        self.solver = solver
        self.production_vars = None
        self.state_vars = None
        self.stock_vars = None
        self.transition_vars = None

    @staticmethod
    def _add_production_variables(num_types: int, num_time_periods: int, solver: pywraplp):
        """Create production variables.

        A production variable $x^t_p$ is a binary variable which is one if and only if an item of machine type $t$ is
        produced in time period $p$.

        :param num_types: the number of considered machines types
        :param num_time_periods: the number of considered time periods
        :param solver: the underlying solver for which to built the variables
        :return: A dictionary mapping each (machine_type, time_period) tuple to its production variable
        """
        production_vars = dict()
        for (machine_type, time_period) in product(range(num_types), range(num_time_periods)):
            production_vars[(machine_type, time_period)] = solver.BoolVar(
                name=f'x_{machine_type}_{time_period}')
        return production_vars

    @staticmethod
    def _add_state_variables(num_types: int, num_time_periods: int, solver: pywraplp):
        """Create state variables.

        A state variable $y^t_p$ is a binary variable which is one if and only if the machine is configured
        to produce an item of machine type $t$ in time period $p$.

        :param num_types: the number of considered machines types
        :param num_time_periods: the number of considered time periods
        :param solver: the underlying solver for which to built the variables
        :return: A dictionary mapping each (machine_type, time_period) tuple to its state variable

        """
        state_vars = dict()
        for (machine_type, time_period) in product(range(num_types), range(num_time_periods)):
            state_vars[(machine_type, time_period)] = solver.BoolVar(name=f'y_{machine_type}_{time_period}')
        return state_vars

    @staticmethod
    def _add_stock_variables(num_types: int, num_time_periods: int, solver: pywraplp):
        """Create stock variables.

         A stock variable $s^t_p$ is a non-negative real variable which represents the number of items of machine type
         $t$ on stock in time period $p$.

        :param num_types: the number of considered machines types
        :param num_time_periods: the number of considered time periods
        :param solver: the underlying solver for which to built the variables
        :return: A dictionary mapping each (machine_type, time_period) tuple to its stock variable
        """
        stock_vars = dict()
        for (machine_type, time_period) in product(range(num_types), range(-1, num_time_periods)):
            stock_vars[(machine_type, time_period)] = solver.NumVar(lb=0., ub=solver.infinity(),
                                                                    name=f's_{machine_type}_{time_period}')
        return stock_vars

    @staticmethod
    def _add_transition_variables(num_types: int, num_time_periods: int, solver: pywraplp):
        """Create transition variables.

        A transition variable $u^ij_p$ is a binary variable which is one if and only if the machine's state
        changed from being configured for machine type $i$ in time period $p-1$ to machine type $j$ in time period $p$.
        """
        transition_vars = dict()
        for type_i, type_j, time_period in product(range(num_types), range(num_types), range(1, num_time_periods)):
            transition_vars[(type_i, type_j, time_period)] = solver.BoolVar(name=f'u_{type_i}_{type_j}_{time_period}')
        return transition_vars

    def _add_initial_stock_constraints(self):
        """Add initial stock constraints.
        
        The initial stock constraints ensure that the initial stock of any machine type is zero.
        """
        for machine_type in range(self.prob_input.num_types):
            stock_var = self.stock_vars[(machine_type, -1)]
            self.solver.Add(stock_var == 0., name=f'init_stock_{machine_type}')

    def _add_demand_constraints(self):
        """Add demand constraints.

        A demand constraint wrt machine type $t$ and time period $p$ ensures that the stock of machine type $t$ in
        time period $p-1$ plus the value of the production variable $x^t_p$ equals the demand of $t$ in time period
        $p$ plus the stock in time period $p$.
        """
        for (machine_type, time_period) in product(range(self.prob_input.num_types),
                                                   range(self.prob_input.num_time_periods)):
            lhs = self.stock_vars[(machine_type, time_period - 1)] + self.production_vars[(machine_type, time_period)]
            rhs = self.prob_input.get_demand(machine_type, time_period) + self.stock_vars[
                (machine_type, time_period)]
            self.solver.Add(lhs == rhs, name=f'demand_{machine_type}_{time_period}')

    def _add_state_constraints(self):
        """Add state constraints.

        A state constraint wrt machine type $t$ and time period $p$ ensures that the machine is ready to produce machine
        type $t$ in time period $p$ when producing machine type $t$ in time period $p$.
        """
        for (machine_type, time_period) in product(range(self.prob_input.num_types),
                                                   range(self.prob_input.num_time_periods)):
            lhs = self.production_vars[(machine_type, time_period)]
            rhs = self.state_vars[(machine_type, time_period)]
            self.solver.Add(lhs <= rhs, name=f'state_{machine_type}_{time_period}')

    def _add_transition_constraints(self):
        """Add transition constraints.

        A transition constraint for the transition variable $u^ij_p$ ensures that $u^ij_p$ is set to one if both state
        variables $y^i_{p-1}$ and $y^j_p$ are one.
        """
        for (type_i, type_j, time_period) in product(range(self.prob_input.num_types), range(self.prob_input.num_types),
                                                     range(1, self.prob_input.num_time_periods)):
            lhs = self.transition_vars[(type_i, type_j, time_period)]
            rhs = self.state_vars[(type_i, time_period - 1)] + self.state_vars[(type_j, time_period)] - 1
            self.solver.Add(lhs >= rhs, name=f'transition_{type_i}_{type_j}_{time_period}')

    def _add_configuration_constraints(self):
        """Add configuration constraints.

        A configuration constraint for time period $p$ ensures that the machine is configured to being able to produce
        exactly one machine type.
        """
        for (time_period) in range(self.prob_input.num_time_periods):
            lhs = self.solver.Sum(
                [self.state_vars[(machine_type, time_period)] for machine_type in range(self.prob_input.num_types)])
            rhs = 1
            self.solver.Add(lhs == rhs, name=f'config_{time_period}')

    def _add_objective(self):
        """Add objective function and minimization direction.

        The objective function is the sum of stocking costs and transition costs.
        The stocking costs represent the costs incurred for producing items before their due data, i.e., putting items
        into stock. The transition costs represent the costs incurred for changing the machine configuration from one
        machine type to another.
        """
        inventory_costs = [self.prob_input.inventory_cost * self.stock_vars[(machine_type, time_period)] for
                           machine_type, time_period in product(range(self.prob_input.num_types),
                                                                range(self.prob_input.num_time_periods))]
        stock_objective = self.solver.Sum(inventory_costs)
        transition_costs = [
            self.prob_input.transition_cost[type_i][type_j] * self.transition_vars[(type_i, type_j, time_period)]
            for type_i, type_j, time_period in
            product(range(self.prob_input.num_types), range(self.prob_input.num_types),
                    range(1, self.prob_input.num_time_periods)) if type_i != type_j
        ]
        transition_objective = self.solver.Sum(transition_costs)
        self.solver.Minimize(stock_objective + transition_objective)

    @classmethod
    def build_mip(cls, prob_input: Input, solver):
        """Build mip formulation for the given lot sizing instance via the given solver.

        :param prob_input: the input problem instance to consider
        :param solver: the solver instance to use
        """
        ins = cls(prob_input, solver)
        ins.production_vars = ins._add_production_variables(prob_input.num_types, prob_input.num_time_periods, solver)
        ins.state_vars = ins._add_state_variables(prob_input.num_types, prob_input.num_time_periods, solver)
        ins.stock_vars = ins._add_stock_variables(prob_input.num_types, prob_input.num_time_periods, solver)
        ins.transition_vars = ins._add_transition_variables(prob_input.num_types, prob_input.num_time_periods, solver)
        ins._add_initial_stock_constraints()
        ins._add_demand_constraints()
        ins._add_state_constraints()
        ins._add_configuration_constraints()
        ins._add_transition_constraints()
        ins._add_objective()
        return ins
