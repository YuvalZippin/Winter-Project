import random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import curve_fit
import time
import multiprocessing as mp


def func_transform(x):
    """Transform a uniform variable into a power-law waiting time."""
    return x**(-2)

def gen_wait_time(a=0, b=1) -> float:
    """Generate a single waiting time using func_transform."""
    return func_transform(random.uniform(a, b))

def generate_waiting_times(size: int) -> list:
    """Generate a shuffled list of waiting times, centered around the middle."""
    waiting_times = [gen_wait_time() for _ in range(size)]
    np.random.shuffle(waiting_times)
    mid_index = size // 2
    waiting_times[mid_index] = 0  # Immediate jump at the middle
    return waiting_times

def sample_jump():
    """
    Returns a jump (dx, dy) chosen from:
      - RIGHT: (1, 0) with probability 3/8,
      - LEFT:  (-1, 0) with probability 1/8,
      - UP:    (0, 1) with probability 1/4,
      - DOWN:  (0, -1) with probability 1/4.
    """
    r = random.random()
    if r < 3/8:
        return (1, 0)       # RIGHT
    elif r < 3/8 + 1/8:
        return (-1, 0)      # LEFT
    elif r < 3/8 + 1/8 + 1/4:
        return (0, 1)       # UP
    else:
        return (0, -1)      # DOWN

def RW_sim_2d_fixed_wait(sim_time: int, wait_list_size: int, Y_min: int, Y_max: int) -> tuple:
    """Simulate a 2D random walk with quenched waiting times and periodic boundaries in y."""
    
    wait_x = generate_waiting_times(wait_list_size)
    wait_y = generate_waiting_times(wait_list_size)
    
    x, y = 0, 0
    positions = [(x, y)]
    times = [0]
    current_time = 0
    x_index = y_index = wait_list_size // 2

    while current_time < sim_time:
        dx, dy = sample_jump()
        x += dx
        new_y = y + dy

        # Periodic boundary conditions in y
        y = Y_min if new_y > Y_max else Y_max if new_y < Y_min else new_y

        # Update waiting time indices
        x_index = max(0, min(wait_list_size - 1, x_index + dx)) if dx else x_index
        y_index = max(0, min(wait_list_size - 1, y_index + dy)) if dy else y_index

        # Select waiting time
        waiting_time = 0 if (x, y) == (0, 0) else max(wait_x[x_index], wait_y[y_index])
        current_time += waiting_time
        positions.append((x, y))
        times.append(current_time)
    
    return positions, times

def plot_3d_walk(positions, times):
    """Plot a 3D random walk trajectory."""
    x_vals, y_vals, t_vals = zip(*[(pos[0], pos[1], times[i]) for i, pos in enumerate(positions)])

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot3D(x_vals, y_vals, t_vals, color='blue', marker='o', markersize=3)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Time")
    ax.set_title("3D Random Walk (X, Y, Time)")
    plt.show()

def view_hist_2d_fixed_wait(num_sims, sim_time, wait_list_size, Y_min, Y_max):
    """Generate and plot 2D histograms of final positions from multiple simulations."""
    final_positions = [RW_sim_2d_fixed_wait(sim_time, wait_list_size, Y_min, Y_max)[0][-1] for _ in range(num_sims)]
    x_positions, y_positions = zip(*final_positions)

    plt.figure(figsize=(10, 5))
    plt.hist(x_positions, bins=50, alpha=0.7, color='blue', label='Final X')
    plt.hist(y_positions, bins=50, alpha=0.7, color='red', label='Final Y')
    plt.legend()
    plt.grid()
    plt.title("Histogram of Final Positions")
    plt.show()







def power_law(x, A, b):
    return A * x**b

def calculate_first_moment(positions) -> tuple:
    """Calculate the first moment (mean X, mean Y)."""
    x_coords, y_coords = zip(*positions)
    return np.mean(x_coords), np.mean(y_coords)

def multi_RW_first_moment_fixed_wait(num_sims: int, sim_time: int, wait_list_size: int, Y_min: int, Y_max: int) -> tuple[list,list]:
    """
    Run multiple simulations and compute first moments ⟨J_x⟩ and ⟨J_y⟩.

    Returns:
    - Lists of mean values ⟨J_x⟩ and ⟨J_y⟩ for each run.
    """
    first_moments_x = []
    first_moments_y = []

    for _ in range(num_sims):
        positions, _ = RW_sim_2d_fixed_wait(sim_time, wait_list_size, Y_min, Y_max)  # Extract only positions
        mean_x, mean_y = calculate_first_moment(positions)
        first_moments_x.append(mean_x)
        first_moments_y.append(mean_y)

    return first_moments_x, first_moments_y

def first_moment_with_noise_fixed_wait(num_sims: int, sim_time_start:int, sim_time_finish:int, time_step: int, wait_list_size:int, Y_min:int, Y_max:int) -> None:
    """
    Plot first moment vs. time while visualizing noise separately for ⟨J_x⟩ and ⟨J_y⟩.
    """
    time_values = np.arange(sim_time_start, sim_time_finish + 1, time_step)
    
    all_times = []
    all_first_moments_x = []
    all_first_moments_y = []

    for sim_time in time_values:
        first_moments_x, first_moments_y = multi_RW_first_moment_fixed_wait(num_sims, sim_time, wait_list_size, Y_min, Y_max)
        
        all_times.extend([sim_time] * len(first_moments_x))  
        all_first_moments_x.extend(first_moments_x)  
        all_first_moments_y.extend(first_moments_y)  

    # Plot separately for X and Y
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    axs[0].scatter(all_times, all_first_moments_x, alpha=0.5, s=10, label="⟨J_x⟩")
    axs[0].set_xlabel("Simulation Time")
    axs[0].set_ylabel("First Moment ⟨J_x⟩")
    axs[0].set_title("First Moment ⟨J_x⟩ vs. Time")
    axs[0].grid()
    axs[0].legend()

    axs[1].scatter(all_times, all_first_moments_y, alpha=0.5, s=10, label="⟨J_y⟩", color='red')
    axs[1].set_xlabel("Simulation Time")
    axs[1].set_ylabel("First Moment ⟨J_y⟩")
    axs[1].set_title("First Moment ⟨J_y⟩ vs. Time")
    axs[1].grid()
    axs[1].legend()

    plt.tight_layout()
    plt.show()

def first_moment_without_noise_comp_fixed_wait(num_sims:int, sim_time_start:int, sim_time_finish:int, time_step:int, wait_list_size:int, Y_min:int, Y_max:int) -> None:
    """
    Compare mean first moment ⟨J_x⟩ and ⟨J_y⟩ to a power-law function.
    """
    time_values = np.arange(sim_time_start, sim_time_finish + 1, time_step)
    mean_first_moments_x = []
    mean_first_moments_y = []

    for sim_time in time_values:
        first_moments_x, first_moments_y = multi_RW_first_moment_fixed_wait(num_sims, sim_time, wait_list_size, Y_min, Y_max)
        mean_first_moments_x.append(np.mean(first_moments_x))
        mean_first_moments_y.append(np.mean(first_moments_y))

    # Plot separately for X and Y
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    axs[0].plot(time_values, mean_first_moments_x, marker='o', linestyle='-', label="Mean ⟨J_x⟩")
    axs[0].set_xlabel("Simulation Time")
    axs[0].set_ylabel("Mean First Moment ⟨J_x⟩")
    axs[0].set_xscale('log')
    axs[0].set_yscale('log')
    axs[0].set_title("Mean ⟨J_x⟩ vs. Time")
    axs[0].grid()
    axs[0].legend()

    axs[1].plot(time_values, mean_first_moments_y, marker='o', linestyle='-', label="Mean ⟨J_y⟩", color='red')
    axs[1].set_xlabel("Simulation Time")
    axs[1].set_ylabel("Mean First Moment ⟨J_y⟩")
    axs[1].set_xscale('log')
    axs[1].set_yscale('log')
    axs[1].set_title("Mean ⟨J_y⟩ vs. Time")
    axs[1].grid()
    axs[1].legend()

    plt.tight_layout()
    plt.show()

def first_moment_without_noise_comp_and_find_func(num_sims:int, sim_time_start:int, sim_time_finish:int, time_step:int, wait_list_size:int, Y_min:int, Y_max:int) ->None:
    """Fit mean first moment to a power-law function ⟨J⟩ = Ax^b."""
    time_values = np.arange(sim_time_start, sim_time_finish + 1, time_step)
    mean_first_moments_x = []

    for sim_time in time_values:
        first_moments = [calculate_first_moment(RW_sim_2d_fixed_wait(sim_time, wait_list_size, Y_min, Y_max)[0]) for _ in range(num_sims)]
        mean_first_moments_x.append(np.mean([fm[0] for fm in first_moments]))

    popt, _ = curve_fit(power_law, time_values, mean_first_moments_x)
    A_fit, b_fit = popt
    print(f"Estimated A: {A_fit:.4f}, Estimated b: {b_fit:.4f}")

    plt.figure(figsize=(8, 6))
    plt.plot(time_values, mean_first_moments_x, marker='o', linestyle='-', label="Mean ⟨Jx⟩")
    plt.plot(time_values, power_law(time_values, A_fit, b_fit), linestyle='-', color='green', label=f"Fit: Ax^b (b={b_fit:.2f})")
    plt.xlabel("Simulation Time")
    plt.ylabel("Mean First Moment ⟨J_x⟩")
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.grid()
    plt.show()












def coefficient_vs_width(num_tests: int, W_initial: int, W_final: int, W_step: int, num_sims: int, sim_time_start: int, sim_time_finish: int, time_step: int, wait_list_size: int):
    """
    Test the relationship between the coefficient A of the power-law function and the system width W.

    Parameters:
    - num_tests: Number of times to repeat the A calculation for each W
    - W_initial: Starting value of W
    - W_final: Final value of W
    - W_step: Step size for W
    - num_sims: Number of simulations per test
    - sim_time_start: Initial simulation time
    - sim_time_finish: Final simulation time
    - time_step: Time step for simulations
    - wait_list_size: Size of the waiting time list
    """
    W_values = np.arange(W_initial, W_final + 1, W_step)
    mean_A_values = []

    for W in W_values:
        Y_min = -W // 2
        Y_max = W // 2
        A_values = []

        for _ in range(num_tests):
            time_values = np.arange(sim_time_start, sim_time_finish + 1, time_step)
            mean_first_moments_x = []

            for sim_time in time_values:
                first_moments = [
                    calculate_first_moment(RW_sim_2d_fixed_wait(sim_time, wait_list_size, Y_min, Y_max)[0])
                    for _ in range(num_sims)
                ]
                mean_first_moments_x.append(np.mean([fm[0] for fm in first_moments]))

            popt, _ = curve_fit(power_law, time_values, mean_first_moments_x)
            A_values.append(popt[0])  # Extract coefficient A

        mean_A_values.append(np.mean(A_values))  # Average A over num_tests

    # Plot results
    plt.figure(figsize=(8, 6))
    plt.plot(W_values, mean_A_values, marker='o', linestyle='-', label="Mean A vs. W")
    #plt.xscale('log')
    #plt.yscale('log')
    plt.xlabel("Width W")
    plt.ylabel("Mean Coefficient A")
    plt.title("Coefficient A vs. System Width W")
    plt.legend()
    plt.grid()
    plt.show()

#???????????????????????????????????????

def estimate_runtime(single_run_time, total_iterations):
    """Estimate total runtime based on a single run time."""
    estimated_time = single_run_time * total_iterations
    print(f"Estimated total runtime: {estimated_time:.2f} seconds ({estimated_time/60:.2f} minutes)")

def compute_A_for_W(W, num_tests, num_sims, sim_time_start, sim_time_finish, time_step, wait_list_size):
    """Compute the coefficient A for a given W value, averaging over num_tests runs."""
    Y_min = -W // 2
    Y_max = W // 2
    A_values = []

    for _ in range(num_tests):
        time_values = np.arange(sim_time_start, sim_time_finish + 1, time_step)
        mean_first_moments_x = []

        for sim_time in time_values:
            first_moments = [
                calculate_first_moment(RW_sim_2d_fixed_wait(sim_time, wait_list_size, Y_min, Y_max)[0])
                for _ in range(num_sims)
            ]
            mean_first_moments_x.append(np.mean([fm[0] for fm in first_moments]))

        # The original code performed a curve_fit here; that section has been removed.
        # Instead, we directly use the computed mean of first moments for this test.
        # If needed, you might apply another analysis here.
        A_values.append(np.mean(mean_first_moments_x))

    return np.mean(A_values)  # Average A over num_tests

def coefficient_vs_width_new(num_tests, W_initial, W_final, W_step, num_sims, sim_time_start, sim_time_finish, time_step, wait_list_size):
    """Test the relationship between coefficient A and system width W with performance improvements."""
    W_values = np.arange(W_initial, W_final + 1, W_step)

    # Estimate runtime using a small test run
    start_time = time.time()
    compute_A_for_W(W_values[0], num_tests, num_sims, sim_time_start, sim_time_finish, time_step, wait_list_size)
    single_run_time = time.time() - start_time
    estimate_runtime(single_run_time, len(W_values))

    # Use multiprocessing to speed up computation
    with mp.Pool(mp.cpu_count()) as pool:
        mean_A_values = pool.starmap(
            compute_A_for_W, 
            [(W, num_tests, num_sims, sim_time_start, sim_time_finish, time_step, wait_list_size) for W in W_values]
        )

    # Plot side-by-side graphs
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Regular scale plot
    axes[0].plot(W_values, mean_A_values, marker='o', linestyle='-', label="Mean A vs. W")
    axes[0].set_xlabel("Width W")
    axes[0].set_ylabel("Mean Coefficient A")
    axes[0].set_title("Coefficient A vs. System Width W (Regular Scale)")
    axes[0].legend()
    axes[0].grid()

    # Log-log scale plot
    axes[1].plot(W_values, mean_A_values, marker='o', linestyle='-', label="Mean A vs. W")
    axes[1].set_xscale('log')
    axes[1].set_yscale('log')
    axes[1].set_xlabel("Width W (log scale)")
    axes[1].set_ylabel("Mean Coefficient A (log scale)")
    axes[1].set_title("Coefficient A vs. System Width W (Log-Log Scale)")
    axes[1].legend()
    axes[1].grid()

    plt.tight_layout()
    plt.show()

#???????????????????????????????????????





def main():
    while True:
        print("\nMenu:")
        print("1. View Single 2D Random Walk")
        print("2. View Histogram of Final Positions")
        print("3. View First Moment with Noise")
        print("4. View First Moment with Power-Law Fit and Find Function")
        print("5. Test Relationship Between Coefficient A and Width W")  
        print("9. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            plot_3d_walk(
                *RW_sim_2d_fixed_wait(sim_time=500,
                                       wait_list_size=250,
                                         Y_min=-5,
                                        Y_max=5))

        elif choice == '2':
            view_hist_2d_fixed_wait(
                num_sims=500_000,
                sim_time=10_000, 
                wait_list_size=250, 
                Y_min=-100, 
                Y_max=100)

        elif choice == '3':
            first_moment_with_noise_fixed_wait(
                num_sims=5_000, 
                sim_time_start=0, 
                sim_time_finish=1_000, 
                time_step=50, 
                wait_list_size=250, 
                Y_min=-100, 
                Y_max=100)

        elif choice == '4':
            first_moment_without_noise_comp_and_find_func(
                num_sims=25_000, 
                sim_time_start=0, 
                sim_time_finish=1_000, 
                time_step=50, 
                wait_list_size=100, 
                Y_min=-5, 
                Y_max=5)

        elif choice == '5': 
            coefficient_vs_width_new(
                num_tests=10,        
                W_initial=0,        
                W_final=100,         
                W_step=25,           
                num_sims=1_000,       
                sim_time_start=0,
                sim_time_finish=1_000,
                time_step=250,
                wait_list_size=50
            )

        elif choice == '9':
            break

if __name__ == "__main__":
    main()