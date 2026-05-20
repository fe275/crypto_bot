def format_price(p):
    if p >= 1:
        return f"{p:,.2f}"
    return f"{p:.6f}"
