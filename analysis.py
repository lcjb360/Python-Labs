import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

iv_graph = True
steepest_line = True
derivative = True
dvt_over_time = False
lvt_over_time = False

if (iv_graph or steepest_line or derivative) and (dvt_over_time or lvt_over_time):
    print("Please only select compatible graph types")
    exit()

#parse xml file
data_file = 'Data/Ba133_uniradiated_linear.xml'

#parse data
#input: xml file
#output: array of datasets, each dataset containing two arrays of currents (means ([0][0]) and stds ([0][1])) and voltages (means ([1][0]) and stds ([1][1]))
def xml_to_datasets(data_file):
    tree = ET.parse(data_file)
    root = tree.getroot()
    datasets = []
    for dataset in root:
        currents = []
        current_std = []
        voltages = []
        voltage_std = []
        for entry in dataset:
            if entry.tag == 'Current':
                currents.append(float(entry[0].text))
                current_std.append(float(entry[1].text))
            elif entry.tag == 'Voltage':
                voltages.append(float(entry[0].text))
                voltage_std.append(float(entry[1].text))
        item = [[currents, current_std], [voltages, voltage_std]]
        datasets.append(item)
    return datasets

#plot data
def plot_iv(datasets):
    i = 0
    for dataset in datasets:
        currents = dataset[0][0]
        current_std = dataset[0][1]
        voltages = dataset[1][0]
        voltage_std = dataset[1][1]
        if i % 10 == 0:
            plt.errorbar(voltages,currents,xerr = voltage_std, yerr = current_std, label = "uniradiated", color = (i/len(voltages), 0, 1 - i/len(voltages)))
        else:
            plt.errorbar(voltages,currents,xerr = voltage_std, yerr = current_std, color = (i/len(voltages), 0, 1 - i/len(voltages)))
        i+=1

#linear fit at steepest point to find threshold voltage
def plot_steepest_line(datasets):
    for dataset in datasets:
        currents = dataset[0][0]
        current_std = dataset[0][1]
        voltages = dataset[1][0]
        voltage_std = dataset[1][1]
        max_derivative = 0
        max_derivative_index = 0
        for i in range(len(currents) - 1):
            gradient = (currents[i + 1] - currents[i]) / (voltages[i + 1] - voltages[i])
            if gradient > max_derivative and currents[i] > 0:
                max_derivative = gradient
                max_derivative_index = i
                gradient_err = gradient * np.sqrt((current_std[i] / currents[i])**2 + (voltage_std[i + 1] / voltages[i + 1])**2 + (voltage_std[i] / voltages[i])**2)
        f = lambda x : max_derivative * (x - voltages[max_derivative_index]) + currents[max_derivative_index]
        plt.errorbar(voltages, list(map(f,(voltages))),fmt="--", color = 'red')

        #error calculations
        x_intercept = (-currents[max_derivative_index] / max_derivative) + voltages[max_derivative_index]
        error = np.sqrt((currents[max_derivative_index] / max_derivative) * np.sqrt((current_std[max_derivative_index] / currents[max_derivative_index])**2 + (gradient_err / max_derivative)**2)**2 + voltage_std[max_derivative_index]**2)
        print("Threshold voltage: ", x_intercept, "+/-", error)

def calculate_derivative(x, y):
    derivative = np.array([])
    for i in range(1, len(y) - 1):
        gradient = (y[i + 1] - y[i - 1]) / (x[i + 1] - x[i - 1])
        derivative = np.append(derivative, gradient)
    return list(derivative)

def calculate_smoothed_derivative(x, y):
    derivative = np.array([])
    r = 3
    for i in range(r, len(y) - r - 1):
        #TODO: Implement smoothing algorithm
        pass

#calculate and plot derivative
def plot_derivative(datasets):
    for dataset in datasets:
        currents = dataset[0][0]
        voltages = dataset[1][0]
        derivative = calculate_derivative(voltages, currents)
        derivative2 = calculate_derivative(voltages[1:-1], derivative)
        max_current = max(currents)
        scaled_derivative2 = np.array(derivative2) * (max_current / max(derivative2))
        offset = int(-(len(derivative2) - len(voltages)) / 2)
        voltages = voltages[offset:-offset]
        plt.errorbar(voltages,scaled_derivative2,fmt="--", color = 'green')
        index_max_derivative2 = derivative2.index(max(derivative2))
        max_derivative2_voltage = voltages[index_max_derivative2]
        error = max((voltages[index_max_derivative2 + 1]) - max_derivative2_voltage, max_derivative2_voltage - voltages[index_max_derivative2 - 1])
        print("Second Derivative Maximum: ", max_derivative2_voltage, "+/-", error)

#calculate and plot derivative calculation of threshold voltages over time
def plot_derivative_thresholds_time(datasets):
    max_derivative2_voltages = []
    errors = []
    times = range(0, len(datasets))
    for dataset in datasets:
        currents = dataset[0][0]
        current_std = dataset[0][1]
        voltages = dataset[1][0]
        voltage_std = dataset[1][1]
        derivative = calculate_derivative(voltages, currents)
        derivative2 = calculate_derivative(voltages[1:-1], derivative)
        offset = int(-(len(derivative2) - len(voltages)) / 2)
        voltages = voltages[offset:-offset]
        index_max_derivative2 = derivative2.index(max(derivative2))
        max_derivative2_voltages.append(voltages[index_max_derivative2])
        errors.append(max((voltages[index_max_derivative2 + 1]) - voltages[index_max_derivative2], voltages[index_max_derivative2] - voltages[index_max_derivative2 - 1]))
    plt.errorbar(times, max_derivative2_voltages, xerr = voltage_std, yerrs = errors, color = 'green')


datasets = xml_to_datasets(data_file)
# make graph things
if iv_graph:
    plot_iv(datasets)
    title = "Id vs Vg for a MOSFET"
    plt.xlim(1.35, 2.85)
    plt.ylim(0, 0.00015)
    plt.ylabel('Id')
    plt.xlabel('Vg')
if steepest_line:
    plot_steepest_line(datasets)
if derivative:
    plot_derivative(datasets)
if dvt_over_time:
    plot_derivative_thresholds_time(datasets)
    title = "Threshold Voltage vs Time"
    plt.ylabel('Vt')
    plt.xlabel('Time hrs')    

if iv_graph:
    file_name = "Graphs/" + data_file[5:-4] + "_iv" + ".png"
if dvt_over_time:
    file_name = "Graphs/" + data_file[5:-4] + "_VtT" + ".png"
plt.legend()
plt.title(title)
plt.savefig(fname = file_name)
plt.show()