
import os
import torch
from torch import nn
from torch.profiler import profile, ProfilerActivity

if not torch.cuda.is_available():
    raise RuntimeError("CUDA is unavailable.")

os.makedirs("samples", exist_ok=True)
device = torch.device("cuda:0")

model = nn.Sequential(
    nn.Linear(512, 1024),
    nn.ReLU(),
    nn.Linear(1024, 256),
).to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

# Warm up the GPU
for _ in range(5):
    x = torch.randn(64, 512, device=device)
    target = torch.randn(64, 256, device=device)
    optimizer.zero_grad(set_to_none=True)
    loss = loss_fn(model(x), target)
    loss.backward()
    optimizer.step()

torch.cuda.synchronize()

# Record CPU and GPU activity
with profile(
    activities=[
        ProfilerActivity.CPU,
        ProfilerActivity.CUDA,
    ],
    record_shapes=True,
    profile_memory=True,
) as prof:
    for step in range(10):
        x = torch.randn(64, 512, device=device)
        target = torch.randn(64, 256, device=device)

        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(model(x), target)
        loss.backward()
        optimizer.step()

        prof.step()

torch.cuda.synchronize()
prof.export_chrome_trace("samples/single_gpu_trace.json")

print("Trace saved: samples/single_gpu_trace.json")
print("GPU:", torch.cuda.get_device_name(0))
print("Final loss:", loss.item())
