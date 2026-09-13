import numpy as np
import pytest
from PIL import Image, ImageCms

from polaroid_split.cli import main
from polaroid_split.image_io import effective_dpi, expand_box, load_scan, split_scan


def test_dpi_and_margin():
    image = Image.new("RGB", (5100, 7016))
    assert effective_dpi(image) == (600, 600)
    image.info["dpi"] = (300, 150)
    assert effective_dpi(image) == (300, 150)
    image.info["dpi"] = (float("nan"), 0)
    assert effective_dpi(image) == (600, 600)
    assert expand_box((20, 20, 100, 100), 0.5, (600, 600), image.size) == (8, 8, 112, 112)
    with pytest.raises(ValueError, match="beyond"):
        expand_box((0, 0, 10, 10), 0.5, (600, 600), image.size)


def test_pixels_metadata_and_conflict(scan_factory, tmp_path):
    source = tmp_path / "a scan.png"
    image = scan_factory((0, 3))
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    exif = Image.Exif()
    exif[274] = 1
    exif[256] = 510
    image.save(source, dpi=(60, 60), icc_profile=profile, exif=exif)
    output = tmp_path / "outputs"
    paths, empty = split_scan(source, output, 0)
    assert len(paths) == 2 and empty == ["top-right", "bottom-left"]
    with Image.open(paths[0]) as crop:
        np.testing.assert_array_equal(np.asarray(crop), np.asarray(image)[42:296, 35:244])
        assert crop.info["icc_profile"] == profile
        assert crop.info["dpi"] == pytest.approx((60, 60), abs=0.02)
        assert not crop.getexif()
    before = {path: path.read_bytes() for path in paths}
    with pytest.raises(FileExistsError):
        split_scan(source, output, 0)
    assert all(path.read_bytes() == data for path, data in before.items())


def test_exif_orientation_and_dpi_swap(tmp_path):
    source = tmp_path / "oriented.tif"
    image = Image.new("RGB", (702, 510), "red")
    exif = Image.Exif()
    exif[274] = 6
    # PNG leaves orientation for the explicit transpose rather than TIFF decoder handling.
    source = source.with_suffix(".png")
    image.save(source, exif=exif, dpi=(120, 60))
    with load_scan(source) as result:
        assert result.size == (510, 702)
        assert effective_dpi(result) == pytest.approx((60, 120), abs=0.02)
        assert result.getexif().get(274) is None


def test_multipage_tiff(tmp_path):
    source = tmp_path / "pages.tiff"
    image = Image.new("RGB", (510, 702))
    image.save(source, save_all=True, append_images=[image])
    with pytest.raises(ValueError, match="multi-page"):
        load_scan(source)


def test_batch_continues_and_is_nonrecursive(scan_factory, tmp_path, capsys):
    (tmp_path / "a-broken.jpg").write_bytes(b"broken")
    scan_factory((0,)).save(tmp_path / "b good.png")
    subfolder = tmp_path / "nested"
    subfolder.mkdir()
    scan_factory().save(subfolder / "hidden.png")
    assert main([str(tmp_path)]) == 1
    assert len(list((tmp_path / "split").glob("*.png"))) == 1
    assert "a-broken.jpg" in capsys.readouterr().err


@pytest.mark.parametrize("margin", ["-1", "nan", "inf", "abc"])
def test_invalid_margin(margin):
    with pytest.raises(SystemExit) as error:
        main(["unused", "--margin-mm", margin])
    assert error.value.code == 2


def test_uncertain_writes_nothing(scan_factory, tmp_path):
    from PIL import ImageDraw

    image = scan_factory()
    ImageDraw.Draw(image).rectangle((35, 42, 240, 280), fill="black")
    source = tmp_path / "uncertain.png"
    image.save(source)
    with pytest.raises(ValueError, match="uncertain"):
        split_scan(source, tmp_path / "out", 0)
    assert not (tmp_path / "out").exists()


def test_failed_publication_rolls_back(scan_factory, tmp_path, monkeypatch):
    from polaroid_split import image_io

    source = tmp_path / "scan.png"
    scan_factory().save(source)
    real_link = image_io.os.link
    calls = 0

    def fail_second(src, dst):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated publication failure")
        real_link(src, dst)

    monkeypatch.setattr(image_io.os, "link", fail_second)
    output = tmp_path / "out"
    with pytest.raises(OSError, match="simulated"):
        split_scan(source, output, 0)
    assert list(output.iterdir()) == []
