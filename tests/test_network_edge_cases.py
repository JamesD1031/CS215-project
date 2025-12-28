import pytest

from dmh_flow import FlowNetwork


def test_no_self_loop_allowed() -> None:
    g = FlowNetwork(3)
    with pytest.raises(ValueError, match="self-loops"):
        g.add_edge(1, 1, 1.0)
