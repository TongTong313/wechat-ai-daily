# 里面存在GUI相关操作

from pynput.keyboard import Controller, Key

# ======================= GUI 按键操作 =======================

keyboard = Controller()


def press_keys(*keys: str):
    """同时按下多个按键（组合键）
    pynput 的 Key 属性包括：ctrl, alt, shift, cmd, enter, space, tab 等

    Args:
        *keys (str): 按键参数
    """
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
