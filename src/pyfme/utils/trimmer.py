# -*- coding: utf-8 -*-
"""
Python Flight Mechanics Engine (PyFME).
Copyright (c) AeroPython Development Team.
Distributed under the terms of the MIT License.

Trimmer
-------
This module solves the problem of calculating the values of the state and
control vectors that satisfy the state equations of the aircraft at the initial
condition (or any other given condition. This cannot be done analytically
because of the very complex functional dependence of the erodynamic data.
Instead, it must be done with a numerical algorithm which iteratively adjusts
the independent variables until some solution criterion is met.
"""
from warnings import warn
import numpy as np
from math import sqrt, sin, cos, tan, atan
from scipy.optimize import least_squares

from pyfme.utils.coordinates import wind2body
from pyfme.environment.isa import atm


def steady_state_flight_trim(aircraft, h, TAS, gamma=0, turn_rate=0,
                             dyn_eqs=None, verbose=0):
    """Finds a combination of values of the state and control variables that
    correspond to a steady-state flight condition. Steady-state aircraft flight
    can be defined as a condition in which all of the motion variables are
    constant or zero. That is, the linear and angular velocity components are
    constant (or zero), and all acceleration components are zero.

    Parameters
    ----------
    aircraft : aircraft class
        Aircraft class with methods get_forces, get_moments
    h : float
        Geopotential altitude for ISA (m).
    TAS : float
        True Air Speed (m/s).
    gamma : float, optional
        Flight path angle (rad).
    turn_rate : float, optional
        Turn rate, d(psi)/dt (rad/s).

    Returns
    -------
    lin_vel : float array
        [u, v, w] air linear velocity body-axes (m/s).
    ang_vel : float array
        [p, q, r] air angular velocity body-axes (m/s).
    theta : float
        Pitch angle (rad).
    phi : float
        Bank angle (rad).
    alpha : float
        Angle of attack (rad).
    beta : float
        Sideslip angle (rad).
    control_vector : array_like
        [delta_e, delta_ail, delta_r, delta_t].

    Notes
    -----
    See section 3.4 in [1] for the algorithm description.
    See section 2.5 in [1] for the definition of steady-state flight condition.

    References
    ----------
    .. [1] Stevens, BL and Lewis, FL, "Aircraft Control and Simulation",
        Wiley-lnterscience.
    """

    if dyn_eqs is None:
        from pyfme.models.euler_flat_earth import linear_and_angular_momentum_eqs
        dynamic_eqs = linear_and_angular_momentum_eqs

    # TODO: try to look for a good inizialization method
    alpha_0 = 0.05 * np.sign(gamma)
    betha_0 = 0.001 * np.sign(turn_rate)
    delta_e_0 = 0.05
    delta_ail_0 = 0.01 * np.sign(turn_rate)
    delta_r_0 = 0.01 * np.sign(turn_rate)
    delta_t_0 = 0.5

    initial_guess = (alpha_0,
                     betha_0,
                     delta_e_0,
                     delta_ail_0,
                     delta_r_0,
                     delta_t_0)

    args = (h, TAS, gamma, turn_rate, aircraft, dynamic_eqs)

    # TODO: pass max deflection of the controls inside aircraft.
    lower_bounds = (-1, -0.5, -1, -1, -1, 0)
    upper_bounds = (+1, +0.5, +1, +1, +1, 1)

    results = least_squares(func, x0=initial_guess, args=args, verbose=verbose,
                            bounds=(lower_bounds, upper_bounds))

    trimmed_params = results['x']
    fun = results['fun']
    cost = results['cost']

    if cost > 1e-7 or any(abs(fun) > 1e-3):
        warn("Trim process did not converge", RuntimeWarning)
        if trimmed_params[5] > 0.99:
            warn("Probably not enough power for demanded conditions")

    alpha = trimmed_params[0]
    beta = trimmed_params[1]

    delta_e = trimmed_params[2]
    delta_ail = trimmed_params[3]
    delta_r = trimmed_params[4]
    delta_t = trimmed_params[5]

    # What happens if we have two engines and all that kind of things...?
    control_vector = delta_e, delta_ail, delta_r, delta_t

    if abs(turn_rate) < 1e-8:
        phi = 0
    else:
        phi = turn_coord_cons(turn_rate, alpha, beta, TAS, gamma)

    theta = rate_of_climb_cons(gamma, alpha, beta, phi)

    # w = turn_rate * k_h
    # k_h = sin(theta) i_b + sin(phi) * cos(theta) j_b + cos(theta) * sin(phi)
    # w = p * i_b + q * j_b + r * k_b
    p = - turn_rate * sin(theta)
    q = turn_rate * sin(phi) * cos(theta)
    r = turn_rate * cos(theta) * sin(phi)

    ang_vel = np.array([p, q, r])
    lin_vel = wind2body((TAS, 0, 0), alpha, beta)

    return lin_vel, ang_vel, theta, phi, alpha, beta, control_vector


def turn_coord_cons(turn_rate, alpha, beta, TAS, gamma=0):
    """Calculates phi for coordinated turn.
    """

    g0 = 9.81
    G = turn_rate * TAS / g0

    if abs(gamma) < 1e-8:
        phi = G * cos(beta) / (cos(alpha) - G * sin(alpha) * sin(beta))
        phi = atan(phi)

    else:
        a = 1 - G * tan(alpha) * sin(beta)
        b = sin(gamma) / cos(beta)
        c = 1 + G**2 * cos(beta)**2

        sq = sqrt(c * (1 - b**2) + G**2 * sin(beta)**2)

        num = (a-b**2) + b * tan(alpha) * sq
        den = a**2 - b**2 * (1 + c * tan(alpha)**2)

        phi = atan(G * cos(beta) / cos(alpha) * num / den)

    return phi


def turn_coord_cons_horizontal_and_small_beta(turn_rate, alpha, TAS):
    """Calculates phi for coordinated turn given that gamma is equal to cero
    and beta is small (beta << 1).
    """

    g0 = 9.81
    G = turn_rate * TAS / g0

    phi = G / cos(alpha)
    phi = atan(phi)

    return phi


def rate_of_climb_cons(gamma, alpha, beta, phi):
    """Calculates theta for the given ROC, wind angles, and roll angle.
    """
    a = cos(alpha) * cos(beta)
    b = sin(phi) * sin(beta) + cos(phi) * sin(alpha) * cos(beta)

    sq = sqrt(a**2 - sin(gamma)**2 + b**2)

    theta = (a * b + sin(gamma) * sq) / (a**2 - sin(gamma)**2)
    theta = atan(theta)

    return theta


def func(trimmed_params, h, TAS, gamma, turn_rate, aircraft, dynamic_eqs):
    """Function to optimize
    """
    alpha = trimmed_params[0]
    beta = trimmed_params[1]

    delta_e = trimmed_params[2]
    delta_ail = trimmed_params[3]
    delta_r = trimmed_params[4]
    delta_t = trimmed_params[5]

    if abs(turn_rate) < 1e-8:
        phi = 0
    else:
        phi = turn_coord_cons(turn_rate, alpha, beta, TAS, gamma)

    theta = rate_of_climb_cons(gamma, alpha, beta, phi)

    # w = turn_rate * k_h
    # k_h = sin(theta) i_b + sin(phi) * cos(theta) j_b + cos(theta) * sin(phi)
    # w = p * i_b + q * j_b + r * k_b
    p = - turn_rate * sin(theta)
    q = turn_rate * sin(phi) * cos(theta)
    r = turn_rate * cos(theta) * sin(phi)

    ang_vel = np.array([p, q, r])

    lin_vel = wind2body((TAS, 0, 0), alpha, beta)

    # FIXME: This implied some changes in the aircraft model.
    # psi angle does not influence the attitude of the aircraft for gravity
    # force projection. So it is set to 0.
    attitude = np.array([theta, phi, 0])
    _, _, rho, _ = atm(h)
    forces, moments = aircraft.get_forces_and_moments(TAS, rho, alpha, beta,
                                                      delta_e, 0, delta_ail,
                                                      delta_r, delta_t,
                                                      attitude)
    mass, inertia = aircraft.mass_and_inertial_data()

    vel = np.concatenate((lin_vel[:], ang_vel[:]))

    output = dynamic_eqs(0, vel, mass, inertia, forces, moments)

    return output
