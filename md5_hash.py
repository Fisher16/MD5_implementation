from bitarray import bitarray
import struct
import math

import sys

def add_32(a,b):
    return (a+b)% (2**32)

#python bitwise operations
#https://www.journaldev.com/26737/python-bitwise-operators
#&AND; |OR; ^XOR;~Ones’ Compliment; <<LShift; >>RShift

#Let X <<< s denote the 32-bit value obtained by circularly shifting (rotating) X left by s bit positions.
#shift left n OR shift right (32-n)
def rotate_left(x,n):
    return (x<<n)| (x>>(32-n))

def F(x,y,z):
    return (x& y)| (~x& z)
def G(x,y,z):
    return (x& z)| (y& ~z)
def H(x,y,z):
    return x^y^z
def I(x,y,z):
    return y^ (x| ~z)

SHIFT_AMOUNTS={
    'round1': [7, 12, 17, 22],
    'round2': [5,  9, 14, 20],
    'round3': [4, 11, 16, 23],
    'round4': [6, 10, 15, 21]
}
SINE_TABLE=[math.floor((2**32)* abs(math.sin(i + 1))) for i in range(64)]

round_index={
    range(0 ,16):'round1',
    range(16,32):'round2',
    range(32,48):'round3',
    range(48,64):'round4'
}
def get_round_index(i):
    for k,v in round_index.items():
        if i in k:
            return v
k1=lambda i: i
k2=lambda i: ((5*i)+1)% 16
k3=lambda i: ((3*i)+5)% 16
k4=lambda i: (7*i)% 16

round_funcs={
    'round1':(k1,F),
    'round2':(k2,G),
    'round3':(k3,H),
    'round4':(k4,I)
}

def step_1_padding(m_str):
    m_array = bitarray(endian="big")
    m_array.frombytes(m_str.encode("utf-8"))

    m_array.append(1)
    while len(m_array)% 512 != 448:
        m_array.append(0)
    
    return bitarray(m_array, endian="little")

def step_2_concat_len(m_str,m_array):
    length = (8*len(m_str))% (2**64)
    
    #https://stackoverflow.com/questions/42652436/how-to-convert-ctypes-to-bytes
    #https://docs.python.org/3.7/library/struct.html
    #Q: unsigned long long; < little; > big
    appendix = bitarray(endian="little")
    appendix.frombytes(struct.pack("<Q", length))

    result = m_array.copy()
    result.extend(appendix)
    return result

def step_3_init_state():
    A = 0x67452301
    B = 0xEFCDAB89
    C = 0x98BADCFE
    D = 0x10325476
    #here simple dict with keys 'A','B','C','D' and following values
    return {'A':A,'B':B,'C':C,'D':D}

def step_4_calc(state,m_padded):
    #N is number of words
    N = len(m_padded)// 32

    #Chunks of 512 bits (32*16)
    for ch_i in range(N// 16):
        #ch_i*512: offset chunk; i offset word; 32 word length; 16 block length
        X = [m_padded[((ch_i*512)+(i*32)):((ch_i*512)+(i*32)+32)] for i in range(16)]

        #to int
        X = [int.from_bytes(word.tobytes(), byteorder="little") for word in X]

        A = state['A']
        B = state['B']
        C = state['C']
        D = state['D']

        #4 rounds x 16 operations
        for i in range(4*16):
            round_index=get_round_index(i)
            ki,FGHI=round_funcs.get(round_index)
            
            #shift array
            s=SHIFT_AMOUNTS[round_index]
            #value dependent on i
            s_val=s[i % 4]
            
            #ki returns mod 16
            k=ki(i)
            #tmp value for one of F,G,H or I func
            tmp=FGHI(B,C,D)

            #tmp := tmp + A + SINE_TABLE[i] + Message[k]  // M[k] must be a 32-bits block
            #consecutive addition
            tmp = add_32(tmp, X[k])
            tmp = add_32(tmp, SINE_TABLE[i])
            tmp = add_32(tmp, A)
            
            #add B and rotate s_val
            tmp = rotate_left(tmp, s_val)
            tmp = add_32(tmp, B)

            # rotate the registers one step
            A = D
            D = C
            C = B
            B = tmp

        #update state
        state['A'] = add_32(state['A'], A)
        state['B'] = add_32(state['B'], B)
        state['C'] = add_32(state['C'], C)
        state['D'] = add_32(state['D'], D)
        
    return state

def format_state_val(val):
    F=struct.unpack("<I",struct.pack(">I",val))[0]
    return format(F, '08x')
def step_5_print(out_state):
    hex_strings=[format_state_val(out_state[k]) for k in ['A','B','C','D']]
    return "".join(hex_strings)

def md5_hash(m_str):
    m_array=step_1_padding(m_str)
    m_padded=step_2_concat_len(m_str,m_array)
    internal_state=step_3_init_state()
    out_state=step_4_calc(internal_state,m_padded)
    return step_5_print(out_state)

def main():
    data = sys.stdin.buffer.read()
    print(md5_hash(
        data.decode(encoding='utf-8',errors='ignore')))

if __name__ == '__main__':
    main()