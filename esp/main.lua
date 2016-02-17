K0 = 0xdecafbeddeadbeefcaffeebabe421337
K1 = 0xbe421337decafbeddeadbeefcaffeeba
K2 = 0xcaffeebabe421337decafbeddeadbeef
KH0 = 0x01234567890123467890123456789012
KH1 = 0x98765432109876543210987654321098


function cnt_padding(cnt)
   result = ""
   h = cnt
   for i=0,15,1 do
      a = h % 256
      h = h / 256
      result = string.char(a) .. result
   end
   return result
end

cnt_rand_insecure = 0
function rand_insecure()
   result = crypto.encrypt(AES-ECB, KH0, cnt_padding(cnt_rand_insecure))
   cnt_rand_insecure = cnt_rand_insecure + 1
   return result
end

-- TODO: save cnt_rand_secure
cnt_rand_secure = 0
function rand_secure()
   result = crypto.encrypt(AES-ECB, KH1, cnt_padding(cnt_rand_secure))
   cnt_rand_secure = cnt_rand_secure + 1
   return result
end


state = 0
tc = nil
nc = nil
oc = nil
pc = nil
mode = nil

function recv(c, pl)
   if state == 0 and pl:len() == 2 and pl:byte(0) == 0x0 and pl:byte(1) == 0x42 then
      msgid = string.char(0x01)
      tc = rand_insecure()
      msg = msgid .. tc
      c:send(msg)
      state = state + 1
   elseif state == 1 and pl:len() == 50 and pl:byte(0) == 0x2 then
      mode = pl:byte(1)
      nc = pl:byte(2,17)
      h_rec = pl:byte(18,49)
      h_own = crypto.hmac("sha256", tc .. mode .. nc, K0)
      if h_rec == h_own then
	 msgid = string.char(0x03)
	 oc = rand_secure()
	 if mode == 0x01 then
	    pc = rand_secure() -- TODO: trim to 4 digits
	 else
	    pc = string.char(0xff) .. string.char(0xff)
	 end
	 msg = msgid .. oc
	 c:send(msg)
	 state = state + 1
      end
   elseif state == 2 and pl:len() == 49 and pl:byte(0) == 0x4 then
      ac = pl:byte(1,16)
      h_rec = pl:byte(17,48)
      h_own = crypto.hmac("sha256", nc .. pc .. oc .. ac, K1)
      if h_rec == h_own then
	 msgid = string.char(0x05)
	 h = crypto.hmac("sha256", ac, K2)
	 msg = msgid .. h
	 c:send(msg)
	 state = 0
      end
   else
      c:close()
   end
end



sv = net.createServer(net.TCP, 30)

sv:listen(42001, function(c)
	     c:on("receive", recv)
end)

