# monte carlo testing for the volume of a d-dimensional sphere
import numpy as np
import math
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 16

def monte_carlo_sphere_volume(d, num_samples):
    # Generate random points in the d-dimensional cube [-1, 1]^d
    points = np.random.uniform(-1, 1, (num_samples, d))
    distances = np.linalg.norm(points, axis=1)
    inside_sphere = np.sum(distances <= 1)
    cube_volume = 2 ** d
    sphere_volume_estimate = (inside_sphere / num_samples) * cube_volume
    return sphere_volume_estimate

# fraction of points in the skin
def monte_carlo_sphere_skin_fraction(d, num_samples, epsilon):
    # Generate random points in the d-dimensional cube [-1, 1]^d
    points = np.random.uniform(-1, 1, (num_samples, d))
    distances = np.linalg.norm(points, axis=1)
    inside_sphere = np.sum(distances <= 1)
    inside_skin = np.sum((distances > 1 - epsilon) & (distances <= 1))
    if inside_sphere == 0:
        return 0
    skin_fraction_estimate = inside_skin / inside_sphere
    return skin_fraction_estimate

if __name__ == "__main__":
    dimensions = list(range(1, 16))
    num_samples = 10**6
    epsilon = 0.1
    # fraction of points in the skin
    skin_fractions = []
    for d in dimensions:
        skin_fraction = monte_carlo_sphere_skin_fraction(d, num_samples, epsilon)
        skin_fractions.append(skin_fraction)
        print(f"Dimension: {d}, Skin Fraction: {skin_fraction:.6f}")
    # plot the skin fractions
    plt.figure(figsize=(10, 6))
    plt.semilogy(dimensions, skin_fractions, marker='o', linestyle='-')
    plt.xlabel('Dimension')
    plt.ylabel('Fraction of Points in Skin')
    plt.title(f'Fraction of Points in the Skin Sphere (ε={epsilon})')
    plt.grid(True, which="both", ls="--")
    plt.xticks(dimensions)
    plt.ylim(0, 1)
    plt.show()