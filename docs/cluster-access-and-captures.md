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

## 4. Fixture sets

| Path | Source | Contents |
|---|---|---|
| `fixtures/cw0bec_blackwell_healthy/` | **Live capture** from `cw0bec` (above) | `nvidia-smi.txt`, `nvidia-smi_-q.txt`, `nvidia-smi_nvlink_-s.txt`, `query_gpu.csv`, `dmesg_xid.txt` (empty — healthy) |
| `fixtures/synth_gpu_fault/` | **Synthesized** from the healthy set | `query_gpu.csv` edited so GPU 3 has 12 uncorrectable ECC + 91 °C; `dmesg_xid.txt` with Xid 79/48 on GPU 3's real PCI bus (`0000:46:00`) so G3/G5 correlate on `gpu:3` |
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
```
