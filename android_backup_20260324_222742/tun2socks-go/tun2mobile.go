package tun2mobile

import (
	"strconv"

	"github.com/xjasonlyu/tun2socks/v2/engine"
)

// StartTun runs tun2socks on the TUN fd from VpnService.Builder.establish().
// proxyURL example: socks5://127.0.0.1:1080
// bindIface: loopback ifname (usually "lo"). Binds outbound SOCKS dials to that iface so
// traffic to 127.0.0.1 is not mis-routed into the VPN tunnel. Empty string skips binding.
func StartTun(fd int, mtu int, proxyURL string, bindIface string) error {
	k := &engine.Key{
		MTU:      mtu,
		Device:   "fd://" + strconv.Itoa(fd),
		Proxy:    proxyURL,
		LogLevel: "error",
	}
	if bindIface != "" {
		k.Interface = bindIface
	}
	engine.Insert(k)
	return engine.Start()
}

func StopTun() error {
	return engine.Stop()
}
