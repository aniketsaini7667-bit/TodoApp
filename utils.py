def hex_to_rgba(hex_color, default=(220, 53, 69, 255)):
    hex_color = hex_color.strip().lstrip('#')
    try:
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    except:
        pass
    return default
