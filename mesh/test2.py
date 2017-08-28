import struct,lzma,math

def next_greater_power_of_2(x):
    return 2**(x-1).bit_length()

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

data=loadFile("sibenik.dat")
print("")
# print("(0:3)@{}".format(uintBitsToFloat(data[0:3])))
# print("(3:6)@{}".format(uintBitsToFloat(data[3:6])))

print("(0,1)@{}".format(data[0:2]))
print("(2,3)@{}".format(data[2:4]))
print("(4,5)@{}".format(data[4:6]))
print("(6,7)@{}".format(uintBitsToFloat(data[6:8])))


cameraFrameSize=8
pointLightFrameSize=9


camerasStart=data[0]
pointLightsStart=data[2]

camera0FramesStart=data[camerasStart+0*2+0]
camera0FramesNum=  data[camerasStart+0*2+1]
camera0FramesEnd=data[camera0FramesStart+camera0FramesNum*cameraFrameSize]

pointLight0FramesStart=data[pointLightsStart+0*2+0]
pointLight0FramesNum=  data[pointLightsStart+0*2+1]
pointLight0FramesEnd=pointLight0FramesStart+pointLight0FramesNum*pointLightFrameSize

print("{} {} {}".format(camera0FramesStart,camera0FramesEnd,camera0FramesNum))
print("{} {} {}".format(pointLight0FramesStart,pointLight0FramesEnd,pointLight0FramesNum))

for i in range(0,pointLight0FramesNum):
    j=pointLight0FramesStart+i*pointLightFrameSize


    frame=uintBitsToFloat(data[j+0])
    col=uintToVec4(data[j+1])
    energy=uintBitsToFloat(data[j+2])
    dist=uintBitsToFloat(data[j+3])
    linAtten=uintBitsToFloat(data[j+4])
    quadAtten=uintBitsToFloat(data[j+5])
    pos=uintBitsToFloat(data[j+6:j+9])

    print("")
    print("frame {:0.7f}".format(frame))
    print("col {}".format(col))
    print("energy {}".format(energy))
    print("dist {}".format(dist))
    print("linAtten {}".format(linAtten))
    print("quadAtten {}".format(quadAtten))
    print("pos {}".format(pos))



    # aaaa[i]=vec4(pos,frame);
