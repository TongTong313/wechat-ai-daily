# 里面存在GUI相关操作

from pynput.keyboard import Controller, Key
import pyautogui
from pathlib import Path
import logging
import time
import pyperclip

# ======================= GUI 按键操作 =======================

keyboard = Controller()


def press_keys(*keys: str):
    """同时按下多个按键（组合键）
    pynput 的 Key 属性包括：ctrl, alt, shift, cmd, enter, space, tab 等

    Args:
        *keys (str): 按键参数
    """
    # 记录按键操作
    keys_str = " + ".join(keys)
    logging.info(f"正在按下组合键: {keys_str}")

    # 将字符串转换为 Key 对象
    parsed_keys = []
    for k in keys:
        if hasattr(Key, k):
            parsed_keys.append(getattr(Key, k))
        else:
            parsed_keys.append(k)

    # 按下所有按键
    for k in parsed_keys:
        keyboard.press(k)

    # 释放所有按键（逆序）
    for k in reversed(parsed_keys):
        keyboard.release(k)

    logging.info(f"已成功按下并释放组合键: {keys_str}")


# ======================= 滚动操作 =======================


def scroll_down(amount: int = -800) -> None:
    """向下滚动页面

    使用 pyautogui.scroll() 实现页面滚动。
    负数表示向下滚动，正数表示向上滚动。

    Args:
        amount (int): 滚动量，默认为 -800（向下滚动约大半屏内容）
                - 负数：向下滚动
                - 正数：向上滚动
                - 数值越大，滚动距离越远
    """
    pyautogui.scroll(amount)


# ======================= 屏幕缩放比例操作 =======================

def get_screen_scale_ratio() -> tuple:
    """获取屏幕缩放比例

    用于处理 Retina 等高分辨率显示屏的坐标转换。
    截图使用物理像素，而点击使用逻辑坐标。

    Returns:
        tuple: (scale_x, scale_y) 缩放比例
    """
    screen_width, screen_height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    scale_x = screenshot.width / screen_width
    scale_y = screenshot.height / screen_height
    return scale_x, scale_y


# ======================= 截图操作 =======================

def screenshot_current_window(save_path: str) -> str:
    """截取当前屏幕截图并保存

    Args:
        save_path (str): 截图保存路径（必须提供）

    Returns:
        str: 截图保存路径
    """
    # 确保目录存在
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    # 截取屏幕并保存
    screenshot = pyautogui.screenshot()
    screenshot.save(save_path)
    logging.info(f"截图已保存到: {save_path}")

    return save_path


# ======================= 点击操作 =======================
def click_relative_position(rel_x: float, rel_y: float, click_delay: float = 0.5) -> None:
    """将相对坐标转换为屏幕逻辑坐标并点击

    VLM 返回的是相对坐标（0-1 范围），需要转换为实际屏幕坐标。
    同时需要处理高分辨率显示屏的缩放问题。

    转换流程：
    1. 获取截图尺寸（物理像素）
    2. 计算物理像素坐标 = 相对坐标 * 截图尺寸
    3. 获取屏幕缩放比例
    4. 转换为逻辑坐标 = 物理像素坐标 / 缩放比例
    5. 执行点击

    Args:
        rel_x (float): 相对 x 坐标 (0-1)
        rel_y (float): 相对 y 坐标 (0-1)
        click_delay (float): 点击后的延迟时间（秒），默认 0.5 秒
    """
    # 获取截图尺寸（物理像素）
    screenshot = pyautogui.screenshot()
    physical_x = rel_x * screenshot.width
    physical_y = rel_y * screenshot.height
    logging.info(
        f"相对坐标: ({rel_x:.4f}, {rel_y:.4f}) -> 物理像素: ({physical_x:.0f}, {physical_y:.0f})")

    # 获取缩放比例并转换为逻辑坐标
    scale_x, scale_y = get_screen_scale_ratio()
    click_x = int(physical_x / scale_x)
    click_y = int(physical_y / scale_y)
    logging.info(
        f"缩放比例: ({scale_x}, {scale_y}) -> 逻辑坐标: ({click_x}, {click_y})")

    # 执行点击
    pyautogui.click(click_x, click_y)
    time.sleep(click_delay)
    logging.info(f"已点击位置: ({click_x}, {click_y})")


def click_button_based_on_img(img_path: str, click_delay: float = 0.5) -> None:
    """根据图片路径点击按钮

    Args:
        img_path (str): 图片路径
        click_delay (float): 点击后的延迟时间（秒），默认 0.5 秒
    """

    button_location = pyautogui.locateOnScreen(img_path,
                                               confidence=0.8,
                                               grayscale=True)
    logging.info(f"图像识别结果: {button_location}")

    if button_location is None:
        logging.error(f"无法在屏幕上找到按钮")
        raise RuntimeError(f"无法在屏幕上找到目标按钮。\n"
                           f"请确保：\n"
                           f"1. 目标界面已显示\n"
                           f"2. 模板图片 {img_path} 存在\n"
                           f"3. 屏幕分辨率与模板图片匹配\n"
                           f"4. 可以尝试调整 confidence 参数（当前为 0.8）")

    # 获取按钮中心点的物理像素坐标
    center_x, center_y = pyautogui.center(button_location)
    logging.info(f"找到目标按钮，物理像素坐标: ({center_x}, {center_y})")

    # ============================================================
    # 显示屏坐标转换（处理 Retina 等高分辨率显示屏）
    # ============================================================
    # 问题背景：
    #   - macOS Retina 显示屏使用 2x 缩放（或更高）
    #   - pyautogui.screenshot() 返回的是物理像素（如 3840x2160）
    #   - pyautogui.locateOnScreen() 基于截图，返回物理像素坐标
    #   - pyautogui.click() 使用的是逻辑坐标（如 1920x1080）
    #
    # 如果不做转换：
    #   - 识别到物理像素坐标 (1765, 938)
    #   - 直接点击会被系统理解为逻辑坐标 (1765, 938)
    #   - 实际点击到物理像素 (3530, 1876)，位置完全错误！
    #
    # 解决方案：
    #   - 计算缩放比例 = 截图尺寸 / 逻辑屏幕尺寸
    #   - 将物理像素坐标除以缩放比例，得到正确的逻辑坐标
    # ============================================================

    # 获取逻辑屏幕尺寸和截图尺寸，计算缩放比例
    scale_x, scale_y = get_screen_scale_ratio()
    logging.info(f"屏幕缩放比例: x={scale_x}, y={scale_y}")

    # 将物理像素坐标转换为逻辑坐标
    click_x = int(center_x / scale_x)
    click_y = int(center_y / scale_y)
    logging.info(f"转换后的逻辑坐标: ({click_x}, {click_y})")

    # 使用逻辑坐标点击按钮
    pyautogui.click(click_x, click_y)
    time.sleep(click_delay)
    logging.info(f"已点击位置: ({click_x}, {click_y})")

# ======================= 复制操作 =======================


def copy_all_content(os_name: str, load_delay: float = 3.0, press_delay: float = 0.5) -> str:
    """复制当前页面全部内容，并返回内容文本

    步骤：
    1. 等待页面加载完成
    2. Ctrl+A 全选页面内容
    3. Ctrl+C 复制到剪贴板
    4. 从剪贴板读取内容并返回

    Args:
        os_name (str): 操作系统名称
        load_delay (float): 页面加载延迟时间（秒），默认 3.0 秒
        press_delay (float): 按键间隔时间（秒），默认 0.5 秒

    Returns:
        str: 页面内容文本
    """
    try:
        # 等待页面加载完成
        logging.info("等待页面加载...")
        time.sleep(load_delay)

        # 全选内容
        logging.info("正在全选页面内容 (Ctrl/cmd+A)...")
        if os_name == "darwin":
            press_keys("cmd", "a")
        else:
            press_keys("ctrl", "a")
        time.sleep(press_delay)

        # 复制内容
        logging.info("正在复制文章内容 (Ctrl/cmd+C)...")
        if os_name == "darwin":
            press_keys("cmd", "c")
        else:
            press_keys("ctrl", "c")
        time.sleep(press_delay)

        # 从剪贴板读取内容
        content = pyperclip.paste()
        logging.info(f"已复制页面内容，长度: {len(content)} 字符")

        return content

    except Exception as e:
        logging.exception("复制页面内容失败")
        raise
