import torch
import torch.nn as nn
import torch.nn.functional as F


class SeparableConv2d(nn.Module):
    """Depthwise separable convolution used in XceptionNet."""

    def __init__(
        self, in_channels: int, out_channels: int, kernel_size: int = 3,
        padding: int = 1, bias: bool = False,
    ) -> None:
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_channels, in_channels, kernel_size,
            padding=padding, groups=in_channels, bias=bias,
        )
        self.pointwise = nn.Conv2d(in_channels, out_channels, 1, bias=bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pointwise(self.depthwise(x))


class Block(nn.Module):
    """Xception entry/middle/exit block with separable convolutions and skip connections."""

    def __init__(
        self, in_channels: int, out_channels: int, reps: int = 3,
        start_with_relu: bool = True, grow_first: bool = True,
    ) -> None:
        super().__init__()
        self.skip_conv = nn.Conv2d(in_channels, out_channels, 1, stride=2, bias=False)
        self.skip_bn = nn.BatchNorm2d(out_channels)
        self.do_skip = True

        self.relu = nn.ReLU(inplace=True)
        rep = []

        channels = in_channels
        if grow_first:
            rep.append(self.relu)
            rep.append(SeparableConv2d(channels, out_channels, 3, padding=1))
            rep.append(nn.BatchNorm2d(out_channels))
            channels = out_channels

        for _ in range(reps - 1):
            rep.append(self.relu)
            rep.append(SeparableConv2d(channels, channels, 3, padding=1))
            rep.append(nn.BatchNorm2d(channels))

        if not grow_first:
            rep.append(self.relu)
            rep.append(SeparableConv2d(channels, out_channels, 3, padding=1))
            rep.append(nn.BatchNorm2d(out_channels))

        if not start_with_relu:
            rep = rep[1:]

        rep.append(nn.MaxPool2d(3, stride=2, padding=1))
        self.rep = nn.Sequential(*rep)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = self.skip_bn(self.skip_conv(x))
        out = self.rep(x)
        return out + identity


class XceptionFingerprint(nn.Module):
    """Modified XceptionNet for GAN fingerprint extraction.

    Adapted from Xception architecture to produce a compact
    fingerprint embedding that captures generator-specific artifacts.
    """

    def __init__(self, num_classes: int = 2, embedding_dim: int = 2048) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, stride=2, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(32)
        self.relu = nn.ReLU(inplace=True)

        self.conv2 = nn.Conv2d(32, 64, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(64)

        self.block1 = Block(64, 128, reps=2, start_with_relu=False, grow_first=True)
        self.block2 = Block(128, 256, reps=2, start_with_relu=True, grow_first=True)
        self.block3 = Block(256, 728, reps=2, start_with_relu=True, grow_first=True)

        self.middle = nn.Sequential(*[Block(728, 728, reps=3, start_with_relu=True, grow_first=True) for _ in range(8)])

        self.block4 = Block(728, 1024, reps=2, start_with_relu=True, grow_first=False)

        self.conv3 = SeparableConv2d(1024, 1536, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(1536)
        self.conv4 = SeparableConv2d(1536, embedding_dim, 3, padding=1)
        self.bn4 = nn.BatchNorm2d(embedding_dim)

        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.fingerprint_proj = nn.Linear(embedding_dim, 512)
        self.classifier = nn.Linear(512, num_classes)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))

        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.middle(x)
        x = self.block4(x)

        x = self.relu(self.bn3(self.conv3(x)))
        x = self.relu(self.bn4(self.conv4(x)))

        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        fingerprint = self.fingerprint_proj(x)
        logits = self.classifier(fingerprint)
        return logits, fingerprint

    def extract_fingerprint(self, x: torch.Tensor) -> torch.Tensor:
        _, fingerprint = self.forward(x)
        return fingerprint
