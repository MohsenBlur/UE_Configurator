from ue_configurator.ui.utils import infer_cvar_type


def test_infer_int_range():
    dtype, vmin, vmax, options = infer_cvar_type("0-10", "5")
    assert dtype == "int" and vmin == 0 and vmax == 10 and options is None


def test_infer_float_default():
    dtype, vmin, vmax, options = infer_cvar_type("", "0.5")
    assert dtype == "float" and options is None


def test_infer_enum_string():
    dtype, vmin, vmax, options = infer_cvar_type("Low|High", "Low")
    assert dtype == "str" and options == ["Low", "High"]

