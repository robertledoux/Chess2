#!/usr/bin/env pypy
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
from itertools import count
from collections import Counter, OrderedDict, namedtuple
import math
import getpass
import string
import random

# The table size is the maximum number of elements in the transposition table.
TABLE_SIZE = 1e6

# This constant controls how much time we spend on looking for optimal moves.
NODES_SEARCHED = 1e4

# Mate value must be greater than 8*queen + 2*(rook+knight+bishop)
# King value is set to twice this value such that if the opponent is
# 8 queens up, but we got the king, we still exceed MATE_VALUE.
MATE_VALUE = 30000
MIDLINE_VALUE = 60000

# Our board is represented as a 120 character string. The padding allows for
# fast detection of moves that don't stay within the board.
A1, H1, A8, H8 = 91, 98, 21, 28

classic_piece_to_army_piece_dict = {
    #      c    n    e    r    t    a
    'P': ['P', 'L', 'P', 'P', 'P', 'P'],
    'B': ['B', 'B', 'X', 'B', 'B', 'T'],
    'N': ['N', 'N', 'Y', 'N', 'N', 'H'],
    'R': ['R', 'R', 'Z', 'G', 'R', 'E'],
    'Q': ['Q', 'M', 'O', 'A', 'U', 'J'],
    'K': ['K', 'C', 'C', 'C', 'W', 'C']}

###############################################################################
# Move and evaluation tables
###############################################################################

N, E, S, W, H = -10, 1, 10, -1, 0

directions = {
    # pawns
    'P': (N, 2*N, N+W, N+E),
    'L': (N, E, S, W, N+E, S+E, S+W, N+W),
    # bishops
    'B': (N+E, S+E, S+W, N+W),
    'X': (N, E, S, W, N+E, S+E, S+W, N+W, 2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    'T': (N+E, S+E, S+W, N+W, (N+E)*2, (S+E)*2, (S+W)*2, (N+W)*2),
    # knights
    'N': (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    'Y': (N, E, S, W, N+E, S+E, S+W, N+W, 2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    'H': (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    # rooks
    'R': (N, E, S, W),
    'Z': (N, E, S, W, N+E, S+E, S+W, N+W, 2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    'G': (
        21, 22, 23, 24, 25, 26, 27, 28,
        31, 32, 33, 34, 35, 36, 37, 38,
        41, 42, 43, 44, 45, 46, 47, 48,
        51, 52, 53, 54, 55, 56, 57, 58,
        61, 62, 63, 64, 65, 66, 67, 68,
        71, 72, 73, 74, 75, 76, 77, 78,
        81, 82, 83, 84, 85, 86, 87, 88),
    'E': (N, E, S, W),
    # queens
    'Q': (N, E, S, W, N+E, S+E, S+W, N+W),
    'M': (N, E, S, W, N+E, S+E, S+W, N+W),
    'O': (N, E, S, W, N+E, S+E, S+W, N+W),
    'A': (
        31, 32, 33, 34, 35, 36, 37, 38,
        41, 42, 43, 44, 45, 46, 47, 48,
        51, 52, 53, 54, 55, 56, 57, 58,
        61, 62, 63, 64, 65, 66, 67, 68,
        71, 72, 73, 74, 75, 76, 77, 78,
        81, 82, 83, 84, 85, 86, 87, 88),
    'U': (N, E, S, W, H, N+E, S+E, S+W, N+W),
    'J': (N, E, S, W, 2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    # kings
    'K': (N, E, S, W, N+E, S+E, S+W, N+W),
    'W': (N, E, S, W, H, N+E, S+E, S+W, N+W),
    'C': (N, E, S, W, N+E, S+E, S+W, N+W)
}

#Piece-Square Tables
pst = {
    # Classic Pawn
    'P': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 198, 198, 198, 198, 198, 198, 198, 198, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 178, 208, 208, 208, 208, 208, 208, 178, 0,
        0, 178, 238, 238, 238, 238, 238, 238, 178, 0,
        0, 178, 218, 218, 218, 218, 218, 218, 178, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 198, 198, 198, 198, 198, 198, 198, 198, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Nemesis Pawn
    'L': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 198, 198, 198, 198, 198, 198, 198, 198, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 178, 198, 208, 218, 218, 208, 198, 178, 0,
        0, 178, 198, 218, 238, 238, 218, 198, 178, 0,
        0, 178, 198, 208, 218, 218, 208, 198, 178, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 198, 198, 198, 198, 198, 198, 198, 198, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Classic Bishop
    'B': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 797, 824, 817, 808, 808, 817, 824, 797, 0,
        0, 814, 841, 834, 825, 825, 834, 841, 814, 0,
        0, 818, 845, 838, 829, 829, 838, 845, 818, 0,
        0, 824, 851, 844, 835, 835, 844, 851, 824, 0,
        0, 827, 854, 847, 838, 838, 847, 854, 827, 0,
        0, 826, 853, 846, 837, 837, 846, 853, 826, 0,
        0, 817, 844, 837, 828, 828, 837, 844, 817, 0,
        0, 792, 819, 812, 803, 803, 812, 819, 792, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Empowered Bishop
    'X': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 797, 824, 817, 808, 808, 817, 824, 797, 0,
        0, 814, 841, 834, 825, 825, 834, 841, 814, 0,
        0, 818, 845, 838, 829, 829, 838, 845, 818, 0,
        0, 824, 851, 844, 835, 835, 844, 851, 824, 0,
        0, 827, 854, 847, 838, 838, 847, 854, 827, 0,
        0, 826, 853, 846, 837, 837, 846, 853, 826, 0,
        0, 817, 844, 837, 828, 828, 837, 844, 817, 0,
        0, 792, 819, 812, 803, 803, 812, 819, 792, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Animals Tiger
    'T': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 797, 824, 817, 808, 808, 817, 824, 797, 0,
        0, 814, 841, 834, 825, 825, 834, 841, 814, 0,
        0, 818, 845, 838, 829, 829, 838, 845, 818, 0,
        0, 824, 851, 844, 835, 835, 844, 851, 824, 0,
        0, 827, 854, 847, 838, 838, 847, 854, 827, 0,
        0, 826, 853, 846, 837, 837, 846, 853, 826, 0,
        0, 817, 844, 837, 828, 828, 837, 844, 817, 0,
        0, 792, 819, 812, 803, 803, 812, 819, 792, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Classic Knight
    'N': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 627, 762, 786, 798, 798, 786, 762, 627, 0,
        0, 763, 798, 822, 834, 834, 822, 798, 763, 0,
        0, 817, 852, 876, 888, 888, 876, 852, 817, 0,
        0, 797, 832, 856, 868, 868, 856, 832, 797, 0,
        0, 799, 834, 858, 870, 870, 858, 834, 799, 0,
        0, 758, 793, 817, 829, 829, 817, 793, 758, 0,
        0, 739, 774, 798, 810, 810, 798, 774, 739, 0,
        0, 683, 718, 742, 754, 754, 742, 718, 683, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Empowered Knight
    'Y': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 627, 762, 786, 798, 798, 786, 762, 627, 0,
        0, 763, 798, 822, 834, 834, 822, 798, 763, 0,
        0, 817, 852, 876, 888, 888, 876, 852, 817, 0,
        0, 797, 832, 856, 868, 868, 856, 832, 797, 0,
        0, 799, 834, 858, 870, 870, 858, 834, 799, 0,
        0, 758, 793, 817, 829, 829, 817, 793, 758, 0,
        0, 739, 774, 798, 810, 810, 798, 774, 739, 0,
        0, 683, 718, 742, 754, 754, 742, 718, 683, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Animals Wild Horses
    'H': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 627, 762, 786, 798, 798, 786, 762, 627, 0,
        0, 763, 798, 822, 834, 834, 822, 798, 763, 0,
        0, 817, 852, 876, 888, 888, 876, 852, 817, 0,
        0, 797, 832, 856, 868, 868, 856, 832, 797, 0,
        0, 799, 834, 858, 870, 870, 858, 834, 799, 0,
        0, 758, 793, 817, 829, 829, 817, 793, 758, 0,
        0, 739, 774, 798, 810, 810, 798, 774, 739, 0,
        0, 683, 718, 742, 754, 754, 742, 718, 683, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Classic Rooks
    'R': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Empowered Rooks
    'Z': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Reaper Ghosts
    'G': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1258, 1263, 1263, 1263, 1263, 1263, 1263, 1258, 0,
        0, 1258, 1263, 1263, 1263, 1263, 1263, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1234, 1234, 1234, 1234, 1234, 1234, 1234, 1234, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Animals Elephants
    'E': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Classic Queens
    'Q': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Nemesis Nemesis
    'M': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 2200, 2600, 2600, 2600, 2600, 2600, 2600, 2200, 0,
        0, 2200, 2500, 2500, 2500, 2500, 2500, 2500, 2200, 0,
        0, 2200, 2500, 2500, 2500, 2500, 2500, 2500, 2200, 0,
        0, 2200, 2500, 2500, 2500, 2500, 2500, 2500, 2200, 0,
        0, 2200, 2500, 2500, 2500, 2500, 2500, 2500, 2200, 0,
        0, 2200, 2500, 2500, 2500, 2500, 2500, 2500, 2200, 0,
        0, 2200, 2500, 2500, 2500, 2500, 2500, 2500, 2200, 0,
        0, 1900, 1900, 1900, 1900, 1900, 1900, 1900, 1900, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Empowered Queen
    'O': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Reaper Reaper
    'A': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1234, 1234, 1234, 1234, 1234, 1234, 1234, 1234, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Two Kings Warrior Queen
    'U': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 60200, 60325, 60400, 60400, 60400, 60400, 60325, 60200, 0,
        0, 60150, 60250, 60300, 60300, 60300, 60300, 60250, 60150, 0,
        0, 60150, 60175, 60200, 60200, 60200, 60200, 60175, 60150, 0,
        0, 60100, 60100, 60100, 60100, 60100, 60100, 60100, 60100, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Animals Jungle Queen
    'J': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Classic King
    'K': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 60098, 60132, 60073, 60025, 60025, 60073, 60132, 60098, 0,
        0, 60119, 60153, 60094, 60046, 60046, 60094, 60153, 60119, 0,
        0, 60146, 60180, 60121, 60073, 60073, 60121, 60180, 60146, 0,
        0, 61000, 61000, 61000, 61000, 61000, 61000, 61000, 61000, 0,
        0, 60196, 60230, 60171, 60123, 60123, 60171, 60230, 60196, 0,
        0, 60224, 60258, 60199, 60151, 60151, 60199, 60258, 60224, 0,
        0, 60287, 60321, 60262, 60214, 60214, 60262, 60321, 60287, 0,
        0, 60298, 60332, 60273, 60225, 60225, 60273, 60332, 60298, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Two Kings Warrior King
    'W': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 62000, 0,
        0, 60200, 60325, 60400, 60400, 60400, 60400, 60325, 60200, 0,
        0, 60150, 60250, 60300, 60300, 60300, 60300, 60250, 60150, 0,
        0, 60150, 60175, 60200, 60200, 60200, 60200, 60175, 60150, 0,
        0, 60100, 60100, 60100, 60100, 60100, 60100, 60100, 60100, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Generic King
    'C': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 60098, 60132, 60073, 60025, 60025, 60073, 60132, 60098, 0,
        0, 60119, 60153, 60094, 60046, 60046, 60094, 60153, 60119, 0,
        0, 60146, 60180, 60121, 60073, 60073, 60121, 60180, 60146, 0,
        0, 61000, 61000, 61000, 61000, 61000, 61000, 61000, 61000, 0,
        0, 60196, 60230, 60171, 60123, 60123, 60171, 60230, 60196, 0,
        0, 60224, 60258, 60199, 60151, 60151, 60199, 60258, 60224, 0,
        0, 60287, 60321, 60262, 60214, 60214, 60262, 60321, 60287, 0,
        0, 60298, 60332, 60273, 60225, 60225, 60273, 60332, 60298, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
}

# Piece Value Tables
"""
For a given piece, give it a "weight" from -1 to 2. When dueling with
opp piece, add the weight to the piece's rank and compare with the
opp piece's rank. If greater, bid weight. If equal, bid weight -1.
If less, bid 0.

Standard piece values: P:1, B:3, N:3, R:5, Q:9, K:4
-1 to 2 is not as much room as this. Maybe convert it to quarter poitns?
P:0.25, B:0.75, N:0.75, R:1.25, Q:2.25, K:1?
I like that the -1-2 spread has malluses.

How about instead: value everything with P:1. Compare values of dueling
pieces, with -1-2 modifiers from differences in stone levels.
"""
pvt = {
    'P': 1,  # classic pawn
    'L': 2,  # nemesis pawn
    'B': 3,  # classic bishop
    'X': 4,  # empowered bishop
    'T': 3,  # animals tiger
    'N': 3,  # classic knight
    'Y': 4,  # empowered knight
    'H': 3,  # animals wild horse
    'R': 5,  # classic rook
    'Z': 6,  # empowered rook
    'E': 5,  # animals elephant
    'Q': 9,  # classic queen
    'O': 3,  # empowered queen
    'A': 7,  # reaper reaper
    'J': 8,  # animals jungle queen
}

###############################################################################
# Chess logic
###############################################################################

class Position(namedtuple('Position', 'board color second score wa ba ws bs wc bc ep kp')):
    """ A state of a chess game
    board -- a 120 char representation of the board
    color -- whose turn it is
    second -- in a king's turn?
    score -- the board evaluation
    wa -- white army
    ba -- black army
    ws -- white stones
    bs -- black stones
    wc -- the castling rights
    bc -- the opponent castling rights
    ep - the en passant square
    kp - the king passant square
    """

    def genMoves(self, second=False):
        # For each of our pieces, iterate through each possible 'ray' of moves,
        # as defined in the 'directions' map. The rays are broken e.g. by
        # captures or immediately in case of pieces such as knights.
        royal = []
        for space, char in enumerate(self.board):
            if any(var in char for var in ('k', 'c', 'u', 'w')):
                royal.append(space)
        for i, p in enumerate(self.board):
            if not p.isupper(): continue
            for d in directions[p]:
                if second:  # Two Kings Warrior King turn.
                    for j in count(i+d, d):
                        if not any(var in p for var in ('U', 'W')):
                            break
                        q = self.board[j]
                        if self.board[j].isspace(): break
                        if q.isupper(): break
                        if d == H:  # whirlwind
                            cant = False
                            for dr in (N, E, S, W, N+E, S+E, S+W, N+W):
                                if any(var in self.board[i+dr] for var in ('U', 'W')):
                                    cant = True
                            if not cant: yield(i, j)
                        else: yield(i, j)
                        break
                else:  # Non-Warrior King turn
                    if any(var in p for var in ('A', 'G')):
                        q = self.board[d]
                        if p == 'G':
                            if q == '.':
                                yield (i, d)
                        else:
                            if not self.isPieceInvulnerable(self.board, i, d):
                                if q.isupper(): break
                                yield (i, d)
                    else:
                        elephant = False
                        for j in count(i+d, d):
                            try:
                                q = self.board[j]
                            except IndexError:
                                print("i: {}, j: {}, board: {}".format(i, j, self.board))
                            # Stay inside the board
                            if q.isspace(): break
                            # Castling
                            if i == A1 and q == 'K' and self.wc[0]:
                                yield (j, j-2)
                            if i == H1 and q == 'K' and self.wc[1]:
                                yield (j, j+2)
                            # No friendly captures, except for Wild Horses and Elephants
                            if q.isupper():
                                if p == q: pass
                                elif p != 'H' and p != 'E': break
                                elif p == 'E':
                                    if not self.isPieceInvulnerable(self.board, i, j):
                                        if not elephant:
                                            elephant = True
                                            yield(i, j)
                            # Classic pawn stuff
                            if p == 'P' and d in (N+W, N+E) and q == '.' and j not in (self.ep, self.kp): break
                            if p == 'P' and d in (N, 2*N) and q != '.': break
                            if p == 'P' and d == 2*N and (i < A1+N or self.board[i+N] != '.'): break
                            crawlers = ['P', 'L', 'T', 'N', 'H', 'O', 'U', 'K', 'W', 'C']
                            # Check invinsibility
                            if self.isPieceInvulnerable(self.board, i, j): break
                            # Nemesis pawn stuff
                            elif p == 'L':
                                if d in (N, E, S, W, S+W, S+E) and q != '.': break
                                # 1 2 3
                                # 4   5
                                # 6 7 8
                                for k in royal:
                                    row = i // 10 - k // 10
                                    column = i % 10 - k % 10
                                    if row > 0: # 1, 2, 3
                                        if column > 0 and d in (N, W, N+W): # 1
                                            yield (i, j)
                                        elif column == 0 and d == N: # 2
                                            yield (i, j)
                                        elif column < 0 and d in (N, E, N+E): # 3
                                            yield (i, j)
                                    elif row == 0: # 4, 5
                                        if column > 0 and d == W: # 4
                                            yield (i, j)
                                        elif column < 0 and d == E: # 5
                                            yield (i, j)
                                    elif row < 0: # 6, 7, 8
                                        if column > 0 and d in (S, W, S+W): # 6
                                            yield (i, j)
                                        elif column == 0 and d == S: # 7
                                            yield (i, j)
                                        elif column < 0 and d in (S, E, S+E): # 8
                                            yield (i, j)
                            elif any(var in p for var in ('X', 'Y', 'Z')):
                                for dr in (N, E, S, W):
                                    idr = i+dr
                                    if p == 'X':
                                        if d in (N+E, S+E, S+W, N+W):
                                            yield(i, j)
                                        elif self.board[idr] == 'Y' and d in (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W):
                                            yield(i, j)
                                            crawlers.append('X')
                                        elif self.board[idr] == 'Z' and d in (N, E, S, W):
                                            yield(i, j)
                                    elif p == 'Y':
                                        if self.board[idr] == 'X' and d in (N+E, S+E, S+W, N+W):
                                            yield(i, j)
                                        elif d in (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W):
                                            yield(i, j)
                                            crawlers.append('Y')
                                        elif self.board[idr] == 'Z' and d in (N, E, S, W):
                                            yield(i, j)
                                    elif p == 'Z':
                                        if self.board[idr] == 'X' and d in (N+E, S+E, S+W, N+W):
                                            yield(i, j)
                                        elif self.board[idr] == 'Y' and d in (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W):
                                            yield(i, j)
                                            crawlers.append('Z')
                                        elif d in (N, E, S, W):
                                            yield(i, j)
                            elif any(var in p for var in ('U', 'W')):
                                if d == H: # whirlwind
                                    cant = False
                                    for dr in (N, E, S, W, N+E, S+E, S+W, N+W):
                                        if any(var in self.board[i+dr] for var in ('U', 'W')):
                                            cant = True
                                    if not cant: yield(i, j)
                                else: yield(i, j)
                            elif p == 'T' and d in ((N+E)*2, (S+E)*2, (S+W)*2, (N+W)*2) and self.board[i+(d//2)].isupper():
                                break
                            elif p == 'M' and q not in ('k', 'u', 'w', 'c', '.'):
                                break
                            # Move it
                            else: yield (i, j)
                            # Stop limited movement pieces from going too far
                            if p == 'E' and self.distance(i, j) > 4: break
                            if p == 'E' and self.board[j-d].isupper(): break
                            # Stop crawlers from sliding
                            if p == 'J' and d in (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W): break
                            if p in crawlers: break
                            # No sliding after captures
                            if q.islower(): break

    def distance(self, fromPos, toPos):
        return int(math.sqrt((toPos // 10 - fromPos // 10)**2 + (toPos % 10 - fromPos % 10)**2))

    def isPieceInvulnerable(self, board, fromPos, toPos):
        if any(var in board[fromPos] for var in ('K', 'W', 'U', 'C')):
            if any(var in board[toPos] for var in ('g', ' ', '\n')):
                return True
        elif board[fromPos] == 'E':
            if any(var in board[toPos] for var in ('C', 'm', 'g', ' ', '\n')):
                return True
        else:
            if any(var in board[toPos] for var in ('m', 'g', ' ', '\n')):
                return True
        if any(var in board[toPos] for var in ('e', ' ', '\n')):
            if self.distance(fromPos, toPos) >= 3:
                return True
        return False

    def rotate(self):
        ep = 119 if self.ep == 0 else self.ep
        kp = 119 if self.kp == 0 else self.kp
        return Position(
            self.board[::-1].swapcase(),
            not self.color, False, -self.score,
            self.ba, self.wa, self.bs, self.ws,
            self.bc, self.wc, 119-ep, 119-kp)

    def move(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        put = lambda board, i, p: board[:i] + p + board[i+1:]
        # Copy variables and reset ep and kp
        board, color, second = self.board, self.color, self.second
        wa, ba, ws, bs = self.wa, self.ba, self.ws, self.bs
        wc, bc, ep, kp = self.wc, self.bc, 0, 0
        score = self.score + self.value(move)
        # Actual move
        if p == 'T' and q != '.':
            board = put(board, j, '.')
        elif p == 'E' and q != '.':
            # 1: move E to next space.
            # 2: start rampage loop
            # 3: which direction?
            # 4: check invulnerability of next square
            # 5: move to next square
            # 6: go to step 3 once
            board = put(board, j, board[i])
            board = put(board, i, '.')
            if 3 - self.distance(i, j) > 0:
                for dr in range(abs(4 - self.distance(i, j))):
                    if dr is 0: continue
                    # is j on the same row?
                    if i // 10 - j // 10 == 0: # same row
                        # is j east or west?
                        if i - j < 0: # west
                            if not self.isPieceInvulnerable(board, j + int(dr / 2), j + dr):
                                board = put(board, j + dr, 'E')
                                board = put(board, j + int(dr / 2), '.')
                            else: break
                        else: # east
                            if not self.isPieceInvulnerable(board, j - int(dr / 2), j - dr):
                                board = put(board, j - dr, 'E')
                                board = put(board, j - int(dr / 2), '.')
                            else: break
                    else: # different row
                        # is j north or south?
                        if i - j > 0: # north
                            if not self.isPieceInvulnerable(board, j - int(dr / 2) * 10, j - dr * 10):
                                board = put(board, j - dr * 10, 'E')
                                board = put(board, j - int(dr / 2) * 10, '.')
                            else: break
                        else: # south
                            if not self.isPieceInvulnerable(board, j + int(dr / 2) * 10, j + dr * 10):
                                board = put(board, j + dr * 10, 'E')
                                board = put(board, j + int(dr / 2) * 10, '.')
                            else: break
        elif any(var in p for var in ('U', 'W')):
            if i == j:
                for dr in (N, E, S, W, N+E, S+E, S+W, N+W):
                    if board[i+dr].isspace(): continue
                    else: board = put(board, i+dr, '.')
            else:
                board = put(board, j, board[i])
                board = put(board, i, '.')
        elif p == 'M':
            if any(var in q for var in ('.', 'k', 'u', 'w', 'c')):
                board = put(board, j, board[i])
                board = put(board, i, '.')
        else:
            board = put(board, j, board[i])
            board = put(board, i, '.')
        # Castling rights
        if i == A1: wc = (False, wc[1])
        if i == H1: wc = (wc[0], False)
        if j == A8: bc = (bc[0], False)
        if j == H8: bc = (False, bc[1])
        # Castling
        if p == 'K':
            wc = (False, False)
            if abs(j-i) == 2:
                kp = (i+j)//2
                board = put(board, A1 if j < i else H1, '.')
                board = put(board, kp, 'R')
        # Special pawn stuff
        if p == 'P':
            if A8 <= j <= H8:
                board = put(board, j, 'Q')
            if j - i == N * 2:
                ep = i + N
            if j - i in (N+W, N+E) and q == '.':
                board = put(board, j + S, '.')
        #return Position(board, color, False, score, wa, ba, ws, bs, wc, bc, ep, kp).rotate()
        if second:
            return Position(board, color, False, score, wa, ba, ws, bs, wc, bc, ep, kp).rotate()
        else:
            if wa == 5:
                return Position(board, color, True, score, wa, ba, ws, bs, wc, bc, ep, kp)
            else:
                return Position(board, color, False, score, wa, ba, ws, bs, wc, bc, ep, kp).rotate()

    def value(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        # Actual move
        score = pst[p][j] - pst[p][i]
        # Capture
        if q.islower():
            score += pst[q.upper()][j]
        if q.isupper():
            score -= pst[q][j]//2
        # Castling check detection
        if abs(j - self.kp) < 2:
            score += pst['K'][j]
        # Castling
        if p == 'K' and abs(i - j) == 2:
            score += pst['R'][(i + j)//2]
            score -= pst['R'][A1 if j < i else H1]
        # Special pawn stuff
        if p == 'P':
            if A8 <= j <= H8:
                score += pst['Q'][j] - pst['P'][j]
            if j == self.ep:
                score += pst['P'][j+S]
        if any(var in p for var in ('K', 'U', 'W', 'C')) and 50 < i < 59:
            score = MIDLINE_VALUE
        if q.isupper() and q in ('K', 'U', 'W', 'C'):
            score = -30000
        return score
        #return score * random.uniform(.999, 1.001)

Entry = namedtuple('Entry', 'depth score gamma move')
tp = OrderedDict()


###############################################################################
# Search logic
###############################################################################

nodes = 0
def bound(pos, gamma, depth):
    """ returns s(pos) <= r < gamma    if s(pos) < gamma
        returns s(pos) >= r >= gamma   if s(pos) >= gamma """
    global nodes; nodes += 1
    #print("1. gamma: {}, depth: {}".format(gamma, depth))

    # Look in the table if we have already searched this position before.
    # We use the table value if it was done with at least as deep a search
    # as ours, and the gamma value is compatible.
    entry = tp.get(pos)
    #print("2. entry: {}".format(entry))
    if entry is not None and entry.depth >= depth and (
            entry.score < entry.gamma and entry.score < gamma or
            entry.score >= entry.gamma and entry.score >= gamma):
        #print("2.5. entry.score: {}".format(entry.score))
        return entry.score

    #print("inbetween2&3")
    # Stop searching if we have won/lost.
    if abs(pos.score) >= MATE_VALUE:
        #print("3. pos.score >= MATE_VALUE?")
        #print("pos.score: {}".format(pos.score))
        return pos.score
    #print("inbetween3&4")

    # Null move. Is also used for stalemate checking
    if pos.second:
        #print("nullscore -> pos.second ##############\n######################################################################")
        pos = Position(pos.board, pos.color, False, pos.score,
                pos.wa, pos.ba, pos.ws, pos.bs,
                pos.wc, pos.bc, pos.ep, pos.kp)
        nullscore = bound(pos.rotate(), 1-gamma, depth-3) if depth > 0 else pos.score
    else:
        nullscore = -bound(pos.rotate(), 1-gamma, depth-3) if depth > 0 else pos.score
    #nullscore = -MATE_VALUE*3 if depth > 0 else pos.score
    #print("4. nullscore: {}".format(nullscore))
    if nullscore >= gamma:
        #print("4.5. nullscore >= gamma?")
        #print("{} >= {}".format(nullscore, gamma))
        return nullscore
    #print("inbetween4&5")

    # We generate all possible, pseudo legal moves and order them to provoke
    # cuts. At the next level of the tree we are going to minimize the score.
    # This can be shown equal to maximizing the negative score, with a slightly
    # adjusted gamma value.
    best, bmove = -3*MATE_VALUE, None
    for move in sorted(pos.genMoves(pos.second), key=pos.value, reverse=True):
        #print("5. move: {}".format(move))
        # We check captures with the value function, as it also contains ep and kp
        if depth <= 0 and pos.value(move) < 150:
            #print("5.5. depth <= 0 and pos.value(move) < 150?")
            #print("depth: {}, pos.value(move): {}".format(depth, pos.value(move)))
            break
        if pos.second:
            #print("pos.second into bound")
            score = bound(pos.move(move), 1-gamma, depth-1)
        else:
            #print("else into bound")
            score = -bound(pos.move(move), 1-gamma, depth-1)
        if score > best:
            #print("5.6. score > best?\n{} > {}?".format(score, best))
            best = score
            bmove = move
        if score >= gamma:
            #print("5.7. score >= gamma?\n{} > {}?".format(score, gamma))
            break

    #print("inbetween5&6")
    # If there are no captures, or just not any good ones, stand pat
    if depth <= 0 and best < nullscore:
        #print("6. depth <= 0 and best < nullscore?")
        #print("depth: {}, best: {}, nullscore: {}".format(depth, best, nullscore))
        return nullscore

    #print("inbetween6&7")
    # Check for stalemate. If best move loses king, but not doing anything
    # would save us. Not at all a perfect check.
    if depth > 0 and best <= -MATE_VALUE is None and nullscore > -MATE_VALUE:
        #print("7. best: 0")
        best = 0
    #print("inbetween7&8")

    # We save the found move together with the score, so we can retrieve it in
    # the play loop. We also trim the transposition table in FILO order.
    # We prefer fail-high moves, as they are the ones we can build our pv from.
    if entry is None or depth >= entry.depth and best >= gamma:
        tp[pos] = Entry(depth, best, gamma, bmove)
        if len(tp) > TABLE_SIZE:
            tp.pop()
    #print("FINAL. best: {}".format(best))
    return best


def search(pos, maxn=NODES_SEARCHED):
    """ Iterative deepening MTD-bi search """
    global nodes; nodes = 0

    # We limit the depth to some constant, so we don't get a stack overflow in
    # the end game.
    for depth in range(1, 99):
        # The inner loop is a binary search on the score of the position.
        # Inv: lower <= score <= upper
        # However this may be broken by values from the transposition table,
        # as they don't have the same concept of p(score). Hence we just use
        # 'lower < upper - margin' as the loop condition.
        lower, upper = -3*MATE_VALUE, 3*MATE_VALUE
        while lower < upper - 3:
            #print("lower: {}, upper: {}".format(lower, upper))
            gamma = (lower+upper+1)//2
            score = bound(pos, gamma, depth)
            if score >= gamma:
                lower = score
            if score < gamma:
                upper = score

        print("Searched %d nodes. Depth %d. Score %d(%d/%d)" % (nodes, depth, score, lower, upper))

        # We stop deepening if the global N counter shows we have spent too
        # long, or if we have already won the game.
        if nodes >= maxn or abs(score) >= MATE_VALUE:
            break

    # If the game hasn't finished we can retrieve our move from the
    # transposition table.
    entry = tp.get(pos)
    if entry is not None:
        return entry.move, score
    return None, score


###############################################################################
# User interface
###############################################################################

# Python 2 compatability
if sys.version_info[0] == 2:
    input = raw_input


def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1]) - 1
    return A1 + fil - 10*rank


def render(i):
    rank, fil = divmod(i - A1, 10)
    return chr(fil + ord('a')) + str(-rank + 1)


def main():

    print("White Player, choose an army:")
    print("1. Classic  2. Nemesis  3. Empowered")
    print("4. Reaper 5. Two Kings 6. Animals")
    while True:
        print('Type the number, not the name.')
        userInput = getpass.getpass('> ')
        if userInput in string.digits:
            if int(userInput) < 7:
                if int(userInput) > 0:
                    break
            print('Please enter only one of the above.')
        else:
            print('Please enter only one character')
    wArmy = int(userInput)

    print("Black Player, choose an army:")
    print("1. Classic   2. Nemesis  3. Empowered")
    print("4. Reaper 5. Two Kings 6. Animals")
    while True:
        print('Type the number, not the name.')
        userInput = getpass.getpass('> ')
        if userInput in string.digits:
            if int(userInput) < 7:
                if int(userInput) > 0:
                    break
            print('Please enter only one of the above.')
        else:
            print('Please enter only one of the above.')
    bArmy = int(userInput)

    army_name_dict = {
        1: ('RNBQKBNR', 'P' * 8),
        2: ('RNBMCBNR', 'L' * 8),
        3: ('ZYXOCXYZ', 'P' * 8),
        4: ('GNBACBNG', 'P' * 8),
        5: ('RNBUWBNR', 'P' * 8),
        6: ('EHTJCTHE', 'P' * 8)}

    blackArmy = str(army_name_dict[bArmy][0][::-1].lower())
    blackPawns = str(army_name_dict[bArmy][1].lower())
    whiteArmy = str(army_name_dict[wArmy][0])
    whitePawns = str(army_name_dict[wArmy][1])

    initial = (
        '         \n'  #   0 -  9
        '         \n'  #  10 - 19
        ' '+blackArmy+'\n'  #  20 - 29
        ' '+blackPawns+'\n'  #  30 - 39
        ' ........\n'  #  40 - 49
        ' ........\n'  #  50 - 59
        ' ........\n'  #  60 - 69
        ' ........\n'  #  70 - 79
        ' '+whitePawns+'\n'  #  80 - 89
        ' '+whiteArmy+'\n'  #  90 - 99
        '         \n'  # 100 -109
        '          '   # 110 -119
    )

    pos = Position(initial, 0, False, 0, wArmy, bArmy, 3, 3, (True,True), (True,True), 0, 0)
    while True:
        # We add some spaces to the board before we print it.
        # That makes it more readable and pleasing.
        print(' '.join(pos.board))

        ## We query the user until she enters a legal move.
        #move = None
        #while move not in pos.genMoves():
            #crdn = input("Your move: ")
            #if crdn == 'exit': sys.exit(0)
            #try:
                #move = parse(crdn[0:2]), parse(crdn[2:4])
                #print(str(move))
                ## Inform the user when invalid input (e.g. "help") is entered
            #except ValueError:
                #print("Invalid input. Please enter a move in the proper format (e.g. g8f6)")
            #except IndexError:
                #print("Invalid input. Please enter a move in the proper format (e.g. g8f6)")
        #pos = pos.move(move)
        #if pos.second:
            #print(' '.join(pos.board))
            #move = None
            #while move not in pos.genMoves():
                #crdn = input("Your move: ")
                #if crdn == 'exit': sys.exit(0)
                #try:
                    #move = parse(crdn[0:2]), parse(crdn[2:4])
                    ## Inform the user when invalid input (e.g. "help") is entered
                #except ValueError:
                    #print("Invalid input. Please enter a move in the proper format (e.g. g8f6)")
                #except IndexError:
                    #print("Invalid input. Please enter a move in the proper format (e.g. g8f6)")
            #pos = pos.move(move)

        print(' '.join(pos.rotate().board))
        move, score = search(pos)
        print("My move:", render(119-move[0]) + render(119-move[1]))
        pos = pos.move(move)

        if pos.second:
            move, score = search(pos)
            print(str(move))
            if move:
                print(' '.join(pos.rotate().board))
                print("My move:", render(119-move[0]) + render(119-move[1]))
                pos = pos.move(move)
            else:
                score = 0
                pos = Position(pos.board, pos.color, False, score,
                        pos.wa, pos.ba, pos.ws, pos.bs,
                        pos.wc, pos.bc, pos.ep, pos.kp)
                pos = pos.rotate()

        #move = None
        #while move not in pos.genMoves():
            #crdn = input("Your move: ")
            #if crdn == 'exit': sys.exit(0)
            #try:
              #move = parse(crdn[0:2]), parse(crdn[2:4])
              ## Inform the user when invalid input (e.g. "help") is entered
            #except ValueError:
              #print("Invalid input. Please enter a move in the proper format (e.g. g8f6)")
            #except IndexError:
              #print("Invalid input. Please enter a move in the proper format (e.g. g8f6)")
        #pos = pos.move(move)

        if score <= -MATE_VALUE:
            print(' '.join(pos.board))
            print("You won")
            break
        if score >= MATE_VALUE:
            print(' '.join(pos.board))
            print("You lost")
            break


if __name__ == '__main__':
    main()
