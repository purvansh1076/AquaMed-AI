from app.data.fao56_penman_monteith import calculate_fao56_et0


def test_et0_bounds_indian_summer():
    et0 = calculate_fao56_et0(
        lat_deg=19.0,
        day_of_year=120,
        t_min=22.0,
        t_max=38.0,
        t_mean=30.0,
        rh_mean=45.0,
        wind_2m=2.0,
        rs_mj=22.0,
        elevation_m=540.0,
    )
    assert 0.0 <= et0 <= 15.0
    assert et0 > 0.0


def test_et0_zero_solar_nonnegative():
    et0 = calculate_fao56_et0(
        lat_deg=19.0,
        day_of_year=120,
        t_min=20.0,
        t_max=30.0,
        t_mean=25.0,
        rh_mean=60.0,
        wind_2m=1.0,
        rs_mj=0.0,
        elevation_m=540.0,
    )
    assert et0 >= 0.0
