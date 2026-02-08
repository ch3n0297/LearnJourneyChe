# Tailscale CLI No Output — Debug Workflow(subscriber for health.Change Issue)

---

## <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" style="vertical-align:text-bottom;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 4h13M8 9h13M8 14h13M8 19h13M3 4h.01M3 9h.01M3 14h.01M3 19h.01"/></svg> 1. Issue Inspection Workflow

### 1.1 Check whether `tailscaled` is running

`ps aux | grep tailscaled`

### 1.2 Check service status

`sudo systemctl status tailscaled`

### 1.3 Inspect logs

`sudo journalctl -u tailscaled --no-pager -n 50`

---

## <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" style="vertical-align:text-bottom;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L15 12m0 0L9.75 7M15 12H3"/></svg> 2. Problem Identified (Based on Incident)

The logs repeatedly showed:

`subscriber for health.Change is slow`

Meaning:

- A subscriber to `health.Change` events stalled.
    
- `tailscaled` blocked waiting for it.
    
- All CLI commands hung with no output.
    
- `> log.txt` captured nothing because stdout was never flushed.
    

This is an **internal event-loop stall**, not a networking problem.

---

## <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" style="vertical-align:text-bottom;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> 3. Fix Procedures

### 3.1 Restart `tailscaled`

`sudo systemctl restart tailscaled`

### 3.2 Remove stale Unix socket

`sudo rm /run/tailscale/tailscaled.sock sudo systemctl restart tailscaled`

### 3.3 Full stop → cleanup → start

`sudo systemctl stop tailscaled sudo tailscaled --cleanup sudo systemctl start tailscaled`

### 3.4 Reboot if still stuck

`sudo reboot`

---

## <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" style="vertical-align:text-bottom;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 18.5A6.5 6.5 0 1118.5 12 6.507 6.507 0 0112 18.5z"/></svg> 4. Verification Steps

### 4.1 Validate CLI output

`tailscale status`

### 4.2 Test connectivity

`tailscale ping 100.100.100.100`

### 4.3 Confirm logs are clean

`sudo journalctl -u tailscaled -n 50`

If the “slow subscriber” log is gone, the issue is resolved.