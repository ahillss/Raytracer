import struct,lzma,math

def next_greater_power_of_2(x):
    return 2**(x-1).bit_length()

print(next_greater_power_of_2(0))

def uintBitsToFloat(a):
    if isinstance(a,tuple):
        return [struct.unpack('f', struct.pack("I",x))[0] for x in a]
    else:
        return struct.unpack('f', struct.pack("I",a))[0]

def uintToVec4(v):
    return [x/255 for x in [v&255,(v>>8)&255,(v>>16)&255,(v>>24)&255]]
    # return [x     for x in [v&255,(v>>8)&255,(v>>16)&255,(v>>24)&255]]


def uintToBytes4(v):
    return [v&255,(v>>8)&255,(v>>16)&255,(v>>24)&255]

def loadFile(fn):
    with lzma.open(fn, "rb") as fh:
        b=fh.read()
        return struct.unpack('{}I'.format(len(b)//4),b)

# aaa=struct.unpack('I',struct.pack('4B',55,97,126,212))[0]
# bbb=[aaa&255,(aaa>>8)&255,(aaa>>16)&255,(aaa>>24)&255]
# print(aaa)
# print(bbb)

data=loadFile("../test.dat")
print("")
print("(0:3)@{}".format(uintBitsToFloat(data[0:3])))
print("(3:6)@{}".format(uintBitsToFloat(data[3:6])))

stk=[6]

prims=[]

while len(stk)>0:
    node=stk.pop()

    a=data[node]
    b=data[node+1]

    ntype=a&3

    if ntype==3:
        primsNum=a>>2
        primsStart=b
        # print("({}:{})@leaf {} {}".format(node,node+2,primsStart,primsNum))

        if primsNum==1:
            prims.append(primsStart)
        elif primsNum>1:
            prims.extend(data[primsStart:primsStart+primsNum])
    else:
        axis=ntype
        aboveChild=a>>2
        belowChild=node+2
        split=uintBitsToFloat(data[node+1])
        # print("({}:{})@branch{} {}".format(node,node+2,axis,split))
        stk.append(aboveChild)
        stk.append(belowChild)

prims=list(set(prims))
# print(prims)

for prim in prims:
    tri=data[prim:prim+4]
    # print(tri)

    mtrlLoc=tri[3]

    mtrlCol=data[mtrlLoc]
    texSlot=0
    print("")
    for texSlot in range(0,6):
        texLoc=data[mtrlLoc+1+texSlot*2]
        texUV=data[mtrlLoc+1+texSlot*2+1]
        # print(uintToVec4(mtrlCol))
        print("{} {}".format(texLoc,texUV))
    #verts=[data[x:x+5] for x in tri]
    # pos
    # print("")
    # print(tri)

    # for v in verts:
    #     # print(uintBitsToFloat(v[0:3]))
    #     # print([x*2-1 for x in uintToVec4(v[3])[0:3]])
    #     # print(uintToVec4(v[3]))
    #     # print(uintToVec4(v[4]))
    #     # print("")

    #     with open("ouput2.txt", "a") as myfile:
    #         myfile.write("{} {} {}\n".format(*uintToBytes4(v[4])[0:3]))


# for tri in tris:
#     for i in range(0,3):
#         v=data[tri[i]:tri[i]+5]
#         print(v)
# print(tris)

import functools
def edgeCompare(a,b):
    if a[0] < b[0]:
        return -1
    elif a[0] > b[0]:
        return 1
    else:
        return 0

# xxx=[("a",3),("",4),("c",5)]
# xxx.sort(key=functools.cmp_to_key(edgeCompare))
# print(xxx)

a={"a":1,"b":2}
print(len(a))
print(math.fmod(-4.6,1.0))
