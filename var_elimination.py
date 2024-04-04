"""
We assume factors in factorList in the format: 
[[X],[[1,0.5][0,0.5]]] where the first entry in the probability list represent T/F values

Code partially adapted from https://github.com/EvianWang/VariableEliminationAlgorithm/blob/master/vea_example.py
"""
from tkinter import W
import numpy as np
from copy import deepcopy



def restrict(factor, variable, value): 
    """
        This function restrict a factor based on a value assigned to the variable
    """
    # index of variable 
    idx = next((i for i, var in enumerate(factor[0]) if var == variable), None)

    # filter rows based on value 
    filtered_rows = [row for row in factor[1] if row[idx] == value]
    factor[1] = filtered_rows

    # Now we can remove the variable that we have successfully restricted
    factor[0].pop(idx)
    factor[1] = [row[:idx] + row[idx+1:] for row in factor[1]]

    return factor

def multiply(factor1,factor2):
    product_factor = create_empty_table(factor1[0], factor2[0]) 

    coe = 0.5

    # Fill the variable entries
    # In the order of (1, 1) (1, 0)....
    while len(product_factor[1]) * coe >= 1:
        i = 0
        switch = False
        counter = 0
        for i in range(len(product_factor[1])):
            if counter >= len(product_factor[1]) * coe:
                switch = not switch
                counter = 0
            if not switch:
                product_factor[1][i].append(1)
            else:
                product_factor[1][i].append(0)
            counter += 1
        coe *= 0.5

    #calculate the probabilities
    for i, row in enumerate(product_factor[1]):
        ind1 = find_ind(product_factor[0], row, factor1)
        ind2 = find_ind(product_factor[0], row, factor2)
        val1 = factor1[1][ind1][-1]
        val2 = factor2[1][ind2][-1]
        product = val1 * val2
        row.append(product)

    return product_factor

def sumout(factor,variable):
    ret = []
    varlist = list(factor[0])
    varlist.remove(variable)
    new_var_list = varlist
    new_var_list.sort()
    ret.append(new_var_list)
    num_of_entry = 2 ** len(new_var_list)
    ret.append([[] for _ in range(num_of_entry)])

    # Fill the variable entries
    # In the order of (1, 1) (1, 0)....
    coe = 0.5
    while len(ret[1]) * coe >= 1:
        i = 0
        switch = False
        counter = 0
        for i in range(len(ret[1])):
            if counter >= len(ret[1]) * coe:
                switch = not switch
                counter = 0
            if not switch:
                ret[1][i].append(1)
            else:
                ret[1][i].append(0)
            counter += 1
        coe *= 0.5
    #summing out the variable

    for i in range(num_of_entry):
        prob = calculate_sum(ret[0],ret[1][i],factor)
        ret[1][i].append(prob)

    return ret 

def normalize(factor):
    length = len(factor[1])
    result_factor = list()
    result_factor.append(factor[0])
    result_factor.append(factor[1])

    s = sum([factor[1][i][-1] for i in range(length)])
    #normalize the factor
    for i, row in enumerate(result_factor[1]):
        row[-1] = factor[1][i][-1] / s

    return result_factor

def inference(factorList,queryVariables,orderedListOfHiddenVariables,evidenceList):
    print(factorList)
    n = len(factorList)

    len_evi = len(evidenceList)
    len_q = len(queryVariables)

    # restrict the evidence variables
    for i in range(len_evi):
        for j in range(n):
            if evidenceList[i][0] in factorList[j][0]:
                restrict(factorList[j], evidenceList[i][0], evidenceList[i][1])

    # remove the evidence variable 
    for i in range(len_evi): 
        orderedListOfHiddenVariables.remove(evidenceList[i][0])

    for i in range(len_q):
        orderedListOfHiddenVariables.remove(queryVariables[i][0])

    # sum out factors 
    for current_hid_var in reversed(orderedListOfHiddenVariables):
        result = find_factors(factorList, current_hid_var) 
         
        # Multiply the factors that contain the same hidden variables
        while len(result) > 1:
            fac1, fac2 = result.pop(), result.pop()
            prod_fac = multiply(fac1, fac2)
            result.append(prod_fac)

        # Sum out the final factor
        temp = sumout(result[0], current_hid_var)
        factorList.append(temp)

    # multipy all of the other factors 
    while len(factorList) > 1:
        fac3 = factorList.pop()
        fac4 = factorList.pop()
        new_fac = multiply(fac3,fac4)
        factorList.append(new_fac)
        
    # normaliaze the final factor
    final_distribution = normalize(factorList[0])

    # find the final prob with queryVariables
    if final_distribution[0][0] == queryVariables[0][0]:
        for distribution in final_distribution[1]:
            if distribution[0] == queryVariables[0][1]:
                final_result = distribution[-1]
                break
    print("final_result: ",final_result)
    return final_distribution, final_result

def create_empty_table(var_names1, var_names2):
    union_names = list(set().union(var_names1, var_names2))
    num_entries = 2**len(union_names)
    ret = list()
    ret.append(union_names)
    ret.append([[] for _ in range(num_entries)]) 
    
    return ret

def find_ind(varlist, goal, source):
    ind_arr = []
    val_arr = []
    
    for var in varlist:
        for j, src_var in enumerate(source[0]):
            if var == src_var:
                ind_arr.append(j)
                val_arr.append(goal[varlist.index(var)])
    
    for i, row in enumerate(source[1]):
        if all(row[j] == val_arr[ind_arr.index(j)] for j in ind_arr):
            return i

# helper functions
def calculate_sum(varlist, goal, source):
    """
        Here we are calculating the sum of values from source that match the status in goal 
    """
    sum_result = 0
    ind_arr = []
    val_arr = []
    
    for var in varlist:
        for j, src_var in enumerate(source[0]):
            if var == src_var:
                ind_arr.append(j)
                val_arr.append(goal[varlist.index(var)])
    
    for _, row in enumerate(source[1]):
        if all(row[j] == val_arr[ind_arr.index(j)] for j in ind_arr):
            sum_result += row[-1]
    
    return sum_result

def find_factors(factorlist,variable):
    """
        Find factor that has the variable present
    """
    ret = []

    for factor in factorlist[:]:
        if variable in factor[0]:
            factorlist.remove(factor)
            ret.append(factor)

    return ret

def main():
    # Lets define some probabilities
    OC = [['OC'], [[1, 0.8], [0, 0.2]]]

    # Trav (Traveling)
    TRAV = [['Trav'], [[1, 0.05], [0, 0.95]]]

    # Fraud
    FRAUD = [['Fraud', 'Trav'], [[1, 1, 0.01], [0, 1, 0.99], [1, 0, 0.004], [0, 0, 0.996]]]

    # FP (Foreign Purchase)
    FP = [['FP', 'Fraud', 'Trav'], 
        [[1, 1, 1, 0.9], [0, 1, 1, 0.1],
        [1, 0, 1, 0.9], [0, 0, 1, 0.1],
        [1, 1, 0, 0.1], [0, 1, 0, 0.9],
        [1, 0, 0, 0.01], [0, 0, 0, 0.99]]]

    # IP (Internet Purchase)
    IP = [['IP', 'OC', 'Fraud'], 
        [[1, 1, 1, 0.15], [0, 1, 1, 0.85],
        [1, 1, 0, 0.1], [0, 1, 0, 0.9],
        [1, 0, 1, 0.051], [0, 0, 1, 0.949],
        [1, 0, 0, 0.001], [0, 0, 0, 0.999]]]

    # CRP (Computer-Related Purchase)
    CRP = [['CRP', 'OC'], 
        [[1, 1, 0.1], [0, 1, 0.9],
            [1, 0, 0.01], [0, 0, 0.99]]]

    # Q1 P(Fraud)
    # Answer: 0.0043
    inference([deepcopy(OC), deepcopy(TRAV), deepcopy(FRAUD), deepcopy(FP), deepcopy(IP), deepcopy(CRP)], [['Fraud', 1]], ['Trav', 'FP', 'Fraud', 'IP', 'OC', 'CRP'], [])

    # Q2 P(Fraud | FP and not IP and CRP) 
    # Answer: 0.0143
    inference([deepcopy(OC), deepcopy(TRAV), deepcopy(FRAUD), deepcopy(FP), deepcopy(IP), deepcopy(CRP)], [['Fraud', 1]], ['Trav', 'FP', 'Fraud', 'IP', 'OC', 'CRP'], [['FP', 1], ['IP', 0], ['CRP', 1]])

    # Q3 P(Fraud | FP and not IP and CRP and Trav)
    # Answer: 0.00945
    inference([deepcopy(OC), deepcopy(TRAV), deepcopy(FRAUD), deepcopy(FP), deepcopy(IP), deepcopy(CRP)], [['Fraud', 1]], ['Trav', 'FP', 'Fraud', 'IP', 'OC', 'CRP'], [['FP', 1], ['IP', 0], ['CRP', 1], ['Trav', 1]])

    # Q4 difference between P(Fraud | IP) and P(Fraud | (IP and CRP))
    # Answer - Decreased probability by 0.0009 
    _, final_result1 = inference([deepcopy(OC), deepcopy(TRAV), deepcopy(FRAUD), deepcopy(FP), deepcopy(IP), deepcopy(CRP)], [['Fraud', 1]], ['Trav', 'FP', 'Fraud', 'IP', 'OC', 'CRP'], [['IP', 1]])
    _, final_result2 = inference([deepcopy(OC), deepcopy(TRAV), deepcopy(FRAUD), deepcopy(FP), deepcopy(IP), deepcopy(CRP)], [['Fraud', 1]], ['Trav', 'FP', 'Fraud', 'IP', 'OC', 'CRP'], [['IP', 1], ['CRP', 1], ['Trav', 0]])

    difference = final_result1 - final_result2
    print(difference)

if __name__ == "__main__":
    main() 