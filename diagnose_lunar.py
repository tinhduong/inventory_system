import vnlunar, datetime
day, month, year = 26, 12, 1990
start_dt = datetime.datetime(year, month, 1)
print(f"Searching for Lunar {day}/{month}/{year} starting from {start_dt}")
for offset in range(-60, 150): # Expanded range
    check_dt = start_dt + datetime.timedelta(days=offset)
    res = vnlunar.get_lunar_date(check_dt.day, check_dt.month, check_dt.year)
    if res['day'] == day and res['month'] == month and res['year'] == year:
        print(f"Found: {check_dt.strftime('%Y-%m-%d')}")
        break
else:
    print("Not found")
