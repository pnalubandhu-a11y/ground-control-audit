"""The module catalog must match the reference `audit -l` exactly."""

from collections import Counter

from audit.core.catalog import MODULES


def test_catalog_has_51_modules_with_reference_group_counts():
    assert len(MODULES) == 51
    by_group = Counter(m.group for m in MODULES)
    assert by_group == {"A": 11, "B": 14, "C": 16, "G": 10}


def test_module_ids_are_unique():
    ids = [m.id for m in MODULES]
    assert len(ids) == len(set(ids))


def test_known_modules_have_exact_reference_names():
    by_id = {m.id: m.name for m in MODULES}
    assert by_id["A1"] == "pernic_routing_tables"
    assert by_id["B14"] == "rdma_counters"
    assert by_id["C16"] == "cluster_node_discovery"
    assert by_id["G5"] == "gpu_xid_errors"
