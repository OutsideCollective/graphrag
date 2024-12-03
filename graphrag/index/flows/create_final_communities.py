# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final communities."""

from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd


def create_final_communities(
    base_entity_nodes: pd.DataFrame,
    base_relationship_edges: pd.DataFrame,
    base_communities: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to transform final communities."""
    # aggregate entity ids for each community
    entity_ids = base_communities.merge(base_entity_nodes, on="title", how="inner")
    entity_ids = (
        entity_ids.groupby("community").agg(entity_ids=("id", list)).reset_index()
    )

    # aggregate relationships ids for each community
    # these are limited to only those where the source and target are in the same community
    max_level = base_communities["level"].max()
    all_grouped = pd.DataFrame(
        columns=["community", "level", "relationship_ids", "text_unit_ids"]  # type: ignore
    )
    for level in range(max_level + 1):
        communities_at_level = base_communities.loc[base_communities["level"] == level]
        sources = base_relationship_edges.merge(
            communities_at_level, left_on="source", right_on="title", how="inner"
        )
        targets = sources.merge(
            communities_at_level, left_on="target", right_on="title", how="inner"
        )
        matched = targets.loc[targets["community_x"] == targets["community_y"]]
        text_units = matched.explode("text_unit_ids")
        grouped = (
            text_units.groupby(["community_x", "level_x"])
            .agg(relationship_ids=("id", list), text_unit_ids=("text_unit_ids", list))
            .reset_index()
        )
        grouped.rename(
            columns={"community_x": "community", "level_x": "level"}, inplace=True
        )
        all_grouped = pd.concat([
            all_grouped,
            grouped.loc[:, ["community", "level", "relationship_ids", "text_unit_ids"]],
        ])

    # deduplicate the lists
    all_grouped["relationship_ids"] = all_grouped["relationship_ids"].apply(
        lambda x: sorted(set(x))
    )
    all_grouped["text_unit_ids"] = all_grouped["text_unit_ids"].apply(
        lambda x: sorted(set(x))
    )

    # join it all up and add some new fields
    communities = all_grouped.merge(entity_ids, on="community", how="inner")
    communities["id"] = communities["community"].apply(lambda _x: str(uuid4()))
    communities["human_readable_id"] = communities["community"]
    communities["title"] = "Community " + communities["community"].astype(str)

    # add fields for incremental update tracking
    communities["period"] = datetime.now(timezone.utc).date().isoformat()
    communities["size"] = communities.loc[:, "entity_ids"].apply(lambda x: len(x))

    return communities.loc[
        :,
        [
            "id",
            "human_readable_id",
            "community",
            "level",
            "title",
            "entity_ids",
            "relationship_ids",
            "text_unit_ids",
            "period",
            "size",
        ],
    ]
