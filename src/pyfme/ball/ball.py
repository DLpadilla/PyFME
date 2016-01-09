# -*- coding: utf-8 -*-
"""
Created on Fri Jan  8 18:53:17 2016

@author: Juan
"""

import numpy as np


def Geometric_Data():

    """ Provides the value of some geometric data.

    Data
    ----

    r    radius(m)
    S_circle    Surface (m^2)
    S_sphere    Surface (m^2)

    References
    ----------
    Return
    ------
    r    radius(m)
    Sw    Surface (m^2)

    Raises
    ------
    See Also
    --------
    Notes
    -----
    References
    ----------
    .. [1]
    """
    r = 0.111
    S_circle = np.pi * r ** 2
    S_sphere = 4 * np.pi * r ** 2

    return r, S_circle, S_sphere


def Mass_and_Inertial_Data(r):

    """ Provides the value of some mass and inertial data.

    Data
    -----
    mass   (kg)
    Ixxb Moment of Inertia x-axis (Kg * m2)
    Iyyb Moment of Inertia y-axis (Kg * m2)
    Izzb Moment of Inertia z-axis (Kg * m2)

    Return
    ------
    mass
    I_matrix    Array

    Raises
    ------
    See Also
    --------
    Notes
    -----
    References
    ----------
    .. [1]
    """

    mass = 0.440
    Ixxb = 2 * mass * (r ** 2) / 3
    Iyyb = Ixxb
    Izzb = Ixxb

    I_matrix = np.diag([Ixxb, Iyyb, Izzb])

    return mass, I_matrix


def Ball_forces(velocity_vector, rho, radius):
    """ Given a vector velocity gives the forces and moments.
    Data for a soccer ball (smooth sphere)

    Data
    -----
    velocity_vector = np.array([u, v, w, p, q, r])    air velocity body-axes
                                                        (m/s)
    rho    air density(m/kg^3)
    A_front    Front section (m^2)
    C_magnus    magnus effect coefficient force
    F_magnus    magnus force (Pa)
    Cd    Drag coefficient
    D    drag force (Pa)
    Sn    effective spin number (wn*r/V)
    V    velocity modulus (m/s)
    wn    angular velocity perpendicular to the linear velocity (m/s)
    Re    Reynolds number
    mu = 1.983 e-5   viscosity (kg/s/m)
    radius    (m)
    dir_F_magnus    director vector of the magnus Force (body axes)
    F_magnus_vector_body    magnus Forces vector (body axes)
    Fx_magnus_body    magnus Forces x-body-axes
    Fy_magnus_body    magnus Forces y-body-axes
    Fz_magnus_body    magnus Forces z-body-axes

    Sn    C_magnus    [1]
    ---------------
    0     0
    0.04  0.1
    0.10  0.16
    0.20  0.23
    0.40  0.33

    Re       Cd    [1]
    --------------
    38000    0.49
    100000    0.50
    160000    0.51
    200000    0.51
    250000    0.49
    300000    0.46
    330000    0.39
    350000    0.20
    375000    0.09
    400000    0.07
    500000    0.07
    800000    0.10
    2000000    0.15
    4000000    0.18


    Return
    ------

    Raises
    ------
    See Also
    --------
    Notes
    -----
    References
    ----------
    "Aerodynamics of Sports Balls" Annual Review of Fluid Mechanics, 1875.17:15
    [1]
    """

    A_front = np.pi * radius ** 2

    mu = 1.983 * 10 ** -5
    Re_list = [38000, 100000, 160000, 200000, 250000, 300000, 330000, 350000,
               375000, 400000, 500000, 800000, 200000, 4000000]
    Cd_list = [0.49, 0.50, 0.51, 0.51, 0.49, 0.46, 0.39, 0.20, 0.09, 0.07,
               0.07, 0.10, 0.15, 0.18]
    Sn_list = [0.00, 0.04, 0.10, 0.20, 0.40]
    Cl_list = [0.00, 0.10, 0.16, 0.23, 0.33]

    u, v, w = velocity_vector[:3]
    p, q, r = velocity_vector[3:]

    V = np.linalg.norm(velocity_vector[:3])
    Re = rho * V * radius / mu

    if Re < Re_list[0]:
        raise ValueError("Reynolds number cannot be lower than 38000.")
    elif Re > Re_list[-1]:
        raise ValueError("Reynolds number cannot be higher than 4e6.")
    else:
        Cd = np.interp(Re, Re_list, Cd_list)

    wn = np.sqrt((v * r - w * q) ** 2 + (w * p - u * r) ** 2 +
                 (u * q - v * p) ** 2)

    Sn = wn * radius / V

    if Sn < Sn_list[0]:
        raise ValueError("Effective Spin number cannot be less than 0.")
    elif Sn > Sn_list[-1]:
        raise ValueError("Effective Spin number cannot be bigger than 0.40.")
    else:
        C_magnus = np.interp(Sn, Sn_list, Cl_list)

    D = 0.5 * rho * V ** 2 * A_front * Cd

    F_magnus = 0.5 * rho * V ** 2 * A_front * C_magnus
    dir_F_magnus = np.array([v * r - w * q, w * p - u * r, u * q - v * p]) / wn
    F_magnus_vector_body = dir_F_magnus * F_magnus
    Fx_magnus_body = F_magnus_vector_body[0]
    Fy_magnus_body = F_magnus_vector_body[1]
    Fz_magnus_body = F_magnus_vector_body[2]

    return D, F_magnus, Cd, C_magnus, F_magnus_vector_body, Fx_magnus_body, \
        Fy_magnus_body, Fz_magnus_body
