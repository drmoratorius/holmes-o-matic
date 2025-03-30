#import machine
#import time
#from machine import Pin, ADC
import ujson

def UTIL_getJSON(path):
    with open(path, 'r') as file:
        json_data = file.read()
    return ujson.loads(json_data)

def UTIL_convertBinaryValue(binary_value):
    if isinstance(binary_value, bytes):
        bool_list = []
        for byte in binary_value:
            binary_str = bin(byte)[2:]
            while len(binary_str) < 8:
                binary_str = '0' + binary_str
            bool_list.extend([bit == '0' for bit in binary_str])
        return bool_list
    return []
    
def UTIL_compare_bool_arrays(arr1, arr2):
    if len(arr1) != len(arr2):
        print("Arrays must be of the same length.")
        return []
    changed_indices = []
    for i in range(len(arr1)):
        if arr1[i] != arr2[i]:
            changed_indices.append(i)
    return changed_indices

def UTIL_bools_to_byte(b1, b2, b3, b4, b5, b6, b7, b8):
    byte_value = (b1 << 7) | (b2 << 6) | (b3 << 5) | (b4 << 4) | (b5 << 3) | (b6 << 2) | (b7 << 1) | b8
    return bytearray([byte_value])

