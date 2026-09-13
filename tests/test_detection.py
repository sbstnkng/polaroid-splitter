import pytest
from PIL import Image, ImageDraw

from polaroid_split.detection import State, detect


@pytest.mark.parametrize("occupied", [(), (0,), (0, 3), (0, 1, 2, 3)])
def test_occupancy(scan_factory, occupied):
    slots = detect(scan_factory(occupied))
    assert [i for i, slot in enumerate(slots) if slot.state == State.OCCUPIED] == list(occupied)
    assert all(slot.state != State.UNCERTAIN for slot in slots)


@pytest.mark.parametrize("scale", [1, 2, 4])
@pytest.mark.parametrize("shift", [0, 6])
def test_coordinates_and_reversed_adapter_shift(scan_factory, scale, shift):
    slots = detect(scan_factory(scale=scale, shift=shift))
    assert all(slot.state == State.OCCUPIED for slot in slots)
    assert slots[0].box == (35 * scale, (42 + shift) * scale, 244 * scale, (296 + shift) * scale)


def test_incomplete_rectangle_is_uncertain(scan_factory):
    image = scan_factory(())
    ImageDraw.Draw(image).rectangle((35, 42, 100, 295), fill="white")
    assert detect(image)[0].state == State.UNCERTAIN


def test_empty_dark_adapter():
    assert all(slot.state == State.EMPTY for slot in detect(Image.new("RGB", (510, 702))))


def test_wrong_framing():
    with pytest.raises(ValueError, match="framing"):
        detect(Image.new("RGB", (500, 500)))
