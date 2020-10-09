"""Module responsible for handling the input file."""

from itertools import product

from typing import List


class InputError(Exception):
    """Base class for input exceptions."""


class Input:
    """Class responsible for reading the input file."""

    def __init__(self):
        self.num_types = None
        self.num_time_periods = None
        self.demand = dict()
        self.overall_demand = None
        self.inventory_cost = None
        self.transition_cost = dict()

    def __str__(self):
        """Return string representation."""
        return f'{self.num_time_periods}\n{self.num_types}\n' + "\n".join(
            [str(v) for v in self.demand.values()]) + "\n" + str(self.inventory_cost) + "\n" + "\n".join(
            [str(v) for v in self.transition_cost.values()])

    @classmethod
    def read_file(cls, file: str):
        """Reads given input file and creates instance containing corresponding data.

        :param file: the input filename (including path)
        """
        ins = cls()
        try:
            with open(file, mode='r', encoding='utf8') as file_input:
                times, types, *rest = (line.strip() for line in file_input if line.strip() != '')
                ins.num_time_periods = int(times)
                ins.num_types = int(types)
                for i, demand in enumerate(rest[:ins.num_types]):
                    ins.demand[i] = [int(j) for j in demand.split()]
                ins.overall_demand = sum([sum(ins.demand[i]) for i in range(ins.num_types)])
                ins.inventory_cost = int(rest[ins.num_types])
                for i, cost in enumerate(rest[-ins.num_types:]):
                    ins.transition_cost[i] = [int(j) for j in cost.split()]

        except FileNotFoundError:
            raise InputError(f'File {file} not found.')
        else:
            return ins

    def get_demand(self, machine_type: int, time_period: int) -> int:
        """Returns the demand of machine type at time slot.

        :param machine_type: the machine type to consider
        :param time_period: the time period to consider
        """
        if time_period >= self.num_time_periods:
            raise InputError(
                f'Given time period {time_period} expected to be smaller than overall number {self.num_time_periods}.')
        if machine_type >= self.num_types:
            raise InputError(
                f'Given machine type {machine_type} expected to be smaller than overall number {self.num_types}.')
        return self.demand[machine_type][time_period]

    def get_overall_demand(self, machine_type: int, time_period: int) -> int:
        """Returns the overall demand of machine type until (inclusive) time period.

        :param machine_type: the machine type to consider
        :param time_period: the time period to consider
        """
        if time_period >= self.num_time_periods:
            raise InputError(
                f'Given time period {time_period} expected to be smaller than overall number {self.num_time_periods}.')
        if machine_type >= self.num_types:
            raise InputError(
                f'Given machine type {machine_type} expected to be smaller than overall number {self.num_types}.')
        return sum(self.demand[machine_type][:time_period + 1])

    def is_feasible(self, solution: List[int]) -> bool:
        """Returns true if given solution is feasible. Otherwise, false.

        :param solution: the schedule to check feasibility for
        """
        if len(solution) != self.num_time_periods:
            raise InputError(
                f'Length of given solution {len(solution)} does not coincide with expected length {self.num_time_periods}.')
        num_produced_items_schedule = dict()
        for machine_type in range(self.num_types):
            num_produced_items_schedule[machine_type] = self.__compute_num_produced_item_schedule(machine_type,
                                                                                                  solution)
        for machine_type, time_slot in product(range(self.num_types), range(self.num_time_periods)):
            if num_produced_items_schedule[machine_type][time_slot] < self.get_overall_demand(machine_type, time_slot):
                return False
        return True

    def __compute_num_produced_item_schedule(self, machine_type: int, solution: List[int]) -> List[int]:
        """Computes the schedule representing the number of produced items for given machine type based on given
        solution.
        """
        schedule = [0] * self.num_time_periods
        num_produced = 0
        for time_slot, item in enumerate(solution):
            if item == machine_type:
                num_produced += 1
                schedule[time_slot:] = [num_produced] * len(schedule[time_slot:])
        return schedule

    def compute_costs(self, schedule: List[int]) -> int:
        """Returns the overall costs of given schedule.

        :param schedule: the schedule to compute the costs for
        """
        return self.compute_transition_cost(schedule) + self.compute_inventory_cost(schedule)

    def compute_transition_cost(self, schedule: List[int]) -> int:
        """Returns the transition cost of the given schedule."""
        prev_state = -1
        transition_cost = 0
        for state in schedule:
            if state == -1:
                continue
            if state != prev_state and prev_state != -1:
                transition_cost += self.transition_cost[prev_state][state]
            prev_state = state
        return transition_cost

    def compute_inventory_cost(self, schedule: List[int]) -> int:
        """Returns the inventory cost of the given schedule."""
        inventory_cost = 0
        for machine_type in range(self.num_types):
            demand = [index for index, item in enumerate(self.demand[machine_type]) if item == 1]
            production = [index for index, item in enumerate(schedule) if item == machine_type]
            demand += [self.num_time_periods - 1] * (len(production) - len(demand))
            difference = [d - p for d, p in zip(demand, production)]
            inventory_cost += sum(difference) * self.inventory_cost
        return inventory_cost
