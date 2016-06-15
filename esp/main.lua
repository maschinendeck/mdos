if sv ~= nil then
   sv:close()
end

gpio.mode(1, gpio.OUTPUT)
gpio.write(1, gpio.LOW)




K0 = string.char(0xde,0xca,0xfb,0xed,0xde,0xad,0xbe,0xef,0xca,0xff,0xee,0xba,0xbe,0x42,0x13,0x37)
K1 = string.char(0xbe,0x42,0x13,0x37,0xde,0xca,0xfb,0xed,0xde,0xad,0xbe,0xef,0xca,0xff,0xee,0xba)
K2 = string.char(0xca,0xff,0xee,0xba,0xbe,0x42,0x13,0x37,0xde,0xca,0xfb,0xed,0xde,0xad,0xbe,0xef)
KH0 = string.char(0x01,0x23,0x45,0x67,0x89,0x01,0x23,0x46,0x78,0x90,0x12,0x34,0x56,0x78,0x90,0x12)
KH1 = string.char(0x98,0x76,0x54,0x32,0x10,0x98,0x76,0x54,0x32,0x10,0x98,0x76,0x54,0x32,0x10,0x98)

function tmr_relay_off()
   gpio.write(1, gpio.LOW)
   tmr.unregister(0)
   disp_off()
end

function cnt_padding(cnt)
   result = ""
   h = cnt
   for i=0,15,1 do
      a = h % 256
      h = math.floor(h / 256)
      result = string.char(a) .. result
   end
   return result
end

cnt_rand_insecure = 9999
function rand_insecure()
   result = crypto.encrypt("AES-ECB", KH0, cnt_padding(cnt_rand_insecure))
   cnt_rand_insecure = cnt_rand_insecure + 1
   return result
end


function save_cnt_rand_secure()
   file.open("cnt_rand_secure", "w")
   file.write(string.format("%x",cnt_rand_secure))
   file.close()
end
function load_cnt_rand_secure()
   if not file.exists("cnt_rand_secure") then
      file.open("cnt_rand_secure", "w")
      file.write("0")
      file.close()
   end
   file.open("cnt_rand_secure", "r")
   cnt_rand_secure_str = file.read(1024)
   file.close()
   cnt_rand_secure = tonumber(cnt_rand_secure_str,16) + 128
   save_cnt_rand_secure()
end
load_cnt_rand_secure()


function rand_secure()
   result = crypto.encrypt("AES-ECB", KH1, cnt_padding(cnt_rand_secure))
   cnt_rand_secure = cnt_rand_secure + 1
   if cnt_rand_secure % 128 == 0 then
      save_cnt_rand_secure()
   end
   return result
end


state = 0
tc = nil
nc = nil
oc = nil
pc = nil
mode = nil


--- Returns HEX representation of num
function num2hex(num)
   local hexstr = '0123456789abcdef'
   local s = ''
   while num > 0 do
      local mod = num % 16
      s = string.sub(hexstr, mod+1, mod+1) .. s
      num = math.floor(num / 16)
   end
   if s == '' then s = '0' end
   return s
end

function explode_string(s)
   local l = s:len()
   local result = ""
   for i=1,l,1 do
      result = result .. '0x' .. num2hex(s:byte(i)) .. ','
   end
   return result
end


function disc(c)
   print ("disconnected")
   state = 0
   tc = nil
   nc = nil
   oc = nil
   pc = nil
   mode = nil
end

function recv(c, pl)
   local ip, port = c:getpeer()
   print ("data from " .. ip)
   msg = nil
   print ("received " .. pl:len() .. " bytes: " .. explode_string(pl) .. " string: " .. pl)
   if pl:len() == 1 and pl:byte(1) == 0x23 then
      print "PING/PONG"
      msg = string.char(0x42)
      -- c:send(string.char(0x42))
   elseif state == 0 and pl:len() == 2 and pl:byte(1) == 0x0 and pl:byte(2) == 0x42 then
      print "0:"
      msgid = string.char(0x01)
      tc = rand_insecure()
      print ("tc " .. explode_string(tc))
      msg = msgid .. tc
      -- c:send(msg)
      state = state + 1
   elseif state == 1 and pl:len() == 50 and pl:byte(1) == 0x2 then
      print "2:"
      mode = pl:sub(2,2)
      nc = pl:sub(3,18)
      h_rec = pl:sub(19,50)
      h_own = crypto.hmac("sha256", tc .. mode .. nc, K0)
      print ("mode " .. explode_string(mode))
      print ("nc " .. explode_string(nc))
      print ("h_rec " .. explode_string(h_rec))
      print ("h_own " .. explode_string(h_own))
      if h_rec == h_own then
	 msgid = string.char(0x03)
	 oc = rand_secure()
	 print ("oc " .. explode_string(oc))
	 if mode == string.char(0x01) then
	    local pc_src = rand_secure()
	    local pc_num = (pc_src:byte(1) * 256 + pc_src:byte(2)) % 10000
        disp_write_num_reverse(pc_num)
	    pc = ""
	    for i=1,4,1 do
	       pc = pc .. string.char(pc_num % 10)
	       pc_num = math.floor(pc_num / 10)
	       --pc = string.char(pc_src:byte(1) % 10) .. string.char(pc_src:byte(2) % 10) .. string.char(pc_src:byte(3) % 10) .. string.char(pc_src:byte(4) % 10)
	    end     
	 else
	    pc = string.char(0xff) .. string.char(0xff) .. string.char(0xff) .. string.char(0xff)
	 end
	 print ("pc " .. explode_string(pc))
	 msg = msgid .. oc
	 -- c:send(msg)
	 state = state + 1
      else
	 c:close()
   disp_write_fail()
      end
   elseif state == 2 and pl:len() == 49 and pl:byte(1) == 0x4 then
      print "4:"
      ac = pl:sub(2,17)
      h_rec = pl:sub(18,49)
      h_own = crypto.hmac("sha256", nc .. pc .. oc .. ac, K1)
      print ("ac " .. explode_string(ac))
      print ("h_rec " .. explode_string(h_rec))
      print ("h_own " .. explode_string(h_own))
      if h_rec == h_own then
	 print ("OK")
	 gpio.write(1, gpio.HIGH)
    disp_write_open()
	 tmr.register(0, 3000, tmr.ALARM_SINGLE, tmr_relay_off)
	 tmr.start(0)
	 --tmr.delay(4000000)
	 --gpio.write(1, gpio.LOW)
	 msgid = string.char(0x05)
	 h = crypto.hmac("sha256", ac, K2)
	 msg = msgid .. h
	 -- c:send(msg)
	 state = 0
      else
	 c:close()
   disp_write_fail()
      end
   else
      c:close()
      disp_write_fail()
   end
   if msg ~= nil then
      print ("send " .. msg:len() .. " bytes: " .. explode_string(msg) .. " string: " .. msg)
      c:send(msg)
   end
end


sv = net.createServer(net.TCP, 30)

sv:listen(42001, function(c)
	     c:on("receive", recv)
	     c:on("disconnection", disc)
end)

