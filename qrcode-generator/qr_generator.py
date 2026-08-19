# -*- coding: utf-8 -*-
"""二维码生成器（tkinter 桌面版）。

支持四种类型：
- 文本：直接编码输入的文字
- URL：直接编码 URL 文本
- 文件：编码本地文件的 file:/// URI
- 视频：编码本地视频的 file:/// URI

用法：
    python qr_generator.py
"""

import os
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import qrcode
from PIL import Image, ImageTk

# 预览显示尺寸（像素）
PREVIEW_SIZE = (400, 400)

# 视频文件选择器的扩展名过滤
VIDEO_FILETYPES = [
    ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.ts *.m4v *.3gp"),
    ("所有文件", "*.*"),
]
ALL_FILETYPES = [("所有文件", "*.*")]


def to_file_uri(path):
    """把本地文件路径转为 file:/// URI（如 file:///C:/Users/x/video.mp4）。"""
    return pathlib.Path(path).resolve().as_uri()


def build_qr_content(kind, value):
    """根据类型构造二维码要编码的内容。"""
    if kind in ("文本", "URL"):
        return value
    # 文件 / 视频：编码 file:// URI
    return to_file_uri(value)


def make_qr_image(content, box_size=12, border=4):
    """生成二维码，返回 PIL.Image。"""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)
    # make_image() 返回 PilImage 包装类，get_image() 取出真正的 PIL.Image
    return qr.make_image(fill_color="black", back_color="white").get_image()


class QRGeneratorApp:
    """tkinter 主窗口。"""

    def __init__(self, root):
        self.root = root
        self.root.title("二维码生成器")
        self.root.resizable(False, False)

        self.kind = tk.StringVar(value="URL")
        self.url_value = tk.StringVar()
        self.path_value = tk.StringVar()

        # 当前生成的二维码（PIL.Image），以及 tkinter 显示用的引用
        self.current_image = None
        self._photo = None

        self._build_ui()
        self._on_type_change()

    def _build_ui(self):
        # 类型选择
        ttk.Label(self.root, text="类型：").grid(
            row=0, column=0, padx=(12, 4), pady=(12, 4), sticky="w"
        )
        self.type_combo = ttk.Combobox(
            self.root,
            textvariable=self.kind,
            values=["文本", "URL", "文件", "视频"],
            state="readonly",
            width=12,
        )
        self.type_combo.grid(row=0, column=1, padx=4, pady=(12, 4), sticky="w")
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # URL 输入行
        self.url_label = ttk.Label(self.root, text="URL：")
        self.url_label.grid(row=1, column=0, padx=(12, 4), pady=4, sticky="w")
        self.url_entry = ttk.Entry(self.root, textvariable=self.url_value, width=45)
        self.url_entry.grid(row=1, column=1, padx=4, pady=4, sticky="we")

        # 文件 / 视频输入行
        self.path_label = ttk.Label(self.root, text="文件：")
        self.path_label.grid(row=2, column=0, padx=(12, 4), pady=4, sticky="w")
        self.path_entry = ttk.Entry(self.root, textvariable=self.path_value, width=35)
        self.path_entry.grid(row=2, column=1, padx=4, pady=4, sticky="we")
        self.browse_btn = ttk.Button(self.root, text="浏览…", command=self._browse)
        self.browse_btn.grid(row=2, column=2, padx=(4, 12), pady=4, sticky="e")

        # 操作按钮
        self.generate_btn = ttk.Button(
            self.root, text="生成二维码", command=self._generate
        )
        self.generate_btn.grid(row=3, column=0, columnspan=3, pady=(12, 4))

        self.save_btn = ttk.Button(
            self.root, text="保存图片", command=self._save, state="disabled"
        )
        self.save_btn.grid(row=4, column=0, columnspan=3, pady=4)

        # 预览区
        self.preview_label = ttk.Label(
            self.root, text="（二维码预览将显示在这里）", anchor="center"
        )
        self.preview_label.grid(row=5, column=0, columnspan=3, padx=12, pady=(4, 12))

        self.root.columnconfigure(1, weight=1)

    def _on_type_change(self, event=None):
        """切换类型时，显示/隐藏对应的输入行并更新标签。"""
        kind = self.kind.get()
        if kind in ("文本", "URL"):
            self.path_label.grid_remove()
            self.path_entry.grid_remove()
            self.browse_btn.grid_remove()
            self.url_label.config(text="文本：" if kind == "文本" else "URL：")
            self.url_label.grid()
            self.url_entry.grid()
        else:
            self.url_label.grid_remove()
            self.url_entry.grid_remove()
            self.path_label.config(text="视频：" if kind == "视频" else "文件：")
            self.path_label.grid()
            self.path_entry.grid()
            self.browse_btn.grid()

    def _browse(self):
        """弹出文件选择对话框。"""
        filetypes = VIDEO_FILETYPES if self.kind.get() == "视频" else ALL_FILETYPES
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.path_value.set(path)

    def _generate(self):
        """校验输入并生成二维码，显示在预览区。"""
        kind = self.kind.get()

        if kind in ("文本", "URL"):
            value = self.url_value.get().strip()
            if not value:
                messagebox.showwarning("提示", "请输入内容")
                return
            content = value
        else:
            path = self.path_value.get().strip()
            if not path:
                messagebox.showwarning("提示", "请先选择文件")
                return
            if not os.path.exists(path):
                messagebox.showerror("错误", f"文件不存在：\n{path}")
                return
            content = build_qr_content(kind, path)

        try:
            image = make_qr_image(content)
        except qrcode.exceptions.DataOverflowError:
            messagebox.showerror("错误", "内容过长，超出了二维码容量")
            return

        self.current_image = image
        self._show_preview(image)
        self.save_btn.config(state="normal")

    def _show_preview(self, image):
        """把 PIL 图像缩放到预览尺寸并显示。"""
        preview = image.resize(PREVIEW_SIZE, Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(preview)
        self.preview_label.config(image=self._photo, text="")

    def _save(self):
        """把当前二维码保存为 PNG 文件。"""
        if self.current_image is None:
            return
        path = filedialog.asksaveasfilename(
            title="保存二维码",
            defaultextension=".png",
            initialfile="qrcode.png",
            filetypes=[("PNG 图片", "*.png")],
        )
        if path:
            self.current_image.save(path)
            messagebox.showinfo("完成", f"二维码已保存到：\n{path}")


def main():
    root = tk.Tk()
    QRGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
