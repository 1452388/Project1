# -*- coding: utf-8 -*-
"""二维码生成服务：qrcode + Pillow，支持尺寸、Logo、边框文字。"""

import io
import zipfile
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.schemas import QRConfig

# Logo 占二维码主体的比例（不宜过大，否则影响识别）
LOGO_RATIO = 0.22
# 边框文字的字体大小（相对二维码尺寸）
CAPTION_FONT_RATIO = 0.08


class QRService:
    """二维码生成核心逻辑。"""

    SIZE_MAP = settings.QR_SIZES  # {"small": 200, "medium": 400, "large": 600}
    BOX_SIZE_MAP = {"small": 6, "medium": 12, "large": 18}
    BORDER = 4

    @staticmethod
    def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """加载中文字体；找不到时退回默认字体。"""
        import platform
        system = platform.system()
        # 跨平台字体路径
        if system == "Windows":
            candidates = [
                Path("C:/Windows/Fonts/msyh.ttc"),      # 微软雅黑
                Path("C:/Windows/Fonts/simhei.ttf"),    # 黑体
                Path("C:/Windows/Fonts/simsun.ttc"),    # 宋体
            ]
        elif system == "Darwin":  # macOS
            candidates = [
                Path("/System/Library/Fonts/STHeiti Light.ttc"),
                Path("/System/Library/Fonts/PingFang.ttc"),
            ]
        else:  # Linux / Vercel
            candidates = [
                Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
                Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            ]
        for font_path in candidates:
            if font_path.exists():
                try:
                    return ImageFont.truetype(str(font_path), size)
                except OSError:
                    continue
        return ImageFont.load_default()

    @classmethod
    def generate(cls, content: str, config: QRConfig | None = None) -> Image.Image:
        """生成二维码 PIL Image（含可选 Logo 与边框文字）。"""
        config = config or QRConfig()
        size = cls.SIZE_MAP.get(config.size, cls.SIZE_MAP["medium"])
        box_size = cls.BOX_SIZE_MAP.get(config.size, cls.BOX_SIZE_MAP["medium"])

        # 1. 生成基础二维码（PIL 图像）
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # 高容错，容纳 Logo
            box_size=box_size,
            border=cls.BORDER,
        )
        qr.add_data(content)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # 2. 缩放至目标尺寸
        qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)

        # 3. 嵌入 Logo
        if config.logo_path:
            logo_path = Path(config.logo_path)
            if logo_path.exists():
                qr_image = cls._add_logo(qr_image, logo_path)

        # 4. 添加边框文字（画布整体增高一行文字高度）
        if config.caption:
            qr_image = cls._add_caption(qr_image, config.caption, size)

        return qr_image

    @staticmethod
    def _add_logo(qr_image: Image.Image, logo_path: Path) -> Image.Image:
        """在二维码中心嵌入 Logo，Logo 表面加白底圆角边框增强识别。"""
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = int(qr_image.width * LOGO_RATIO)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

        # 白底圆角 padding（与二维码同色背景区域对齐）
        pad = int(logo_size * 0.12)
        total = logo_size + pad * 2
        frame = Image.new("RGBA", (total, total), (255, 255, 255, 255))
        frame.paste(logo, (pad, pad), logo)

        pos = ((qr_image.width - total) // 2, (qr_image.height - total) // 2)
        qr_image.paste(frame, pos, frame)
        return qr_image

    @classmethod
    def _add_caption(cls, qr_image: Image.Image, caption: str, qr_size: int) -> Image.Image:
        """在二维码上方绘制边框文字，返回增高后的画布。"""
        font_size = max(int(qr_size * CAPTION_FONT_RATIO), 14)
        font = cls._load_font(font_size)
        # 测量文字宽度，不足时画布加宽
        dummy = ImageDraw.Draw(qr_image)
        text_bbox = dummy.textbbox((0, 0), caption, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        canvas_width = max(qr_image.width, text_width + font_size * 2)
        # 顶部预留：文字高度 + 上下间距
        top_margin = text_height + int(font_size * 0.8)
        canvas = Image.new("RGB", (canvas_width, qr_image.height + top_margin), "white")
        canvas.paste(qr_image, ((canvas_width - qr_image.width) // 2, top_margin))

        draw = ImageDraw.Draw(canvas)
        text_x = (canvas_width - text_width) // 2
        # 修正 bbox baseline 偏移
        text_y = (top_margin - text_height) // 2 - text_bbox[1]
        draw.text((text_x, text_y), caption, fill="black", font=font)
        return canvas

    @classmethod
    def to_png_bytes(cls, image: Image.Image) -> bytes:
        """PIL Image → PNG bytes。"""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    @classmethod
    def batch_generate_zip(
        cls, items: list[tuple[str, str, QRConfig]]
    ) -> bytes:
        """批量生成：items = [(文件名, 内容, 配置), ...]，返回 ZIP bytes。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content, config in items:
                img = cls.generate(content, config)
                png = cls.to_png_bytes(img)
                zf.writestr(filename, png)
        return buf.getvalue()