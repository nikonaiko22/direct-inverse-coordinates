from math import radians, degrees, sin, cos, tan, atan, atan2

def dms_to_deg(deg, min, sec, hemi, tipo):
    """Convierte grados, minutos, segundos y hemisferio a decimal (convención: lat N+, S-, lon E-, W+)"""
    val = abs(float(deg)) + float(min)/60 + float(sec)/3600
    if tipo == "lat":
        if hemi == "S":
            val = -val
    elif tipo == "lon":
        if hemi == "E":
            val = -val
    return val

def sodano_directo(phi1_deg, lon1_deg, Az12_deg, S, a, f_inv):
    # f_inv es el inverso del achatamiento: por ejemplo, para Internacional es 297.0
    f = 1 / float(f_inv)
    b = a * (1 - f)  # CORRECCIÓN: calcula b de la forma b = a * (1 - (1/f))
    e2 = (a**2 - b**2) / a**2

    # 1
    φ1 = radians(phi1_deg)
    β1 = atan((b/a) * tan(φ1))
    # 2
    A12 = radians(Az12_deg)
    cosβ0 = cos(β1) * sin(A12)
    # 3
    g = cos(β1) * cos(A12)
    # 4
    m1 = (1 + (e2/2) * sin(β1)**2) * (1 - cosβ0**2)
    # 5
    φs = S / b
    # 6
    a1 = (1 + (e2/2) * sin(β1)**2) * (sin(β1)**2 * cos(φs) + g * sin(β1) * sin(φs))
    # 8
    Term1 = φs + a1 * (-(e2/2)*sin(φs)) + m1 * (-(e2/4)*φs + (e2/4)*sin(φs)*cos(φs))
    # 9
    Term2 = (
        a1**2 * (5*e2**2/8 * sin(φs)*cos(φs)) +
        m1**2 * (
            (11*e2**2/64)*φs
            - (13*e2**2/64)*sin(φs)*cos(φs)
            - (e2**2/8)*φs*cos(φs)**2
            + (5*e2**2/32)*sin(φs)*cos(φs)**3
        )
    )
    # 10
    Term3 = a1 * m1 * (
        (3*e2**2/8)*sin(φs)
        + (e2**2/4)*φs*cos(φs)
        - (5*e2**2/8)*sin(φs)*cos(φs)**2
    )
    # 7
    φ0 = Term1 + Term2 + Term3
    # 11
    cotA21 = (g * cos(φ0) - sin(β1) * sin(φ0)) / cosβ0
    A21 = degrees(atan2(1, cotA21))
    # 12
    cotλ = (cos(β1) * cos(φ0) - sin(β1) * sin(φ0) * cos(A12)) / (sin(φ0) * sin(A12))
    # 13
    L = -atan(cotλ)
    # 14
    λ1 = radians(lon1_deg)
    λ2 = λ1 + L
    # 15
    senβ2 = sin(β1) * cos(φ0) + g * sin(φ0)
    # 16
    cosβ2 = ((cosβ0)**2 + (g * cos(φ0) - sin(β1) * sin(φ0))**2)**0.5
    # 17
    β2 = atan2(senβ2, cosβ2)
    # 18
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