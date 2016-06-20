-- when this file is reloaded, close running server
if sv ~= nil then
   sv:close()
end

print("started")

function first_initialization()
   debug_output = true

   gpio.mode(1, gpio.OUTPUT)
   gpio.write(1, gpio.LOW)

   load_keys()
   
   cnt_rand_insecure = 9999
   load_cnt_rand_secure()

   state = 0
   tc = nil
   nc = nil
   oc = nil
   pc = nil
   mode = nil

end

function load_keys()
   file.open("keyfile", "r")
   keys = {K0=nil, K1=nil, K2=nil, KH0=nil, KH1=nil}
   local line = file.readline()
   for k,v in ipairs(keys) do
      if line == nil then
	 error("keyfile too short")
      end
      while line:find("#") ~= nil do
	 line = file.readline()
	 if line == nil then
	    error("keyfile too short")
	 end
      end
      keys[k] = parse_key(line)
      if debug_output then
	 -- note that if we would use printd here, explode_string would be executed also in non-debug mode
	 print("init: " .. k .. "=" explode_string(keys[k]))
      end
      line = file.readline()
   end
   file.close()
end

function parse_key(keystr)
   local l = keystr:len()
   local key = ""
   for i=1,l,2 do
      key = key .. tonumber(keystr:sub(i,i+1),16)
   end
   return key
end

function printd(s, v=nil)
   if debug_output then
      if v == nil then
	 print(s)
      else
	 print(s .. explode_string(v))
      end
   end
end

function tmr_handler()
   gpio.write(1, gpio.LOW) -- switch off relay
   tmr.unregister(0) -- reset timer
   disp_off() -- switch off display
end

function tmr_start()
   tmr.register(0, 3000, tmr.ALARM_SINGLE, tmr_handler)
   tmr.start(0)
end

function open_door()
   gpio.write(1, gpio.HIGH)
   disp_write_open()
   tmr_start()
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

function rand_insecure()
   result = crypto.encrypt("AES-ECB", keys["KH0"], cnt_padding(cnt_rand_insecure))
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


function rand_secure()
   result = crypto.encrypt("AES-ECB", keys["KH1"], cnt_padding(cnt_rand_secure))
   cnt_rand_secure = cnt_rand_secure + 1
   if cnt_rand_secure % 128 == 0 then
      save_cnt_rand_secure()
   end
   return result
end




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
   printd ("disconnected")
   state = 0
   tc = nil
   nc = nil
   oc = nil
   pc = nil
   mode = nil
end


function process_pl_0(pl)
   printd "0:"
   local msgid = string.char(0x01)
   tc = rand_insecure()
   printd ("tc ", tc)
   local msg = msgid .. tc
   state = state + 1
   return msg
end


function process_pl_2(pl)
   printd "2:"
   local mode = pl:sub(2,2)
   nc = pl:sub(3,18)
   local h_rec = pl:sub(19,50)
   local h_own = crypto.hmac("sha256", tc .. mode .. nc, keys["K0"])
   printd ("mode ", mode)
   printd ("nc ", nc)
   printd ("h_rec ", h_rec)
   printd ("h_own ", h_own)
   if h_rec == h_own then
      local msgid = string.char(0x03)
      oc = rand_secure()
      printd ("oc ", oc)
      if mode == string.char(0x01) then
	 local pc_src = rand_secure()
	 local pc_num = (pc_src:byte(1) * 256 + pc_src:byte(2)) % 10000
	 disp_write_num_reverse(pc_num)
	 pc = ""
	 for i=1,4,1 do
	    pc = pc .. string.char(pc_num % 10)
	    pc_num = math.floor(pc_num / 10)
	 end     
      else
	 -- CURRENTLY DISABLED: mode w/o presence challenge
	 pc = string.char(0xff) .. string.char(0xff) .. string.char(0xff) .. string.char(0xff)
	 return nil
      end
      printd ("pc ", pc)
      local msg = msgid .. oc
      state = state + 1
      return msg
   end
   return nil
end

function process_pl_4(pl)
   printd "4:"
   ac = pl:sub(2,17)
   local h_rec = pl:sub(18,49)
   local h_own = crypto.hmac("sha256", nc .. pc .. oc .. ac, keys["K1"])
   printd ("ac ", ac)
   printd ("h_rec ", h_rec)
   printd ("h_own ", h_own)
   if h_rec == h_own then
      printd ("OK")
      open_door()
      --tmr.delay(4000000)
      --gpio.write(1, gpio.LOW)
      local msgid = string.char(0x05)
      local h = crypto.hmac("sha256", ac, keys["K2"])
      local msg = msgid .. h
      state = 0
      return msg
   end
   return nil
end

function recv(c, pl)
   local msg = nil
   local ip, port = c:getpeer()
   printd ("data from " .. ip)
   local msg = nil
   if debug_output then
      print ("state: " .. state .. " received " .. pl:len() .. " bytes: " .. explode_string(pl) .. " string: " .. pl)
   end
   if pl:len() == 1 and pl:byte(1) == 0x23 then
      printd "PING/PONG"
      msg = string.char(0x42)
   elseif state == 0 and pl:len() == 2 and pl:byte(1) == 0x0 and pl:byte(2) == 0x42 then
      msg = process_pl_0(pl)
   elseif state == 1 and pl:len() == 50 and pl:byte(1) == 0x2 then
      msg = process_pl_2(pl)
   elseif state == 2 and pl:len() == 49 and pl:byte(1) == 0x4 then
      msg = process_pl_4(pl)
   end
   if msg ~= nil then
      -- printd ("send " .. msg:len() .. " bytes: " .. explode_string(msg) .. " string: " .. msg)
      c:send(msg)
   else
      c:close()
      disp_write_fail()
      tmr_start()
      state = 0
   end
end

first_initialization()

sv = net.createServer(net.TCP, 30)

sv:listen(42001, function(c)
	     c:on("receive", recv)
	     c:on("disconnection", disc)
end)

