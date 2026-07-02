from main import Dinic


def test_dinic_max_flow_simple_path():
    graph = Dinic(4)
    graph.add_edge(0, 1, 2)
    graph.add_edge(1, 2, 1)
    graph.add_edge(2, 3, 2)

    flow = graph.max_flow(0, 3)

    assert flow == 1


def test_dinic_max_flow_no_path_returns_zero():
    graph = Dinic(3)
    graph.add_edge(0, 1, 1)
    # No edge from node 1 to sink 2

    flow = graph.max_flow(0, 2)

    assert flow == 0
