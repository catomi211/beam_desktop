# Beam Designer

Beam Designer is a Tkinter desktop application for preliminary beam analysis. It supports:

- Simply supported and cantilever beams.
- Multiple point loads and uniformly distributed loads.
- Upward and downward loads.
- Steel W-shapes and lumber members.
- Reactions, shear, moment, deflection, and bending-stress calculations.
- Pass/fail checks.
- Saved `.beam.json` designs.
- CSV result exports.
- Multi-page PDF calculation sheets.

## Calculations

Beam Designer uses linear-elastic Euler-Bernoulli beam theory for prismatic members. It does not include continuous beams, buckling, shear deformation, torsion, lateral-torsional stability, dynamic loading, connections, or second-order effects.

### Units and sign convention

| Quantity | Unit |
|---|---|
| Beam position and span | ft |
| Point loads | kip |
| Distributed loads | kip/ft |
| Reactions and shear | kip |
| Elastic modulus | ksi |
| Moment of inertia | in^4 |
| Section modulus | in^3 |
| Moment | kip-ft |
| Deflection | in |

Downward loads are positive in the app's signed load system. Upward loads are negative.

### Member properties

Each member provides:

```text
E  = elastic modulus
I  = moment of inertia
S  = section modulus
Fb = allowable bending stress
```

Example: W12 x 26 steel:

```text
E  = 29,000 ksi
I  = 204 in^4
S  = 33.4 in^3
Fb = 24 ksi
```

### Loads

For a point load P at position a:

```text
P_signed =  P for a downward load
P_signed = -P for an upward load
```

For a uniformly distributed load w from position a to position b:

```text
W = w_signed * (b - a)

xW = (a + b) / 2
```

The optional self-weight is an assumed downward uniform load spanning the full beam. The assumed weight is member-specific and is shown separately from the member section properties.

### Reactions

#### Simply supported beam

The app sums all loads and moments about the left support.

```text
Moment about left support =
    sum(P_signed * a) + sum(W * xW)

Right reaction:
    RR = Moment about left support / span

Left reaction:
    RL = sum(P_signed) + sum(W) - RR
```

The vertical equilibrium equation is:

```text
RL + RR + sum(P_signed) + sum(W) = 0
```

#### Cantilever beam

```text
Fixed-end vertical reaction:
    Rfixed = sum(P_signed) + sum(W)

Fixed-end moment:
    Mfixed = -[sum(P_signed * a) + sum(W * xW)]
```

### Shear

For a simply supported beam, shear at position x is:

```text
V(x) = RL
       - sum(P_signed[i]) for every point load located at or left of x
       - sum[w_signed[j] * covered_length[j]]

covered_length[j] =
    max(0, min(x, b[j]) - a[j])
```

At a point load, shear jumps by the signed load magnitude. The moment remains continuous at that location.

### Moment

For a simply supported beam:

```text
M(x) = RL * x
       - sum(P_signed[i] * (x - a[i]))
         for every point load located at or left of x

       - sum[
            w_signed[j] * covered_length[j]
            * (x - (a[j] + covered_end[j]) / 2)
         ]
```

where:

```text
covered_end[j] = min(x, b[j])
covered_length[j] = max(0, covered_end[j] - a[j])
```

Within a distributed-load segment:

```text
Shear varies linearly.
Moment varies quadratically.
```

The app reports the maximum positive shear, maximum negative shear, maximum positive moment, maximum negative moment, and governing absolute moment.

### Deflection

The app uses linear-elastic Euler-Bernoulli beam theory.

Moment in kip-ft is converted to inch-kips:

```text
Moment_in_kip_in = M(x) * 12
```

Curvature is:

```text
kappa(x) = -Moment_in_kip_in / (E * I)
```

The curvature is numerically integrated once for rotation and again for deflection:

```text
theta(x) = integral from 0 to x of kappa(s) ds

y(x) = integral from 0 to x of theta(s) ds
```

The integration uses trapezoidal accumulation on a grid containing:

- 0 ft.
- The beam span.
- Every point-load position.
- Every distributed-load start and end position.
- Additional numerical grid points.

#### Simply supported boundary conditions

```text
y(0) = 0
y(L) = 0
```

The app applies a rigid-body rotation correction to enforce zero deflection at both supports:

```text
y_corrected(x) = y(x) - y(L) * x / L
```

#### Cantilever boundary conditions

```text
y(0) = 0
theta(0) = 0
```

The maximum absolute deflection is:

```text
y_max_absolute = max |y(x)|
```

### Bending stress

The governing moment is converted to kip-in:

```text
Mgoverning_kip_in = |Mgoverning_kip_ft| * 12
```

The bending stress is:

```text
fb = Mgoverning_kip_in / S
```

The bending check is:

```text
fb <= allowable bending stress  -> PASS
fb >  allowable bending stress  -> FAIL
```

### Deflection check

The default allowable deflection is:

```text
y_allowable = L_in / 360

L_in = span in feet * 12
```

A user-entered deflection limit replaces the default `L / 360` limit.

```text
|y_max_absolute| <= y_allowable  -> PASS
|y_max_absolute| >  y_allowable  -> FAIL
```

## Calculation workflow

1. The UI collects support type, span, loads, member selection, cut locations, and self-weight state.
2. Input validation rejects invalid spans, load ranges, magnitudes, members, cuts, and deflection limits.
3. Invalid designs clear or hide results instead of displaying stale values.
4. Loads are converted to signed kip values.
5. Reactions are calculated from vertical equilibrium.
6. Shear and moment are evaluated across the beam grid.
7. Moment is converted to curvature and integrated for rotation and deflection.
8. Governing values, bending stress, and pass/fail checks are calculated.
9. Tkinter displays metrics and status cards while Matplotlib redraws the beam and diagrams.
10. CSV and PDF exports use the latest valid calculation results.

## Install

Install the required packages:

```text
pip install -r requirements.txt
```

## Run

Start the app from the project directory:

```text
python app.py
```
