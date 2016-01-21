# -*- coding: utf-8 -*-
"""
Anemometry related functions
"""

from math import asin, atan, sqrt


def calculate_alpha_beta_TAS(u, v, w):
    """
    Calculate the angle of attack (AOA), angle of sideslip (AOS) and true air
    speed from the **aerodynamic velocity** in body coordinates.

    Parameters
    ----------
    u : float
        x-axis component of aerodynamic velocity.
    v : float
        y-axis component of aerodynamic velocity.
    w : float
        z-axis component of aerodynamic velocity.

    Returns
    -------
    alpha : float
        Angle of attack (rad).
    betha : float
        Angle of sideslip (rad).
    TAS : float
        True Air Speed.

    Notes
    -----
    See [1] or [2] for frame of reference definition.
    See [3] for formula derivation.

    $$ TAS = sqrt(u^2 + v^2 + w^2)$$

    $$ alpha = \atan(w / u) $$
    $$ beta = \asin(v / TAS) $$

    References
    ----------
    .. [1] B. Etkin, "Dynamics of Atmospheric Flight," Courier Corporation,
        pp. 104-120, 2012.
    .. [2] Gómez Tierno, M.A. et al, "Mecánica del Vuelo," Garceta, pp. 1-12,
        2012.
    .. [3] Stevens, BL and Lewis, FL, "Aircraft Control and Simulation",
        Wiley-lnterscience, pp. 64, 1992.
    """

    TAS = sqrt(u ** 2 + v ** 2 + w ** 2)

    alpha = atan(w / u)
    beta = asin(v / TAS)

    return alpha, beta, TAS


def calculate_dynamic_pressure(rho, TAS):
    """Calculates the dynamic pressure.

    Parameters
    ----------
    rho : float
        Air density (kg/m³).
    TAS : float
        True Air Speed (m/s).

    Returns
    -------
    q_inf : float
        Dynamic pressure.

    Notes
    -----
    $$ q_{inf} = 1/2  · rho · TAS² $$
    """

    return 0.5 * rho * TAS ** 2


def calculate_viscosity_Sutherland(T):
    """Calculates the viscosity of the air

    Parameters
    -----------
    T : float
        Temperature (K)

    Returns
    -----------
    visc : float
        viscosity of the air (kg/(m s))

    Notes
    -----------
    Acoording to [1] the limis for this function are:

    p < p_c =36 Atm (3.65 MPa)
    T < 2000 K

    According to [2] the limits for this function are:

    T < 550 K


    """

    visc_0 = 1.176*1e-5  # kg(m s)
    T_0 = 273.1 # K
    b = 0.4042 # nondimensional


    return visc_0 * (T /T_0)**(3/2) * ((1 + b)/((T/T_0) + b))
