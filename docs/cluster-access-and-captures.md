# Cluster access & fixture provenance

How the recorded fixtures under `fixtures/` were obtained, so anyone can
reproduce them or judge their authenticity. No secrets are stored in this repo —
only the resulting command output.

## 1. Cluster

| | |
|---|---|
| Cluster | CoreWeave `cw0bec` (workshops) |
| kube context | `workshops_US-EAST-06A` |
| API server | `https://cw0bec-0cc74ae9.k8s.us-east-06a.coreweave.com` |
| Identity | `pnalubandhu+cw0bec@coreweave.com` (CoreWeave org) |
| Nodes | 8× GPU nodes, all `Ready` (k8s v1.36.2) |
| GPUs | **8× NVIDIA RTX PRO 6000 Blackwell Server Edition per node** (driver 580.173.02, CUDA 13.0) |

> Note: despite the project's original "H100" framing, the live `cw0bec` nodes
> are **Blackwell RTX PRO 6000** (PCIe, no NVLink fabric). The docs were
> corrected to match. See `DESIGN.md` §3.1.

## 2. How to log in

A kubeconfig for the workshop cluster was provided as a downloaded file
(carries a short-lived `cwtoken`, so no password/SSH key is needed):

```bash
export KUBECONFIG=~/Downloads/CWKubeconfig_workshops_US-EAST-06A

# verify
kubectl config get-contexts                 # -> workshops_US-EAST-06A (current)
kubectl get nodes                           # -> 8 GPU nodes Ready
```

All access was **read-only** (`kubectl get`, `kubectl exec ... nvidia-smi`). No
resources were created, modified, or deleted on the cluster.

## 3. Where the GPU data came from

`nvidia-smi` runs on the host, not inside most pods. The GPU-operator's
**device-plugin DaemonSet** pod has `/usr/bin/nvidia-smi` on its PATH, so it is
the cleanest read-only capture point:

```bash
NS=cw-nvidia-gpu-operator
POD=nvidia-device-plugin-daemonset-d45gq      # on node gd10ffc
```

### Commands run (each piped to a fixture file)

```bash
kubectl -n $NS exec $POD -- nvidia-smi                       > nvidia-smi.txt
kubectl -n $NS exec $POD -- nvidia-smi -q                    > nvidia-smi_-q.txt
kubectl -n $NS exec $POD -- nvidia-smi nvlink -s             > nvidia-smi_nvlink_-s.txt
kubectl -n $NS exec $POD -- nvidia-smi \
  --query-gpu=index,name,pci.bus_id,temperature.gpu,\
ecc.errors.uncorrected.aggregate.total,\
ecc.errors.corrected.aggregate.total --format=csv            > query_gpu.csv
```

Cleanup applied to the raw output:
- `kubectl exec` prepends a `Defaulted container "..."` line (stderr) — stripped
  from every fixture so the file is exactly what `nvidia-smi` emits on a host.
- `nvidia-smi nvlink -s` produced **no output** — these Blackwell cards have no
  NVLink. The fixture records that explicitly so module G6 returns `NA`.

### Fabric (IB / NIC) data

`ibstat` / `rdma` CLIs are not in the pod, but `/sys/class/infiniband/` is. A
shell loop dumps each device's state/link/rate/firmware into a parseable file:

```bash
kubectl -n $NS exec $POD -- sh -c 'for d in /sys/class/infiniband/*/; do
  ... echo state/phys_state/rate/fw_ver/hca_type/counters/hw_counters ...
done'                                                          > ib_sysfs.txt

kubectl -n $NS exec $POD -- sh -c 'for n in /sys/class/net/*/; do
  ... echo rx_errors/tx_errors/rx_dropped/tx_dropped/rx_crc_errors ...
done'                                                          > net_stats.txt
```

Real result: **9× ConnectX-7 (MT41692), 100 Gb/s EDR, all ACTIVE / LinkUp,
fw 32.43.4100.**

> Caveat (honest): the `ports/1/counters/` subdir is **not exposed** inside the
> container (`No such file or directory`), so the error/congestion counters in
> the healthy `ib_sysfs.txt` are a **`0` baseline** (realistic for a healthy
> node), not read values. Device/state/rate/firmware ARE real. Reading live
> counters needs a privileged host-level pod, which was deliberately not created.

### Host (Group A) data

```bash
kubectl -n $NS exec $POD -- sh -c 'for n in /sys/class/net/*/; do ... mtu/operstate/carrier ... done' > net_links.txt
kubectl -n $NS exec $POD -- uname -r                       > kernel.txt
kubectl -n $NS exec $POD -- sh -c 'grep -i huge /proc/meminfo' > meminfo.txt
kubectl -n $NS exec $POD -- cat /proc/net/if_inet6         > ipv6.txt
kubectl -n $NS exec $POD -- sh -c 'grep -c mlx5 /proc/interrupts' > interrupts.txt
kubectl -n $NS exec $POD -- nvidia-smi topo -m | sed 's/\x1b\[[0-9;]*m//g' > nvidia_topo.txt
```

Real results: kernel `6.17.13-…-coreweave-amd64`, driver `580.173.02`, eth0 MTU
9000 up, THP active, 160 mlx5 IRQ lines, and a real `nvidia-smi topo -m` matrix
showing **all 9 NICs on NUMA 0** (GPU0–3 `NODE`-local, GPU4–7 `SYS`).

> Caveats (honest):
> - The pod's **network namespace only shows `eth0`** (no `ip`/`lspci`, no host
>   view of eth1/ibp*). So A2/A3 see one NIC and A4 returns `NA`.
> - **`ip_rule.txt` is synthesized** — the pod has no iproute2 / host netns.
>   It models realistic per-NIC policy routing so A1 can be exercised; a live
>   host run reads real `ip rule show`.

## 4. Fixture sets

| Path | Source | Contents |
|---|---|---|
| `fixtures/cw0bec_blackwell_healthy/` | **Live capture** from `cw0bec` (above) | GPU: `nvidia-smi.txt`, `nvidia-smi_-q.txt`, `nvidia-smi_nvlink_-s.txt`, `query_gpu.csv`, `dmesg_xid.txt` (empty). Fabric: `ib_sysfs.txt` (real device/link + 0-counter baseline), `net_stats.txt`. Host: `net_links.txt`, `kernel.txt`, `meminfo.txt`, `ipv6.txt`, `interrupts.txt`, `nvidia_topo.txt` (all real), `ip_rule.txt` (synthesized) |
| `fixtures/synth_gpu_fault/` | **Synthesized** from the healthy set | `query_gpu.csv` edited so GPU 3 has 12 uncorrectable ECC + 91 °C; `dmesg_xid.txt` with Xid 79/48 on GPU 3's real PCI bus (`0000:46:00`) so G3/G5 correlate on `gpu:3` |
| `fixtures/synth_fabric_fault/` | **Synthesized** from the healthy IB dump | `ib_sysfs.txt`: mlx5_4 link errors (symbol/LER/LLI), mlx5_5 port DOWN, mlx5_6 congestion; `net_stats.txt`: eth1 tx errors — exercises B14/B13/B11/B3 |
| `fixtures/nccl_healthy/nccl.log` | **Provided** real log (`~/Downloads/real_healthy.nccl.log`) | SUNK 2×8 H100 all-reduce, RDMA over `NET/IB…GDRDMA`, ~435 GB/s |
| `fixtures/nccl_tcp_fallback/nccl.log` | **Provided** real log (`~/Downloads/real_misconfig.nccl.log`) | Same job, bad `NCCL_IB_HCA=ibp99` → silent fallback to `NET/Socket` (TCP), ~3.4 GB/s |

### Provenance honesty

- The **`nvidia-smi` fixtures** are my own live, read-only captures from the
  `cw0bec` Blackwell nodes.
- The **`synth_gpu_fault`** set is hand-edited (the live nodes are healthy); it
  is aligned to a real GPU's PCI bus id so the correlation is faithful.
- The **NCCL logs** were **not** captured by me — they are pre-existing real
  logs from a SUNK 2×8 **H100** training run, provided as files and copied in
  verbatim.

## 5. Reproducing

```bash
export KUBECONFIG=~/Downloads/CWKubeconfig_workshops_US-EAST-06A
# re-run any command from §3; strip the leading 'Defaulted container' line.
```

Fixtures let the whole tool run and be tested off-hardware:

```bash
audit -u gpu_fault  --fixture fixtures/cw0bec_blackwell_healthy   # all pass
audit -u gpu_fault  --fixture fixtures/synth_gpu_fault            # GPU-3 verdict
audit -m N1         --fixture fixtures/nccl_tcp_fallback          # NCCL TCP-fallback verdict
audit -u preflight  --fixture fixtures/cw0bec_blackwell_healthy   # GPU + fabric, all pass
audit -u preflight  --fixture fixtures/synth_fabric_fault         # rdma_link_down verdict
```
