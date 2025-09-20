## To set up a manual IP address for the Ethernet port

I connect with my Mac using an Ethernet cable.

* Save old setup
    ```bash
    nmcli con show "Wired connection 1" > "network_settings.beforeStaticIPforETH.txt"
    more network_settings.beforeStaticIPforETH.txt 
    ```

* Set up 192.168.2.2 as static address for the Ethernet port. 

    Requires that, on the mac side, we set a manual address of 192.168.2.1 on the USB Ethernet port.

    ```bash
    sudo nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addr 192.168.2.2/24
    sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.2.1 ipv4.dns 192.168.2.1
    sudo nmcli device reapply eth0
    ```

* Show the current network setting
    ```bash
    nmcli connection show
    ```
