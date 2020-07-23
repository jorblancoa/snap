# Copyright (c) 2019, EPFL/Blue Brain Project

# This file is part of BlueBrain SNAP library <https://github.com/BlueBrain/snap>

# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3.0 as published
# by the Free Software Foundation.

# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.

# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Miscellaneous utilities."""

import collections
import json
import itertools

import numpy as np
import six

from bluepysnap.exceptions import BluepySnapError
from bluepysnap.sonata_constants import DYNAMICS_PREFIX


def load_json(filepath):
    """Load JSON from file."""
    with open(filepath) as f:
        return json.load(f)


def is_iterable(v):
    """Check if `v` is any iterable (strings are considered scalar)."""
    return isinstance(v, collections.Iterable) and not isinstance(v, six.string_types)


def ensure_list(v):
    """Convert iterable / wrap scalar into list (strings are considered scalar)."""
    if is_iterable(v):
        return list(v)
    else:
        return [v]


def roundrobin(*iterables):
    """Roundrobin function.

    roundrobin('ABC', 'D', 'EF') --> A D E B F C.
    From: https://docs.python.org/3.6/library/itertools.html
    """
    num_active = len(iterables)

    # cannot use six.next. Need the function and not the call and cannot use ternary operator
    if six.PY3:  # pragma: no cover
        next_wrapper = lambda x: x.__next__
    else:  # pragma: no cover
        next_wrapper = lambda x: x.next

    nexts = itertools.cycle(next_wrapper(iter(it)) for it in iterables)
    while num_active:
        try:
            for next_ in nexts:
                yield next_.__call__()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = itertools.cycle(itertools.islice(nexts, num_active))


def add_dynamic_prefix(properties):
    """Add the dynamic prefix to a list of properties."""
    return [DYNAMICS_PREFIX + name for name in list(properties)]


def euler2mat(az, ay, ax):
    """Build 3x3 rotation matrices from az, ay, ax rotation angles (in that order).

    Args:
        az: rotation angles around Z (Nx1 NumPy array; radians)
        ay: rotation angles around Y (Nx1 NumPy array; radians)
        ax: rotation angles around X (Nx1 NumPy array; radians)

    Returns:
        List with Nx3x3 rotation matrices corresponding to each of N angle triplets.

    See Also:
        https://en.wikipedia.org/wiki/Euler_angles#Rotation_matrix (R = X1 * Y2 * Z3)
    """
    if len(az) != len(ay) or len(az) != len(ax):
        raise BluepySnapError("All angles must have the same length.")
    c1, s1 = np.cos(ax), np.sin(ax)
    c2, s2 = np.cos(ay), np.sin(ay)
    c3, s3 = np.cos(az), np.sin(az)

    mm = np.array([
        [c2 * c3, -c2 * s3, s2],
        [c1 * s3 + c3 * s1 * s2, c1 * c3 - s1 * s2 * s3, -c2 * s1],
        [s1 * s3 - c1 * c3 * s2, c3 * s1 + c1 * s2 * s3, c1 * c2],
    ])

    return [mm[..., i] for i in range(len(az))]


def quaternion2mat(aqw, aqx, aqy, aqz):
    """Build 3x3 rotation matrices from quaternions.

    Args:
        aqw: w component of quaternions (Nx1 NumPy array; float)
        aqx: x component of quaternions (Nx1 NumPy array; float)
        aqy: y component of quaternions (Nx1 NumPy array; float)
        aqz: z component of quaternions (Nx1 NumPy array; float)

    Returns:
        List with Nx3x3 rotation matrices corresponding to each of N quaternions.

    See Also:
        https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    """

    def normalize_quaternions(qs):
        """Normalize a bunch of quaternions along axis==1.

        Args:
            qs: quaternions (Nx4 NumPy array; float)

        Returns:
           numpy array of normalized quaternions
        """
        return qs / np.sqrt(np.einsum('...i,...i', qs, qs)).reshape(-1, 1)

    aq = np.dstack([np.asarray(aqw), np.asarray(aqx), np.asarray(aqy), np.asarray(aqz)])[0]
    aq = normalize_quaternions(aq)

    w = aq[:, 0]
    x = aq[:, 1]
    y = aq[:, 2]
    z = aq[:, 3]

    mm = np.array([[w * w + x * x - y * y - z * z, 2 * x * y - 2 * w * z, 2 * w * y + 2 * x * z],
                   [2 * w * z + 2 * x * y, w * w - x * x + y * y - z * z, 2 * y * z - 2 * w * x],
                   [2 * x * z - 2 * w * y, 2 * w * x + 2 * y * z, w * w - x * x - y * y + z * z]])

    return [mm[..., i] for i in range(len(aq))]
