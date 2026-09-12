"""Equitable Network Growth (ENG) corridor analysis for the MBTA bus network.

Submitted to the MIT Policy Hackathon 2025 (Transit track) by Team TartanSparks.
Second place.

The package is organised in two halves:

``indices``, ``service``, ``spatial`` and ``jobs``
    The corridor-selection pipeline. These need the challenge datasets in
    ``data/raw/`` to run. See ``data/README.md``.

``fiscal``
    The cost-benefit model. It depends only on the published route metrics in
    ``data/processed/`` and the documented assumptions, so it runs anywhere and
    is covered by tests.
"""

from eng_corridors import config, fiscal, indices

__all__ = ["config", "fiscal", "indices"]
__version__ = "1.0.0"
