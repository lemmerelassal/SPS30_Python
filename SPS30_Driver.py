# SPS30 Driver
# Written by Lemmer El Assal (December 2018)


import serial
#from struct import *

class SPS30:
    debuglevel = 0
    ser = serial.Serial('COM3')
    adr = b'\x00'
    cmd = b'\x00'
    l = b'\x00'
    data = bytes([0])
    chk = b'\x00'
    state = b'\x00'
    txbuffer = b'\x00'
    rxbuffer = b'\x00'

    def __init__(self):
        self.adr = bytes([0])
        self.ser.baudrate = 115200
        self.ser.timeout = 2
        
    def SetDebugLevel(self, val):
        self.debuglevel = val
        
    def StartMeasurement(self):
        self.ExecuteCommand(b'\x00', b'\x01\x03')
    
    def StopMeasurement(self):
        self.ExecuteCommand(b'\x01', bytearray())
    
    def ReadMeasuredValues(self):
        self.ExecuteCommand(b'\x03', bytearray())
        # temp = []
        # for i in range(int(self.rxbuffer[4]/4)):
            # temp.append(unpack('f',self.rxbuffer[(5+(i*4)):(4+((i+1)*4))]))
        # return temp
        return self.rxbuffer[5:4+self.rxbuffer[4]]
        
    def ReadAutoCleaningInterval(self):
        self.ExecuteCommand(b'\x80', b'\x00')
        return self.rxbuffer[5:4+self.rxbuffer[4]]
    
    def WriteAutoCleaningInterval(self, value):
        temp = bytes([0, ((value >> 24) & 255), ((value >> 16) & 255), ((value >> 8) & 255), ((value >> 0) & 255)])
        self.ExecuteCommand(b'\x80', temp)
    
    def Reset(self):
        self.ExecuteCommand(b'\xD3', bytearray())
    
    def StartFanCleaning(self):
        self.ExecuteCommand(b'\x56', bytearray())
    
    # Get Device Information
    # <type>: 1 - Product name
    #         2 - Article code
    #         3 - Serial number
    
    def GetDeviceInformation(self, type):
        self.ExecuteCommand(b'\xD0', bytes([type]))
        return self.rxbuffer[5:4+self.rxbuffer[4]]
    
    def ExecuteCommand(self, command, data):
        self.cmd = command
        self.data = data
        self.AssembleFrame()
        self.WriteTxBuffer()
        self.ReadRxBuffer()
        self.state = self.rxbuffer[3]
        if self.debuglevel > 0:
            self.PrintState()
        return
    
    def WriteTxBuffer(self):
        self.ser.write(self.txbuffer)
        return
        
    def ReadRxBuffer(self):
        self.rxbuffer = self.ser.read(262) # 7 bytes for overhead, maximum of 255 data bytes
        
        if self.rxbuffer[4] > 0:
            print('Before unstuffing:')
            print('Rx buffer size: ', len(self.rxbuffer))
            print('Rx data size: ', self.rxbuffer[4])
            
            print('After unstuffing:')
            self.ByteUnstuffing()
            print('Rx buffer size: ', len(self.rxbuffer))
            print('Rx data size: ', self.rxbuffer[4])
            
            for i in range(self.rxbuffer[4]):
                print('[', i, ']: ', hex(self.rxbuffer[5+i]))
        return
    
    def AssembleFrame(self):
        self.l = bytes([len(self.data) & 255])
        self.txbuffer = self.adr + self.cmd + self.l + self.data
        self.CalcCrc()
        self.txbuffer += self.chk
        self.ByteStuffing()
        return
		
        
    def ByteStuffing(self):
        res = bytes()
        for i in range(len(self.txbuffer)):
            if self.txbuffer[i] == int('0x7E',16):
                res += b'\x7D\x5E'
            elif self.txbuffer[i] == int('0x7D',16):
                res += b'\x7D\x5D'
            elif self.txbuffer[i] == int('0x11',16):
                res += b'\x7D\x31'
            elif self.txbuffer[i] == int('0x13',16):
                res += b'\x7D\x33'
            else:
                res += bytes([self.txbuffer[i]]);
        self.txbuffer = b'\x7E' + res + b'\x7E'
        return
    
    def ByteUnstuffing(self):
        res = bytes() #self.rxbuffer[1:-1]
        i = 0
        while i < len(self.rxbuffer):
            if self.rxbuffer[i] == int('0x7D',16):
                i += 1
                if self.rxbuffer[i] == int('0x5E',16):
                    res += b'\x7E'
                elif self.rxbuffer[i] == int('0x5D',16):
                    res += b'\x7D'
                elif self.rxbuffer[i] == int('0x31',16):
                    res += b'\x11'
                elif self.rxbuffer[i] == int('0x33',16):
                    res += b'\x13'
                else:
                    print('Unstuffing error')
            else:
                res += bytes([self.rxbuffer[i]])
            i += 1
        self.rxbuffer = res
        return
       
    def CalcCrc(self):
        self.chk = 0
        for i in range(len(self.txbuffer)):
            self.chk += self.txbuffer[i]
        self.chk &= 255
        self.chk ^= 255
        self.chk = bytes([self.chk])
        return
        
    def PrintState(self):
        errormsg = {
            0: "No error",
            1: "Wrong data length for this command (too much or little data)",
            2: "Unknown command",
            3: "No access right for command",
            4: "Illegal command parameter or parameter out of allowed range",
            40: "Internal function argument out of range",
            67: "Command not allowed in current state"
        }
        print(errormsg.get(self.state))
        return
        
    # def CalcCrc(self):
        # self.chk = 255
        # for i in range(len(self.txbuffer)):
            # self.chk ^= self.txbuffer[i];
            # for j in range(8):
                # if self.chk & int('0x80',16):
                    # self.chk = (self.chk << 1) ^ 49;
                # else:
                    # self.chk = (self.chk << 1)
        # self.chk = bytes([self.chk & 255])
        # print('CRC: ')
        # print(self.chk)
        # return

s = SPS30()
s.SetDebugLevel(1)
s.StartMeasurement()
s.StopMeasurement()
print(s.ReadMeasuredValues())
# s.Reset()
# s.StartFanCleaning()
s.WriteAutoCleaningInterval(100)

s.GetDeviceInformation(1)
s.GetDeviceInformation(2)
s.GetDeviceInformation(3)

s.ReadAutoCleaningInterval()
