/**
 * Vietnamese Lunar Calendar Conversion (Hồ Ngọc Đức algorithm)
 * FIXED getLunarMonth11 logic where k was not updated correctly.
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

    function getNewMoon(k) {
        var t = k / 1236.85;
        var t2 = t * t;
        var t3 = t2 * t;
        return 2451550.09765 + 29.530588853 * k + 0.0001337 * t2 - 0.00000015 * t3 + 0.00073 * Math.sin((201.56 + 1.178 * k) * Math.PI / 180);
    }

    function getSunLongitude(jdn) {
        var t = (jdn - 2451545.0) / 36525.0;
        var l = 280.46645 + 36000.76983 * t + 0.0003032 * t * t;
        var m = 357.52910 + 35999.05030 * t - 0.0001559 * t * t - 0.00000045 * t * t * t;
        var c = (1.914602 - 0.004817 * t) * Math.sin(m * Math.PI / 180) + 0.019993 * Math.sin(2 * m * Math.PI / 180);
        return (l + c) % 360;
    }
    
    function getLunarMonth11(y, timezone) {
        var k = INT((y - 2000) * 12.3685);
        var nm = getNewMoon(k);
        var off = timezone / 24.0;
        var sunLong = getSunLongitude(nm - 0.5 + off);
        if (sunLong >= 285) k -= 1;
        else if (sunLong < 255) k += 1;
        return INT(getNewMoon(k) + 0.5 + off);
    }

    function getLeapMonthOffset(a11, timezone) {
        var k = INT((a11 - 2451550.0) / 29.530588853 + 0.5);
        var last = -1;
        var off = timezone / 24.0;
        for (var i = 1; i <= 14; i++) {
            var nm = getNewMoon(k + i);
            var lon = getSunLongitude(nm - 0.5 + off);
            var s = INT(lon / 30);
            if (s == last) return i;
            last = s;
        }
        return 0;
    }

    return {
        solarToLunar: function(dd, mm, yy, timezone) {
            timezone = timezone || 7;
            var jd = getJulianDay(dd, mm, yy);
            var k = INT((jd - 2451550.0) / 29.530588853);
            var off = timezone / 24.0;
            var nm = getNewMoon(k);
            if (INT(nm + 0.5 + off) > jd) nm = getNewMoon(k - 1);
            
            var a11 = getLunarMonth11(yy, timezone);
            if (a11 > jd) a11 = getLunarMonth11(yy - 1, timezone);
            
            var k_a11 = INT((a11 - 2451550) / 29.530588853 + 0.5);
            var k_jd = INT((jd - 2451550) / 29.530588853);
            var diff = k_jd - k_a11;
            var monthStart = INT(getNewMoon(k_a11 + diff) + 0.5 + off);
            if (monthStart > jd) {
                diff--;
                monthStart = INT(getNewMoon(k_a11 + diff) + 0.5 + off);
            }
            
            var lunarDay = jd - monthStart + 1;
            var leapOff = getLeapMonthOffset(a11, timezone);
            var lunarMonth, lunarLeap = false;
            
            if (leapOff > 0 && diff >= leapOff) {
                lunarMonth = (diff + 10) % 12 + 1;
                if (diff == leapOff) lunarLeap = true;
                else if (diff > leapOff) lunarMonth = (diff + 9) % 12 + 1;
            } else {
                lunarMonth = (diff + 10) % 12 + 1;
            }
            
            var lunarYear = yy;
            var a11_prev = getLunarMonth11(yy - 1, timezone);
            var k_m11_prev = INT((a11_prev - 2451550.0) / 29.530588853 + 0.5);
            var leap_prev = getLeapMonthOffset(a11_prev, timezone);
            var nm1 = INT(getNewMoon(k_m11_prev + (leap_prev > 0 ? 3 : 2)) + 0.5 + off);
            if (jd < nm1) lunarYear = yy - 1;

            return { day: lunarDay, month: lunarMonth, year: lunarYear, leap: lunarLeap };
        },

        lunarToSolar: function(ld, lm, ly, lleap, timezone) {
            timezone = timezone || 7;
            var off = timezone / 24.0;
            var a11 = (lm >= 11) ? getLunarMonth11(ly, timezone) : getLunarMonth11(ly-1, timezone);
            
            var k = INT((a11 - 2451550.0) / 29.530588853 + 0.5);
            var leapOff = getLeapMonthOffset(a11, timezone);
            
            var diff = (lm >= 11) ? (lm - 11) : (lm + 1);
            if (leapOff > 0 && (diff > leapOff || (diff == leapOff && lleap))) {
                diff++;
            }
            
            var nm = getNewMoon(k + diff);
            var jd = INT(nm + 0.5 + off) + ld - 1;
            return getSolarDay(jd);
        }
    };
})();
