import unittest
from unittest.mock import Mock, patch

from lot_sizing.input import Input


class InputTest(unittest.TestCase):
    """Tests for class: Input"""

    def setUp(self):
        with patch('lot_sizing.input.open') as mock_open:
            mock_open.return_value.__enter__ = mock_open
            mock_open.return_value.__iter__ = Mock(
                return_value=iter(["6",  # number of time periods
                                   "3",  # number of machine types
                                   "1 0 0 0 1 0",  # demand machine type 0
                                   "0 1 0 0 1 0",  # demand machine type 1
                                   "0 0 0 0 0 1",  # demand machine type 2
                                   "10",  # inventory cost per item per time slot
                                   "0 1 1",  # transition cost machine type 0
                                   "3 0 2",  # transition cost machine type 1
                                   "4 5 0"])  # transition cost machine type 2
            )
            self.input = Input.read_file(mock_open)
            self.feasible_schedule = [0, 1, 2, 0, 1, -1]
            self.other_feasible_schedule = [0, 1, -1, 1, 0, 2]
            self.infeasible_schedule = [0, 2, 1, 0, 1, -1]

    def test_num_time_slots(self):
        self.assertEqual(6, self.input.num_time_periods)

    def test_num_types(self):
        self.assertEqual(3, self.input.num_types)

    def test_inventory_cost(self):
        self.assertEqual(10, self.input.inventory_cost)

    def test_check_feasibility(self):
        self.assertTrue(self.input.is_feasible(self.feasible_schedule))
        self.assertTrue(self.input.is_feasible(self.other_feasible_schedule))
        self.assertFalse(self.input.is_feasible(self.infeasible_schedule))

    def test_overall_demand(self):
        self.assertEqual(1, self.input.get_overall_demand(0, 0))
        self.assertEqual(1, self.input.get_overall_demand(0, 1))
        self.assertEqual(2, self.input.get_overall_demand(0, 4))
        self.assertEqual(2, self.input.get_overall_demand(0, 5))
        self.assertEqual(0, self.input.get_overall_demand(1, 0))
        self.assertEqual(1, self.input.get_overall_demand(1, 1))
        self.assertEqual(2, self.input.get_overall_demand(1, 4))
        self.assertEqual(0, self.input.get_overall_demand(2, 2))
        self.assertEqual(1, self.input.get_overall_demand(2, 5))

    def test_compute_transition_cost(self):
        self.assertEqual(8, self.input.compute_transition_cost(self.feasible_schedule))
        self.assertEqual(5, self.input.compute_transition_cost(self.other_feasible_schedule))

    def test_compute_inventory_cost(self):
        self.assertEqual(40, self.input.compute_inventory_cost(self.feasible_schedule))
        self.assertEqual(10, self.input.compute_inventory_cost(self.other_feasible_schedule))

    def test_compute_cost(self):
        self.assertEqual(48, self.input.compute_costs(self.feasible_schedule))
        self.assertEqual(15, self.input.compute_costs(self.other_feasible_schedule))


if __name__ == '__main__':
    unittest.main()
