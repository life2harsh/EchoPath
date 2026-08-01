import pytest
import torch

from echopath.commands.train_cnn import _build_model


@pytest.mark.parametrize("architecture", ["lenet", "vgg", "resnet"])
def test_cnn_architecture_output_shape(architecture: str) -> None:
    model = _build_model(architecture, num_classes=8, n_mels=64, frames=128)
    output = model(torch.zeros(2, 1, 64, 128))
    assert output.shape == (2, 8)
