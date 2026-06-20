import torch
import torch.nn as nn
import torch.nn.functional as F


class Meso4(nn.Module):
    """Meso-4 network for deepfake detection.

    A shallow CNN designed for deepfake classification that uses
    four convolutional blocks followed by dense layers.
    """

    def __init__(self, num_classes: int = 2) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(3, 8, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(8)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(8, 8, 5, padding=2)
        self.bn2 = nn.BatchNorm2d(8)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.conv3 = nn.Conv2d(8, 16, 5, padding=2)
        self.bn3 = nn.BatchNorm2d(16)
        self.pool3 = nn.MaxPool2d(2, 2)

        self.conv4 = nn.Conv2d(16, 16, 5, padding=2)
        self.bn4 = nn.BatchNorm2d(16)
        self.pool4 = nn.MaxPool2d(2, 2)

        self.dropout = nn.Dropout(0.5)
        self.fc1 = nn.Linear(16 * 14 * 14, 16)
        self.fc2 = nn.Linear(16, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class InceptionBlock(nn.Module):
    """Inception-style block used in MesoInception-4."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.branch1 = nn.Conv2d(in_channels, out_channels, 1)

        self.branch2 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
        )

        self.branch3 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1),
            nn.Conv2d(out_channels, out_channels, 5, padding=2),
        )

        self.branch_pool = nn.Sequential(
            nn.MaxPool2d(3, 1, padding=1),
            nn.Conv2d(in_channels, out_channels, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.cat([
            self.branch1(x),
            self.branch2(x),
            self.branch3(x),
            self.branch_pool(x),
        ], dim=1)


class MesoInception4(nn.Module):
    """MesoInception-4 — deepfake detector with Inception blocks.

    Uses Inception-style convolutions for richer feature extraction
    compared to Meso-4.
    """

    def __init__(self, num_classes: int = 2) -> None:
        super().__init__()
        self.inception1 = InceptionBlock(3, 2)
        self.bn1 = nn.BatchNorm2d(8)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.inception2 = InceptionBlock(8, 4)
        self.bn2 = nn.BatchNorm2d(16)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.conv3 = nn.Conv2d(16, 16, 5, padding=2)
        self.bn3 = nn.BatchNorm2d(16)
        self.pool3 = nn.MaxPool2d(2, 2)

        self.conv4 = nn.Conv2d(16, 16, 5, padding=2)
        self.bn4 = nn.BatchNorm2d(16)
        self.pool4 = nn.MaxPool2d(2, 2)

        self.dropout = nn.Dropout(0.5)
        self.fc1 = nn.Linear(16 * 14 * 14, 16)
        self.fc2 = nn.Linear(16, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool1(F.relu(self.bn1(self.inception1(x))))
        x = self.pool2(F.relu(self.bn2(self.inception2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        return self.fc2(x)
