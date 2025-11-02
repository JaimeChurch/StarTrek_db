inputs = [
    [3,5],
    [5,1],
    [10,2]
]

sleep = inputs[0][0]
study = inputs[0][1]

outputs = [75,82,93]

input_node_0 = None
input_node_1 = None

hidden_node_0 = None
hidden_node_1 = None
hidden_node_2 = None

output_node_0 = None

#key: weight_layer_from_to
weight_0_0_0 = 0
weight_0_0_1 = 0
weight_0_0_2 = 0

weight_0_1_0 = 0
weight_0_1_1 = 0
weight_0_1_2 = 0

weight_1_0_0 = 0
weight_1_1_0 = 0
weight_1_2_0 = 0

def activation_function(x):
    e=2.718281828459045
    return 1 / (1 + e**(-x))

input_node_0 = sleep
input_node_1 = study

hidden_node_0 = activation_function(sleep * weight_0_0_0 + study * weight_0_1_0)
hidden_node_1 = activation_function(sleep * weight_0_0_1 + study * weight_0_1_1)
hidden_node_2 = activation_function(sleep * weight_0_0_2 + study * weight_0_1_2)

output_node_0 = activation_function(
    hidden_node_0 * weight_1_0_0 
    +  hidden_node_1 * weight_1_1_0 
    +  hidden_node_2 * weight_1_2_0
)

print("Inputs: (" + str(sleep) + ", " + str(study) + ")  Output: " + str(output_node_0))
