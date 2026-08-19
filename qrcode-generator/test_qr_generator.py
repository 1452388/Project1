# -*- coding: utf-8 -*-
"""qr_generator 核心逻辑的单元测试。

运行：
    python test_qr_generator.py
"""

import os
import tempfile
import unittest

from PIL import Image

import qr_generator


class TestToFileUri(unittest.TestCase):
    def test_windows_path_becomes_file_uri(self):
        # 用临时文件确保路径存在，resolve() 行为稳定
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            path = f.name
        try:
            uri = qr_generator.to_file_uri(path)
            self.assertTrue(uri.startswith("file:///"), uri)
            self.assertIn("\\", path)  # Windows 反斜杠
            self.assertNotIn("\\", uri)  # URI 里应为正斜杠
            self.assertTrue(uri.endswith(".mp4"), uri)
        finally:
            os.remove(path)


class TestBuildQrContent(unittest.TestCase):
    def test_text_is_encoded_verbatim(self):
        self.assertEqual(
            qr_generator.build_qr_content("文本", "你好，世界"),
            "你好，世界",
        )

    def test_url_is_encoded_verbatim(self):
        self.assertEqual(
            qr_generator.build_qr_content("URL", "https://example.com"),
            "https://example.com",
        )

    def test_file_uses_file_uri(self):
        content = qr_generator.build_qr_content("文件", "C:\\x\\a.mp4")
        self.assertTrue(content.startswith("file:///"), content)

    def test_video_uses_file_uri(self):
        content = qr_generator.build_qr_content("视频", "C:\\x\\b.mp4")
        self.assertTrue(content.startswith("file:///"), content)


class TestMakeQrImage(unittest.TestCase):
    def test_returns_nonempty_image(self):
        img = qr_generator.make_qr_image("https://example.com")
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.size[0], 0)
        self.assertGreater(img.size[1], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
