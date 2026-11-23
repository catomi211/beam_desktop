# Beam Designer

Beam Designer is a Tkinter desktop app for preliminary beam analysis. It supports simply supported and cantilever beams, point and distributed loads, member properties, reaction/shear/moment/deflection calculations, pass/fail checks, saved beam designs, CSV result exports, and PDF calculation sheets.

## Calculations

Beam Designer uses linear-elastic Euler-Bernoulli beam theory for prismatic members. It does not include continuous beams, buckling, shear deformation, torsion, lateral-torsional stability, dynamic loading, connections, or second-order effects.

### Units and sign convention

- Geometry and load positions: feet.
- Loads: kips or kips per foot.
- Member modulus: ksi.
- Moment of inertia: in⁴.
- Section modulus: in³.
- Reactions and shear: kips.
- Moment: kip-ft.
- Deflection: inches.
- Downward loads are positive in the app's load-sign system. Upward loads are negative.

### Member properties

The app provides built-in steel W-shape and lumber selections. Each member supplies:

$$
E = \text{elastic modulus}
$$

$$
I = \text{moment of inertia}
$$

$$
S = \text{section modulus}
$$

$$
F_b = \text{allowable bending stress}
$$

For example, the W12×26 steel section uses $E = 29{,}000$ ksi, $I = 204$ in⁴, $S = 33.4$ in³, and $F_b = 24$ ksi.

### Loads

For a point load $P$ at position $a$, the signed load is:

$$
P_{\text{signed}}
=
\begin{cases}
P, & \text{downward}\\
-P, & \text{upward}
\end{cases}
$$

For a uniformly distributed load with magnitude $w$ from $a$ to $b$, the total load and centroidal position are:

$$
W = w_{\text{signed}}(b-a)
$$

$$
x_W = \frac{a+b}{2}
$$

The optional self-weight is treated as an assumed downward uniform load spanning the full beam. Its assumed value is member-specific and is displayed separately from the verified section properties.

### Reactions

For a simply supported beam, the code sums all loads and moments about the left support:

$$
\Sigma F_y = R_L + R_R + \Sigma P_{\text{signed}} + \Sigma W = 0
$$

With downward and upward loads represented using signed values:

$$
R_R = \frac{\Sigma \left(P_{\text{signed}}a\right)
+ \Sigma \left(Wx_W\right)}{L}
$$

$$
R_L = \Sigma P_{\text{signed}}+\Sigma W-R_R
$$

For a cantilever, the fixed support reaction is:

$$
R_{\text{fixed}}
=
\Sigma P_{\text{signed}}+\Sigma W
$$

and the fixed-end moment is:

$$
M_{\text{fixed}}
=
-\left[
\Sigma \left(P_{\text{signed}}a\right)
+
\Sigma \left(Wx_W\right)
\right]
$$

### Shear and moment

The app evaluates shear and moment along a numerical beam grid that includes the beam ends and all point-load, distributed-load start, and distributed-load end locations.

For a simply supported beam:

$$
V(x)
=
R_L
-\sum_{a_i \leq x}P_{\text{signed},i}
-\sum w_{\text{signed},j}
\left[\min(x,b_j)-a_j\right]_+
$$

where

$$
\left[z\right]_+ =
\begin{cases}
z, & z>0\\
0, & z\leq 0
\end{cases}
$$

The moment at position $x$ is:

$$
M(x)
=
R_Lx
-\sum_{a_i \leq x}
P_{\text{signed},i}(x-a_i)
-\sum w_{\text{signed},j}
\frac{\left[\min(x,b_j)-a_j\right]_+^2}{2}
$$

Point loads produce an instantaneous shear jump but leave moment continuous. Distributed-load segments change shear linearly and moment quadratically.

### Deflection

The app evaluates moment in kip-ft and converts it to inch-kips before calculating curvature:

$$
\kappa(x)
=
-\frac{M(x)\,(12)}{EI}
$$

Here, $EI$ is in kip-in² because $E$ is in ksi and $I$ is in in⁴.

Starting with zero rotation and deflection at the cantilever fixed end, or an adjusted linear rigid-body rotation for a simply supported beam, the code numerically integrates:

$$
\theta(x)
=
\int_0^x \kappa(s)\,ds
$$

$$
y(x)
=
\int_0^x \theta(s)\,ds
$$

The simply supported result is shifted so that deflection is zero at both beam ends:

$$
y_{\text{corrected}}(x)
=
y(x)-y(L)\frac{x}{L}
$$

For a cantilever:

$$
y(0)=0,\qquad \theta(0)=0
$$

For a simply supported beam:

$$
y(0)=0,\qquad y(L)=0
$$

The numerical integrations use trapezoidal accumulation on a grid containing support points, point-load locations, and uniform-load boundaries. The governing deflection is:

$$
\left|y\right|_{\max}
=
\max_x \left|y(x)\right|
$$

### Bending stress

The governing moment is converted to kip-in:

$$
M_{\max,\text{in}}
=
\left|M_{\max}\right|_{\text{kip-ft}}(12)
$$

Bending stress is:

$$
f_b
=
\frac{M_{\max,\text{in}}}{S}
$$

The bending check is:

$$
f_b \leq F_b
\quad\Rightarrow\quad
\text{PASS}
$$

$$
f_b > F_b
\quad\Rightarrow\quad
\text{FAIL}
$$

### Deflection check

The default allowable deflection is:

$$
y_{\text{allow}}
=
\frac{L}{360}
$$

where $L$ is converted from feet to inches:

$$
L_{\text{in}} = L_{\text{ft}}(12)
$$

A user-entered deflection limit replaces \(L/360\). The result passes when:

$$
\left|y\right|_{\max}\leq y_{\text{allow}}
$$

## Calculation workflow

1. The Tkinter UI reads support type, span, loads, member selection, cut locations, and self-weight state.
2. Input validation rejects invalid spans, load ranges, magnitudes, members, cuts, and deflection limits.
3. Invalid designs clear or hide results instead of showing stale values.
4. Loads are normalized to signed kip values.
5. Support reactions are calculated from vertical equilibrium.
6. Shear and moment are evaluated across the numerical beam grid.
7. Moment is converted to curvature and numerically integrated for rotation and deflection.
8. Governing moments, deflections, locations, bending stress, and deflection checks are calculated.
9. Tkinter displays the metrics and pass/fail cards while Matplotlib redraws the beam and diagrams.
10. CSV and PDF exports use the latest valid calculation results.

## Install

Install the required Python packages:

```text
pip install -r requirements.txt
```

## Run

Start the app from the project directory:

```text
python app.py
```
