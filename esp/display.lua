numbertable = { string.char(0x3f,0x0c),
		string.char(0x06,0x00),
		string.char(0xdb,0x00),
		string.char(0x8f,0x00),
		string.char(0xe6,0x00),
		string.char(0x69,0x20),
		string.char(0xfd,0x00),
		string.char(0x07,0x00),
		string.char(0xff,0x00),
		string.char(0xef,0x00)
} 

id  = 0
sda = 6
scl = 5
addr = 0x70

i2c.setup(id, sda, scl, i2c.SLOW)

function disp_write_raw(str)
   i2c.start(id)
   i2c.address(id, addr, i2c.TRANSMITTER)
   i2c.write(id,str)
   i2c.stop(id)
end

-- setup / turn on oscillator
disp_write_raw(string.char(0x21))

-- set blink off and enable display
disp_write_raw(string.char(0x81))

-- set display brightness to max
disp_write_raw(string.char(0xef))

function disp_write_num(n)
    local msg = ""
    local a = n
    for i=1,4,1 do
        local b = (a % 10) + 1
        msg = numbertable[b] .. msg
        a = math.floor(a/10)
    end
    disp_write_raw(string.char(0x00) .. msg)
end

function disp_write_num_reverse(n)
    local msg = ""
    local a = n
    for i=1,4,1 do
        local b = (a % 10) + 1
        msg = msg .. numbertable[b] 
        a = math.floor(a/10)
    end
    disp_write_raw(string.char(0x00) .. msg)
end

function disp_off()
    disp_write_raw(string.char(0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00))
end

function disp_write_open()
    disp_write_raw(string.char(0x00,0x3f,0x00,0xf3,0x00,0xf9,0x00,0x36,0x21))
end

function disp_write_fail()
    disp_write_raw(string.char(0x00,0x71,0x00,0xf7,0x00,0x00,0x12,0x38,0x00))
end

-- write something
--disp_write_raw(string.char(0x00) .. numbertable[1] .. numbertable[2] .. numbertable[3] .. numbertable[4])

--disp_write_num(1337)
	       
