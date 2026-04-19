import math

def INT(n):
    return math.floor(n)

def get_julian_day(d, m, y):
    a = INT((14 - m) / 12)
    y = y + 4800 - a
    m = m + 12 * a - 3
    return d + INT((153 * m + 2) / 5) + 365 * y + INT(y / 4) - INT(y / 100) + INT(y / 400) - 32045

def get_solar_day(jd):
    l = jd + 68569
    n = INT((4 * l) / 146097)
    l = l - INT((146097 * n + 3) / 4)
    i = INT((4000 * (l + 1)) / 1461001)
    l = l - INT((1461 * i) / 4) + 31
    j = INT((80 * l) / 2447)
    d = l - INT((2447 * j) / 80)
    l = INT(j / 11)
    m = j + 2 - 12 * l
    y = 100 * (n - 49) + i + l
    return d, m, y

def get_new_moon(k):
    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    return 2451550.09765 + 29.530588853 * k + 0.0001337 * t2 - 0.00000015 * t3 + 0.00073 * math.sin((201.56 + 1.178 * k) * math.pi / 180)

def get_sun_longitude(jdn):
    t = (jdn - 2451545.0) / 36525.0
    l = 280.46645 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52910 + 35999.05030 * t - 0.0001559 * t * t - 0.00000045 * t * t * t
    c = (1.914602 - 0.004817 * t) * math.sin(m * math.pi / 180) + 0.019993 * math.sin(2 * m * math.pi / 180)
    return (l + c) % 360

def get_lunar_month_11(y, timezone=7):
    k = INT((y - 2000) * 12.3685)
    nm = get_new_moon(k)
    off = timezone / 24.0
    sun_long = get_sun_longitude(nm - 0.5 + off)
    if sun_long >= 285: k -= 1
    elif sun_long < 255: k += 1
    return INT(get_new_moon(k) + 0.5 + off)

def get_leap_month_offset(a11, timezone=7):
    k = INT((a11 - 2451550.0) / 29.530588853 + 0.5)
    last = -1
    off = timezone / 24.0
    for i in range(1, 15):
        nm = get_new_moon(k + i)
        lon = get_sun_longitude(nm - 0.5 + off)
        s = INT(lon / 30)
        if s == last: return i
        last = s
    return 0

def convert_solar_to_lunar(dd, mm, yy, timezone=7):
    jd = get_julian_day(dd, mm, yy)
    k = INT((jd - 2451550.0) / 29.530588853)
    off = timezone / 24.0
    nm = get_new_moon(k)
    if INT(nm + 0.5 + off) > jd: nm = get_new_moon(k - 1)
    
    a11 = get_lunar_month_11(yy, timezone)
    if a11 > jd: a11 = get_lunar_month_11(yy - 1, timezone)
    
    k_a11 = INT((a11 - 2451550) / 29.530588853 + 0.5)
    k_jd = INT((jd - 2451550) / 29.530588853)
    diff = k_jd - k_a11
    month_start = INT(get_new_moon(k_a11 + diff) + 0.5 + off)
    if month_start > jd:
        diff -= 1
        month_start = INT(get_new_moon(k_a11 + diff) + 0.5 + off)
    
    lunar_day = jd - month_start + 1
    leap_off = get_leap_month_offset(a11, timezone)
    lunar_leap = False
    
    if leap_off > 0 and diff >= leap_off:
        lunar_month = (diff + 10) % 12 + 1
        if diff == leap_off: lunar_leap = True
        elif diff > leap_off: lunar_month = (diff + 9) % 12 + 1
    else:
        lunar_month = (diff + 10) % 12 + 1
    
    lunar_year = yy
    a11_prev = get_lunar_month_11(yy - 1, timezone)
    k_m11_prev = INT((a11_prev - 2451550.0) / 29.530588853 + 0.5)
    leap_prev = get_leap_month_offset(a11_prev, timezone)
    m1_k = k_m11_prev + (3 if leap_prev > 0 else 2)
    nm1 = INT(get_new_moon(m1_k) + 0.5 + off)
    if jd < nm1: lunar_year = yy - 1
    
    return lunar_day, lunar_month, lunar_year, lunar_leap

def convert_lunar_to_solar(ld, lm, ly, lleap=False, timezone=7):
    off = timezone / 24.0
    a11 = get_lunar_month_11(ly, timezone)
    if lm == 11 or lm == 12:
        _, _, solar_year = get_solar_day(a11)
        if ly <= solar_year: a11 = get_lunar_month_11(ly - 1, timezone)
    else:
        a11 = get_lunar_month_11(ly - 1, timezone)
    
    k = INT((a11 - 2451550.0) / 29.530588853 + 0.5)
    leap_off = get_leap_month_offset(a11, timezone)
    diff = (lm - 11) if lm >= 11 else (lm + 1)
    if leap_off > 0 and (diff > leap_off or (diff == leap_off and lleap)):
        diff += 1
    
    nm = get_new_moon(k + diff)
    jd = INT(nm + 0.5 + off) + ld - 1
    return get_solar_day(jd)
