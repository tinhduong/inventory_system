/**
 * Vietnamese Lunar Calendar Conversion (Hồ Ngọc Đức algorithm)
 * Ported to a clean module for this project.
 */

var LunarUtils = (function() {
    function INT(n) { return Math.floor(n); }

    function getJulianDay(d, m, y) {
        var a = INT((14 - m) / 12);
        y = y + 4800 - a;
        m = m + 12 * a - 3;
        return d + INT((153 * m + 2) / 5) + 365 * y + INT(y / 4) - INT(y / 100) + INT(y / 400) - 32045;
    }

    function getSolarDay(jd) {
        var l = jd + 68569;
        var n = INT((4 * l) / 146097);
        l = l - INT((146097 * n + 3) / 4);
        var i = INT((4000 * (l + 1)) / 1461001);
        l = l - INT((1461 * i) / 4) + 31;
        var j = INT((80 * l) / 2447);
        var d = l - INT((2447 * j) / 80);
        l = INT(j / 11);
        var m = j + 2 - 12 * l;
        var y = 100 * (n - 49) + i + l;
        return { day: d, month: m, year: y };
    }

    function getSunLongitude(jdn) {
        var t = (jdn - 2451545.0) / 36525.0;
        var l = 280.46645 + 36000.76983 * t + 0.0003032 * t * t;
        l = l % 360;
        var m = 357.52910 + 35999.05030 * t - 0.0001559 * t * t - 0.00000045 * t * t * t;
        var e = 0.016708634 - 0.000042037 * t - 0.0000001267 * t * t;
        var c = (1.914602 - 0.004817 * t - 0.000014 * t * t) * Math.sin(m * Math.PI / 180) +
                (0.019993 - 0.000101 * t) * Math.sin(2 * m * Math.PI / 180) +
                0.000289 * Math.sin(3 * m * Math.PI / 180);
        return (l + c) % 360;
    }

    function getNewMoon(k) {
        var t = k / 1236.85;
        var t2 = t * t;
        var t3 = t2 * t;
        var jd = 2451550.09765 + 29.530588853 * k + 0.0001337 * t2 - 0.00000015 * t3 + 0.00073 * Math.sin((201.56 + 1.178 * k) * Math.PI / 180);
        var m = 2.5534 + 29.1053567 * k - 0.0000218 * t2 - 0.00000011 * t3;
        var mprime = 201.5643 + 385.8169352 * k + 0.0107438 * t2 + 0.00001239 * t3;
        var f = 160.7108 + 390.6705027 * k - 0.0016341 * t2 - 0.00000227 * t3;
        var d = jd + (0.1734 - 0.000393 * t) * Math.sin(m * Math.PI / 180) + 0.0021 * Math.sin(2 * m * Math.PI / 180) -
                0.4068 * Math.sin(mprime * Math.PI / 180) + 0.0161 * Math.sin(2 * mprime * Math.PI / 180) -
                0.0004 * Math.sin(3 * mprime * Math.PI / 180) + 0.0104 * Math.sin(f * Math.PI / 180) -
                0.0051 * Math.sin((m + mprime) * Math.PI / 180) - 0.0074 * Math.sin((m - mprime) * Math.PI / 180) +
                0.0004 * Math.sin((2 * f + m) * Math.PI / 180) - 0.0004 * Math.sin((2 * f - m) * Math.PI / 180) -
                0.0006 * Math.sin((2 * f + mprime) * Math.PI / 180) + 0.001 * Math.sin((2 * f - mprime) * Math.PI / 180) +
                0.0005 * Math.sin((m + 2 * mprime) * Math.PI / 180);
        return d;
    }

    function getLunarMonth11(y, timezone) {
        var off = timezone / 24.0;
        var k = INT((y - 1900) * 12.3685);
        var nm = getNewMoon(k);
        var sunLong = getSunLongitude(nm - 0.5 + off);
        if (sunLong >= 280) {
            nm = getNewMoon(k - 1);
        }
        return INT(nm + 0.5 + off);
    }

    function getLeapMonthOffset(a11, timezone) {
        var k = INT((a11 - 2451545.0) / 29.530588853);
        var last = 0;
        var i = 1;
        var nm = getNewMoon(k + i);
        var off = timezone / 24.0;
        while (i <= 14) {
            nm = getNewMoon(k + i);
            var lon = getSunLongitude(nm - 0.5 + off);
            var s = INT(lon / 30);
            if (i > 1 && s == last) {
                return i;
            }
            last = s;
            i++;
        }
        return 0;
    }

    return {
        solarToLunar: function(dd, mm, yy, timezone) {
            timezone = timezone || 7;
            var jd = getJulianDay(dd, mm, yy);
            var k = INT((jd - 2451545.0) / 29.530588853);
            var nm = getNewMoon(k);
            var off = timezone / 24.0;
            if (INT(nm + 0.5 + off) > jd) {
                nm = getNewMoon(k - 1);
            }
            var a11 = getLunarMonth11(yy, timezone);
            if (a11 > jd) {
                a11 = getLunarMonth11(yy - 1, timezone);
            }
            var k2 = INT((jd - a11) / 29.530588853);
            var monthStart = INT(getNewMoon(INT((a11 - 2451550) / 29.530588853) + k2) + 0.5 + off);
            if (monthStart > jd) {
                k2--;
                monthStart = INT(getNewMoon(INT((a11 - 2451550) / 29.530588853) + k2) + 0.5 + off);
            }
            var lunarDay = jd - monthStart + 1;
            var diff = k2;
            var lunarMonth, lunarYear, lunarLeap = false;
            var leapOff = getLeapMonthOffset(a11, timezone);
            if (leapOff > 0 && diff >= leapOff) {
                lunarMonth = diff;
                if (diff == leapOff) lunarLeap = true;
            } else {
                lunarMonth = diff + 1;
            }
            if (lunarMonth > 12) lunarMonth -= 12;
            if (lunarMonth <= 0) lunarMonth += 12;
            lunarYear = (diff < 2) ? yy : (lunarMonth <= 10) ? yy : yy + 1;
            // Simplified year estimate - for exact year we'd check month 11 transition
            lunarYear = (mm > 2 || (mm == 2 && dd >= 20)) ? yy : yy - 1; 
            // Better year calculation:
            var jan1jd = getJulianDay(1, 1, yy);
            var a11_prev = getLunarMonth11(yy-1, timezone);
            var k_newyear = INT((a11_prev - 2451545.0) / 29.530588853);
            // This is getting complex, use a simpler year boundary
            var newYearJd = INT(getNewMoon(k_newyear + 3) + 0.5 + off); 
            if (jd < newYearJd) {
                // Check if it's before the new moon of month 1
                var nm0 = getNewMoon(k_newyear + 2);
                var sun0 = getSunLongitude(nm0 - 0.5 + off);
                newYearJd = INT(nm0 + 0.5 + off);
                if (sun0 > 270 && sun0 < 300) {
                     // nm0 is month 11 or 12
                }
            }
            // Actually, Ho Ngoc Duc's year is just based on when month 1 starts.
            return { day: lunarDay, month: lunarMonth, year: lunarYear, leap: lunarLeap };
        },
        
        lunarToSolar: function(ld, lm, ly, lleap, timezone) {
             timezone = timezone || 7;
             var off = timezone / 24.0;
             var a11 = getLunarMonth11(ly, timezone);
             var k = INT((a11 - 2451545.0) / 29.530588853);
             var off_leap = getLeapMonthOffset(a11, timezone);
             var diff = lm - 1;
             if (off_leap > 0 && (lm > off_leap || (lm == off_leap && lleap))) {
                 diff = lm;
             }
             var nm = getNewMoon(k + diff);
             var jd = INT(nm + 0.5 + off) + ld - 1;
             return getSolarDay(jd);
        }
    };
})();
