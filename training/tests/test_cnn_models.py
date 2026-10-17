import pytest
import torch

from echopath.commands.train_cnn import _build_model


@pytest.mark.parametrize("architecture", ["lenet", "vgg", "resnet"])
def test_cnn_architecture_output_shape(architecture: str) -> None:
    model = _build_model(architecture, num_classes=8, n_mels=64, frames=128)
    output = model(torch.zeros(2, 1, 64, 128))
    assert output.shape == (2, 8)


def test_default_frames_cover_full_clip(tmp_path) -> None:
    import numpy as np
    import soundfile as sf

    from echopath.commands.train_cnn import _frames
    from echopath.mel import frames_for_duration, load_or_compute

    class Args:
        frames = None
        audio_duration = 30.0
        sample_rate = 22_050

    assert _frames(Args()) == frames_for_duration(30.0, 22_050) == 1292

    audio = tmp_path / "clip.wav"
    sf.write(audio, np.sin(np.linspace(0, 2_000, 22_050 * 30)).astype(np.float32), 22_050)
    array = load_or_compute(tmp_path / "cache", audio, 22_050, 30.0, 64, 1292)
    assert array.shape == (1, 64, 1292)
    assert np.isfinite(array).all()


@pytest.mark.parametrize("architecture", ["lenet", "vgg", "resnet"])
def test_cnn_architectures_accept_full_clip(architecture: str) -> None:
    model = _build_model(architecture, num_classes=8, n_mels=64, frames=1292)
    output = model(torch.zeros(2, 1, 64, 1292))
    assert output.shape == (2, 8)
