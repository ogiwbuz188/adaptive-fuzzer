# Sandbox threat model

## Implemented boundary

On Linux, `BenchmarkRunner` requires Bubblewrap and refuses to start a target
without it. Each benchmark runs in a new Bubblewrap sandbox with unshared user,
mount, PID, IPC, UTS, cgroup, and network namespaces (`--unshare-all`). The
target and fuzzer share that sandbox so they can exchange local HTTP traffic.
They do not share the host network namespace.

The sandbox mounts `/usr`, the system library directories, selected TLS and
loader configuration, the project `src/` and benchmark tree as read-only, and
the configured data directory as writable. `/tmp` is a private tmpfs. The
process environment is cleared and rebuilt with only the runtime search paths
and a temporary home directory. Bubblewrap is configured to die with its
parent; the outer runner applies per-process resource limits and a wall-clock
timeout, then terminates the benchmark process group on timeout.

## Limits of the boundary

This is namespace-based process isolation, not a VM, container security
certification, or a claim that arbitrary hostile code is safe. It relies on the
host Linux kernel and Bubblewrap configuration. It does not install a dedicated
seccomp policy or use cgroups for aggregate CPU or memory accounting. CPU time,
address space, and file size are limited per process, so those limits are not
aggregate quotas for every descendant process. A benchmark may still exercise
kernel attack surface or cause host load before the wall-clock timeout.

Some host runtime files and system libraries are intentionally visible inside
the namespace. The sandbox is designed for the repository's synthetic
benchmarks, not arbitrary third-party code. Use a disposable machine for
untrusted extensions to the benchmark set, keep Bubblewrap and the kernel
updated, and review mount and resource settings before making broader safety
claims.

The sandbox integration tests verify required Bubblewrap invocation and local
runner behavior; they do not constitute a formal security evaluation or prove
the absence of escape paths.
