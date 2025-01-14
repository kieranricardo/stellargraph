# -*- coding: utf-8 -*-
#
# Copyright 2018 Data61, CSIRO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Mapper tests:

GraphSAGELinkMapper(
        G: nx.Graph,
        ids: List[Any],
        link_labels: List[Any] or np.ndarray,
        batch_size: int,
        num_samples: List[int],
        feature_size: Optional[int] = None,
        name: AnyStr = None,
    )
g
"""
from stellargraph.mapper.link_mappers import *
from stellargraph.core.graph import *
from stellargraph.data.explorer import *
from stellargraph.data.unsupervised_sampler import *

import numpy as np
import networkx as nx
import pytest
import random


def example_Graph_1(feature_size=None):
    G = nx.Graph()
    elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
    G.add_edges_from(elist)

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(feature_size)

    G = StellarGraph(G, node_features="feature")
    return G


def example_DiGraph_1(feature_size=None):
    G = nx.DiGraph()
    elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
    G.add_edges_from(elist)

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(feature_size)

    G = StellarGraph(G, node_features="feature")
    return G


def example_Graph_2(feature_size=None):
    G = nx.Graph()
    elist = [(1, 2), (2, 3), (1, 4), (4, 2)]
    G.add_edges_from(elist)

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = int(v) * np.ones(feature_size)

    G = StellarGraph(G, node_features="feature")
    return G


def example_HIN_1(feature_size_by_type=None):
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3], label="movie")
    G.add_nodes_from([4, 5], label="user")
    G.add_edges_from([(0, 4), (1, 4), (1, 5), (2, 4), (3, 5)], label="rating")
    G.add_edges_from([(4, 5)], label="friend")

    # Add example features
    if feature_size_by_type is not None:
        for v, vdata in G.nodes(data=True):
            nt = vdata["label"]
            vdata["feature"] = int(v) * np.ones(feature_size_by_type[nt], dtype="int")

    G = StellarGraph(G, node_features="feature")
    return G


def example_HIN_homo(feature_size_by_type=None):
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3, 4, 5], label="user")
    G.add_edges_from([(0, 4), (1, 4), (1, 5), (2, 4), (3, 5)], label="friend")

    # Add example features
    if feature_size_by_type is not None:
        for v, vdata in G.nodes(data=True):
            nt = vdata["label"]
            vdata["feature"] = int(v) * np.ones(feature_size_by_type[nt], dtype="int")

    G = StellarGraph(G, node_features="feature")
    return G


def example_graph_random(feature_size=None, n_edges=20, n_nodes=6, n_isolates=1):
    """
    Create random homogeneous graph

    Args:
        feature_size: Size of features for each node
        n_edges: Number of edges
        n_nodes: Number of nodes
        n_isolates: Number of isolated nodes

    Returns:
        StellarGraph object
    """
    connected = False
    while not connected:
        G = nx.Graph()
        n_noniso = n_nodes - n_isolates
        edges = [
            (random.randint(0, n_noniso - 1), random.randint(0, n_noniso - 1))
            for _ in range(n_edges)
        ]
        G.add_nodes_from(range(n_nodes))
        G.add_edges_from(edges, label="default")

        # Check connectivity
        connected = nx.is_connected(G.subgraph(range(n_noniso)))

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = int(v) * np.ones(feature_size, dtype="int")
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def example_hin_random(
    feature_size_by_type=None, nodes_by_type={}, n_isolates_by_type={}, edges_by_type={}
):
    """
    Create random heterogeneous graph

    Args:
        feature_size_by_type: Dict of node types to feature size
        nodes_by_type: Dict of node types to number of nodes
        n_isolates_by_type: Dict of node types to number of isolates
        edges_by_type: Dict of edge types to number of edges

    Returns:
        StellarGraph
        Dictionary of node type to node labels
    """
    check_isolates = False
    while not check_isolates:
        G = nx.Graph()
        node_dict = {}
        for nt in nodes_by_type:
            nodes = ["{}_{}".format(nt, ii) for ii in range(nodes_by_type[nt])]
            node_dict[nt] = nodes
            G.add_nodes_from(nodes, label=nt)

        for nt1, nt2 in edges_by_type:
            nodes1 = node_dict[nt1]
            nodes2 = node_dict[nt2]

            niso1 = n_isolates_by_type.get(nt1, 0)
            niso2 = n_isolates_by_type.get(nt2, 0)
            nodes1 = nodes1[:-niso1] if niso1 > 0 else nodes1
            nodes2 = nodes2[:-niso2] if niso2 > 0 else nodes1

            edges = [
                (random.choice(nodes1), random.choice(nodes2))
                for _ in range(edges_by_type[(nt1, nt2)])
            ]
            G.add_edges_from(edges, label="{}_{}".format(nt1, nt2))

        check_isolates = all(
            sum(deg[1] == 0 for deg in nx.degree(G, nodes)) == n_isolates_by_type[nt]
            for nt, nodes in node_dict.items()
        )

    # Add example features
    if feature_size_by_type is not None:
        nt_jj = 0
        for nt, nodes in node_dict.items():
            for ii, n in enumerate(nodes):
                G.node[n]["feature"] = (ii + 10 * nt_jj) * np.ones(
                    feature_size_by_type[nt], dtype="int"
                )
            nt_jj += 1

        G = StellarGraph(G, node_features="feature")

    else:
        G = StellarGraph(G)

    return G, node_dict


class Test_GraphSAGELinkGenerator:
    """
    Tests of GraphSAGELinkGenerator class
    """

    n_feat = 4
    batch_size = 2
    num_samples = [2, 2]

    def test_LinkMapper_constructor(self):

        G = example_Graph_1(self.n_feat)
        edge_labels = [0] * G.number_of_edges()

        generator = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        )
        mapper = generator.flow(G.edges(), edge_labels)
        assert generator.batch_size == self.batch_size
        assert mapper.data_size == G.number_of_edges()
        assert len(mapper.ids) == G.number_of_edges()

        G = example_DiGraph_1(self.n_feat)
        edge_labels = [0] * G.number_of_edges()
        generator = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        )
        mapper = generator.flow(G.edges(), edge_labels)
        assert generator.batch_size == self.batch_size
        assert mapper.data_size == G.number_of_edges()
        assert len(mapper.ids) == G.number_of_edges()

    def test_GraphSAGELinkGenerator_1(self):

        G = example_Graph_2(self.n_feat)
        data_size = G.number_of_edges()
        edge_labels = [0] * data_size

        mapper = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(G.edges(), edge_labels)

        assert len(mapper) == 2

        for batch in range(len(mapper)):
            nf, nl = mapper[batch]
            assert len(nf) == 3 * 2
            for ii in range(2):
                assert nf[ii].shape == (min(self.batch_size, data_size), 1, self.n_feat)
                assert nf[ii + 2].shape == (
                    min(self.batch_size, data_size),
                    2,
                    self.n_feat,
                )
                assert nf[ii + 2 * 2].shape == (
                    min(self.batch_size, data_size),
                    2 * 2,
                    self.n_feat,
                )
                assert len(nl) == min(self.batch_size, data_size)
                assert all(nl == 0)

        with pytest.raises(IndexError):
            nf, nl = mapper[2]

    def test_GraphSAGELinkGenerator_shuffle(self):
        def test_edge_consistency(shuffle):
            G = example_Graph_2(1)
            edges = list(G.edges())
            edge_labels = list(range(len(edges)))

            mapper = GraphSAGELinkGenerator(G, batch_size=2, num_samples=[0]).flow(
                edges, edge_labels, shuffle=shuffle
            )

            assert len(mapper) == 2

            for batch in range(len(mapper)):
                nf, nl = mapper[batch]
                e1 = edges[nl[0]]
                e2 = edges[nl[1]]
                assert nf[0][0, 0, 0] == e1[0]
                assert nf[1][0, 0, 0] == e1[1]
                assert nf[0][1, 0, 0] == e2[0]
                assert nf[1][1, 0, 0] == e2[1]

        test_edge_consistency(True)
        test_edge_consistency(False)

    # def test_GraphSAGELinkGenerator_2(self):
    #
    #     G = example_Graph_1(self.n_feat)
    #     data_size = G.number_of_edges()
    #     edge_labels = [0] * data_size
    #
    #     with pytest.raises(RuntimeWarning):
    #         GraphSAGELinkGenerator(
    #             G,
    #             G.edges(),
    #             edge_labels,
    #             batch_size=self.batch_size,
    #             num_samples=self.num_samples,
    #             feature_size=2 * self.n_feat,
    #         )

    def test_GraphSAGELinkGenerator_not_Stellargraph(self):
        G = nx.Graph()
        elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
        G.add_edges_from(elist)

        # Add example features
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(1)

        with pytest.raises(TypeError):
            GraphSAGELinkGenerator(
                G, batch_size=self.batch_size, num_samples=self.num_samples
            )

    def test_GraphSAGELinkGenerator_zero_samples(self):

        G = example_Graph_1(self.n_feat)
        data_size = G.number_of_edges()
        edge_labels = [0] * data_size

        mapper = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=[0]
        ).flow(G.edges(), edge_labels)

        assert len(mapper) == 2

        for ii in range(1):
            nf, nl = mapper[ii]
            assert len(nf) == 2 * 2
            for j in range(len(nf)):
                if j < self.batch_size:
                    assert nf[j].shape == (
                        min(self.batch_size, data_size),
                        1,
                        self.n_feat,
                    )
                else:
                    assert nf[j].shape == (
                        min(self.batch_size, data_size),
                        0,
                        self.n_feat,
                    )
            assert len(nl) == min(self.batch_size, data_size)
            assert all(nl == 0)

    def test_GraphSAGELinkGenerator_no_samples(self):
        """
        The SampledBFS sampler, created inside the mapper, currently throws a ValueError when the num_samples list is empty.
        This might change in the future, so this test might have to be re-written.

        """
        G = example_Graph_2(self.n_feat)
        data_size = G.number_of_edges()
        edge_labels = [0] * data_size

        mapper = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=[]
        ).flow(G.edges(), edge_labels)

        assert len(mapper) == 2
        with pytest.raises(ValueError):
            nf, nl = mapper[0]

    def test_GraphSAGELinkGenerator_no_targets(self):
        """
        This tests link generator's iterator for prediction, i.e., without targets provided
        """
        G = example_Graph_2(self.n_feat)
        gen = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(G.edges())
        for i in range(len(gen)):
            assert gen[i][1] is None

    def test_GraphSAGELinkGenerator_isolates(self):
        """
        Test for handling of isolated nodes
        """
        n_feat = 4
        n_batch = 2
        n_samples = [2, 2]

        # test graph
        G = example_graph_random(
            feature_size=n_feat, n_nodes=6, n_isolates=2, n_edges=10
        )

        # Check sizes with one isolated node
        head_links = [(1, 5)]
        gen = GraphSAGELinkGenerator(G, batch_size=n_batch, num_samples=n_samples).flow(
            head_links
        )

        ne, nl = gen[0]
        assert pytest.approx([1, 1, 2, 2, 4, 4]) == [x.shape[1] for x in ne]

        # Check sizes with two isolated nodes
        head_links = [(4, 5)]
        gen = GraphSAGELinkGenerator(G, batch_size=n_batch, num_samples=n_samples).flow(
            head_links
        )

        ne, nl = gen[0]
        assert pytest.approx([1, 1, 2, 2, 4, 4]) == [x.shape[1] for x in ne]

    def test_GraphSAGELinkGenerator_unsupervisedSampler_flow(self):
        """
        This tests link generator's initialization for on demand link generation i.e. there is no pregenerated list of samples provided to it.
        """
        n_feat = 4
        n_batch = 2
        n_samples = [2, 2]

        # test graph
        G = example_graph_random(
            feature_size=n_feat, n_nodes=6, n_isolates=2, n_edges=10
        )

        unsupervisedSamples = UnsupervisedSampler(G, nodes=G.nodes)

        gen = GraphSAGELinkGenerator(G, batch_size=n_batch, num_samples=n_samples).flow(
            unsupervisedSamples
        )

        # The flow method is not passed UnsupervisedSampler object or a list of samples is not passed
        with pytest.raises(TypeError):
            gen = GraphSAGELinkGenerator(
                G, batch_size=n_batch, num_samples=n_samples
            ).flow("not_a_list_of_samples_or_a_sample_generator")

        # The flow method is not passed nothing
        with pytest.raises(TypeError):
            gen = GraphSAGELinkGenerator(
                G, batch_size=n_batch, num_samples=n_samples
            ).flow()

    def test_GraphSAGELinkGenerator_unsupervisedSampler_sample_generation(self):

        G = example_Graph_2(self.n_feat)

        unsupervisedSamples = UnsupervisedSampler(G)

        mapper = GraphSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(unsupervisedSamples)

        assert mapper.data_size == 16
        assert self.batch_size == 2
        assert len(mapper) == 8

        for batch in range(len(mapper)):
            nf, nl = mapper[batch]

            assert len(nf) == 3 * 2
            assert len(set(mapper.head_node_types)) == 1

            for ii in range(2):
                assert nf[ii].shape == (
                    min(self.batch_size, mapper.data_size),
                    1,
                    self.n_feat,
                )
                assert nf[ii + 2].shape == (
                    min(self.batch_size, mapper.data_size),
                    2,
                    self.n_feat,
                )
                assert nf[ii + 2 * 2].shape == (
                    min(self.batch_size, mapper.data_size),
                    2 * 2,
                    self.n_feat,
                )
                assert len(nl) == min(self.batch_size, mapper.data_size)
                assert sorted(nl) == [0, 1]

        with pytest.raises(IndexError):
            nf, nl = mapper[8]


class Test_HinSAGELinkGenerator(object):
    """
    Tests of HinSAGELinkGenerator class
    """

    n_feat = {"user": 5, "movie": 10}
    batch_size = 2
    num_samples = [2, 3]

    def test_HinSAGELinkGenerator_constructor(self):

        # Constructor with a homogeneous graph:
        G = example_HIN_homo(self.n_feat)
        links = [(1, 4), (1, 5), (0, 4), (5, 0)]  # ('user', 'user') links
        link_labels = [0] * len(links)

        mapper = HinSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(links, link_labels)

        assert mapper.data_size == len(links)
        assert len(mapper.ids) == len(links)
        assert mapper.head_node_types == ("user", "user")

        # Constructor with a heterogeneous graph:
        G = example_HIN_1(self.n_feat)
        links = [(1, 4), (1, 5), (0, 4), (0, 5)]  # ('movie', 'user') links
        link_labels = [0] * len(links)

        mapper = HinSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(links, link_labels)

        assert mapper.data_size == len(links)
        assert len(mapper.ids) == len(links)
        assert mapper.data_size == len(link_labels)
        assert mapper.head_node_types == ("movie", "user")

    def test_HinSAGELinkGenerator_constructor_multiple_link_types(self):
        G = example_HIN_1(self.n_feat)
        links = [
            (1, 4),
            (1, 5),
            (0, 4),
            (5, 0),
        ]  # first 3 are ('movie', 'user') links, the last is ('user', 'movie') link.
        link_labels = [0] * len(links)

        with pytest.raises(RuntimeError):
            HinSAGELinkGenerator(
                G, batch_size=self.batch_size, num_samples=self.num_samples
            ).flow(links, link_labels)

        links = G.edges()  # all edges in G, which have multiple link types
        link_labels = [0] * len(links)

        with pytest.raises(RuntimeError):
            HinSAGELinkGenerator(
                G, batch_size=self.batch_size, num_samples=self.num_samples
            ).flow(links, link_labels)

    def test_HinSAGELinkGenerator_1(self):
        G = example_HIN_1(self.n_feat)
        links = [(1, 4), (1, 5), (0, 4), (0, 5)]  # selected ('movie', 'user') links
        data_size = len(links)
        link_labels = [0] * data_size

        mapper = HinSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(links, link_labels)

        assert len(mapper) == 2

        for batch in range(len(mapper)):
            nf, nl = mapper[batch]
            assert len(nf) == 10
            assert nf[0].shape == (self.batch_size, 1, self.n_feat["movie"])
            assert nf[1].shape == (self.batch_size, 1, self.n_feat["user"])
            assert nf[2].shape == (
                self.batch_size,
                self.num_samples[0],
                self.n_feat["user"],
            )
            assert nf[3].shape == (
                self.batch_size,
                self.num_samples[0],
                self.n_feat["user"],
            )
            assert nf[4].shape == (
                self.batch_size,
                self.num_samples[0],
                self.n_feat["movie"],
            )
            assert nf[5].shape == (
                self.batch_size,
                np.multiply(*self.num_samples),
                self.n_feat["user"],
            )
            assert nf[6].shape == (
                self.batch_size,
                np.multiply(*self.num_samples),
                self.n_feat["movie"],
            )
            assert nf[7].shape == (
                self.batch_size,
                np.multiply(*self.num_samples),
                self.n_feat["user"],
            )
            assert nf[8].shape == (
                self.batch_size,
                np.multiply(*self.num_samples),
                self.n_feat["movie"],
            )
            assert nf[9].shape == (
                self.batch_size,
                np.multiply(*self.num_samples),
                self.n_feat["user"],
            )

        with pytest.raises(IndexError):
            nf, nl = mapper[2]

    def test_HinSAGELinkGenerator_shuffle(self):
        def test_edge_consistency(shuffle):
            G = example_HIN_1({"user": 1, "movie": 1})
            edges = [(1, 4), (1, 5), (0, 4), (0, 5)]  # selected ('movie', 'user') links
            data_size = len(edges)
            edge_labels = np.arange(data_size)

            mapper = HinSAGELinkGenerator(G, batch_size=2, num_samples=[0]).flow(
                edges, edge_labels, shuffle=shuffle
            )

            assert len(mapper) == 2
            for batch in range(len(mapper)):
                nf, nl = mapper[batch]
                e1 = edges[nl[0]]
                e2 = edges[nl[1]]
                assert nf[0][0, 0, 0] == e1[0]
                assert nf[1][0, 0, 0] == e1[1]
                assert nf[0][1, 0, 0] == e2[0]
                assert nf[1][1, 0, 0] == e2[1]

        test_edge_consistency(True)
        test_edge_consistency(False)

    def test_HinSAGELinkGenerator_no_targets(self):
        """
        This tests link generator's iterator for prediction, i.e., without targets provided
        """
        G = example_HIN_1(self.n_feat)
        links = [(1, 4), (1, 5), (0, 4), (0, 5)]  # selected ('movie', 'user') links
        data_size = len(links)

        gen = HinSAGELinkGenerator(
            G, batch_size=self.batch_size, num_samples=self.num_samples
        ).flow(links)
        for i in range(len(gen)):
            assert gen[i][1] is None

    def test_HinSAGELinkGenerator_isolates(self):
        """
        This tests link generator's iterator for prediction, i.e., without targets provided
        """
        n_batch = 2
        n_samples = [2, 2]

        feature_size_by_type = {"A": 4, "B": 2}
        nodes_by_type = {"A": 5, "B": 5}
        n_isolates_by_type = {"A": 0, "B": 2}
        edges_by_type = {("A", "A"): 5, ("A", "B"): 10}
        Gh, hnodes = example_hin_random(
            feature_size_by_type, nodes_by_type, n_isolates_by_type, edges_by_type
        )

        # Non-isolate + isolate
        head_links = [(hnodes["A"][0], hnodes["B"][-1])]
        gen = HinSAGELinkGenerator(Gh, batch_size=n_batch, num_samples=n_samples).flow(
            head_links
        )

        ne, nl = gen[0]
        assert len(gen._sampling_schema[0]) == len(ne)
        assert pytest.approx([1, 1, 2, 2, 2, 4, 4, 4, 4, 4]) == [x.shape[1] for x in ne]

        # Two isolates
        head_links = [(hnodes["B"][-2], hnodes["B"][-1])]
        gen = HinSAGELinkGenerator(Gh, batch_size=n_batch, num_samples=n_samples).flow(
            head_links
        )

        ne, nl = gen[0]
        assert len(gen._sampling_schema[0]) == len(ne)
        assert pytest.approx([1, 1, 2, 2, 4, 4, 4, 4]) == [x.shape[1] for x in ne]

        # With two isolates, all features are zero
        assert all(pytest.approx(0) == x for x in ne[2:])


class Test_Attri2VecLinkGenerator:
    """
    Tests of Attri2VecLinkGenerator class
    """

    n_feat = 4
    batch_size = 2

    def test_LinkMapper_constructor(self):

        G = example_Graph_1(self.n_feat)
        edge_labels = [0] * G.number_of_edges()

        generator = Attri2VecLinkGenerator(G, batch_size=self.batch_size)
        mapper = generator.flow(G.edges(), edge_labels)
        assert generator.batch_size == self.batch_size
        assert mapper.data_size == G.number_of_edges()
        assert len(mapper.ids) == G.number_of_edges()

        G = example_DiGraph_1(self.n_feat)
        edge_labels = [0] * G.number_of_edges()
        generator = Attri2VecLinkGenerator(G, batch_size=self.batch_size)
        mapper = generator.flow(G.edges(), edge_labels)
        assert generator.batch_size == self.batch_size
        assert mapper.data_size == G.number_of_edges()
        assert len(mapper.ids) == G.number_of_edges()

    def test_Attri2VecLinkGenerator_1(self):

        G = example_Graph_2(self.n_feat)
        data_size = G.number_of_edges()
        edge_labels = [0] * data_size

        mapper = Attri2VecLinkGenerator(G, batch_size=self.batch_size).flow(
            G.edges(), edge_labels
        )

        assert len(mapper) == 2

        for batch in range(len(mapper)):
            nf, nl = mapper[batch]
            assert len(nf) == 2
            assert nf[0].shape == (min(self.batch_size, data_size), self.n_feat)
            assert nf[1].shape == (min(self.batch_size, data_size),)
            assert len(nl) == min(self.batch_size, data_size)
            assert all(nl == 0)

        with pytest.raises(IndexError):
            nf, nl = mapper[2]

    def test_edge_consistency(self):
        G = example_Graph_2(1)
        edges = list(G.edges())
        nodes = list(G.nodes())
        edge_labels = list(range(len(edges)))

        mapper = Attri2VecLinkGenerator(G, batch_size=2).flow(edges, edge_labels)

        assert len(mapper) == 2

        for batch in range(len(mapper)):
            nf, nl = mapper[batch]
            e1 = edges[nl[0]]
            e2 = edges[nl[1]]
            assert nf[0][0, 0] == e1[0]
            assert nf[1][0] == nodes.index(e1[1])
            assert nf[0][1, 0] == e2[0]
            assert nf[1][1] == nodes.index(e2[1])

    def test_Attri2VecLinkGenerator_not_Stellargraph(self):
        G = nx.Graph()
        elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
        G.add_edges_from(elist)

        # Add example features
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(1)

        with pytest.raises(TypeError):
            Attri2VecLinkGenerator(G, batch_size=self.batch_size)

    def test_Attri2VecLinkGenerator_no_targets(self):
        """
        This tests link generator's iterator for prediction, i.e., without targets provided
        """
        G = example_Graph_2(self.n_feat)
        gen = Attri2VecLinkGenerator(G, batch_size=self.batch_size).flow(G.edges())
        for i in range(len(gen)):
            assert gen[i][1] is None

    def test_Attri2VecLinkGenerator_unsupervisedSampler_flow(self):
        """
        This tests link generator's initialization for on demand link generation i.e. there is no pregenerated list of samples provided to it.
        """
        n_feat = 4
        n_batch = 2

        # test graph
        G = example_graph_random(
            feature_size=n_feat, n_nodes=6, n_isolates=2, n_edges=10
        )

        unsupervisedSamples = UnsupervisedSampler(G, nodes=G.nodes)

        gen = Attri2VecLinkGenerator(G, batch_size=n_batch).flow(unsupervisedSamples)

        # The flow method is not passed UnsupervisedSampler object or a list of samples is not passed
        with pytest.raises(TypeError):
            gen = Attri2VecLinkGenerator(G, batch_size=n_batch).flow(
                "not_a_list_of_samples_or_a_sample_generator"
            )

        # The flow method is not passed nothing
        with pytest.raises(TypeError):
            gen = Attri2VecLinkGenerator(G, batch_size=n_batch).flow()

    def test_Attri2VecLinkGenerator_unsupervisedSampler_sample_generation(self):

        G = example_Graph_2(self.n_feat)

        unsupervisedSamples = UnsupervisedSampler(G)

        mapper = Attri2VecLinkGenerator(G, batch_size=self.batch_size).flow(
            unsupervisedSamples
        )

        assert mapper.data_size == 16
        assert self.batch_size == 2
        assert len(mapper) == 8

        for batch in range(len(mapper)):
            nf, nl = mapper[batch]

            assert len(nf) == 2

            assert nf[0].shape == (min(self.batch_size, mapper.data_size), self.n_feat)
            assert nf[1].shape == (min(self.batch_size, mapper.data_size),)
            assert len(nl) == min(self.batch_size, mapper.data_size)
            assert sorted(nl) == [0, 1]

        with pytest.raises(IndexError):
            nf, nl = mapper[8]
