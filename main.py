#!/usr/bin/env python3

from argparse import ArgumentParser

from ortools.linear_solver import pywraplp

from lot_sizing.input import Input
from lot_sizing.model import MipModel


def write_model(filepath: str, solver: pywraplp):
    with open(filepath, 'w') as file:
        file.write(solver.ExportModelAsLpFormat(False))


def create_schedule(model: MipModel):
    """Return the schedule based on the computed solution."""
    epsilon = 0.01
    schedule = [-1] * model.prob_input.num_time_periods
    for time_period in range(model.prob_input.num_time_periods):
        solver_vars = [model.production_vars[(machine_type, time_period)] for machine_type in
                       range(model.prob_input.num_types)]
        solution_values = [x.solution_value() for x in solver_vars]
        produced_type = [index for index, value in enumerate(solution_values) if value > 1. - epsilon]
        if len(produced_type) == 1:
            schedule[time_period] = produced_type[0]
        elif len(produced_type) > 1:
            raise RuntimeError(f'Several machine types {produced_type} produced in time period {time_period}')
    return schedule


cmd_parser = ArgumentParser(
    description='Integer programming formulations for the discrete, single-machine, multi-item, single-level lot sizing problem.')
cmd_parser.add_argument('-f', '--file', metavar="input_file", type=str,
                        help='File containing the input data',
                        required=True)

if __name__ == '__main__':
    cmd_args = cmd_parser.parse_args()
    prob_input = Input.read_file(cmd_args.file)
    solver = pywraplp.Solver.CreateSolver('solver', 'SCIP')
    solver.EnableOutput()
    mip_model = MipModel.build_mip(prob_input, solver)
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        production_schedule = create_schedule(mip_model)
        print(f'Computed schedule: {production_schedule}')
        print(f'Objective value: {solver.Objective().Value()}')
    else:
        print('No optimial solution was computed.')
