



-- Your Wifi connection data
local SSID = "trier.freifunk.net"
local SSID_PASSWORD = ""

local function connect (conn, data)
   local query_data

   conn:on ("receive",
      function (cn, req_data)
         query_data = get_http_req (req_data)
         print (query_data["METHOD"] .. " " .. " " .. query_data["User-Agent"])
         cn:send ("Hello World from ESP8266 and NodeMCU!!")
         -- Close the connection for the request
         cn:close ( )
      end)
end

function wait_for_wifi_conn ( )
   tmr.alarm (1, 1000, 1, function ( )
      if wifi.sta.getip ( ) == nil then
         print ("Waiting for Wifi connection")
      else
         tmr.stop (1)
         print ("ESP8266 mode is: " .. wifi.getmode ( ))
         print ("The module MAC address is: " .. wifi.ap.getmac ( ))
         print ("Config done, IP is " .. wifi.sta.getip ( ))
      end
   end)
end

-- Configure the ESP as a station (client)
wifi.setmode (wifi.STATION)
wifi.sta.config (SSID, SSID_PASSWORD)
wifi.sta.autoconnect (1)

-- Hang out until we get a wifi connection before the httpd server is started.
wait_for_wifi_conn ( )

dofile("display.lua")
