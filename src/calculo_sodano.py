from math import radians, degrees, sin, cos, tan, atan, atan2

def sodano_directo(phi1_deg, lon1_deg, Az12_deg, S, a, f):
    b = a * (1 - f)
    e2 = (a**2 - b**2) / a**2

    φ1 = radians(phi1_deg)
    β1 = atan((b/a) * tan(φ1))
    A12 = radians(Az12_deg)
    cosβ0 = cos(β1) * sin(A12)
    g = cos(β1) * cos(A12)
    m1 = (1 + (e2/2) * sin(β1)**2) * (1 - cosβ0**2)
    φs = S / b
    a1 = (1 + (e2/2) * sin(β1)**2) * (sin(β1)**2 * cos(φs) + g * sin(β1) * sin(φs))

    Term1 = φs + a1 * (-(e2/2)*sin(φs)) + m1 * (-(e2/4)*φs + (e2/4)*sin(φs)*cos(φs))
    Term2 = (
        a1**2 * (5*e2**2/8 * sin(φs)*cos(φs)) +
        m1**2 * (
            (11*e2**2/64)*φs
            - (13*e2**2/64)*sin(φs)*cos(φs)
            - (e2**2/8)*φs*cos(φs)**2
            + (5*e2**2/32)*sin(φs)*cos(φs)**3
        )
    )
    Term3 = a1 * m1 * (
        (3*e2**2/8)*sin(φs)
        + (e2**2/4)*φs*cos(φs)
        - (5*e2**2/8)*sin(φs)*cos(φs)**2
    )

    φ0 = Term1 + Term2 + Term3

    cotA21 = (g * cos(φ0) - sin(β1) * sin(φ0)) / cosβ0
    A21 = degrees(atan2(1, cotA21))
    cotλ = (cos(β1) * cos(φ0) - sin(β1) * sin(φ0) * cos(A12)) / (sin(φ0) * sin(A12))
    L = -atan(cotλ)
    λ1 = radians(lon1_deg)
    λ2 = λ1 + L

    senβ2 = sin(β1) * cos(φ0) + g * sin(φ0)
    cosβ2 = ((cosβ0)**2 + (g * cos(φ0) - sin(β1) * sin(φ0))**2)**0.5
    β2 = atan2(senβ2, cosβ2)
    φ2 = atan((a/b) * tan(β2))

    return {
        "b": b,
        "e2": e2,
        "φ1": phi1_deg,
        "β1": degrees(β1),
        "A12": Az12_deg,
        "cosβ0": cosβ0,
        "g": g,
        "m1": m1,
        "φs": φs,
        "a1": a1,
        "Term1": Term1,
        "Term2": Term2,
        "Term3": Term3,
        "φ0": φ0,
        "cotA21": cotA21,
        "A21": A21,
        "cotλ": cotλ,
        "L": degrees(L),
        "λ1": lon1_deg,
        "λ2": degrees(λ2),
        "senβ2": senβ2,
        "cosβ2": cosβ2,
        "β2": degrees(β2),
        "φ2": degrees(φ2)
    }